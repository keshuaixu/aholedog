from typing import List

import numpy as np
from scipy import signal
from collections import namedtuple
import itertools
import matplotlib.pyplot as plt
import threading

from aholedog.delta_kinematics import inverse_arr, UnsolvableIKError
from aholedog.robot_kinematics import convert_motor_position_vect, MotorPositionOutOfRangeError, convert_motor_position

Step = namedtuple('Step', ['x', 'y', 'rz', 'body_z', 'lift_z', 'period'])
comfy_z = -50


def synth_walk(z, lift_height, period, dt, prev_step: Step, this_step: Step, **kwargs):
    t = np.linspace(0, period, period / dt, endpoint=False)

    z_waveform = signal.square(2.00001 * np.pi * 1 * t)
    z_1 = z + (z_waveform * 0.5 + 1) * lift_height
    z_3 = z_1
    z_2 = z + ((-1) * z_waveform * 0.5 + 1) * lift_height
    z_4 = z_2

    half_t = int(len(t) / 2)
    x_1 = x_3 = np.hstack((np.linspace(- prev_step.x / 2, this_step.x / 2, half_t),
                           np.linspace(this_step.x / 2, -this_step.x / 2, len(t) - half_t)))
    y_1 = y_3 = np.hstack((np.linspace(- prev_step.y / 2, this_step.y / 2, half_t),
                           np.linspace(this_step.y / 2, -this_step.y / 2, len(t) - half_t)))
    x_2 = x_4 = np.hstack((np.linspace(prev_step.x / 2, -this_step.x / 2, len(t) - half_t),
                           np.linspace(- this_step.x / 2, this_step.x / 2, half_t)
                           ))
    y_2 = y_4 = np.hstack((np.linspace(prev_step.y / 2, -this_step.y / 2, len(t) - half_t),
                           np.linspace(- this_step.y / 2, this_step.y / 2, half_t)
                           ))

    return t, np.vstack((x_1, y_1, z_1, x_2, y_2, z_2, x_3, y_3, z_3, x_4, y_4, z_4))


def synth_walk_debug(z, lift_height, period, dt, prev_step: Step, this_step: Step, **kwargs):
    t = np.linspace(0, period, period / dt, endpoint=False)
    # t=1

    # z_waveform = signal.square(2 * np.pi * 1 * t)
    # z_1 = z + (z_waveform * 0.5 + 1) * lift_height
    # z_3 = z_1
    # z_2 = z + ((-1) * z_waveform * 0.5 + 1) * lift_height
    # z_4 = z_2


    z_1 = z_2 = z_3 = z_4 = np.array([this_step.body_z] * t.shape[0])
    x_1 = x_2 = x_3 = x_4 = np.array([this_step.x] * t.shape[0])
    y_1 = y_2 = y_3 = y_4 = np.array([this_step.y] * t.shape[0])
    # x_2 = 0  # TODO
    # x_4 = x_2

    # y_4 = y_2

    return t, np.vstack((x_1, y_1, z_1, x_2, y_2, z_2, x_3, y_3, z_3, x_4, y_4, z_4))


class GaitGenerator:
    def __init__(self, synthesizer=synth_walk):
        self.lines = []
        self.current_cycle_t = 0
        self.current_cycle = np.empty((12, 0))
        self.current_cycle_unfiltered = np.empty((12, 0))
        self.current_step = self.input_step = Step(0, 0, 0, comfy_z, 0, 1)
        self.next_cycle = np.empty((12, 0))
        self.next_cycle_unfiltered = np.empty((12, 0))
        self.combined_cycle = np.empty((12, 0))
        self.lock = threading.RLock()
        b, a = signal.butter(1, 0.2, output='ba')
        self.filter = lambda x: signal.filtfilt(b, a, x, axis=1)
        self.motor_position = np.empty((12, 0))
        self.raw_motor_position = np.empty((12, 0))
        self.synthesizer = synthesizer

    def step(self):
        with self.lock:
            self.current_cycle_t += 1
            if self.current_cycle_t >= self.current_cycle.shape[1]:
                self.current_cycle = self.next_cycle
                self.current_cycle_t = 0
                self.current_cycle_unfiltered = self.next_cycle_unfiltered
                self.current_step = self.input_step

    def update(self, step: Step):
        self.input_step = step
        with self.lock:
            _, self.next_cycle_unfiltered = self.synthesizer(z=step.body_z, lift_height=step.lift_z, period=step.period,
                                                             dt=0.02,
                                                             prev_step=self.current_step,
                                                             this_step=step)
            if self.current_cycle_unfiltered.shape[1] == 0:
                self.current_cycle_unfiltered = self.next_cycle_unfiltered

            filtered = self.filter(np.hstack((self.current_cycle_unfiltered, self.next_cycle_unfiltered)))
            self.current_cycle = filtered[:, :self.current_cycle_unfiltered.shape[1] - 1]
            self.next_cycle = filtered[:, self.current_cycle_unfiltered.shape[1]:]
            self.combined_cycle = filtered
            try:
                self.motor_position = inverse_arr(filtered)
                raw_motor_position = np.apply_along_axis(convert_motor_position, 0, self.motor_position)
                if (raw_motor_position >= 0).all() and (raw_motor_position <= 180).all():
                    self.raw_motor_position = raw_motor_position
                else:
                    raise MotorPositionOutOfRangeError
            except (UnsolvableIKError, MotorPositionOutOfRangeError):
                self.update()

    def plot(self, axarr: List[plt.Axes]):
        if len(self.lines) < 12:
            for i in range(12):
                l1, = axarr[i][0].plot(range(self.combined_cycle.shape[1]), self.combined_cycle[i, :])
                l2 = axarr[i][0].axvline(x=self.current_cycle_t, color='gray', alpha=0.5)
                l3, = axarr[i][1].plot(range(self.raw_motor_position.shape[1]), self.motor_position[i, :])
                l4 = axarr[i][1].axvline(x=self.current_cycle_t, color='gray', alpha=0.5)
                self.lines.append([l1, l2, l3, l4])
        else:
            self.redraw(axarr)
            for ax in axarr:
                for ax2 in ax:
                    ax2.relim()

    def redraw(self, axarr: List[plt.Axes]):
        for i in range(12):
            self.lines[i][0].set_ydata(self.combined_cycle[i, :])
            self.lines[i][1].set_xdata(self.current_cycle_t)
            self.lines[i][2].set_ydata(self.motor_position[i, :])
            self.lines[i][3].set_xdata(self.current_cycle_t)
