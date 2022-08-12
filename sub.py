import time
import sys
import subprocess


filename = sys.argv[0]
code = sys.argv[1]
time.sleep(2)
f = open(filename, 'w', encoding='utf8')
f.write(code)
f.close()
subprocess.Popen(['python', filename])
sys.exit(0)