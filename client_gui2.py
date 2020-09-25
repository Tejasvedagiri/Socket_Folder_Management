import tkinter as tk                
from tkinter import font as tkfont  
import socket 
import json

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
        self.SERVER = "localhost"
        self.PORT = 12122

        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client.connect((self.SERVER, self.PORT))

        self.frames = {}
        for F in (StartPage, PageOne, PageTwo):
            page_name = F.__name__
            frame = F(parent=container, controller=self)
            self.frames[page_name] = frame

            # put all of the pages in the same location;
            # the one on the top of the stacking order
            # will be the one that is visible.
            frame.grid(row=0, column=0, sticky="nsew")

        self.show_frame("StartPage","")

    def close(self):
        data = {}
        data['action'] = 'TERMINATE'
        self.client.sendall(bytes(json.dumps(data),'UTF-8'))
        self.client.close()

    def show_frame(self, page_name,content):
        if page_name == 'PageOne':
            self.data = self.login(content)
        if page_name == 'CreateFolder':
            page_name = 'PageOne'
            self.data = self.createF(content)
        frame = self.frames[page_name]
        print("HERE")
        print(self.data)
        frame.draw(self.data)
        frame.tkraise()

    def login(self, userName):
        data = {}
        data['userName'] = userName
        data['action'] = 'LOGIN'
        self.client.sendall(bytes(json.dumps(data),'UTF-8'))
        in_data =  self.client.recv(1024)
        data = json.loads(in_data.decode())
        return data

    def createF(self, folderName):
        self.data['folderName'] = folderName
        self.data['action'] = 'CREATEFOLDER'
        self.client.sendall(bytes(json.dumps(self.data),'UTF-8'))
        in_data =  self.client.recv(1024)
        self.data = json.loads(in_data.decode())
        return self.data

class StartPage(tk.Frame):

    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)
        self.controller = controller
        
        label = tk.Label(self, text="Welcome to User Dir Management", font=controller.title_font)
        username = tk.StringVar()
        usernameEntry = tk.Entry(self, textvariable=username)

        #usernameEntry = tk.Entry(self, textvariable=username).grid(row=0, column=1)  

        label.pack(side="top", fill="x", pady=10)
        usernameEntry.pack() 
        button1 = tk.Button(self, text="Login",
                            command=lambda: controller.show_frame("PageOne",username.get()))
        
        button1.pack()

    def draw(self,data):
        pass

class PageOne(tk.Frame):

    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)
        self.controller = controller
        self.Lb = tk.Listbox(self)
        self.Lb.pack() 


        tk.Label(self, text="Create Folder").pack()
        createDir = tk.StringVar()
        tk.Entry(self, textvariable=createDir).pack()

        tk.Button(self,text="Create Folder", command=lambda: self.controller.show_frame("CreateFolder",createDir.get())).pack()
        tk.Button(self,text="Log Out", command=lambda: self.controller.show_frame("StartPage","")).pack()

        self.draw({})

    def draw(self, data):
        self.Lb.delete(0,tk.END)
        if bool(data): 
            for i,contents in enumerate(data['dir']):
                print(i)
                self.Lb.insert(i,contents)
        

        

class PageTwo(tk.Frame):

    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)
        self.controller = controller
        label = tk.Label(self, text="This is page 2", font=controller.title_font)
        label.pack(side="top", fill="x", pady=10)
        button = tk.Button(self, text="Go to the start page",
                           command=lambda: controller.show_frame("StartPage"))
        button.pack()


if __name__ == "__main__":
    app = SampleApp()
    try:
        app.mainloop()
    finally:
        app.close()