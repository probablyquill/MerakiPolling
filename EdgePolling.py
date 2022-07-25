import requests
import json
import mysql.connector

class EdgeAPIPolling():
    def __init__(self, sql_login, sql_pw):
        self.SQL_USER = sql_login
        self.SQL_PASS = sql_pw

        #Login wants a POST request with the content formatted as: {"username":"name", "password":"pwd"}
        self.info = {
            'password':'',
            'username':''
        }

        self.io_list = []

    #Request Info from Edge
    def pull_info(self):
        with requests.Session() as s:
            r = s.post(url = "https://streamstation.cloud/api/login/", json = self.info)

            key = r.content.decode('utf-8')
            key = json.loads(key)
            #print("SESSION INFO: ")
            #print(json.dumps(key, indent=2))

            r = s.get(url = "https://streamstation.cloud/api/region/")

            region_info = r.content.decode('utf-8')
            region_info = json.loads(region_info)

            #print("\nREGION INFO: ")
            for element in region_info["items"]:
                region_id = element["id"]

                r = s.get(url = "https://streamstation.cloud/api/region/" + region_id)
                sub_region = r.content.decode("utf-8")
                sub_region = json.loads(sub_region)
                #print(json.dumps(sub_region, indent = 2))

            r = s.get(url = "https://streamstation.cloud/api/input/")
            inputs = r.content.decode('utf-8')
            inputs = json.loads(inputs)

            #print("\nINPUTS: ")
            for item in inputs['items']:
                temp = {
                    "name":item['name'],
                    "status":item['health']['state'],
                    "msg":item['health']['title'],
                    "id":item['id'],
                    "inout": 0
                }
                #print(item['name'] + " | " + item['health']['state'] + " | " + item['health']['title'])
                self.io_list.append(temp)

            r = s.get(url = "https://streamstation.cloud/api/output/")

            outputs = r.content.decode('utf-8')
            outputs = json.loads(outputs)
            
            #print("\nOUTPUTS: ")
            for output in outputs["items"]:
                temp = {
                    "name":output['name'],
                    "status":output['health']['state'],
                    "msg":output['health']['title'],
                    "id":output['id'],
                    "inout":1
                }
                #print(output['name'] + " | " + output['health']['state'] + " | " + output['health']['title'])
                self.io_list.append(temp)

            #log out
            r = s.post(url = "https://streamstation.cloud/api/logout/", json = key)

    def write_to_db(self):
        #SQL Section
        cnx = mysql.connector.connect(user=self.SQL_USER, password=self.SQL_PASS, host='127.0.0.1', database='edge')

        cur = cnx.cursor()
        cur.execute("TRUNCATE TABLE fields;")
        cur.execute("CREATE TABLE IF NOT EXISTS fields(name TEXT, status TEXT, msg TEXT, edgeID TEXT, isout INT);")

        for item in self.io_list:
            cur.execute("INSERT INTO fields(name, status, msg, edgeID, isout) VALUES (%s, %s, %s, %s, %s)", (item['name'], item['status'], item['msg'], item['id'], item['inout']))

        cnx.commit()
        cur.close()
        cnx.close
        
if __name__ == "__main__":
    poller = EdgeAPIPolling()
    poller.pull_info()
    poller.write_to_db()