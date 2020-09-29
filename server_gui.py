import tkinter as tk                
from tkinter import font as tkfont  
import socket 
import json
import sqlite3
import threading
import os
import time

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
        self.clientAddress = clientAddress
        self.clientsocket = clientsocket
        print ("New connection added: ", clientAddress)

    def run(self):
        print ("Connection from : ", self.clientAddress)
        #self.csocket.send(bytes("Hi, This is from Server..",'utf-8'))
        msg = ''
        while True:
            data = self.csocket.recv(2048)
            msg = data.decode()
            if len(msg) != 0 :
                data = json.loads(msg)
            else:
                data = {}
                data['action'] = 'new'
            print(data)
            if data['action'] =='TERMINATE':
                self.closeClient()
                self.dbUtils.close()
                break
            elif data['action'] == 'CREATEUSER':
                rec = (data['userName'],)
                out = self.dbUtils.createUser(rec)
                self.csocket.send(bytes(json.dumps(out),'UTF-8'))
            elif data['action'] == 'LOGOUT':
                rec = (data['userName'],)
                self.dbUtils.logOut(rec)
                self.dbUtils.close()
                break
            elif data['action'] == 'LOGIN':
                print("HERE")
                rec = (data['userName'],)
                out = self.dbUtils.getUser(rec)
                print(out)
                out['dir'] = self.osUtils.getUserDir(data)
                self.csocket.send(bytes(json.dumps(out),'UTF-8'))
            elif data['action'] == 'CREATEFOLDER':
                out = self.osUtils.createFolder(data)
                self.csocket.send(bytes(json.dumps(out),'UTF-8'))
            elif data['action'] == 'new':
                pass
            else:
                print("Invalid Input")
                self.closeClient()
                break

    def closeClient(self):
        self.dbUtils.close()
        self.csocket.send(bytes("BYE",'UTF-8'))
        print ("Client at ", self.clientAddress , " disconnected...")

class DBUtils():
    def __init__(self,DB_Name):
        self.con = sqlite3.connect(DB_Name ,check_same_thread=False)
        self.create_tables()
        #self.test()

    def create_tables(self):
        
        c = self.con.cursor()
        c.execute('CREATE TABLE IF NOT EXISTS USER (name text PRIMARY KEY,logged_in tinyint)')
        self.con.commit()
        print("TABLE CREATED")
    
    def test(self):
        c = self.con.cursor()
        c.execute("INSERT INTO USER (name,logged_in) values ('Tejas',1)")
        x = c.execute("select * from USER").fetchone()
        print(type(x))
        print(dir(x))
        print(x)

    def getUser(self, rec):
        user_dict = {}
        user_dict['message'] = 'LOGIN FAILED'
        c = self.con.cursor()
        c.execute("SELECT * from USER where name = ?",rec)
        data = c.fetchall()
        c.execute("UPDATE USER set logged_in = 1 where name = ?",rec)
        self.con.commit()
        if len(data) > 0:
            user_dict['message'] = 'LOGIN SUCCESFUL'
            user_dict['userName'] = data[0][0]
        return user_dict

    def createUser(self, rec):
        c = self.con.cursor()
        try:
            c.execute("INSERT INTO USER (name,logged_in) values (?,0)",rec)
            self.con.commit()
        except:
            return {"message":"Failed to create User"}
        return {"message":"Created User"}
    
    def logOut(self,rec):
        c = self.con.cursor()
        print("HELLO")
        c.execute("UPDATE USER set logged_in = 0 where name = ?",rec)
        print("User Logged out",rec)
        self.con.commit()

    def close(self):
        self.con.close()

    def getLoggedUserNames(self):
        c = self.con.cursor()
        data = c.execute("SELECT name from USER where logged_in = 1").fetchall()
        print(data)
        return data
class SampleApp(tk.Tk):

    def __init__(self):
        tk.Tk.__init__(self)

        self.title_font = tkfont.Font(family='Helvetica', size=18, weight="bold", slant="italic")
        self.data = {}
        # the container is where we'll stack a bunch of frames
        # on top of each other, then the one we want visible
        # will be raised above the others
        container = tk.Frame(self)
        container.pack(side="top", fill="both", expand=True)
        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)

        self.server = Server()
        self.server.start()
        self.frames = {}
        page_name = StartPage.__name__
        frame = StartPage(parent=container, controller=self)
        self.frames[page_name] = frame

        frame.grid(row=0, column=0, sticky="nsew")

        self.show_frame("StartPage","")

    def stopServer(self):
        self.server.stop()
        exit()
    def close(self):
        self.server.stop()

    def show_frame(self, page_name,content):
        frame = self.frames[page_name]
        frame.draw(self.data)
        frame.tkraise()

class StartPage(tk.Frame):

    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)
        self.controller = controller
        
        label = tk.Label(self, text="Hello Admin", font=controller.title_font)
        label2 = tk.Label(self, text="List of users Logged In")
        label.pack(side="top", fill="x", pady=10)
        label2.pack()

        button2 = tk.Button(self, text="Exit",
                            command=self.stopThread)
        self.Lb = tk.Listbox(self)
        self.Lb.pack() 

        self.Redraw = Redraw(self.Lb)
        self.Redraw.start()
        button2.pack()

    def stopThread(self):
        self.controller.stopServer()
        self.Redraw.stop()

    def draw(self,data):
        pass

class Redraw(threading.Thread):
    def __init__(self,LB):
        threading.Thread.__init__(self)
        self.LB = LB
        self.dbUtils = DBUtils("TEST.db")
        self.STOP = False

    def run(self):
        print("HERE")
        while not self.STOP:
            self.LB.delete(0,tk.END)
            for i,contents in enumerate(self.dbUtils.getLoggedUserNames()):
                print(contents)
                self.LB.insert(i,contents[0])
            time.sleep(2)
        print("Stopped re Draw thread")
    def stop(self):
        self.STOP = True

class Server(threading.Thread):
    def __init__(self):

        threading.Thread.__init__(self)
        self.STOP = False
    def run(self):
        HOST = 'localhost'
        PORT = 12122

        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server.bind((HOST, PORT))
        print("Server started")
        print("Waiting for client request..")
        while not self.STOP:
            self.server.listen(10)
            print("LLL")
            clientsock, clientAddress = self.server.accept()
            newthread = ClientThread(clientAddress, clientsock)
            newthread.start()
        print("Socket Server Stopped")

    def stop(self):
        print("YES")
        self.server.close()

if __name__ == "__main__":
    app = SampleApp()
    try:
        app.mainloop()
    finally:
        app.close()