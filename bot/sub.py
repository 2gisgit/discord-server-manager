import os
import time

def run(code, filename):
  time.sleep(2)
  f = open(filename, 'w', encoding='utf8')
  f.write(code)
  os.system(f'python {filename}')
  
