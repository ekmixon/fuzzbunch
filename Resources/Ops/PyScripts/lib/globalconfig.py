
import sys, os
from ConfigParser import SafeConfigParser
config = {}
try:
    conf = SafeConfigParser()
    found = conf.read(['C:\\utils\\config.txt', 'D:\\DSZOpsDisk\\Resources\\Ops\\Data\\config.txt'])
    for section in conf.sections():
        config[section] = {item[0]: item[1] for item in conf.items(section)}
except:
    pass
globalpath = config['paths']['sharedpython']
if (globalpath not in sys.path):
    sys.path.append(globalpath)