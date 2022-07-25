import mysql.connector
import meraki
import time

#TODO: Ensure that all SQL queries and requests are properly sanitized.

class MerakiPollingSQL():
    def __init__(self, sql_login, sql_pw, api_key, org_id):
        #Globally accesibile variables
        self.SQL_USER = sql_login
        self.SQL_PASSWORD = sql_pw
        self.API_KEY = api_key
        self.ORG_ID = org_id
        self.networks_and_ids = {}

#Sum information from response JSON
    def sum_network_response(self, response, detect):
        total = 0
        for item in list(response):
            total += item[detect]
        return total

    def delete_old(self, subtract):
        connection = mysql.connector.connect(user=self.SQL_USER, password=self.SQL_PASSWORD, host='127.0.0.1', database='networks')
        cur = connection.cursor()
        now = int(time.time())
        then = now - subtract

        #Selects all data older than "then" and removes it, then saves the updated database.
        cur.execute("DELETE FROM networks WHERE time < " + str(then))
        connection.commit()
        cur.close()
        connection.close()

    def run_data_collection(self):
        dashboard = meraki.DashboardAPI(self.API_KEY)
        response = dashboard.organizations.getOrganizationNetworks(self.ORG_ID)

        con = mysql.connector.connect(user=self.SQL_USER, password=self.SQL_PASSWORD, host='127.0.0.1', database='networks')

        #SQLite database connection
        cur = con.cursor()
        cur.execute("CREATE TABLE IF NOT EXISTS networks(networkID TEXT, name TEXT, number INTEGER, sent INTEGER, recv INTEGER, time INTEGER)")
        
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
                sent = self.sum_network_response(response, 'sent')
                recieved = self.sum_network_response(response, 'recv')
                place = 0

                #This ensures consistency on the meraki dashboard if a network is added or removed while the program is running. After reset, however,
                #if networks have been added and/or removed, dynamic requests on Grafana using the number column may change which network is being displayed.
                if network in self.networks_and_ids.keys():
                    place = self.networks_and_ids[network]
                else:
                    place = len(self.networks_and_ids)
                    self.networks_and_ids[network] = place
                    
                #Commit retrieved data to sql db.
                cur.execute("INSERT INTO networks(networkID, name, number, sent, recv, time) VALUES(%s, %s, %s, %s, %s, %s)", (str(network), str(network_names[i]), str(place), str(sent), str(recieved), str(now)))
            except Exception as e:
                print("Unable to retrieve information on network " + network)
                print(e)

            i += 1
        
        #Save and close database.
        con.commit()
        cur.close()
        con.close()

if __name__ == "__main__":
    polling = MerakiPollingSQL()

    polling.run_data_collection()
    polling.delete_old(7500)