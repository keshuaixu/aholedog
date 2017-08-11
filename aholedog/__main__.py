import pygame
import sys

import time

from aholedog.comm import Comm
from aholedog.gait import GaitGenerator, Step
import matplotlib.pyplot as plt
from threading import Timer
from apscheduler.schedulers.background import BackgroundScheduler


class AHoleDog():
    def __init__(self, realdog=True, joystick=True):

        pygame.init()

        self.realdog = realdog
        self.have_joystick = joystick

        if realdog:
            self.c = Comm()
            self.c.open()

        if joystick:
            # Grab joystick 0
            if pygame.joystick.get_count() == 0:
                raise IOError("No joystick detected")
            self.js = pygame.joystick.Joystick(0)
            self.js.init()

        self.gaitgen = GaitGenerator()
        self.fig, self.axarr = plt.subplots(nrows=12, ncols=2, sharex=True)
        plt.show(block=False)


    def run(self):
        scheduler = BackgroundScheduler()
        scheduler.start()
        if self.have_joystick:
            pass
            # scheduler.add_job(self.read_joysticks, 'interval', seconds=2)
        if self.realdog:
            scheduler.add_job(self.update_servos, 'interval', seconds=0.1)

    def read_joysticks(self):


        # print('{} {} {} {}'.format(self.js.get_axis(0), self.js.get_axis(1), self.js.get_axis(2), self.js.get_axis(3)))

        pygame.event.pump()

        kp = 10

        y = self.js.get_axis(0) * kp
        x = self.js.get_axis(1) * kp
        z = self.js.get_axis(2) * kp
        print('a')
        self.gaitgen.update(Step(x, y, 0, -50 + z, lift_z=5, period=1))
        # plt.clf()
        self.gaitgen.plot(self.axarr)
        self.fig.canvas.draw()
        # plt.show(block=False)
        # plt.draw()
        # plt.show(block=False)



    def update_servos(self):
        self.gaitgen.step()
        self.c.write(self.gaitgen.raw_motor_position[:, self.gaitgen.current_cycle_t])

if __name__ == '__main__':
    dog = AHoleDog(realdog=True)
    dog.run()
    # time.sleep(10)
    while True:
        dog.read_joysticks()
        time.sleep(0.2)