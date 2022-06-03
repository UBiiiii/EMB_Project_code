import sqlite3
from telnetlib import SE
import pyrebase
from time import time
from difflib import SequenceMatcher

firebaseConfig = {
    #insert your firebase config
}

firebase = pyrebase.initialize_app(firebaseConfig)

db = firebase.database()
floor_data = db.get()

conn = sqlite3.connect('./databse.db')

# for floor in floor_data.each():
#     if floor.key() == 0:
#         continue
#     room_data = db.child(floor.key()).get()
#     for room in room_data.each():
#         data = (room.key(), room.val()['name'], room.val()['charge'], room.val()['phone'])
#         sql = "insert into rooms (text room_number, text room_name, text charge, text phone) values (?,?,?,?)"

#         with conn:
#             cur = conn.cursor()
#             cur.execute(sql, data)


#test case 1: 호실 이름으로 찾기.
text = '301'

#sqlite
sql_data = []
sql_t_start = time()
cur = conn.cursor()
cur.execute("select * from rooms")
rows = cur.fetchall()
for row in rows:
    score = max(SequenceMatcher(None, row[1], text).ratio(), SequenceMatcher(None, row[1], text + "연구실").ratio())
    if (text in row[0]) or (text in row[2]) or score > 0.6:
        sql_data.append(row)
conn.close()
print(sql_data)
sql_t_end = time()
print(sql_t_end - sql_t_start)

text = '301'
#firebase
fb_data = []
fb_t_start = time()
floors = db.get()
for floor in floors.each():
    if floor.key() == 0:
        continue
    rooms = db.child(floor.key()).get()
    for room in rooms.each():
        score = max(SequenceMatcher(None, room.val()["name"], text).ratio(), SequenceMatcher(None, room.val()["name"], text + "연구실").ratio())
        if (room.key() in text) or (room.val()["charge"] in text) or score > 0.6:
            fb_data.append(room.val())
print(fb_data)
fb_t_end = time()
print(fb_t_end - fb_t_start)
