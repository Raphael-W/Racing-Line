import sqlite3
from tabulate import tabulate

con = sqlite3.connect("raceTimes.db")
cur = con.cursor()
cur.execute("SELECT * FROM TIMES")
allData = cur.fetchall()
print("Race Times Database:\n")
print(tabulate(allData, headers=['UUID', 'Time', 'Date'], tablefmt='github'))
print()

query = None
while query != '':
    query = input("Enter SQL query: ")
    try:
        cur.execute(query)
        selectedData = allData = cur.fetchall()
        print(tabulate(allData, tablefmt = 'github'))
    except Exception as error:
        print(error)

    print()