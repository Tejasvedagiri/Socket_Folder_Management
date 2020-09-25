import sqlite3
import socket
import threading
import json  
import os
class OSUtils():
    def __init__(self):
        self.base_path = os.path.join(os.getcwd(), "Directories")
        if not os.path.exists(self.base_path):
            os.mkdir(self.base_path)  

    def getUserDir(self,data): 
        path = os.path.join(self.base_path ,  data['userName'])
        if not os.path.exists(path):
            os.mkdir(path)    
        x = os.listdir(path)
        return x

    def createFolder(self,data):
        path = os.path.join(self.base_path , data['userName'], data['folderName'])
        if not os.path.exists(path):
            os.mkdir(path)  
        data['message'] = "Created succefully"
        data['dir'] = self.getUserDir(data)
        return data

class ClientThread(threading.Thread):
    def __init__(self,clientAddress,clientsocket):

        threading.Thread.__init__(self)
        self.csocket = clientsocket
        self.dbUtils =  DBUtils("TEST.db")
        self.osUtils = OSUtils()
        print ("New connection added: ", clientAddress)

    def run(self):
        print ("Connection from : ", clientAddress)
        #self.csocket.send(bytes("Hi, This is from Server..",'utf-8'))
        msg = ''
        while True:
            data = self.csocket.recv(2048)
            msg = data.decode()
            print(msg)
            data = json.loads(msg)
            if data['action'] =='TERMINATE':
                self.closeClient()
                self.dbUtils.close()
                break
            elif data['action'] == 'LOGIN':
                rec = (data['userName'],)
                out = self.dbUtils.getOrCreateUser(rec)
                out['dir'] = self.osUtils.getUserDir(data)
                self.csocket.send(bytes(json.dumps(out),'UTF-8'))
            elif data['action'] == 'CREATEFOLDER':
                out = self.osUtils.createFolder(data)
                self.csocket.send(bytes(json.dumps(out),'UTF-8'))
            else:
                print("Invalid Input")
                self.closeClient()
                break

    def closeClient(self):
        self.dbUtils.close()
        self.csocket.send(bytes("BYE",'UTF-8'))
        print ("Client at ", clientAddress , " disconnected...")

class DBUtils():
    def __init__(self,DB_Name):

        self.con = sqlite3.connect(DB_Name ,check_same_thread=False)
        self.create_tables()
        #self.test()

    def create_tables(self):
        
        c = self.con.cursor()
        c.execute('CREATE TABLE IF NOT EXISTS USER (id INTEGER PRIMARY KEY AUTOINCREMENT, name text not null)')
        self.con.commit()
        print("TABLE CREATED")
    
    def test(self):
        c = self.con.cursor()
        c.execute("INSERT INTO USER (name) values ('Tejas')")
        x = c.execute("select * from USER").fetchone()
        print(type(x))
        print(dir(x))
        print(x)
    
    def getOrCreateUser(self,rec):
        data = self.getUser(rec)
        if len(data) == 0:
            self.createUser(rec)
            data = self.getUser(rec)
        user_dict = {}
        user_dict['id'] = data[0][0]
        user_dict['userName'] = data[0][1]
        user_dict['message'] = 'LOGIN SUCCESFUL'
        return user_dict

    def getUser(self, rec):
        c = self.con.cursor()
        c.execute("SELECT * from USER where name = ?",rec)
        return c.fetchall()

    def createUser(self, rec):
        c = self.con.cursor()
        c.execute("INSERT INTO USER (name) values (?)",rec)
        self.con.commit()

    def close(self):
        self.con.close()
   
dbUtils = DBUtils("TEST.db")
#rec = ("Tejas",)
#print(dbUtils.getOrCreateUser(rec))

HOST = 'localhost'
PORT = 12122


server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server.bind((HOST, PORT))
print("Server started")
print("Waiting for client request..")
while True:
    server.listen(10)
    clientsock, clientAddress = server.accept()
    newthread = ClientThread(clientAddress, clientsock)
    newthread.start()