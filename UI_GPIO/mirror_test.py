from cgitb import text
from dataclasses import dataclass
import os
import sys
from xmlrpc.client import boolean
from Pyrebase_STT import STT
import urllib.request

from db_code import *
import pyrebase

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

from time import sleep, time

import cv2
import qrcode

def resource_path(relative_path):
    base_path = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_path, relative_path)

form = resource_path('navi_mirror.ui')
form_class = uic.loadUiType(form)[0]

form_mic_listening = resource_path('mic_listening.ui')
form_mic_listening_class = uic.loadUiType(form_mic_listening)[0]

form_mic_retry = resource_path('mic_retry.ui')
form_mic_retry_class = uic.loadUiType(form_mic_retry)[0]

firebaseConfig = {
    'apiKey': "AIzaSyDGIQoNHBmyjdiS3YLU_kFoGgyXzVcoM3k",
    'authDomain': "proj2022-3cd0d.firebaseapp.com",
    'databaseURL': "https://proj2022-3cd0d-default-rtdb.firebaseio.com",
    'projectId': "proj2022-3cd0d",
    'storageBucket': "proj2022-3cd0d.appspot.com",
    'messagingSenderId': "752819259660",
    'appId': "1:752819259660:web:dc7e0da1d53f6e7043e129",
    'measurementId': "G-3FSHGHRZ54"
}

firebase = pyrebase.initialize_app(firebaseConfig)

class Thread_btn(QThread):
    signal_next = pyqtSignal(int)
    signal_up = pyqtSignal(int)
    signal_down = pyqtSignal(int)
    def __init__(self, parent):
        QThread.__init__(self)
        self.parent = parent
        self.row = 0
        self.current_page = 0

    def run(self):
        self.parent.signal_current_page.connect(self.count)
        GPIO.setmode(GPIO.BOARD)
        GPIO.setup([12,18,22], GPIO.IN)
        try:
            GPIO.add_event_detect(12, GPIO.RISING, callback=self.test, bouncetime=800)
            GPIO.add_event_detect(18, GPIO.RISING, callback=self.up, bouncetime=800)
            GPIO.add_event_detect(22, GPIO.RISING, callback=self.down, bouncetime=800)
        except:
            GPIO.cleanup()
            GPIO.setmode(GPIO.BOARD)
            GPIO.setup([12,18,22], GPIO.IN)
            GPIO.add_event_detect(12, GPIO.RISING, callback=self.test, bouncetime=800)
            GPIO.add_event_detect(18, GPIO.RISING, callback=self.up, bouncetime=800)
            GPIO.add_event_detect(22, GPIO.RISING, callback=self.down, bouncetime=800)

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

class Thread_mic(QThread):
    signal_retry = pyqtSignal(bool)
    signal_next = pyqtSignal(list)
    signal_ready = pyqtSignal(bool)

    def __init__(self, parent):
        QThread.__init__(self)
        self.parent = parent
        self.r = sr.Recognizer()

        # Get Database
        self.db = firebase.database()
 
    def run(self):
        sleep(1)
        with sr.Microphone() as source:
            self.r.adjust_for_ambient_noise(source)

            self.signal_ready.emit(True)
            print("말을 해!!")
            try:
                audio = self.r.listen(source, timeout = 5)
            except:
                self.signal_retry.emit(True)
                print("실패?")
                sleep(3)
                return
        try:
            input = self.r.recognize_google(audio, language='ko')
            print(input)

        except sr.UnknownValueError:
            self.signal_retry.emit(True)
            print("음성을 인식하지 못 했습니다.")
            return

        except sr.RequestError as e:
            self.signal_retry.emit(True)
            print("에러 {0}".format(e))
            return
        
        room_list = []
        floors = self.db.get()
        for floor in floors.each():
            if floor.key() == 0:
                continue
            rooms = self.db.child(floor.key()).get()
            for room in rooms.each():
                score = SequenceMatcher(None, room.val()["name"], input).ratio()
                if (score > 0.6 or (room.val()["charge"] in input) or (room.key() in input) or (input in room.val()["name"])):
                    information = [room.key()] + [i for i in room.val().values()]
                    room_list.append(information)

        if len(room_list) == 0:
            self.signal_retry.emit(True)
            print("찾지 못했습니다.")
            return

        self.signal_next.emit(room_list)

    def stop(self):
        self.quit()
        self.wait(1000)

# class Thread_sql(QThread):
#     signal_check = pyqtSignal(list)
#     def __init__(self, parent):
#         QThread.__init__(self)
#         self.parent = parent
#         self.sql_db = db_code.sql()
#         self.fb_db = db_code.database()
#         self.parent.signal_search.connect(self.check)
#         self.paretn.signal_update.connect(self.update)

#     def update(self):
#         self.sql_db.clear()
#         rooms = self.fb_db.read_data()
#         for room in rooms:
#             data = (room["number"], room["name"], room["charge"], room["phone"])
#             self.sql_db.insert_rooms(data)

#     def check(self, text):
#         ret = []
#         rows = self.sql_db.search()
#         for row in rows:
#             score = max(SequenceMatcher(None, row[1], input).ratio(), 
#                     SequenceMatcher(None, row[1], input + "연구실").ratio())
#             if score > 0.6 or row[0] in text or row[2] in text or text in row[1]:
#                 ret.append(row)
#         print("check!")
#         self.signal_check.emit(ret)

