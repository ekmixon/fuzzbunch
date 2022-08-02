
import dsz
import dsz.ui
import dsz.cmd
import datetime
import ops
import ops.data
import ops.env
from ops.cmd.safetychecks import doSafetyHandlers
import util
import util.ip
command_classes = {}
aliasoptions = {}
aliashelps = {}
DSZ_PREFIXES = ['async', 'background', 'foreground', 'disablewow64', 'dst', 'guiflag', 'local', 'log', 'monitor', 'nocharescapes', 'notify', 'src', 'stopaliasing', 'task', 'user', 'wait', 'xml']
DSZ_ARG_PREFIXES = ['dst', 'src', 'task', 'user']
NEVER_PRELOAD = ['script', 'python', 'wrappers']

def quickrun(command_string, dszquiet=True, norecord=False):
    comObj = getDszCommand(command_string, dszquiet, norecord)
    return comObj.execute()
CURRENT_USER = ops.env.get('_USER', cmdid=ops.env.SELF)

def getDszCommand(command_string, dszquiet=True, norecord=False, arglist=None, prefixes=None, **options):
    if prefixes is None:
        prefixes = []
    if arglist is None:
        arglist = []
    if command_string.strip().find(' ') > (-1) and options:
        raise OpsCommandException('You cannot both specify options and provide an entire command string.')
    elif (command_string.strip().find(' ') > (-1)):
        (prefixes, plugin, arglist, optdict) = parseCommand(command_string)
    else:
        plugin = command_string
        optdict = {opt: options[opt] for opt in options}
    comObj = None
    try:
        if (plugin[0] == '.'):
            raise OpsCommandException('You cannot issue commands that begin with "." with ops.cmd or dsz.cmd')
        if (plugin not in command_classes):
            __import__(f'ops.cmd.{plugin}')
        comObj = command_classes[plugin](plugin=plugin, arglist=arglist, dszquiet=dszquiet, prefixes=prefixes, norecord=norecord, **optdict)
    except (KeyError, ImportError):
        comObj = DszCommand(plugin=plugin, arglist=arglist, dszquiet=dszquiet, prefixes=prefixes, norecord=norecord, **optdict)
    return comObj

def parseCommand(command_string):
    tokens = util.make_sys_argv('', command_string)[1:]
    prefixes = []
    arglist = []
    optdict = {}
    plugin = ''
    while not plugin and len(tokens) > 0:
        token = tokens.pop(0)
        if (len(filter((lambda x: ((token.find(x) == 0) and ((x != 'user') and (token != 'users')))), DSZ_PREFIXES)) > 0):
            prefixes.append(token)
        else:
            plugin = token
    while (len(tokens) > 0):
        token = tokens.pop(0)
        if (token[0] == '-'):
            tokens.insert(0, token)
            break
        else:
            arglist.append(token)
    while (len(tokens) > 0):
        optname = tokens.pop(0)[1:]
        if (len(tokens) > 0):
            token = tokens.pop(0)
            optval = ''
            while ((token[0] != '-') and (len(tokens) > 0)):
                optval += f' {token}'
                token = tokens.pop(0)
            if (len(tokens) == 0):
                if (token[0] == '-'):
                    tokens.insert(0, token)
                else:
                    optval += f' {token}'
                optdict[optname] = optval[1:] if (len(optval) > 0) else True
            else:
                optdict[optname] = optval[1:] if (len(optval) > 0) else True
                tokens.insert(0, token)
        else:
            optdict[optname] = True
    return (prefixes, plugin, arglist, optdict)

class Command(object, ):

    def __init__(self):
        pass

