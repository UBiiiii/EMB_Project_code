import sqlite3
from time import time
import subprocess

#해당 코드들은 sql을 이용한 맵 이미지 캐싱을 위해 사용된 테스트 코드들입니다.

conn = sqlite3.connect('/home/pi/EMB_Project_code/UI_GPIO/database.db')
cur = conn.cursor()

# sql = "CREATE TABLE IF NOT EXISTS latest(number text, time INTEGER)"
# cur.execute(sql)

# sql = "INSERT INTO  latest (number, time) VALUES ({}, {})".format('305', 456789)

# cur.execute(sql)
# conn.commit()

rows = cur.execute('SELECT * from latest')
print(rows.fetchall())

# for row in cur.execute('SELECT * from latest ORDER BY time DESC LIMIT 1'):
#     num = row[0]

# subprocess.call('rm ./UI_GPIO/download/map/{}.png'.format(num), shell=True)
    
conn.close()