from typing import List

import numpy as np
from scipy import signal
from collections import namedtuple
import itertools
import matplotlib.pyplot as plt
import threading

from aholedog.delta_kinematics import inverse_arr

Step = namedtuple('Step', ['x', 'y', 'rz'])


def synth_walk(z, lift_height, period, dt, prev_step: Step, this_step: Step, **kwargs):
    t = np.linspace(0, period, period / dt, endpoint=False)

    z_waveform = signal.square(2 * np.pi * 1 * t)
    z_1 = z + (z_waveform * 0.5 + 1) * lift_height
    z_3 = z_1
    z_2 = z + ((-1) * z_waveform * 0.5 + 1) * lift_height
    z_4 = z_2

    x_1 = y_1 = x_2 = y_2 = x_3 = y_3 = x_4 = y_4 = np.zeros(len(t))
    half_t = int(len(t) / 2)
    x_1 = x_3 = np.hstack((np.linspace(- prev_step.x / 2, this_step.x / 2, half_t),
                           np.linspace(this_step.x / 2, -this_step.x / 2, len(t) - half_t)))
    y_1 = y_3 = np.hstack((np.linspace(- prev_step.y / 2, this_step.y / 2, half_t),
                           np.linspace(this_step.y / 2, -this_step.y / 2, len(t) - half_t)))
    # x_2 = 0  # TODO
    # x_4 = x_2

    # y_4 = y_2

    return t, np.vstack((x_1, y_1, z_1, x_2, y_2, z_2, x_3, y_3, z_3, x_4, y_4, z_4))


class GaitGenerator:
    def __init__(self):
        self.current_cycle_t = 0
        self.current_cycle = np.empty((12, 0))
        self.current_cycle_unfiltered = np.empty((12, 0))
        self.current_step = self.input_step = Step(0, 0, 0)
        self.next_cycle = np.empty((12, 0))
        self.next_cycle_unfiltered = np.empty((12, 0))
        self.combined_cycle = np.empty((12, 0))
        self.lock = threading.Lock()
        b, a = signal.butter(1, 0.2, output='ba')
        self.filter = lambda x: signal.filtfilt(b, a, x, axis=1)
        self.motor_position = np.empty((12, 0))

    def foot_position(self):
        with self.lock:
            self.current_cycle_t += 1
            if self.current_cycle_t >= self.current_cycle.shape[1]:
                self.current_cycle = self.next_cycle
                self.current_cycle_t = 0
                self.current_cycle_unfiltered = self.next_cycle_unfiltered
                self.current_step = self.input_step
            position = self.current_cycle[:, self.current_cycle_t]
        return position

    def update(self, step: Step):
        self.input_step = step
        with self.lock:
            _, self.next_cycle_unfiltered = synth_walk(z=-60, lift_height=5, period=1, dt=0.01,
                                                       prev_step=self.current_step,
                                                       this_step=step)
            if self.current_cycle_unfiltered.shape[1] == 0:
                self.current_cycle_unfiltered = self.next_cycle_unfiltered

            filtered = self.filter(np.hstack((self.current_cycle_unfiltered, self.next_cycle_unfiltered)))
            self.current_cycle = filtered[:, :self.current_cycle_unfiltered.shape[1] - 1]
            self.next_cycle = filtered[:, self.current_cycle_unfiltered.shape[1]:]
            self.combined_cycle = filtered
            self.motor_position = inverse_arr(filtered)


def plot(gaitgen: GaitGenerator, axarr: List[plt.Axes]):
    for i in range(12):
        axarr[i][0].plot(range(gaitgen.combined_cycle.shape[1]), gaitgen.combined_cycle[i, :])
        axarr[i][0].axvline(x=gaitgen.current_cycle_t, color='gray', alpha=0.5)
        axarr[i][1].plot(range(gaitgen.motor_position.shape[1]), gaitgen.motor_position[i, :])
        axarr[i][1].axvline(x=gaitgen.current_cycle_t, color='gray', alpha=0.5)


gaitgen = GaitGenerator()
gaitgen.update(Step(0, 0, 0))
gaitgen.update(Step(0, 0, 0))
gaitgen.update(Step(0, 0, 0))
fig, axarr = plt.subplots(nrows=12, ncols=2, sharex=True)
plot(gaitgen, axarr)
plt.show()
