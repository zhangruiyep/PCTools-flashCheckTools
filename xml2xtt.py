''' change history:
2015-07-01	1.01	zhangrui: fix bug - tests only display status on the last test, because all tests have same index value
2015-07-06	1.02	zhangrui: fix bug - tests is unchecked if original template has more than 1 element "Unchecked"
2015-07-10	1.03	zhangrui: remove debug msg
2015-08-05	1.04	zhangrui: new feature - find prog_emmc_firehose_*.mbn and set it in QPHONEMS_SaharaArmPrgDownload, so it can work for different platforms now.
'''

import xml.dom.minidom
import sys
import random
import findFile

def genRandHex():
	randint = random.randint(0, 0xFFFF)	
	return hex(randint)[2:]

def genIndex():
	#index format 8-4-4-4-12
	index = genRandHex()+genRandHex()+"-"+genRandHex()+"-"+genRandHex()+"-"+genRandHex()+"-"+genRandHex()+genRandHex()+genRandHex()
	#print index
	return index


# insert a test block into firehose folder
def insertBlock(firehoseFolder, startSector, numSector, imageName):
	#print "insertBlock "+startSector+"  "+numSector+"  "+imageName
	tests = firehoseFolder.getElementsByTagName("DotNetTest")
	first = 1
	
	# find QPHONEMS_UploadEmmcImage_FireHose_NoPatch, will insert before it
	for test in tests:
		prop = test.getElementsByTagName("DotNetProperties")[0]
		TestName = prop.getElementsByTagName("TestName")[0]
		TestNameData = TestName.childNodes[0].data
		#print "TestNameData = %s" % TestNameData
		
		if TestNameData == "QPHONEMS_UploadEmmcImage_FireHose_NoPatch":
			#print "get QPHONEMS_UploadEmmcImage_FireHose_NoPatch"
			testNoPatch = test
			break

	# find first useful test, then clone a new one, modify the value
	for test in tests:
		prop = test.getElementsByTagName("DotNetProperties")[0]
		TestName = prop.getElementsByTagName("TestName")[0]
		TestNameData = TestName.childNodes[0].data
		#print "TestNameData = %s" % TestNameData
		
		if TestNameData == "QPHONEMS_BackupEmmcDataBlock_FireHose":
			newTest = test.cloneNode(1)
			# change index
			index = newTest.getElementsByTagName("Index")[0]
			index.childNodes[0].nodeValue = genIndex()
			# mark checked
			uncheckeds = newTest.getElementsByTagName("DotNetProperties")[0].getElementsByTagName("CheckStateTest")
			for unchecked in uncheckeds:
				newTest.getElementsByTagName("DotNetProperties")[0].removeChild(unchecked)
			# modify paras
			paras = newTest.getElementsByTagName("DotNetProperties")[0].getElementsByTagName("Parameters")[0].getElementsByTagName("ParameterCls")
			#print "newTest"
			for para in paras:
				paraName = para.getElementsByTagName("Name")[0]
				paraNameData = paraName.childNodes[0].data
				paraValue = para.getElementsByTagName("Value")[0]
				if paraValue.hasChildNodes():
					paraValueData = paraValue.childNodes[0].nodeValue
					#print "Name="+paraNameData+"  Value="+paraValueData
				if paraNameData == "startSector":
					paraValue.childNodes[0].nodeValue = startSector
				if paraNameData == "numPartitionSectors":
					paraValue.childNodes[0].nodeValue = numSector
				if paraNameData == "imagefile":
					paraValue.childNodes[0].nodeValue = imageName
			#print "insert newtest"
			firehoseFolder.insertBefore(newTest, testNoPatch)
			break
			
			
# get Folder by name
def getFolderByName(parentNode, name):
	folders = parentNode.getElementsByTagName("FolderTest")
	for folder in folders:
		FolderProperties = folder.getElementsByTagName("FolderProperties")[0]
		TestName = FolderProperties.getElementsByTagName("TestName")[0]
		fname = TestName.childNodes[0].data
		#print "folder name = %s" % fname
		if fname == name:
			return folder
	return -1

# clean the useless tests in original file
def initReadTest(firehoseFolder):
	tests = firehoseFolder.getElementsByTagName("DotNetTest")
	first = 1
	for test in tests:
		prop = test.getElementsByTagName("DotNetProperties")[0]
		TestName = prop.getElementsByTagName("TestName")[0]
		TestNameData = TestName.childNodes[0].data
		#print "TestNameData = %s" % TestNameData
		
		if TestNameData == "QPHONEMS_BackupEmmcDataBlock_FireHose":
			if first == 1:
				#print "get first"
				refTest = test.cloneNode(1)
				prop = refTest.getElementsByTagName("DotNetProperties")[0]
				e = DOMTreeOut.createElement("CheckStateTest")
				n = DOMTreeOut.createTextNode("Unchecked")
				e.appendChild(n)
				prop.appendChild(e)
				first = 0
				firehoseFolder.insertBefore(refTest, test)
			#print "removed"
			firehoseFolder.removeChild(test)

			
