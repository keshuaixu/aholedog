from .delta_kinematics import inverse as per_leg_ik
import numpy as np

servo_zero_offset = [-65, -60, -60, -55, -60, -60, -67, -60, -60, -57, -60, -60]
#  [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]


def convert_motor_position(angles):
    return (180 - np.array(angles)) + np.array(servo_zero_offset)
