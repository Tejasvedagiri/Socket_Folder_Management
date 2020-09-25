import socket
import json   

SERVER = "localhost"
PORT = 12122

def login(userName):
    data = {}
    data['userName'] = userName
    data['action'] = 'LOGIN'
    return data

def createFolder(data, folderName):
    data['folderName'] = folderName
    data['action'] = 'CREATEFOLDER'
    return data

try:
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect((SERVER, PORT))
    client.sendall(bytes(json.dumps(login("Tejas")),'UTF-8'))
    while True:
        in_data =  client.recv(1024)
        data = json.loads(in_data.decode())
        print("From Server :" ,data)
        data = createFolder(data,"Test")
        client.sendall(bytes(json.dumps(data),'UTF-8'))
        in_data =  client.recv(1024)
        data = json.loads(in_data.decode())
        print(data)
        out_data = input()
        client.sendall(bytes(out_data,'UTF-8'))
        if out_data=='TERMINATE':
            break
except:
    print("God Dam it!")
finally:
    data = {}
    data['action'] = 'TERMINATE'
    client.sendall(bytes(json.dumps(data),'UTF-8'))
    client.close()