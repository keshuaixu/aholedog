import hid
import struct


class Comm:
    def __init__(self):
        self.h = hid.device()

    def open(self, vid=0x16c0, pid=0x0486):
        self.h.open(vid, pid)
        self.h.set_nonblocking(1)

    def write(self, angles):
        out = struct.pack('b' * len(angles) + 'x' * (64 - len(angles)), angles)
        self.h.write(out)
