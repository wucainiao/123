import sqlite3
conn=sqlite3.connect('xianxia_dev.db')
cur=conn.cursor()
print('PRAGMA table_info(meridian):')
for row in cur.execute("PRAGMA table_info('meridian')"):
    print(row)
print('\nSQL for meridian:')
for row in cur.execute("SELECT sql FROM sqlite_master WHERE name='meridian' LIMIT 1"):
    print(row)
conn.close()
