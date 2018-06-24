import glob
import subprocess
import os
import salome_version

try:
    file = glob.glob1("/tmp", "*pid*")
    command = ""
    if os.path.exists("/usr/bin/gnome-terminal"):
        command = 'gnome-terminal -t "SALOME %s - Shell session" -e ' + 'tail -f ' + "/tmp/" + str(file[0])
    elif os.path.exists("/usr/bin/konsole"):
        command = 'PATH="/usr/bin:/sbin:/bin" LD_LIBRARY_PATH="" konsole -e ' + 'tail -f ' + "/tmp/" + str(file[0])
    elif os.path.exists("/usr/bin/xterm"):
        command = 'xterm -T "SALOME %s - Shell session" -e ' + 'tail -f ' + "/tmp/" + str(file[0])
    else:
        print "Neither xterm nor gnome-terminal nor konsole is installed."
    if command is not "":
        try:
            subprocess.check_call(command, shell = True)
        except Exception, e:
            print "Error: ",e
except:
    None


