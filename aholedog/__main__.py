import pygame
import sys

import time

from multiprocessing import Process

from aholedog.comm import Comm
from aholedog.gait import GaitGenerator, Step, synth_walk_debug, synth_walk
import matplotlib.pyplot as plt
from threading import Timer, Thread
from apscheduler.schedulers.background import BackgroundScheduler

from aholedog.plot import GaitPlotter


def do_forever(f, t):
    while True:
        f()
        time.sleep(t)

class AHoleDog():
    def __init__(self, realdog=True, joystick=True, plot=True):

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

        self.gaitgen = GaitGenerator(synthesizer=synth_walk)
        if plot:
            self.plotter = GaitPlotter(self.gaitgen)


    def run_multiprocess(self):
        Thread(target=do_forever(self.read_joysticks, 0.1)).start()
        Process(target=do_forever(self.update_servos, 0.03)).start()


    def run_scheduler(self):
        scheduler = BackgroundScheduler()
        scheduler.start()
        if self.have_joystick:
            scheduler.add_job(self.read_joysticks, 'interval', seconds=0.1)
        if self.realdog:
            scheduler.add_job(self.update_servos, 'interval', seconds=0.02)



    def read_joysticks(self):
        # print('{} {} {} {}'.format(self.js.get_axis(0), self.js.get_axis(1), self.js.get_axis(2), self.js.get_axis(3)))

        pygame.event.pump()

        kp = 15

        y = self.js.get_axis(0) * kp
        x = self.js.get_axis(1) * kp
        # z = self.js.get_axis(2) * 10
        # z = 8
        # throttle = self.js.get_axis(2)
        zz = self.js.get_axis(2)
        print((zz+1)*5)
        self.gaitgen.update(Step(x, y, 0, -54, lift_z=(zz+1)*5, period=0.32))



    def update_servos(self):
        self.gaitgen.step()
        self.c.write(self.gaitgen.raw_motor_position[:, self.gaitgen.current_cycle_t])

if __name__ == '__main__':
    # dog = AHoleDog(realdog=True, plot=True)
    # dog.run_scheduler()
    # time.sleep(10)
    # dog.run_multiprocess()
    dog = AHoleDog(realdog=True, joystick=True, plot=False)
    dog.run_scheduler()
    # dog.c.write()
    while True:
        time.sleep(1)