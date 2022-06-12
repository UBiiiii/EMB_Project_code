import pyrebase
import sqlite3

import subprocess

firebaseConfig = {
    #input your firebase config
}

firebase = pyrebase.initialize_app(firebaseConfig)

# firebase storage로부터 경로 이미지 다운로드 및 url 반환을 위한 클래스
class storage:
    def __init__(self):
        self.stor = firebase.storage()

    def download_file(self, filename):
        self.stor.child("result/floor{}/{}.png".format(filename[0], filename)).download('',"/home/pi/EMB_Project_code/UI_GPIO/download/map/" + filename+".png")

    def get_url(self, filename):
        return self.stor.child("result/floor{}/{}.png".format(filename[0], filename)).get_url(token='')

# firebase realtime database로부터 데이터 다운로드를 위한 클래스
class database:
    def __init__(self):
        self.db = firebase.database()

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

    def redirect(self, number):
        ret = number
        
        ret = self.db.child("{}/{}/redirect".format(number[0], number)).get().val()
        if ret != None:
            return str(ret)
        else:
            return number

# 경로 이미지 캐싱을 위한 클래스
class sql:
    def __init__(self):
        self.conn = sqlite3.connect('/home/pi/EMB_Project_code/UI_GPIO/database.db')
        cur = self.conn.cursor()
        sql = "CREATE TABLE IF NOT EXISTS latest(number text, time integer)"
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
    def insert_latest(self, num, time):
        with self.conn:
            cur = self.conn.cursor()
            sql = 'INSERT INTO latest (number, time) VALUES ({}, {})'.format(num, time)
            cur.execute(sql)
            self.conn.commit()

    # text is string.
    def search(self):
        with self.conn:
            cur = self.conn.cursor()
            cur.execute('SELECT * from rooms')
            rows = cur.fetchall()

        return rows

    def check_len(self):
        with self.conn:
            cur = self.conn.cursor()
            maps = cur.execute('SELECT * FROM latest')
        
        return len(maps.fetchall())

    def check_map(self, room):
        print(room)
        with self.conn:
            cur = self.conn.cursor()
            sql = 'SELECT * FROM latest WHERE number = {}'.format(room)
            cur.execute(sql)
            word = cur.fetchall()
            if len(word) <1:
                return False
            else:
                return True

    def delete(self):
        with self.conn:
            cur = self.conn.cursor()
            sql = 'SELECT number FROM latest ORDER BY time LIMIT 1'
            cur.execute(sql)
            room = cur.fetchall()
            print(room[0][0])
            sql = 'DELETE FROM latest where number = {}'.format(room[0][0])
            cur.execute(sql)
            self.conn.commit()
            subprocess.call('rm /home/pi/EMB_Project_code/UI_GPIO/download/map/{}.png'.format(room[0][0]), shell=True)
            subprocess.call('rm /home/pi/EMB_Project_code/UI_GPIO/download/qr/{}.png'.format(room[0][0]), shell=True)

    def clear(self):
        sql = "DELETE from rooms"
        return self.conn.execute("DELETE from rooms").rowcount