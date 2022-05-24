import pyrebase
import sqlite3

import datetime

from enum import auto
import sys

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

def page_next():
    global current_page
    current_page += 1


def row_down():
    global current_row
    current_row += 1


def row_up():
    global current_row
    current_row -= 1


class authorization:
    def __init__(self):
        self.auth = firebase.auth()


class storage:
    def __init__(self):
        self.stor = firebase.storage()

    def upload(self, file_name, cloud_file_name, path=None):
        if path:
            self.stor.child(path).child(cloud_file_name).put(file_name)
        else:
            self.stor.child(cloud_file_name).put(file_name)

    def download_file(self, filename):
        self.stor.child('result').child('floor' + filename[0]).child(filename+".png").download("", filename+".png")

    def get_url(self, filename):
        return self.stor.child("result/floor{}/{}.png".format(filename[0], filename)).get_url(token='')


class database:
    def __init__(self):
        self.db = firebase.database()

    def push(self, path, data):
        self.db.child(path).push(data)

    def set(self, path, data):
        self.db.child(path).set(data)

    def update(self, path, data):
        self.db.child(path).update(data)

    def delete(self, path, key):
        self.db.child(path).child(key).remove()

    def read_key(self, path=None):
        if path:
            datas = self.db.child(path).get()
        else:
            datas = self.db.get()
        ret = []
        for data in datas.each():
            ret.append(data.key())
        return ret

    def read_data(self, path=None, keyword=None):

        floors = self.db.get()

        ret = []
        for floor in floors.each():
            if floor.key() == 0:
                continue
            rooms = self.db.child(floor.key()).get()
            for room in rooms.each():
                room.val()["number"] = room.key()
                ret.append(room.val())
        return ret


class sql:
    def __init__(self):
        self.conn = sqlite3.connect('./database.db')
        cur = self.conn.cursor()
        sql = "CREATE TABLE IF NOT EXISTS rooms(number, name, charge, phone)"
        cur.execute(sql)

        sql = "CREATE TABLE IF NOT EXISTS latest(number, root, qr, time)"
        cur.execute(sql)

    # sql is string, data is tuple

    def execute(self, sql, data=None):
        with self.conn:
            cur = self.conn.cursor()
            if data:
                try:
                    cur.executemany(sql, data)
                except:
                    return -1
            else:
                try:
                    cur.execute(sql)
                except:
                    return -1

            self.conn.commit()
            return 1

        # data is tuple.

    def insert_rooms(self, data):
        sql = "INSERT INTO  rooms (number, name, charge, phone) VALUES (?, ?, ?, ?)"
        return self.execute(sql, data)

        # data is tuple.

    def insert_latest(self, data):
        sql = "INSERT INTO latest (number, root, qr, time) VALUES (?, ?, ?, ?)"
        return self.execute(sql, data)

        # text is string.

    def search(self):
        with self.conn:
            cur = self.conn.cursor()
            cur.execute("SELECT * from rooms")
            rows = cur.fetchall()

        return rows

    # rooms and data are list.
    # rooms: 변화된 방 번호
    # data: 방들의 키
    def update_changes(self, rooms, data):
        update_sql = []
        cur = self.conn.cursor()
        for i in range(len(rooms)):
            room = rooms[i]
            key_chain = data[i].key()
            for key in key_chain:
                sql = "UPDATE rooms SET {} = ? WHERE room_number = {}".format(key, data[i][key], room)
                if self.execute(sql) == -1:
                    print("Update failed. point is {}.".format(key))
                    return -1

    def clear(self):
        sql = "DELETE from rooms"
        return self.conn.execute("DELETE from rooms").rowcount