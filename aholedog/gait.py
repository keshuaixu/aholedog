import numpy as np
from scipy import signal
from collections import namedtuple

Step = namedtuple('Step', ['x', 'y', 'rz'])


def synth_walk(z, lift_height, period, dt, prev_step: Step, this_step: Step, **kwargs):
    t = np.linspace(0, period, dt)

    z_waveform = signal.square(2 * np.pi * 1 * t)
    z_1 = (z + z_waveform * 0.5 + 1) * lift_height
    z_3 = z_1
    z_2 = (z + (-1) * z_waveform * 0.5 + 1) * lift_height
    z_4 = z_2

    half_t = int(len(t) / 2)
    x_1 = np.horzcat(np.linspace(- prev_step.x / 2, this_step.x / 2, half_t),
                     np.linspace(this_step.x / 2, -this_step.x / 2, len(t) - half_t))
    y_1 = np.horzcat(np.linspace(- prev_step.y / 2, this_step.y / 2, half_t),
                     np.linspace(this_step.y / 2, -this_step.y / 2, len(t) - half_t))
    x_2 = 0  # TODO
    x_3 = x_1
    x_4 = x_2
    y_3 = y_1
    y_4 = y_2