class DszCommand(Command, ):
    optgroups = []
    reqgroups = []

    def __init__(self, plugin, dszbackground=False, dszmonitor=False, dszlog=False, dszuser=None, prefixes=[], dszquiet=True, override=False, norecord=False, arglist=[], autocache=False, **optdict):
        Command.__init__(self)
        self.norecord = norecord
        self.autocache = autocache
        if (plugin.find(' ') > 0):
            (self.prefixes, self.__plugin, self.arglist, self.optdict) = parseCommand(plugin)
        else:
            self.__plugin = plugin
            self.prefixes = prefixes
            self.arglist = arglist
            self.optdict = optdict
        self.dszquiet = dszquiet
        self.override = override
        if 'background' not in self.prefixes:
            self.dszbackground = dszbackground
        if 'monitor' not in self.prefixes:
            self.dszmonitor = dszmonitor
        if 'log' not in self.prefixes:
            self.dszlog = dszlog
        if (self.dszuser is None):
            self.dszuser = dszuser
        self.__channel = 0
        self.__success = None
        self.__result = None
        try:
            __import__(f'ops.override.{plugin}')
            if ('stopaliasing' not in self.prefixes):
                self.prefixes.append('stopaliasing')
        except ImportError:
            pass

    def safetyCheck(self):
        return doSafetyHandlers(self)

    def validateInput(self):
        for optkey in self.optdict:
            if (type(self.optdict[optkey]) is str):
                self.optdict[optkey] = self.optdict[optkey].strip()
                if ((self.optdict[optkey][0] == '"') and (self.optdict[optkey][(-1)] != '"')):
                    self.optdict[optkey] += '"'
        return True

    def execute(self):
        (issafe, safetymsg) = self.safetyCheck()
        if issafe:
            return self._actual_execute()
        ops.error('Scripted command safety check failed!')
        ops.error(f'Command: {str(self)}')
        ops.error(f'Failure: {safetymsg}')
        if self.override:
            if override_run := dsz.ui.Prompt(
                'Your command did not pass the safety check, do you still want to run it?',
                False,
            ):
                return self._actual_execute()
        ops.error('The command will not be run')

    def _actual_execute(self):
        if self.dszquiet:
            x = dsz.control.Method()
            dsz.control.echo.Off()
        cmdstr = str(self)
        if ops.env.get(f'OPS_SAFE_{self.plugin}') is not None:
            cmdstr = f'stopaliasing {cmdstr}'
        if ((not self.dszquiet) and (self.plugin not in NEVER_PRELOAD)):
            ops.preload(self.plugin)
        dszflag = 0 if self.norecord else dsz.RUN_FLAG_RECORD
        timestamp = datetime.datetime.now()
        (success, cmdid) = dsz.cmd.RunEx(cmdstr, dszflag)
        self.__success = success
        self.__channel = cmdid
        self.__result = None
        try:
            self.__result = ops.data.getDszObject(cmdid=cmdid)
            if self.autocache:
                ops.db.get_voldb().save_ops_object(self.__result)
            self.__result.__dict__['cache_timestamp'] = timestamp
            return self.__result
        except ImportError:
            return None

    def stop(self):
        if (self.result is not None):
            self.result.update()
        if (self.result.commandmetadata.isrunning == 1):
            dsz.cmd.Run(('stop %d' % self.channel))

    def __str__(self):
        cmdstr = ''.join(f'{prefix} ' for prefix in self.prefixes)
        cmdstr += f'{self.plugin} '
        for arg in self.arglist:
            cmdstr += f'{arg} '
        for optkey in self.optdict:
            if (type(self.optdict[optkey]) == bool):
                if (self.optdict[optkey] == True):
                    cmdstr += f'-{optkey} '
            elif self.optdict[optkey] is not None:
                cmdstr += f'-{optkey} {self.optdict[optkey]} '
        return ops.utf8(cmdstr)

    def _getBackground(self):
        return ('background' in self.prefixes)

    def _setBackground(self, val):
        if val and 'background' not in self.prefixes:
            self.prefixes.append('background')
        elif ((not val) and ('background' in self.prefixes)):
            self.prefixes.remove('background')
    dszbackground = property(_getBackground, _setBackground)

    def _getmonitor(self):
        return ('monitor' in self.prefixes)

    def _setmonitor(self, val):
        if val and 'monitor' not in self.prefixes:
            self.prefixes.append('monitor')
        elif ((not val) and ('monitor' in self.prefixes)):
            self.prefixes.remove('monitor')
    dszmonitor = property(_getmonitor, _setmonitor)

    def _getuser(self):
        for prefix in self.prefixes:
            if (prefix.find('user') == 0):
                splits = prefix.split('=')
                return splits[1]
        return None

    def _setuser(self, value):
        for prefix in self.prefixes:
            if (prefix.find('user') == 0):
                self.prefixes.remove(prefix)
        if (value is None):
            return
        self.prefixes.append(f'user={value}')
    dszuser = property(_getuser, _setuser)

    def _getlog(self):
        return ('log' in self.prefixes)

    def _setlog(self, val):
        if val and 'log' not in self.prefixes:
            self.prefixes.append('log')
        elif ((not val) and ('log' in self.prefixes)):
            self.prefixes.remove('log')
    dszlog = property(_getlog, _setlog)

    def _getdst(self):
        for prefix in self.prefixes:
            if (prefix.find('dst=') == 0):
                splits = prefix.split('=')
                return splits[1]
        return None

    def _setdst(self, value):
        for prefix in self.prefixes:
            if (prefix.find('dst=') == 0):
                self.prefixes.remove(prefix)
        if (value is None):
            return
        self.prefixes.append(f'dst={value}')
    dszdst = property(_getdst, _setdst)

    def _getResult(self):
        return self.__result
    result = property(_getResult)

    def _getSuccess(self):
        return self.__success
    success = property(_getSuccess)

    def _getChannel(self):
        return self.__channel
    channel = property(_getChannel)

    def _getPlugin(self):
        return self.__plugin
    plugin = property(_getPlugin)

