'''
navi_mirror.py
Overall scenario for navigation mirror.
Written By. Team Excitement of Creativitiy
Git : https://github.com/UBiiiii/EMB_Project_code/tree/master/UI_GPIO
Released : June 12, 2022
'''

# Import modules
from cgitb import text
from dataclasses import dataclass
import os
import sys
from xmlrpc.client import boolean
from Pyrebase_STT import STT
import urllib.request

from db_code import *
import pyrebase

from PyQt5 import QtCore, QtGui, QtWidgets, QtMultimedia
from PyQt5.QtGui import QMovie, QFontDatabase, QFont
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5 import uic

import speech_recognition as sr
from difflib import SequenceMatcher

import background_rc
import description_rc
import mic_rc
import button_rc
import select_rc

import RPi.GPIO as GPIO

from time import sleep, time

import cv2
import qrcode

import pygame

def resource_path(relative_path):
    base_path = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_path, relative_path)

# generate class from .ui files.
# .ui files are made in Qt designer.
form = resource_path('navi_mirror.ui')
form_class = uic.loadUiType(form)[0]

form_mic_listening = resource_path('mic_listening.ui')
form_mic_listening_class = uic.loadUiType(form_mic_listening)[0]

form_mic_retry = resource_path('mic_retry.ui')
form_mic_retry_class = uic.loadUiType(form_mic_retry)[0]

firebaseConfig = {
    #input your firebase config
}

firebase = pyrebase.initialize_app(firebaseConfig)

# Create a thread to control GPIO. Initialization and settings for buttons using GPIO, GPIO pins for ultrasonic sensors.
# Communication with the main thread by pressing a button or using a signal generated from an ultrasonic sensor.
class Thread_GPIO(QThread):
    signal_next = pyqtSignal(int)
    signal_up = pyqtSignal(int)
    signal_down = pyqtSignal(int)
    signal_wakeup = pyqtSignal(bool)
    def __init__(self, parent):
        QThread.__init__(self)
        self.parent = parent
        self.row = 0
        self.current_page = 0
        self.TRIG = 10
        self.ECHO = 18

    def run(self):
        self.parent.signal_current_page.connect(self.count)
        GPIO.setmode(GPIO.BOARD)
        GPIO.setup([22, 21, 32], GPIO.IN)
        try:
            GPIO.add_event_detect(21, GPIO.RISING, callback=self.test, bouncetime=500)
            GPIO.add_event_detect(32, GPIO.RISING, callback=self.up, bouncetime=500)
            GPIO.add_event_detect(22, GPIO.RISING, callback=self.down, bouncetime=500)
            GPIO.setup(self.ECHO, GPIO.IN)
            GPIO.setup(self.TRIG, GPIO.OUT)
        except:
            GPIO.cleanup()
            GPIO.setmode(GPIO.BOARD)
            GPIO.setup([22, 21, 32], GPIO.IN)
            GPIO.add_event_detect(21, GPIO.RISING, callback=self.test, bouncetime=500)
            GPIO.add_event_detect(32, GPIO.RISING, callback=self.up, bouncetime=500)
            GPIO.add_event_detect(22, GPIO.RISING, callback=self.down, bouncetime=500)
            GPIO.setup(self.ECHO, GPIO.IN)
            GPIO.setup(self.TRIG, GPIO.OUT)

        GPIO.setup(self.ECHO, GPIO.IN)
        GPIO.setup(self.TRIG, GPIO.OUT)

        GPIO.output(self.TRIG, GPIO.LOW)
        while True:
            if self.current_page == 0:
                GPIO.output(self.TRIG, GPIO.HIGH)
                sleep(0.00001)
                GPIO.output(self.TRIG, GPIO.LOW)
                start = time()
                while GPIO.input(self.ECHO) == 0:
                    start = time()

                while GPIO.input(self.ECHO) == 1:
                    stop = time()
                check_time = stop - start
                distance = check_time * 34300/2
                if distance < 100:
                    self.signal_wakeup.emit(True)
                print('Distance : %.1f cm' % distance)
                sleep(1)
            else:
                sleep(5)

    # Implementation of actions according to signals sent from each GPIO input and main thread.
    def count(self, page):
        self.current_page = page

    def test(self,a):
        if self.current_page != 2:
            self.signal_next.emit(self.row)

    def up(self, a):
        if self.current_page == 3:
            self.signal_up.emit(self.row)
    
    def down(self, a):
        if self.current_page == 3:
            self.signal_down.emit(self.row)
    
    def stop(self):
        self.quit()
        self.wait(1000)


