import RPI.GPIO as GPIO
import time
from PyQt5 import QtCore
from PyQt5.QtCore import *

# GPIO.setmode(GPIO.BCM)
# GPIO.setwarnings(False)
#
# TRIG = 23
# ECHO = 24
#
# GPIO.setup(TRIG, GPIO.OUT)
# GPIO.setup(ECHO, GPIO.IN)
#
# GPIO.output(TRIG, True)
# time.sleep(2)
#
# try:
#     while True:
#         GPIO.output(TRIG, True)
#         time.sleep(0.00001)
#         GPIO.output(TRIG, False)
#
#         while GPIO.input(ECHO) == 0:
#             start = time.time()
#
#         while GPIO.INPUT(ECHO) == 1:
#             stop = time.time()
#
#         check_time = stop - start
#         distance = check_time * 34300 / 2
#         print('Distance : %.1f cm' & distance)
#         time.sleep(0.4)
#
# except KeyboardInterrupt:
#     GPIO.cleanup()


class Thread_US(QThread):
    signal_detect = pyqtSignal(bool)
    def _init__(self, parent):
        QThread.__init__(self)
        self.parent = parent
        self.current_page = 0
        self.TRIG = 32
        self.ECHO = 36

    def run(self):
        GPIO.setmode(GPIO.BOARD)
        GPIO.setup(32, GPIO.OUT)
        GPIO.setup(36, GPIO.IN)

        GPIO.output(self.TRIG, True)
        time.sleep(2)W

        try:
            while True:
                GPIO.output(self.TRIG, True)
                time.sleep(0.00001)
                GPIO.output(self.TRIG, False)

                while GPIO.input(self.ECHO) == 0:
                    start = time.time()

                while GPIO.input(self.ECHO) == 1:
                    stop = time.time()

                check_time = stop - start
                distance = check_time * 343 / 2
                if distance < 2:
                    self.signal_detect.emit(True)
                    time.sleep(10)
                time.sleep(0.4)

        except KeyboardInterrupt:
            GPIO.cleanup()