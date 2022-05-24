from dataclasses import dataclass
import os
import sys
import time
from xmlrpc.client import boolean
from Pyrebase_STT import STT
import urllib.request
import qrcode
from PIL.ImageQt import ImageQt
import cv2

from db_code import storage

from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtGui import QMovie
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

from time import sleep

def resource_path(relative_path):
    base_path = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_path, relative_path)

form_wait = resource_path('navi_mirror_wait.ui')
form_wait_class = uic.loadUiType(form_wait)[0]

form_start = resource_path('navi_mirror_start.ui')
form_start_class = uic.loadUiType(form_start)[0]

form_listening = resource_path('navi_mirror_listening.ui')
form_listening_class = uic.loadUiType(form_listening)[0]

form_mic_listening = resource_path('mic_listening.ui')
form_mic_listening_class = uic.loadUiType(form_mic_listening)[0]

form_search = resource_path('navi_mirror_search.ui')
form_search_class = uic.loadUiType(form_search)[0]

form_mic_search = resource_path('mic_search.ui')
form_mic_search_class = uic.loadUiType(form_mic_search)[0]

form_done = resource_path('navi_mirror_done.ui')
form_done_class = uic.loadUiType(form_done)[0]

form_map = resource_path('navi_mirror_map.ui')
form_map_class = uic.loadUiType(form_map)[0]

class Thread_btn(QThread):
    signal_next = pyqtSignal(bool)
    signal_up = pyqtSignal(bool)
    signal_down = pyqtSignal(bool)
    def __init__(self, parent):
        QThread.__init__(self)
        self.parent = parent
        self.row = 0

    def run(self):
        GPIO.setmode(GPIO.BOARD)
        GPIO.setup([12,18,22], GPIO.IN)
        try:
            GPIO.add_event_detect(12, GPIO.RISING, callback=self.next, bouncetime=800)
            GPIO.add_event_detect(18, GPIO.RISING, callback=self.up, bouncetime=800)
            GPIO.add_event_detect(22, GPIO.RISING, callback=self.down, bouncetime=800)
        except:
            GPIO.cleanup()
            GPIO.setmode(GPIO.BOARD)
            GPIO.setup([12,18, 22], GPIO.IN)
            GPIO.add_event_detect(12, GPIO.RISING, callback=self.next, bouncetime=800)
            GPIO.add_event_detect(18, GPIO.RISING, callback=self.up, bouncetime=800)
            GPIO.add_event_detect(22, GPIO.RISING, callback=self.down, bouncetime=800)

    def next(self,a):
        self.signal_next.emit(True)
    
    def up(self, a):
        self.signal_up.emit(True)
    
    def down(self, a):
        self.signal_down.emit(True)

    def stop(self):
        self.quit()
        print('GPIO QUIT')
        self.wait(1000)

class Thread_wait(QThread):
    signal_sleep = pyqtSignal(bool)
    def __init__(self, parent):
        QThread.__init__(self)
        self.parent = parent
        self.wait_time = 0
    
    def run(self):
        while self.wait_time < 10:
            if self.wait_time == -1:
                break
            sleep(1)
            self.wait_time += 1
            print(self.wait_time)
        self.signal_sleep.emit(True)

    def stop(self):
        self.quit()
        print("thread exit")
        self.wait(1000)

class Thread_mic(QThread):
    signal_next = pyqtSignal(list)
    def __init__(self, parent):
        QThread.__init__(self)
        self.parent = parent

    def run(self):
        search = STT()
        lst = search.run()
        # for i in lst:
        #     print(i)
        self.signal_next.emit(lst)
    
    def stop(self):
        self.quit()
        print('MIC QUIT')
        self.wait(1000)

class wait_window(QMainWindow, form_wait_class):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.setWindowFlags(Qt.FramelessWindowHint)
        
    def threadAction(self):
        self.x = Thread_btn(self) 
        self.x.start()
        self.x.signal_next.connect(self.btn_wait_to_start)

    def btn_wait_to_start(self):
        self.x.stop()
        self.push = start_window()
        self.push.show()
        self.push.threadAction()
        self.deleteLater()
        
class start_window(QMainWindow, form_start_class):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.setWindowFlags(Qt.FramelessWindowHint)
        
    def threadAction(self):
        self.x = Thread_btn(self) 
        self.y = Thread_wait(self)
        self.x.start()
        self.y.start()
        self.x.signal_next.connect(self.btn_start_to_push)
        self.y.signal_sleep.connect(self.start_to_wait)

    def start_to_wait(self):
        self.x.stop()
        self.y.stop()
        self.wait = wait_window()
        self.wait.show()
        self.wait.threadAction()
        self.deleteLater()

    def btn_start_to_push(self):
        self.x.stop()
        self.y.stop()
        self.push = listening_window()
        self.push.show()
        self.push.mic_listening.show()
        self.push.threadAction()
        self.deleteLater()

