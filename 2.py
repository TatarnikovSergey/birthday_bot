import sqlite3
from datetime import datetime, timedelta

date = datetime.now() - timedelta(days=4)
current_date = date.strftime("%d.%m")


con = sqlite3.connect('staff.db')
cur = con.cursor()

result = cur.execute('''
    SELECT name, phone_number 
    FROM staff
    WHERE strftime('%d', date_of_birth) = '20'; 
    
''')

for row in result:
    print(*row)
print(current_date)
con.close()