def insertAll(programs, firehoseFolder):
	for program in programs:
		#print "program:"
		if program.hasAttribute("filename"):
			if program.getAttribute("filename") != "" and program.getAttribute("filename").find("gpt") == -1:
				#print "filename=%s" % program.getAttribute("filename")
				if program.getAttribute("label").find("bak") != -1:
					insertBlock(firehoseFolder, program.getAttribute("start_sector"), program.getAttribute("num_partition_sectors"), program.getAttribute("filename")+".read.bak")
				else:
					insertBlock(firehoseFolder, program.getAttribute("start_sector"), program.getAttribute("num_partition_sectors"), program.getAttribute("filename")+".read")

def insertSystem(programs, firehoseFolder):
	start = ""
	end = ""
	first = 1
	last = 0

	for program in programs:
		if program.hasAttribute("filename"):
			if program.getAttribute("filename").find("system") != -1:
				#print "got system " + program.getAttribute("filename")
				# find the first system partition
				if first == 1:
					#print "got first"
					start = program.getAttribute("start_sector")
					first = 0
					last = 1					
			else:
				#print "not system"
				# find the partition after system
				if last == 1:
					end = program.getAttribute("start_sector")	
					#print "got first block after system" + end				
					break
					
	insertBlock(firehoseFolder, start, str(int(end) - int(start)), "system.img.read")

def insertArmPrg(ArmPrg, saharaFolder):
	tests = saharaFolder.getElementsByTagName("DotNetTest")
	
	for test in tests:
		prop = test.getElementsByTagName("DotNetProperties")[0]
		TestName = prop.getElementsByTagName("TestName")[0]
		TestNameData = TestName.childNodes[0].data
		#print "TestNameData = %s" % TestNameData
		
		if TestNameData == "QPHONEMS_SaharaArmPrgDownload":
			#print "get QPHONEMS_SaharaArmPrgDownload"
			paras = test.getElementsByTagName("DotNetProperties")[0].getElementsByTagName("Parameters")[0].getElementsByTagName("ParameterCls")		
			for para in paras:
				paraName = para.getElementsByTagName("Name")[0]
				paraNameData = paraName.childNodes[0].data
				paraValue = para.getElementsByTagName("Value")[0]
				if paraValue.hasChildNodes():
					paraValueData = paraValue.childNodes[0].nodeValue
					#print "Name="+paraNameData+"  Value="+paraValueData
				if paraNameData == "sFilename":
					paraValue.childNodes[0].nodeValue = ArmPrg				
	
def genXtt(outFile, onlysystem):

	SerializeComponents = DOMTreeOut.documentElement
	theRootTest = SerializeComponents.getElementsByTagName("theRootTest")[0]

	saharaFolder = getFolderByName(theRootTest, "Sahara")
	if saharaFolder == -1:
		print "sahara not found"
		return -1
	else:
		#print "got sahara"
		armPrgFiles = findFile.findFile("prog_emmc_firehose*")
		if len(armPrgFiles) == 0:
			print "prog_emmc_firehose_*.mbn not found"
			return -1
		elif len(armPrgFiles) > 1:
			print "find multi prog_emmc_firehose_*.mbn, error"
			return -1
		armPrg = armPrgFiles[0]
		insertArmPrg(armPrg, saharaFolder)
				
	firehoseFolder = getFolderByName(theRootTest, "FireHose_ImageDownload")
	if firehoseFolder == -1:
		print "firehose folder not found"
		return -1

	else:
		#print "got firehose"
		initReadTest(firehoseFolder)
		
		data = DOMTreeIn.documentElement
		programs = data.getElementsByTagName("program")

		if onlysystem:
			insertSystem(programs, firehoseFolder)
		else:
			insertAll(programs, firehoseFolder)
		
		f = open(outFile,"wb")
		DOMTreeOut.writexml(f)
		f.close()
		print outFile+" generation done"
		return 0
		
	
# main	
if len(sys.argv) != 4:
	print "Usage: \txml2xtt [all/system] template.xtt output.xtt"
	print "Ver: \t1.04 2015-08-05"
else:
	DOMTreeIn = xml.dom.minidom.parse("rawprogram0.xml")
	DOMTreeOut = xml.dom.minidom.parse(sys.argv[2])
	if sys.argv[1] == "system":
		genXtt(sys.argv[3], 1)
	else:
		genXtt(sys.argv[3], 0)
