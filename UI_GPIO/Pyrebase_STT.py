# import pyrebase
# import speech_recognition as sr
# from difflib import SequenceMatcher

# #-*- coding: utf-8 -*-

# class STT:
#     def __init__(self):
#         firebaseConfig = {
                #insert your firebase config
#         }

#         firebase = pyrebase.initialize_app(firebaseConfig)
#         # Get Database
#         self.db = firebase.database()

#     def run(self):
#         # Obtain audio from the microphone
#         r = sr.Recognizer()
#         with sr.Microphone() as source:
#             r.adjust_for_ambient_noise(source)
            
#             print("Say something!")
#             try:
#                 audio = r.listen(source, timeout=5)
#             except:
#                 print("시간이 초과되었습니다.")
#                 return

#         # STT
#         try:
#             input = r.recognize_google(audio, language='ko')
#             print(input)
#         except sr.UnknownValueError:
#             print("음성을 인식하지 못 했습니다.")
#             return
#         except sr.RequestError as e:
#             print("에러 {0}".format(e))
#             return

#         # Compare
#         room_list = []
#         floors = self.db.get()
#         for floor in floors.each():
#             if floor.key() == 0:
#                 continue
#             rooms = self.db.child(floor.key()).get()
#             for room in rooms.each():
#                 score = max(SequenceMatcher(None, room.val()["name"], input).ratio(), 
#                             SequenceMatcher(None, room.val()["name"], input + "연구실").ratio())
#                 if score > 0.6 or (room.val()["charge"] in input) or (room.key() in input):
#                     information = [room.key()] + [i for i in room.val().values()]
#                     room_list.append(information)

#         if len(room_list) == 0:
#             print("찾지 못했습니다.")
#             return

#         return room_list

import pyrebase
import speech_recognition as sr
from difflib import SequenceMatcher

#-*- coding: utf-8 -*-

class STT:
    def __init__(self):
        firebaseConfig = {
            #insert your firebase config
        }

        firebase = pyrebase.initialize_app(firebaseConfig)
        # Get Database
        self.db = firebase.database()

        self.recognizer = sr.Recognizer()
        self.mic = sr.Microphone()

        with self.mic as source:
            self.recognizer.adjust_for_ambient_noise(source)

    def run(self):
        # Obtain audio from the microphone
        with self.mic as source:
            print("Say something!")
            try:
                audio = self.recognizer.listen(source, timeout=5)
            except:
                print("시간이 초과되었습니다.")
                return

        # STT
        try:
            input = self.recognizer.recognize_google(audio, language='ko')
            print(input)
        except sr.UnknownValueError:
            print("음성을 인식하지 못 했습니다.")
            return
        except sr.RequestError as e:
            print("에러 {0}".format(e))
            return

        # Compare
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
            print("찾지 못했습니다.")
            return

        return room_list