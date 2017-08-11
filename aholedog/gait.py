import numpy as np
from scipy import signal
from collections import namedtuple
import itertools
import matplotlib.pyplot as plt
import threading

Step = namedtuple('Step', ['x', 'y', 'rz'])
FootPosition = namedtuple('FootPosition',
                          list(map(''.join, itertools.product('xyz', '1234')))
                          )


def synth_walk(z, lift_height, period, dt, prev_step: Step, this_step: Step, **kwargs):
    t = np.linspace(0, period, period / dt, endpoint=False)

    z_waveform = signal.square(2 * np.pi * 1 * t)
    print(z_waveform)
    z_1 = (z + z_waveform * 0.5 + 1) * lift_height
    z_3 = z_1
    z_2 = (z + (-1) * z_waveform * 0.5 + 1) * lift_height
    z_4 = z_2

    # half_t = int(len(t) / 2)
    # x_1 = np.horzcat(np.linspace(- prev_step.x / 2, this_step.x / 2, half_t),
    #                  np.linspace(this_step.x / 2, -this_step.x / 2, len(t) - half_t))
    # y_1 = np.horzcat(np.linspace(- prev_step.y / 2, this_step.y / 2, half_t),
    #                  np.linspace(this_step.y / 2, -this_step.y / 2, len(t) - half_t))
    # x_2 = 0  # TODO
    # x_3 = x_1
    # x_4 = x_2
    # y_3 = y_1
    # y_4 = y_2

    x_1 = y_1 = x_2 = y_2 = x_3 = y_3 = x_4 = y_4 = np.zeros(len(t))

    return t, np.vstack((x_1, y_1, z_1, x_2, y_2, z_2, x_3, y_3, z_3, x_4, y_4, z_4))


class GaitGenerator:
    def __init__(self):
        self.current_cycle_t = 0
        self.current_cycle = np.empty((12, 0))
        self.current_cycle_unfiltered = np.empty((12, 0))
        self.next_cycle = np.empty((12, 0))
        self.next_cycle_unfiltered = np.empty((12, 0))
        self.lock = threading.Lock()
        b, a = signal.butter(1, 0.2, output='ba')
        self.filter = lambda x: signal.filtfilt(b, a, x, axis=1)

    def foot_position(self):
        with self.lock:
            self.current_cycle_t += 1
            if self.current_cycle_t >= self.current_cycle.shape[1]:
                self.current_cycle = self.next_cycle
                self.current_cycle_t = 0
            position = self.current_cycle[:, self.current_cycle_t]
        return position

    def update(self, step: Step):
        _, self.next_cycle_unfiltered = synth_walk(z=-70, lift_height=5, period=1, dt=0.01, prev_step=Step(0, 0, 0),
                                                   this_step=step)
        if self.current_cycle_unfiltered.shape[1] == 0:
            self.current_cycle_unfiltered = self.next_cycle_unfiltered

        filtered = self.filter(np.hstack((self.current_cycle_unfiltered, self.next_cycle_unfiltered)))
        plt.plot(range(filtered[2, :].shape[0]), filtered[2, :])


gaitgen = GaitGenerator()
gaitgen.update(Step(0,0,0))
plt.show()