class listening_window(QMainWindow, form_listening_class):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.setWindowFlags(Qt.FramelessWindowHint)

        self.mic_listening = mic_listening()

    def threadAction(self):
        self.x = Thread_mic(self) 
        self.x.start()
        self.x.signal_next.connect(self.btn_listening_to_search)

    def btn_listening_to_search(self, data):
        self.x.stop()
        self.mic_listening.close()
        self.done = done_window(data)
        self.done.show()
        self.done.threadAction()
        self.deleteLater()

class mic_listening(QWidget, form_mic_listening_class):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.move(464, 1296)

        self.movie = QMovie('mic_listening.gif', QtCore.QByteArray(), self)
        self.movie.setCacheMode(QMovie.CacheAll)

        self.mic_listening_gif.setMovie(self.movie)
        self.movie.start()

class done_window(QMainWindow, form_done_class):
    def __init__(self, data):
        super().__init__()
        self.setupUi(self)
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.object_list_file = data
        self.c_row = 0

        object_lst=[]
        for row in self.object_list_file:
            if len(row) != 4:
                row.pop()
            # object_lst.append('%{}s %{}s %{}s %{}s'.format(44-self.word_count(row[0]), 
            # 44-self.word_count(row[1]), 44-self.word_count(row[2]), 
            # 44-self.word_count(row[3])) % (row[0], row[1], row[2], row[3]))
            object_lst.append('{:<10} {:<40} {:<40} {:<40}'.format(
                row[0], row[1], row[2], row[3]))
        
        print(object_lst)
        for row in object_lst:
            self.object_list.addItem(row)
        
        self.row_max = len(object_lst)
        print(self.row_max)
        self.object_list.setCurrentRow(self.c_row)

    def word_count(self, text):
        count = 0
        sp_txt = text.split(' ')
        for word in sp_txt:
            count += len(word)
        return 4*count + len(sp_txt) - 1

        
    def threadAction(self):
        self.x = Thread_btn(self) 
        self.x.start()
        self.x.signal_next.connect(self.btn_done_to_map)
        self.x.signal_up.connect(self.up)
        self.x.signal_down.connect(self.down)

    def up(self):
        self.c_row += 1
        if self.c_row > self.row_max-1:
            self.c_row = self.row_max-1
        self.object_list.setCurrentRow(self.c_row)

    def down(self):
        self.c_row -= 1
        if self.c_row < 0:
            self.c_row = 0
        self.object_list.setCurrentRow(self.c_row)

    def btn_done_to_map(self):
        self.x.stop()
        data = self.object_list_file[self.c_row][0]
        self.start = map_window(data)
        self.start.show()
        self.start.threadAction()
        self.deleteLater()

class map_window(QMainWindow, form_map_class):
    def __init__(self, data):
        super().__init__()
        self.setupUi(self)
        print(data, type(data))
        self.stor = storage()
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.stor.download_file(data)
        map_img = cv2.imread(data+".png")
        resize_map = cv2.resize(map_img, (610,1300))
        resize_map = cv2.cvtColor(resize_map, cv2.COLOR_BGR2RGB) 
        h,w,c = resize_map.shape
        qImg_map = QtGui.QImage(resize_map.data, w, h, w*c, QtGui.QImage.Format_RGB888)
        pixmap_map = QtGui.QPixmap.fromImage(qImg_map)
        self.map.setPixmap(pixmap_map)

        url = self.stor.get_url(data)
        # # url = "http://cafefiles.naver.net/data21/2006/12/6/291/12801024-1-badpark.jpg"
        # map_url = urllib.request.urlopen(url).read()
        # pixmap_map = QtGui.QPixmap()
        # pixmap_map.loadFromData(map_url)
        # self.map.setPixmap(pixmap_map)

        qr_url = qrcode.make(url)
        # qr_url = qr_url.convert("RGBA")
        # out_qr = ImageQt(qr_url)
        # pixmap_qr = QtGui.QPixmap.fromImage(out_qr)
        qr_url.save("qr.png")
        img = cv2.imread("qr.png")
        resize_img = cv2.resize(img, (370,370))
        resize_img = cv2.cvtColor(resize_img, cv2.COLOR_BGR2RGB) 
        h,w,c = resize_img.shape
        qImg = QtGui.QImage(resize_img.data, w, h, w*c, QtGui.QImage.Format_RGB888)
        pixmap_qr = QtGui.QPixmap.fromImage(qImg)
        self.qr.setPixmap(pixmap_qr)

    def threadAction(self):
        self.x = Thread_btn(self) 
        self.x.start()
        self.x.signal_next.connect(self.btn_map_to_start)

    def btn_map_to_start(self):
        self.x.stop()
        self.start = start_window()
        self.start.show()
        self.start.threadAction()
        self.deleteLater()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    myWindow = wait_window()
    myWindow.threadAction()
    myWindow.show()
    app.exec_()