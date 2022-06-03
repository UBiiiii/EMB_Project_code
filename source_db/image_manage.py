import sqlite3
from time import time
import subprocess

conn = sqlite3.connect('./database.db')
cur = conn.cursor()

# sql = "CREATE TABLE IF NOT EXISTS latest(number text, time INTEGER)"
# cur.execute(sql)

# sql = "INSERT INTO  latest (number, time) VALUES ({}, {})".format('305', 456789)

# cur.execute(sql)
# conn.commit()

rows = cur.execute('SELECT * from latest')
print(len(rows.fetchall()))

# for row in cur.execute('SELECT * from latest ORDER BY time DESC LIMIT 1'):
#     num = row[0]

# subprocess.call('rm ./UI_GPIO/download/map/{}.png'.format(num), shell=True)
    
conn.close()