#     def stop(self):
#         self.quit()
#         self.wait(1000)

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

    def threadAction(self):
        self.btn = Thread_btn(self)
        self.btn.signal_up.connect(self.up)
        self.btn.signal_down.connect(self.down)
        self.btn.signal_next.connect(self.next)
        
        self.mic = Thread_mic(self)
        self.mic.signal_next.connect(self.next)
        self.mic.signal_ready.connect(self.view)
        self.mic.signal_retry.connect(self.retry)

        self.sleep = Thread_wait(self)
        self.sleep.signal_sleep.connect(self.home)

        # self.sql = Thread_sql(self)
        self.btn.start()

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
        

    def view(self):
        self.mic_listening.show()
        # self.sttStart = time.time() # stt check

    def up(self):
        self.c_row += 1
        if self.c_row > self.row_max:
            self.c_row = self.row_max
        self.object_list.setCurrentRow(self.c_row)

    def down(self):
        self.c_row -= 1
        if self.c_row < 0:
            self.c_row = 0
        self.object_list.setCurrentRow(self.c_row)

    def next(self, data):
        print('Push!')
        self.current_page += 1
        if self.current_page == 5:
            self.current_page = 1

        if self.current_page == 6:
            self.mic_retry.close()
            self.current_page = 2
            

        if self.current_page == 1:
            self.object_substitute_list = []
            self.sleep.start()
            # self.start = time.time() #check

        elif self.current_page == 2:
            self.mic_retry.close()
            self.mic_retry.stop()
            self.signal_page_change.emit(True)
            self.mic.start()
        
        elif self.current_page == 3:
            self.mic_listening.close()
            self.object_substitute_list = data
            self.addItem()
            # self.sttDone = time.time() # stt check
        
        elif self.current_page == 4:
            if self.c_row == 0:
                self.current_page = 1
            else:
                self.object_list.clear()
                room = self.object_substitute_list[self.c_row-1][0]
                # if self.sql.check_map(room) == False:
                #     if self.sql.check_len() > 10:
                #         self.sql.delete()
                #     self.stor.download_file(room)
                #     self.sql.insert_latest(room, time())
                self.stor.download_file(room)
                map_img = cv2.imread("./download/map/" +room + ".png")
                resize_map = cv2.resize(map_img, (610,1300))
                resize_map = cv2.cvtColor(resize_map, cv2.COLOR_BGR2RGB) 
                h,w,c = resize_map.shape
                qImg_map = QtGui.QImage(resize_map.data, w, h, w*c, QtGui.QImage.Format_RGB888)
                pixmap_map = QtGui.QPixmap.fromImage(qImg_map)
                self.map.setPixmap(pixmap_map)

                url = self.stor.get_url(room)
                qr_url = qrcode.make(url)
                qr_url.save("./download/qr/" + room + ".png")
                img = cv2.imread("./download/qr/" + room + ".png")
                resize_img = cv2.resize(img, (370,370))
                resize_img = cv2.cvtColor(resize_img, cv2.COLOR_BGR2RGB) 
                h,w,c = resize_img.shape
                qImg = QtGui.QImage(resize_img.data, w, h, w*c, QtGui.QImage.Format_RGB888)
                pixmap_qr = QtGui.QPixmap.fromImage(qImg)
                self.qr.setPixmap(pixmap_qr)
            # self.end = time.time() # check
            print("scenario taked ",self.end - self.start,"stt taked ", 
            self.sttDone - self.sttStart)
            


        
        elif self.current_page == 6:
            self.signal_page_change.emit(True)
            self.current_page = 2
            self.mic.start()
    
        self.signal_current_page.emit(self.current_page)
        self.navi_mirror_scenario.setCurrentIndex(self.current_page)
        print(self.current_page)

    # def search(self, data):
    #     self.        

    def addItem(self):
        self.c_row = 0
        object_lst=[]
        for row in self.object_substitute_list:
            # row.pop()
            if len(row) != 4:
                row.pop()
            # object_lst.append('%{}s %{}s %{}s %{}s'.format(44-self.word_count(row[0]), 
            # 44-self.word_count(row[1]), 44-self.word_count(row[2]), 
            # 44-self.word_count(row[3])) % (row[0], row[1], row[2], row[3]))
            # object_lst.append('{:<10} {:<40} {:<40} {:<40}'.format(
                # row[0], row[1], row[2], row[3]))
            object_lst.append('%{}s %{}s %{}s %{}s'.format(13, 38 - 
            3*(len(row[1]) - len(row[1].split())), 66 - 3*(len(row[2]) - len(row[2].split())), 
            25) % (row[0], row[1], row[2], row[3]))
        
        self.row_max = len(object_lst)
        self.object_list.addItem('처음으로 돌아가기')
        for obj in object_lst:
            self.object_list.addItem(obj)


    def retry(self):
        self.signal_init.emit(True)
        self.mic_listening.close()
        self.current_page = 5
        self.signal_current_page.emit(self.current_page)
        self.navi_mirror_scenario.setCurrentIndex(self.current_page)
        self.sleep.start()
        self.mic_retry.show()
        self.mic_retry.start()

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

class mic_retry(QWidget, form_mic_retry_class):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.move(464, 1296)

        self.movie = QMovie('mic_timeout_10.gif', QtCore.QByteArray(), self)
        self.movie.setCacheMode(QMovie.CacheAll)

        self.mic_retry_gif.setMovie(self.movie)

    def start(self):
        self.movie.start()

    def stop(self):
        self.movie.stop()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    myWindow = MainWindow()
    myWindow.threadAction()
    myWindow.show()
    app.exec_()