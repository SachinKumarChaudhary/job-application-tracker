import sys
import os

path = '/home/SachinKumarChaudhary/Gotjobalert'
if path not in sys.path:
    sys.path.insert(0, path)

os.chdir(path)
os.environ['FLASK_ENV'] = 'production'

from webui import app as application
