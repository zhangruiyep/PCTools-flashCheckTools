''' change history:
2015-09-08	1.00	zhangrui: Add file compare funtion. Only compare the useful part, ingore the pad content in read files.
'''

import os
import sys
import findFile

def compFile(srcfile, dstfile):

	srcsize = os.path.getsize(srcfile)
	dstsize = os.path.getsize(dstfile)
	compsize = min(srcsize, dstsize)
	
	blocksize = 4096
	
	srcf = open(srcfile, 'rb')
	dstf = open(dstfile, 'rb')
	
	while (compsize > 0):
		readsize = min(blocksize, compsize)
		srcbuf = srcf.read(readsize)
		dstbuf = dstf.read(readsize)
		
		if cmp(srcbuf, dstbuf) != 0:
			print "Diff in block", (srcsize-compsize)/blocksize
			return -1
		
		compsize -= blocksize
	
	#print "src == dst"
	return 0

'''
if len(sys.argv) != 3:
	print "Usage: \tcompFile srcFilename dstFilename"
	print "Ver: \t1.00 2015-09-08"
else:
	compFile(sys.argv[1], sys.argv[2])
'''

filesList = ['sbl1.mbn', 'tz.mbn', 'rpm.mbn', 'NON-HLOS.bin', 'emmc_appsboot.mbn', 'boot.img', 'recovery.img']
unsparseList = ['system']

mismatchPartitions = []

for srcfile in filesList:
	dstfile = srcfile+'.read'
	if compFile(srcfile, dstfile) != 0:
		print srcfile, "mismatch"
		mismatchPartitions.append(srcfile)
	#else:
	#	print srcfile, "match"

for srcparti in unsparseList:
	srcfiles = findFile.findFile(srcparti+'*.unsparse')
	partitionMatch = 1
	
	for srcfile in srcfiles:
		dstfile = srcfile+'.read' 
		if compFile(srcfile, dstfile) != 0:
			print srcfile, "mismatch"
			partitionMatch = 0
	#	else:
	#		print srcfile, "match"
			
	if partitionMatch == 0:
		mismatchPartitions.append(srcparti)

print "Partitions need check:", mismatchPartitions
