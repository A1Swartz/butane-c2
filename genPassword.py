import sys
from getpass import getpass
import bcrypt

pwd = getpass()
hash = bcrypt.hashpw(pwd.encode('ascii'), bcrypt.gensalt())

if bcrypt.checkpw(pwd.encode('ascii'), hash):
    print(hash.decode('ascii'))
else:
    print('try again - password and hash did not match')