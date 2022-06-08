import pyrebase
import sqlite3

import subprocess

firebaseConfig = {
    #insert your firebase config
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
        self.stor.child("result/floor{}/{}.png".format(filename[0], filename)).download('',"/home/pi/EMB_Project_code/UI_GPIO/download/map/" + filename+".png")

    def get_url(self, filename):
        return self.stor.child("result/floor{}/{}.png".format(filename[0], filename)).get_url(token='')


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

    def insert_rooms(self, data):
        sql = "INSERT INTO  rooms (number, name, charge, phone) VALUES (?, ?, ?, ?)"
        return self.execute(sql, data)

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