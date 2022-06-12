import pyrebase
import sqlite3

import datetime

#해당 코드들은 파이어베이스의 스토리지와 데이터베이스를 사용하기 위한 코드들입니다.
#firebaseConfig에 개인의 파이어베이스 키를 넣어 바로 사용하면 됩니다.

firebaseConfig = {
    #use your firebaseconfig
}

firebase = pyrebase.initialize_app(firebaseConfig)


class authorization:
    def __init__(self):
        self.auth = firebase.auth()

# storage에서 파일 업로드, 다운로드를 위한 코드
class storage:
    def __init__(self):
        self.stor = firebase.storage()

    def upload(self, file_name, cloud_file_name, path=None):
        if path:
            self.stor.child(path).child(cloud_file_name).put(file_name)
        else:
            self.stor.child(cloud_file_name).put(file_name)

    def download_file(self, path, filename):
        download_name = 'download.jpg'
        self.stor.child(path + filename).download("", download_name)

# realtime database에서 데이터 삽입, 수정, 삭제, 탐색을 구현한 함수
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
        if keyword:
            if path:
                datas = self.db.child(path).order_by_child(keyword).get()
            else:
                datas = self.db.order_by_child(keyword).get()
        else:
            if path:
                datas = self.db.child(path).get()
            else:
                datas = self.db.get()

        ret = []
        for data in datas.each():
            ret.append(data.val())
        return ret

# SQLited에서의 생성, 삽입, 탐색을 구현한 함수
class sql:
    def __init__(self):
        self.conn = sqlite3.connect('./database.db')
        cur = self.conn.cursor()
        sql = "CREATE TABLE IF NOT EXISTS rooms(room_number, room_name, charge, phone)"
        cur.execute(sql)

        sql = "CREATE TABLE IF NOT EXISTS latest(room_number, root, qr, time)"
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
        sql = "INSERT INTO  rooms (room_number, room_name, charge, phone) VALUES (?, ?, ?, ?)"
        return self.execute(sql, data)

        # data is tuple.

    def insert_latest(self, data):
        sql = "INSERT INTO latest (room_number, root, qr) VALUES (?, ?, ?)"
        return self.execute(sql, data)

        # text is string.

    def search(self, text):
        default = "SELECT * FROM rooms"
        with self.conn:
            cur = self.conn.cursor()
            cur.execute("SELECT * from rooms where id=? or name=?", (text, text))
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