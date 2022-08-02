
import glob
import os
import shutil
import sys
import xml.dom.minidom

#------------------------------------------------------------------------------------------
# DOM helper functions
#------------------------------------------------------------------------------------------
def getMatchingChildNodes(node, name):
	return [
		item
		for item in node.childNodes
		if (item.nodeType == node.ELEMENT_NODE) and (item.nodeName == name)
	]
	
def getText(nodelist):
    rc = ""
    for node in nodelist:
        if node.nodeType == node.TEXT_NODE:
            rc = rc + node.data
    return rc

#------------------------------------------------------------------------------------------
def copyFiles(files):

	for item in files:
		src = item[0]
		dst = item[1]
		#print "%s -> %s" % (src, dst)
		try:
			os.makedirs(os.path.dirname(dst))
		except:
			pass
		
		shutil.copy2(src, dst)
	
	return True

#------------------------------------------------------------------------------------------
def handleDir(dirName, dstDir, root, recursive=False):

	#print "handleDir: ENTER (%s)" % dirName
	fileList = []
	fileNodes = getMatchingChildNodes(root, "File")
	for fileNode in fileNodes:
		name = getText(fileNode.childNodes)
		newName = (fileNode.getAttribute("name")) or None
		files = glob.glob(f"{dirName}/{name}")
		for item in files:
			item = os.path.basename(item)
			dstName = newName
			if dstName is None:
				dstName = item
			if (len(dirName) > 0):
				if os.path.isfile(f"{dirName}/{item}"):
					fileList.append((f"{dirName}/{item}", f"{dstDir}/{dirName}/{dstName}"))
			elif (os.path.isfile(item)):
				fileList.append((item, f"{dstDir}/{dstName}"))

	# handle any sub-dirs
	dirNodes = [root] if recursive else getMatchingChildNodes(root, "Dir")
	for dirNode in dirNodes:
		if recursive:
			ignoreNodes = []
			subDirName = f"{dirName}/*" if (len(dirName) > 0) else "*"
		else:
			ignoreNodes = getMatchingChildNodes(dirNode, "Ignore")
			if (len(dirName) > 0):
				subDirName = f'{dirName}/{dirNode.getAttribute("name")}'
			else:
				subDirName = dirNode.getAttribute("name")

		subRecursive = recursive
		if (not subRecursive):
			rStr = dirNode.getAttribute("recursive")
			if ((rStr != None) and (rStr == "true")):
				subRecursive = True
				#print "RECURSIVE (%s)" % subDirName

		#print "Checking for '%s'" % subDirName
		names = glob.glob(f"{subDirName}")
		for name in names:
			if (os.path.basename(name) == ".svn"):
				continue

			# make sure it's not ignored
			ignore = False
			for ignoreNode in ignoreNodes:
				ignoreName = getText(ignoreNode.childNodes)
				#print "<----------------Checking '%s' for ignored '%s'" % (os.path.basename(name), ignoreName)
				if (ignoreName == os.path.basename(name)):
					ignore = True

			if (ignore):
				#print "IGNORING %s" % name
				continue

			if (os.path.isdir(name)):
				dirList = handleDir(os.path.normpath(name), dstDir, dirNode, subRecursive)
				fileList.extend(iter(dirList))
	return fileList
		
#------------------------------------------------------------------------------------------
def main(argv):
#	rootDir = os.path.dirname(argv[0])
#	if (len(rootDir) == 0):
#		rootDir = "."
#	xmlName = "%s/replay.xml" % rootDir

	rootDir = "."
	xmlName = f"{rootDir}/replay.xml"

	dom1 = xml.dom.minidom.parse(xmlName)
	root = dom1.getElementsByTagName("ReplayFiles")

	dstDir = None
	while dstDir is None:
		dstDir = os.path.normpath(f"{rootDir}/../ReplayDisk")
		sys.stdout.write(f"Enter the replay destination directory [{dstDir}]:")
		dir = sys.stdin.readline().rstrip('\r\n')
		if (len(dir) > 0):
			dstDir = dir

	rootList = handleDir(rootDir, dstDir, root[0])
	fileCopyList = list(rootList)
	if (not copyFiles(fileCopyList)):
		return False
#	rootDir = os.path.dirname(argv[0])
#	if (len(rootDir) == 0):
#		rootDir = "."
#	xmlName = "%s/replay.xml" % rootDir

	rootDir = "."
#	rootDir = os.path.dirname(argv[0])
#	if (len(rootDir) == 0):
#		rootDir = "."
#	xmlName = "%s/replay.xml" % rootDir

	rootDir = "."
#	rootDir = os.path.dirname(argv[0])
#	if (len(rootDir) == 0):
#		rootDir = "."
#	xmlName = "%s/replay.xml" % rootDir

	rootDir = "."
	return True
	
#------------------------------------------------------------------------------------------
	
if __name__ == '__main__' and (main(sys.argv) != True):
	sys.exit(-1);