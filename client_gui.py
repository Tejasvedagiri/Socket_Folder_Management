import tkinter as tk
from tkinter import *
import threading
import socket
import json
from functools import partial


SERVER = "localhost"
PORT = 12122

tkWindow = Tk()  
tkWindow.geometry('400x150')  
tkWindow.title('Login Form')

def login(userName, password):
    data = {}
    data['userName'] = userName.get()
    data['action'] = 'LOGIN'
    client.sendall(bytes(json.dumps(data),'UTF-8'))
    in_data =  client.recv(1024)
    data = json.loads(in_data.decode())
    print(data)
    getNextScreen(data)

def createF(folderName, data):
    print(data)
    data['folderName'] = folderName.get()
    data['action'] = 'CREATEFOLDER'
    client.sendall(bytes(json.dumps(data),'UTF-8'))
    in_data =  client.recv(1024)
    data = json.loads(in_data.decode())
    print(data)
    return None

def getNextScreen(data):
    
    DirList = Toplevel(tkWindow) 
    DirList.title("Register")
    DirList.geometry("300x250")

    Lb = Listbox(DirList) 
    for i,contents in enumerate(data['dir']):
        Lb.insert(i,contents)
    Lb.pack() 

    Label(DirList, text="Create Folder").pack()
    createDir = StringVar()
    Entry(DirList, textvariable=createDir).pack()

    createFodler = partial(createF, createDir,data)

    Button(DirList,text="Create Folder", height="2", width="30", command=createFodler).pack()



try:
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect((SERVER, PORT))

    

    #username label and text entry box
    usernameLabel = Label(tkWindow, text="User Name").grid(row=0, column=0)
    username = StringVar()
    usernameEntry = Entry(tkWindow, textvariable=username).grid(row=0, column=1)  

    #password label and password entry box
    passwordLabel = Label(tkWindow,text="Password").grid(row=1, column=0)  
    password = StringVar()
    passwordEntry = Entry(tkWindow, textvariable=password, show='*').grid(row=1, column=1)  

    validateLogin = partial(login, username, password)

    #login button
    loginButton = Button(tkWindow, text="Login", command=validateLogin).grid(row=4, column=0)  

    tkWindow.mainloop()
except:
    print("God Dam it!")
finally:
    data = {}
    data['action'] = 'TERMINATE'
    client.sendall(bytes(json.dumps(data),'UTF-8'))
    client.close()




