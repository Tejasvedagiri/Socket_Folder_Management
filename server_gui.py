import tkinter as tk                
from tkinter import font as tkfont  
import socket 
import json
import sqlite3
import threading
import os
import time
import shutil  

class OSUtils():
    def __init__(self):
        self.base_path = os.path.join(os.getcwd(), "Directories")
        if not os.path.exists(self.base_path):
            os.mkdir(self.base_path)  

    def moveIntoFolder(self,data):
        path = os.path.join(self.base_path ,  data['userName'], data['currentPath'])
        x = []
        if not data['currentPath'] == "":
            x.append('..')
        x.extend(os.listdir(path))
        data['dir'] = x
        return data

    def getUserDir(self,data): 
        path = os.path.join(self.base_path ,  data['userName'], data['currentPath'])
        if not os.path.exists(path):
            os.mkdir(path)    
        x = os.listdir(path)
        if not data['currentPath'] == "":
            x.append('..')
        return x

    def createFolder(self,data):
        path = os.path.join(self.base_path , data['userName'], data['currentPath'],data['folderName'])
        if not os.path.exists(path):
            os.mkdir(path)  
            data['message'] = "Created succefully"
        else :
            data['message'] = "Folder Exisit"
        data['dir'] = self.getUserDir(data)
        return data

    def moveFolder(self,data):
        inpath = os.path.join(self.base_path , data['userName'], data['currentPath'],data['inputdir'])
        targetpath = os.path.join(self.base_path , data['userName'], data['currentPath'], data['targetdir'])
        if not os.path.exists(inpath):
            data['message'] = "Input path does not exsist"
            return data
        if not os.path.exists(targetpath): 
            data['message'] = "Target Dir does not exsist"
            return data
        try:
            shutil.move(inpath, targetpath)  
            data['message'] = "Moved Succefull"
            data['dir'] = self.getUserDir(data)
            return data
        except:
            data['message'] = "Failed to move"
            data['dir'] = self.getUserDir(data)
            return data

    def renameFolder(self,data):
        inpath = os.path.join(self.base_path , data['userName'], data['currentPath'], data['inputdir'])
        targetpath = os.path.join(self.base_path , data['userName'], data['currentPath'], data['targetdir'])
        if not os.path.exists(inpath):
            data['message'] = "Input path does not exsist"
            return data
        if os.path.exists(targetpath): 
            data['message'] = "Target Dir already exsist"
            return data
        shutil.move(inpath, targetpath)  
        data['message'] = "Rename Succefull"
        data['dir'] = self.getUserDir(data)
        return data

    def deleteFolder(self,data):
        path = os.path.join(self.base_path , data['userName'], data['currentPath'], data['folderName'])
        print("HERE")
        if os.path.exists(path):
            os.rmdir(path)  
            data['message'] = "Deleted folder succefully"
        else :
            data['message'] = "Folder not found"
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
            elif data['action'] == 'DELETEFOLDER':
                out = self.osUtils.deleteFolder(data)
                self.csocket.send(bytes(json.dumps(out),'UTF-8'))
            elif data['action'] == 'MOVEFOLDER':
                out = self.osUtils.moveFolder(data)
                self.csocket.send(bytes(json.dumps(out),'UTF-8'))
            elif data['action'] == 'RENAMEFOLDER':
                out = self.osUtils.renameFolder(data)
                self.csocket.send(bytes(json.dumps(out),'UTF-8'))
            elif data['action'] == 'CREATEUSER':
                rec = (data['userName'],)
                out = self.dbUtils.createUser(rec)
                self.csocket.send(bytes(json.dumps(out),'UTF-8'))
            elif data['action'] == 'LOGOUT':
                rec = (data['userName'],)
                self.dbUtils.logOut(rec)
                self.csocket.send(bytes(json.dumps({'message' :"SUCCESFULL"}),'UTF-8'))
            elif data['action'] == 'MOVEINTOFOLDER':
                out= self.osUtils.moveIntoFolder(data)
                self.csocket.send(bytes(json.dumps(out),'UTF-8'))
            elif data['action'] == 'LOGIN':
                rec = (data['userName'],)
                out = self.dbUtils.getUser(rec)
                data['currentPath'] = ""
                out['currentPath'] = ""
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
        c.execute("SELECT * from USER where name = ? AND logged_in = 0",rec)
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
        try:
            while not self.STOP:
                self.LB.delete(0,tk.END)
                for i,contents in enumerate(self.dbUtils.getLoggedUserNames()):
                    print(contents)
                    self.LB.insert(i,contents[0])
                time.sleep(2)
        except:
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
        try:
            while not self.STOP:
                self.server.listen(10)
                print("LLL")
                clientsock, clientAddress = self.server.accept()
                newthread = ClientThread(clientAddress, clientsock)
                newthread.start()
        except:
            print("Socket Server Stopped")
        
    def stop(self):
        self.server.close()

if __name__ == "__main__":
    app = SampleApp()
    try:
        app.mainloop()
    finally:
        app.close()