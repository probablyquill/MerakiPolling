import meraki
import sqlite3
import time

#TODO: Ensure that all SQL queries and requests are properly sanitized.

#Globally accesibile variables
API_KEY = ""
ORG_ID = ""
database = "meraki.db"
networks_and_ids = {}

#Sum information from response JSON
def sum_network_response(response, detect):
    total = 0
    for item in list(response):
        total += item[detect]
    return total

def delete_old():
    con = sqlite3.connect(database)
    cur = con.cursor()
    now = int(time.time())
    then = now - 7500

    #Selects all data older than "then" and removes it, then saves the updated database.
    cur.execute("DELETE FROM networks WHERE time < " + str(then))
    con.commit()
    con.close()

def run_data_collection():
    dashboard = meraki.DashboardAPI(API_KEY)
    response = dashboard.organizations.getOrganizationNetworks(ORG_ID)

    #SQLite database connection
    con = sqlite3.connect(database)
    cur = con.cursor()
    now = int(time.time())
    
    #Create/reset network_ids and network_names arrays.
    network_ids = []
    network_names = []

    #Create parallel lists continaining network names and ids.
    for item in list(response):
        network_ids.append(item['id'])
        network_names.append(item['name'])

    #Iterator to track position in first list.
    i = 0
    for network in network_ids:
        #A network being listed as read only, or otherwise being inaccesable, will result in an error being thrown, hence the try-catch block.
        try:
            response = dashboard.networks.getNetworkTraffic(network, timespan=7200)
            sent = sum_network_response(response, 'sent')
            recieved = sum_network_response(response, 'recv')
            place = 0

            #This ensures consistency on the meraki dashboard if a network is added or removed while the program is running. After reset, however,
            #if networks have been added and/or removed, dynamic requests on Grafana using the number column may change which network is being displayed.
            if network in networks_and_ids.keys():
                place = networks_and_ids[network]
            else:
                place = len(networks_and_ids) + 1
                networks_and_ids[network] = place
                
            #Commit retrieved data to sql db.
            #TODO: Sanitize input
            cur.execute("CREATE TABLE IF NOT EXISTS networks(networkID TEXT, name TEXT, number INTEGER, sent INTEGER, recv INTEGER, time INTEGER)")
            cur.execute("INSERT INTO networks(networkID, name, number, sent, recv, time) VALUES('" + str(network) + "', " + str("'" + network_names[i] + "'") + ", " + str(place) + ", " + str(sent) + ", " + str(recieved) + ", " + str(now) + ")")
        except Exception as e:
            print("Unable to retrieve information on network " + network)
            print(e)

        i += 1
    
    #Save and close database.
    con.commit()
    con.close()

while True:
    run_data_collection()
    delete_old()
    print("Sleeping")
    #Wait for five minutes before looping again.
    #Meraki API calls take ~15-20s total, so the time
    #to sleep for it to happen every ~5 minutes is a bit under 300s.
    time.sleep(285)