# A thread implementation that measures latency. Set to return to the idle or home screen when there is no input on the screen.
# Implemented to stop and stop time measurement when the screen changes while measuring the waiting time.
class Thread_wait(QThread):
    signal_sleep = pyqtSignal(bool)
    def __init__(self, parent):
        QThread.__init__(self)
        self.parent = parent
        self.exit = False
        self.current_time = 0
        self.parent.signal_page_change.connect(self.page_change)
        self.parent.signal_init.connect(self.sig_init)
    
    def run(self):
        self.exit = False
        while self.current_time < 10:
            sleep(0.93)
            if self.exit == True:
                break
            else:
                self.current_time += 1
        
        if self.exit == True:
            self.exit = False
            print("Page Chagne")

        else:
            self.signal_sleep.emit(True)
        
        self.current_time = 0

    def stop(self):
        self.quit()
        print("thread exit")
        self.wait(1000)

    def page_change(self):
        self.exit = True

    def sig_init(self):
        self.exit = False

# Configure a thread that returns a list of destinations through speech recognition.
# When the thread is executed, voice recognition is performed, 
# the voice input from the microphone is compared with the contents stored in the database
# and the destination list is returned as a signal.
# Sends a failure signal when an error(speech recognition failure, destination detection failure) occurs.
class Thread_mic(QThread):
    signal_retry = pyqtSignal(bool)
    signal_next = pyqtSignal(list)
    signal_ready = pyqtSignal(bool)

    def __init__(self, parent):
        QThread.__init__(self)
        self.parent = parent
        self.r = sr.Recognizer()

        # Get Database.
        self.db = firebase.database()
 
    def run(self):
        print('start')
        with sr.Microphone() as source:
            self.r.adjust_for_ambient_noise(source)

            self.signal_ready.emit(True)
            print("말을 해!!")
            try:
                audio = self.r.listen(source, timeout = 5)
                try:
                    input = self.r.recognize_google(audio, language='ko')
                    print(input)
                    room_list = []
                    score_list = []
                    floors = self.db.get()
                    print('db download')
                    for floor in floors.each():
                        if floor.key() == 0:
                            continue
                        rooms = self.db.child(floor.key()).get()

                        for room in rooms.each():
                            score = SequenceMatcher(None, room.val()["name"], input).ratio()
                            if (score > 0.6 or (room.val()["charge"] in input) or (room.key() in input) or (input in room.val()["name"])):
                                information = [room.key(), room.val()['charge'], room.val()['name'], room.val()['phone'], score, room.val()['specific']]
                                room_list.append(information)
                                score_list.append(score)

                    if len(room_list) == 0:
                        self.signal_retry.emit(True)
                        print("찾지 못했습니다.")
                    else:
                        return_list = []
                        score_list.sort()
                        while len(score_list) > 0:
                            score = score_list.pop()
                            for i in room_list:
                                if i[4] == score:
                                    print(i)
                                    return_list.append(i)
                                    room_list.remove(i)
                        self.signal_next.emit(return_list)

                except sr.UnknownValueError:
                    self.signal_retry.emit(True)
                    print("음성을 인식하지 못 했습니다.")

                except sr.RequestError as e:
                    self.signal_retry.emit(True)
                    print("에러 {0}".format(e))
            except:
                self.signal_retry.emit(True)
                print("실패?")
        
    def stop(self):
        print('mic stop')
        self.quit()
        self.wait(1000)

