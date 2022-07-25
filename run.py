from EdgePolling import EdgeAPIPolling
from MerakiMySQL import MerakiPollingSQL
import time
import os

SQL_USR = ""
SQL_PW = ""
API_KEY = ""
ORG_ID = ""

def get_meraki():
    meraki = MerakiPollingSQL(SQL_USR, SQL_PW, API_KEY, ORG_ID)

    meraki.run_data_collection()
    meraki.delete_old(7500)
    os.system("rm *.log")

def get_edge():
    edge = EdgeAPIPolling(SQL_USR, SQL_PW)

    edge.pull_info()
    edge.write_to_db()

if __name__ =="__main__":
    iterations = 60

    while True:
        get_edge()
        time.sleep(10)

        iterations += 1

        if iterations >= 60:
            get_meraki()
            iterations = 0
