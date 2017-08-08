from aholedog.comm import Comm
from aholedog.robot_kinematics import convert_motor_position

c = Comm()
c.open()
print(convert_motor_position([0] * 12))
c.write(convert_motor_position([0] * 12))
