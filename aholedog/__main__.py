from aholedog.gait import GaitGenerator, Step
import matplotlib.pyplot as plt


gaitgen = GaitGenerator()
gaitgen.update(Step(0, 0, 0, -50, lift_z=5, period=1))
fig, axarr = plt.subplots(nrows=12, ncols=2, sharex=True)
gaitgen.plot(axarr)
plt.show()

def read_joysticks():
    pass

def update_servos():
    pass