class OpsCommandException(Exception, ):

    def __init__(self, *args):
        Exception.__init__(self, *args)

def getBoolOption(obj, optname):
    return ((optname in obj.optdict) and obj.optdict[optname])

def getValueOption(obj, optname):
    return obj.optdict[optname] if (optname in obj.optdict) else None

def setBoolOption(obj, val, optname):
    if ((optname in obj.optdict) and ((val is None) or (val is False))):
        del obj.optdict[optname]
    elif val:
        obj.optdict[optname] = True

def setListOption(obj, val, optname, valid):
    if ((val is None) and (optname in obj.optdict)):
        del obj.optdict[optname]
    elif val is not None:
        if (val in valid):
            obj.optdict[optname] = val
        else:
            raise OpsCommandException(f'Invalid value for option -{optname}: {val}')

def setIntOption(obj, val, optname):
    if ((val is None) and (optname in obj.optdict)):
        del obj.optdict[optname]
    elif val is not None:
        try:
            intval = int(val)
            obj.optdict[optname] = intval
        except:
            raise OpsCommandException(
                f'{optname} is required to be an int, you gave {val}'
            )

def setStringOption(obj, val, optname):
    if ((val is None) and (optname in obj.optdict)):
        del obj.optdict[optname]
    elif val is not None:
        try:
            strval = (val.encode('utf8') if (unicode is type(val)) else str(val))
            strval = strval.replace('"', '\\"')
            if (' ' in strval):
                strval = (('"' + strval) + '"')
            obj.optdict[optname] = strval
        except Exception as e:
            raise OpsCommandException(
                f'{optname} is required to be a string, but what you provided could not be converted to a string. Reason: {e}'
            )

def setIpOption(obj, val, optname):
    if ((val is None) and (optname in obj.optdict)):
        del obj.optdict[optname]
    elif val is not None:
        if util.ip.validate(val):
            obj.optdict[optname] = val
        else:
            raise OpsCommandException(
                f'{optname} is required to be a valid IP address, you gave {val}'
            )

def setPortOption(obj, val, optname):
    if ((val is None) and (optname in obj.optdict)):
        del obj.optdict[optname]
    elif val is not None:
        try:
            intval = int(val)
            if ((intval < 0) or (intval > 65535)):
                raise OpsCommandException(('Invalid port, port must be between 0 and 65535, you gave %d' % intval))
        except:
            raise OpsCommandException(
                f'{optname} is required to be a valid port, you gave {val}'
            )

def get_filtered_command_list(cpaddrs=[], isrunning=None, goodwords=[], badwords=[]):
    base = 'commandmetadata'
    i = 0
    retval = []
    while True:
        i += 1
        good = True
        try:
            dsz.cmd.data.Get('commandmetadata::id', dsz.TYPE_INT, i)[0]
        except:
            break
        try:
            if (isrunning is not None) and (
                dsz.cmd.data.ObjectGet(base, 'isrunning', dsz.TYPE_BOOL, i)[0]
                != isrunning
            ):
                good = False
                continue
            try:
                dest = dsz.cmd.data.ObjectGet(base, 'destination', dsz.TYPE_STRING, i)[0]
                if ((cpaddrs != []) and (dest not in cpaddrs)):
                    continue
            except:
                dest = ''
                continue
            fullcommand = dsz.cmd.data.ObjectGet('commandmetadata', 'fullcommand', dsz.TYPE_STRING, i)[0]
            for word in goodwords:
                if (fullcommand.find(word) < 0):
                    good = False
                    break
            for bad in badwords:
                if (fullcommand.find(bad) > (-1)):
                    good = False
                    break
            if (not good):
                continue
            retval.append(i)
        except:
            break
    return retval

def disable_command(plugin, reason):
    flags = dsz.control.Method()
    dsz.control.echo.Off()
    ret = dsz.cmd.Run(('wrappers -register %s "%s" -pre -script wrappers/disabled.py -project Ops' % (plugin, reason)))
    del flags
    return ret