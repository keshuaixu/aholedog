# Stolen from https://gist.github.com/hugs/4231272
# Original code from
# http://forums.trossenrobotics.com/tutorials/introduction-129/delta-robot-kinematics-3276/
# License: MIT

import math
import numpy as np


class UnsolvableIKError(RuntimeError):
    pass


# Specific geometry for bitbeambot:
# http://flic.kr/p/cYaQah
e = 14.66 / 2
f = 21.50
re = 50.00
rf = 15.00

# Trigonometric constants
sqrt3 = math.sqrt(3.0)
pi = math.pi
sin120 = sqrt3 / 2.0
cos120 = -0.5
tan60 = sqrt3
sin30 = 0.5
tan30 = 1.0 / sqrt3


# Forward kinematics: (theta1, theta2, theta3) -> (x0, y0, z0)
#   Returned {error code,theta1,theta2,theta3}
def forward(theta1, theta2, theta3):
    x0 = 0.0
    y0 = 0.0
    z0 = 0.0

    t = (f - e) * tan30 / 2.0
    dtr = pi / 180.0

    theta1 *= dtr
    theta2 *= dtr
    theta3 *= dtr

    y1 = -(t + rf * math.cos(theta1))
    z1 = -rf * math.sin(theta1)

    y2 = (t + rf * math.cos(theta2)) * sin30
    x2 = y2 * tan60
    z2 = -rf * math.sin(theta2)

    y3 = (t + rf * math.cos(theta3)) * sin30
    x3 = -y3 * tan60
    z3 = -rf * math.sin(theta3)

    dnm = (y2 - y1) * x3 - (y3 - y1) * x2

    w1 = y1 * y1 + z1 * z1
    w2 = x2 * x2 + y2 * y2 + z2 * z2
    w3 = x3 * x3 + y3 * y3 + z3 * z3

    # x = (a1*z + b1)/dnm
    a1 = (z2 - z1) * (y3 - y1) - (z3 - z1) * (y2 - y1)
    b1 = -((w2 - w1) * (y3 - y1) - (w3 - w1) * (y2 - y1)) / 2.0

    # y = (a2*z + b2)/dnm
    a2 = -(z2 - z1) * x3 + (z3 - z1) * x2
    b2 = ((w2 - w1) * x3 - (w3 - w1) * x2) / 2.0

    # a*z^2 + b*z + c = 0
    a = a1 * a1 + a2 * a2 + dnm * dnm
    b = 2.0 * (a1 * b1 + a2 * (b2 - y1 * dnm) - z1 * dnm * dnm)
    c = (b2 - y1 * dnm) * (b2 - y1 * dnm) + b1 * b1 + dnm * dnm * (z1 * z1 - re * re)

    # discriminant
    d = b * b - 4.0 * a * c
    if d < 0.0:
        return [1, 0, 0, 0]  # non-existing povar. return error,x,y,z

    z0 = -0.5 * (b + math.sqrt(d)) / a
    x0 = (a1 * z0 + b1) / dnm
    y0 = (a2 * z0 + b2) / dnm

    return [0, x0, y0, z0]


# Inverse kinematics
# Helper functions, calculates angle theta1 (for YZ-pane)
def angle_yz(x0, y0, z0, theta=None):
    y1 = -0.5 * tan30 * f  # f/2 * tg 30
    y0 -= 0.5 * tan30 * e  # shift center to edge
    # z = a + b*y
    a = (x0 * x0 + y0 * y0 + z0 * z0 + rf * rf - re * re - y1 * y1) / (2.0 * z0)
    b = (y1 - y0) / z0

    # discriminant
    d = -(a + b * y1) * (a + b * y1) + rf * (b * b * rf + rf)
    if d < 0:
        return [1, 0]  # non-existing povar.  return error, theta

    yj = (y1 - a * b - math.sqrt(d)) / (b * b + 1)  # choosing outer povar
    zj = a + b * yj
    theta = math.atan(-zj / (y1 - yj)) * 180.0 / pi + (180.0 if yj > y1 else 0.0)

    return [0, theta]  # return error, theta


def inverse(x0, y0, z0):
    theta1 = 0
    theta2 = 0
    theta3 = 0
    status = angle_yz(x0, y0, z0)

    if status[0] == 0:
        theta1 = status[1]
        status = angle_yz(x0 * cos120 + y0 * sin120,
                          y0 * cos120 - x0 * sin120,
                          z0,
                          theta2)
    if status[0] == 0:
        theta2 = status[1]
        status = angle_yz(x0 * cos120 - y0 * sin120,
                          y0 * cos120 + x0 * sin120,
                          z0,
                          theta3)
    theta3 = status[1]

    if not status[0] == 0:
        raise UnsolvableIKError()

    return theta1, theta2, theta3


def inverse_arr(arr: np.core.multiarray):
    horz = []
    leg_dir = [1, 1, -1, -1]
    for t in range(arr.shape[1]):
        vert = []
        for i in range(4):
            th1, th2, th3 = inverse(leg_dir[i] * arr[3 * i + 1, t], leg_dir[i] * arr[3 * i, t], arr[3 * i + 2, t])
            vert.append(np.array([th1, th2, th3]).reshape(3, 1))
        horz.append(np.vstack(tuple(vert)))
    return np.hstack(tuple(horz))
