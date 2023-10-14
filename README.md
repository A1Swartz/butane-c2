# butane-c2
a lightweight, multiplayer, http reverse shell C2, with autorun stages - supports ncat and hoaxshell

***

*THIS DOES NOT EXPLOIT THE SYSTEM ITSELF. IT IS ONLY A CONTROL PANEL **FOR REVERSE SHELLS. NOT FOR RATS.***  

**I DO NOT CONDONE USING THIS IN ACTUAL, ILLEGAL ATTACKS. THIS WAS MEANT FOR STUFF LIKE CTFS, AND LEGAL OPERATIONS.**  
**^ either way, its not like people will actually listen to this**

***
![image](https://github.com/whatotter/butane-c2/assets/42103041/7eb031b5-7156-414d-a1ab-0d338f4efbe5)
***
![image](https://github.com/whatotter/butane-c2/assets/42103041/9518b6ea-bda0-40d2-8242-dd7f033260dd)
***

# usage

### starting
install the required packages:  
```
pip install flask requests flask-socketio python-socketio
```

start the main python script, no sudo required: `python3 main.py`  
 - if you want, add the port you want the shell listener to listen on as an argument: `python3 main.py 12727` - this will eventually switch to an actual argument with argparse  

open your favorite browser, and navigate to `localhost:80`  

create reverse shells with the built in payload generator, revshells.com, or pentest monkey, and just switch the listener ip and port to the one in the main page  
the ui will auto refresh every second, so just wait for the victim to connect back and for the page to get all victims  

### UI usage
if your target disconnects, or you just want to delete the shell, select it by clicking on the box itself, and then press delete on your keyboard twice

to communicate with your target, just press the big connect button - you CAN'T miss it  
as of right now, the only way to go back from the terminal to the main menu is with the back button

i think everything else is pretty simple to use, so nothing much to worry about  

the log console is just there for info, so you dont have to worry about that

# dev notes
### current actually supported communication methods
- NCAT (basic socket)
- HoaxShell

### to add
- meterpreter
- pwncat
  
***
### features from TBD that are done
- login system
- directory explorer
- file downloader
- make the control ui better
- stages
  - this was done with jinja templates
### features TBD (ranking from most important to least)
- logs
- keylogging server
  - run a seperate socket server that will log all data recieved into a gzip compressed text file, for keylogging
  - i think the legality of the project will dive hard with this
- plugins
- being able to change the port

# contributing
you don't have to contribute at all, but if you do decide to, try to pick one part to work on (ex: api, frontend ui, backend shell controller)  
i will be more than happy to listen to anything you have to say (if its not put in the worst way you could say it)  
before you do contribute though, read the below paragraphs

***
### asking for features to be added
please don't ask in the worst way possible, which would be something like this:  

> "add support for cobalt strike communications"

add support how? what do i do? i dont even have cobalt strike? what features do you want?  
a good way instead, would be something like this  

> "can you add support for cobalt strike DNS beacons? maybe even add HTTP(s) support for communication? maybe something like this? (imagine a link to their documentation is here)"  

this would actually help me, and wouldn't get you ignored or closed for being stale - linking documentation or an example of something you want is SUPER useful, because i personally hate researching

***
### cleaning up my code
my code sucks ass. my code works, but it might look really ugly. this is where you (hopefully) come in, and simplify or clean my code, but theres rules  

1. don't increase the complexity of the code
   - this is pretty obvious, i don't want to work on something i obviously dont understand
2. PLEASE comment your code if you accidentally do rule 1.
   - ima be fr, i do the same. i basically never comment my code, and accidentally make the code more complex. but, monkey see monkey do - if you comment your code when contributing, eventually i'll learn to do it too. it also just helps me working on it, so if you do, ty
3. don't purposely remove features
   - if, for example, your implementing X feature, but Y feature overlaps/messes with it, don't remove Y feature - build around it, or if you must, please let me know
   - this shouldn't happen though, so dont worry much about this
