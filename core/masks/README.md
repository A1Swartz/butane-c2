# what's a mask?
a "mask" in this situation is an html file (could be literally anything actually) with an html comment tag  

the comment tag in question is this:
```
<!--%()%-->
```

the hoaxshell manager will automatically replace ``%()%`` with the encoded command, for the victim to parse it  
the victim will send it back normally, but change endpoints  
here's a flowchart:  

![image](https://github.com/whatotter/butane-c2/assets/42103041/521edfeb-8640-4a15-83ed-27167a5b1231)

so a mask could literally just be

```
<!DOCTYPE html>
<html>
<body>

<h1>My First Heading</h1>

<p>My first paragraph.</p>

<!--%()%-->   < heres the comment tag

</body>
</html>
```

the payload will automatically figure out which comment is correct (usually), so you can go crazy with the masks  
yes, that also means you can make pornhub a mask

enjoy 😽
