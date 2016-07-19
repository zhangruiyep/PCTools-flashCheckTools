import os
import fnmatch

def findFile(filename):
	results = []
	for file in os.listdir("."):
		if fnmatch.fnmatch(file, filename):
			#print "found "+file
			results.append(file)
	return results
