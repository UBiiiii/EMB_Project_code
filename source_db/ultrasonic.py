import RPi.GPIO as GPIO
import time
from PyQt5 import QtCore
from PyQt5.QtCore import *

#해당 코드는 초음파 센서 사용을 위해 작성한 코드입니다.

GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

TRIG = 14
ECHO = 4

GPIO.setup(TRIG, GPIO.OUT)
GPIO.setup(ECHO, GPIO.IN)
print('setup')
GPIO.output(TRIG, GPIO.LOW)
time.sleep(2)
print('ready')
try:
    while True:
        GPIO.output(TRIG, GPIO.HIGH)
        time.sleep(0.00001)
        GPIO.output(TRIG, GPIO.LOW)
        start = time.time()
        while GPIO.input(ECHO) == 0:
            start = time.time()

<<<<<<< HEAD
        while GPIO.input(ECHO) == 1:
            stop = time.time()
        print('pulse out')
        check_time = stop - start
        distance = check_time * 34300 / 2
        print('Distance : %.1f cm' % distance)
        time.sleep(1)

except KeyboardInterrupt:
    GPIO.cleanup()


# class Thread_US(QThread):
#     signal_detect = pyqtSignal(bool)
#     def _init__(self, parent):
#         QThread.__init__(self)
#         self.parent = parent
#         self.current_page = 0
#         self.TRIG = 32
#         self.ECHO = 36
#         self.parent.signal_current_page.connect(self.page_chagne)

#     def run(self):
#         GPIO.setmode(GPIO.BOARD)
#         GPIO.setup(32, GPIO.OUT)
#         GPIO.setup(36, GPIO.IN)
=======
        GPIO.output(self.TRIG, True)
        time.sleep(2)

        try:
            while True:
                if self.current_page == 0:
                    GPIO.output(self.TRIG, True)
                    time.sleep(0.00001)
                    GPIO.output(self.TRIG, False)

                    while GPIO.input(self.ECHO) == 0:
                        start = time.time()

                    while GPIO.input(self.ECHO) == 1:
                        stop = time.time()

                    check_time = stop - start
                    distance = check_time * 343 / 2
                    if distance < 3:
                        self.signal_detect.emit(True)
                        time.sleep(10)
                    time.sleep(0.4)
                else:
                    time.sleep(1)
>>>>>>> 4db7ce627212f0041a6fb5b303bf66199b8cb20d

#         GPIO.output(self.TRIG, True)
#         time.sleep(2)

#         try:
#             while True:
#                 if self.current_page != 0:
#                     time.sleep(3)
#                 else:
#                     GPIO.output(self.TRIG, True)
#                     time.sleep(0.00001)
#                     GPIO.output(self.TRIG, False)

#                     while GPIO.input(self.ECHO) == 0:
#                         start = time.time()

#                     while GPIO.input(self.ECHO) == 1:
#                         stop = time.time()

#                     check_time = stop - start
#                     distance = check_time * 343 / 2
#                     if distance < 3:
#                         self.signal_detect.emit(True)
#                         time.sleep(10)
#                     time.sleep(0.4)

#         except KeyboardInterrupt:
#             GPIO.cleanup()
    
#     def page_chagne(self, data):
#         self.current_page = data