# Main thread, it is responsible for managing the UI.
class MainWindow(QMainWindow, form_class):
    signal_update = pyqtSignal(bool)
    signal_search = pyqtSignal(str)
    signal_current_page = pyqtSignal(int)
    signal_page_change = pyqtSignal(bool)
    signal_init = pyqtSignal(bool)
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.setWindowFlags(Qt.FramelessWindowHint)
        
        # Initializing variables for use by functions within the class.
        # Calling the classes required for each action.
        self.current_page = 0
        self.c_row = 0
        self.object_substitute_list = []
        self.navi_mirror_scenario.setCurrentIndex(self.current_page)
        self.mic_listening = mic_listening()
        self.stor = storage()
        self.db = database()
        self.sql = sql()
        self.row_max = 0
        self.mic_retry = mic_retry()

        # Voice and UI preferences
        self.player = QtMultimedia.QMediaPlayer()
        self.player.setVolume(100)
        self.specific.setFontPointSize(26)
        self.specific.setCursorWidth(0)
        self.specific.setStyleSheet("background:black;""color:white;")

    # Execute the threads configured above, and connect each signal to a function.
    def threadAction(self):
        self.GPIO = Thread_GPIO(self)
        self.GPIO.signal_up.connect(self.up)
        self.GPIO.signal_down.connect(self.down)
        self.GPIO.signal_next.connect(self.next)
        self.GPIO.signal_wakeup.connect(self.wakeup)
        
        self.mic = Thread_mic(self)
        self.mic.signal_next.connect(self.next)
        self.mic.signal_ready.connect(self.view)
        self.mic.signal_retry.connect(self.retry)

        self.sleep = Thread_wait(self)
        self.sleep.signal_sleep.connect(self.home)

        self.GPIO.start()

    # A function that changes from the idle screen to the home screen when a person passes within 1 meter forward.
    def wakeup(self):
        self.current_page = 1
        content = QtMultimedia.QMediaContent(QUrl.fromLocalFile("/home/pi/EMB_Project_code/UI_GPIO/sound/hello.mp3"))
        self.object_substitute_list = []
        self.signal_init.emit(True)
        self.sleep.start()
        self.signal_current_page.emit(self.current_page)
        self.navi_mirror_scenario.setCurrentIndex(self.current_page)
        self.player.setMedia(content)
        self.player.play()
        print(self.current_page)

    # A function that changes to the idle screen or home screen after the waiting time has passed.
    def home(self):
        if self.current_page == 1:
            self.current_page = 0

        else:
            self.mic_retry.close()
            self.mic_retry.stop()
            self.object_list.clear()
            self.signal_init.emit(True)
            self.current_page = 1
            self.sleep.start()
        
        self.signal_current_page.emit(self.current_page)
        self.navi_mirror_scenario.setCurrentIndex(self.current_page)
        print(self.current_page)
        
    # When speech recognition is performed, this function outputs a gif to indicate that speech recognition is ready.
    def view(self):
        self.mic_listening.show()
        # self.sttStart = time.time() # stt check

    # A function that implements the action for the 'up' button.
    def up(self):
        self.c_row += 1
        if self.c_row > self.row_max:
            self.c_row = self.row_max
        self.object_list.setCurrentRow(self.c_row)

    # A function that implements the action for the 'down' button.
    def down(self):
        self.c_row -= 1
        if self.c_row < 0:
            self.c_row = 0
        self.object_list.setCurrentRow(self.c_row)

    # A function that implements the action for the 'select' button.
    # Initialize, modify, and save the necessary variables for the screen after pressing the 'select' button.
    def next(self, data):
        print('Push!')
        self.current_page += 1

        # Page for introduce navigation mirror.
        if self.current_page == 1:
            content = QtMultimedia.QMediaContent(QUrl.fromLocalFile("/home/pi/EMB_Project_code/UI_GPIO/sound/hello.mp3"))
            self.object_substitute_list = []
            self.signal_init.emit(True)
            self.sleep.start()
            # self.start = time.time() #check

        # Page for speech recognition.
        elif self.current_page == 2:
            content = QtMultimedia.QMediaContent(QUrl.fromLocalFile("/home/pi/EMB_Project_code/UI_GPIO/sound/listen.mp3"))
            self.mic_retry.close()
            self.mic_retry.stop()
            self.signal_page_change.emit(True)
            self.mic.start()
        
        # Page to show destination list.
        elif self.current_page == 3:
            content = QtMultimedia.QMediaContent(QUrl.fromLocalFile("/home/pi/EMB_Project_code/UI_GPIO/sound/done.mp3"))
            self.mic_listening.close()
            self.object_substitute_list = data
            self.addItem()
            # self.sttDone = time.time() # stt check
        
        # Page to indicate route and QR tag.
        elif self.current_page == 4:
            if self.c_row == 0:
                self.current_page = 1
                self.object_substitute_list = []
                self.signal_init.emit(True)
                self.sleep.start()
                content = QtMultimedia.QMediaContent(QUrl.fromLocalFile("/home/pi/EMB_Project_code/UI_GPIO/sound/space.mp3"))
            else:
                content = QtMultimedia.QMediaContent(QUrl.fromLocalFile("/home/pi/EMB_Project_code/UI_GPIO/sound/map.mp3"))
                self.object_list.clear()
                specific = self.object_substitute_list[self.c_row-1][5]
                # specific = 'test'
                room = self.db.redirect(self.object_substitute_list[self.c_row-1][0])
                if self.sql.check_map(room) == False:
                    if self.sql.check_len() >= 10:
                        self.sql.delete()
                    print('no file exists')
                    print(room)
                    self.stor.download_file(room)
                    self.sql.insert_latest(room, time())
                map_img = cv2.imread("/home/pi/EMB_Project_code/UI_GPIO/download/map/" +room + ".png")
                resize_map = cv2.resize(map_img, (610,1300))
                resize_map = cv2.cvtColor(resize_map, cv2.COLOR_BGR2RGB) 
                h,w,c = resize_map.shape
                qImg_map = QtGui.QImage(resize_map.data, w, h, w*c, QtGui.QImage.Format_RGB888)
                pixmap_map = QtGui.QPixmap.fromImage(qImg_map)
                self.map.setPixmap(pixmap_map)

                url = self.stor.get_url(room)
                qr_url = qrcode.make(url)
                qr_url.save("/home/pi/EMB_Project_code/UI_GPIO/download/qr/" + room + ".png")
                img = cv2.imread("/home/pi/EMB_Project_code/UI_GPIO/download/qr/" + room + ".png")
                resize_img = cv2.resize(img, (370,370))
                resize_img = cv2.cvtColor(resize_img, cv2.COLOR_BGR2RGB) 
                h,w,c = resize_img.shape
                qImg = QtGui.QImage(resize_img.data, w, h, w*c, QtGui.QImage.Format_RGB888)
                pixmap_qr = QtGui.QPixmap.fromImage(qImg)
                self.qr.setPixmap(pixmap_qr)
                self.specific.append(specific)
            # self.end = time.time() # check
            # print("scenario taked ",self.end - self.start,"stt taked ", 
            # self.sttDone - self.sttStart)

        elif self.current_page == 5:
            self.current_page = 1
            self.object_substitute_list = []
            self.specific.clear()
            self.object_list.clear()
            self.signal_init.emit(True)
            content = QtMultimedia.QMediaContent(QUrl.fromLocalFile("/home/pi/EMB_Project_code/UI_GPIO/sound/space.mp3"))
            self.sleep.start()
            
        # Page to indicate speech recognition has failed.
        elif self.current_page == 6:
            self.signal_page_change.emit(True)
            self.mic_retry.close()
            self.mic_retry.stop()
            self.current_page = 2
            content = QtMultimedia.QMediaContent(QUrl.fromLocalFile("/home/pi/EMB_Project_code/UI_GPIO/sound/space.mp3"))
            self.mic.start()
    
        self.signal_current_page.emit(self.current_page)
        self.navi_mirror_scenario.setCurrentIndex(self.current_page)
        self.player.setMedia(content)
        try:
            self.player.play()
            print(self.current_page)
        except:
            print(self.current_page)    
                
    # A function to add the list sent by the voice recognition thread to the screen UI, to output the destination list.
    def addItem(self):
        self.c_row = 0
        object_lst=[]
        for row in self.object_substitute_list:
            object_lst.append('%{}s %{}s %{}s %{}s'.format(13, 38 - 
            3*(len(row[1]) - len(row[1].split())), 66 - 3*(len(row[2]) - len(row[2].split())), 
            25) % (row[0], row[1], row[2], row[3]))
        
        self.row_max = len(object_lst)
        self.object_list.addItem('처음으로 돌아가기')
        for obj in object_lst:
            self.object_list.addItem(obj)

    # A function to move to the speech recognition failure screen when speech recognition fails.
    def retry(self):
        self.signal_init.emit(True)
        self.mic_listening.close()
        self.current_page = 5
        self.signal_current_page.emit(self.current_page)
        self.navi_mirror_scenario.setCurrentIndex(self.current_page)
        content = QtMultimedia.QMediaContent(QUrl.fromLocalFile("/home/pi/EMB_Project_code/UI_GPIO/sound/retry.mp3"))
        self.player.setMedia(content)
        self.player.play()
        self.sleep.start()
        self.mic_retry.show()
        self.mic_retry.start()

# Class for gif output indicating that speech recognition is running.
class mic_listening(QWidget, form_mic_listening_class):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.move(464, 1296)

        self.movie = QMovie('/home/pi/EMB_Project_code/UI_GPIO/mic_listening.gif', QtCore.QByteArray(), self)
        self.movie.setCacheMode(QMovie.CacheAll)

        self.mic_listening_gif.setMovie(self.movie)
        self.movie.start()

# A class for outputting a gif that displays latency.
class mic_retry(QWidget, form_mic_retry_class):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.move(464, 1296)

        self.movie = QMovie('/home/pi/EMB_Project_code/UI_GPIO/mic_timeout_10.gif', QtCore.QByteArray(), self)
        self.movie.setCacheMode(QMovie.CacheAll)

        self.mic_retry_gif.setMovie(self.movie)

    def start(self):
        self.movie.start()

    def stop(self):
        self.movie.stop()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    fontDB = QFontDatabase()
    fontDB.addApplicationFont('home/pi/EMB_Project_code/source_db/BMJUA_ttf.ttf')
    font = QFont()
    font.setFamily('BMJUA_ttf.ttf')
    app.setFont(font)
        
    myWindow = MainWindow()
    myWindow.threadAction()
    myWindow.show()
    app.exec_()