from jinja2 import Environment, FileSystemLoader
import core.utils as utils
import socketio
import os

sio = socketio.Client()
# Create the Jinja2 environment
env = Environment(loader=FileSystemLoader('./stages'))  # This assumes template is in the same directory
shell = None

def parse(line):
    global shell
    line = line.strip()
    command, args = line.split(" ", 1)

    if command in ["run", "exec", "execute"]:
        shell.run(args)
    elif command in ["upload", "up"]:
        shell.upload(args)
    elif command in ["download", "dl"]:
        shell.download(args)


def onConnection(data):
    global shell
    shell = utils.butane(data["uid"])

    for stage in os.listdir("./stages"):
        template = env.get_template(stage)

        output = template.render(data).split("\n")

        for line in output:
            line = line.strip()
            if len(line) != 0:
                print("parsing line \"{}\"".format(line))
                parse(line)

@sio.on('message')
def on_message(data):
    print(f'Received message: {data}')
    
    print(list(data)[0])
    if list(data)[0] == "connection":
        print("connection")
        onConnection(data["connection"])

@sio.event
def connect():
    print('Connected to server')

@sio.event
def disconnect():
    print('Disconnected from server')