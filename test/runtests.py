import os
import sys
import unittest
import runpy
from sys import argv
from time import gmtime, strftime

class AutomateTesting:
	"""
	Used to run the automated testing, including the unittest
	testing, and the setup for that testing.
	"""
	
	# CONSTANTS:
	testScriptsDir = '/testScripts/'
	testLogDir = '/testLogs/'
	makeTestDataDir = '/makeTestData/'
	testDataDir = '/testData/'
	makeScriptPrefix = 'make'
	runpyRunName = "__main__"
	
	def __init__(self, logName=''):
		self.set_log_file_path(logName)
		self.make_test_data()
		self.testLoader = unittest.TestLoader()
		self.testSuite = self.testLoader.discover(os.path.dirname(
												  os.path.abspath(__file__)) + 
												  self.testScriptsDir)
	
	def run_tests(self):
		"""
		Runs the loaded test suite stored in self.testSuite.  Outputs the
		results to the log file specified by self.logFilePath.
		"""
		with open(self.logFilePath, 'w') as logStream:
			textRunner = unittest.TextTestRunner(stream=logStream, verbosity=2)
			textRunner.run(self.testSuite)
		

	def make_test_data(self):
		"""
		The test/makeTestData/ directory contains two types of files.
		The first is a python script, whose name begins with 'make',
		and the other is a .csv file with the same name minus the 'make'.
		The makeTestData() function runs the __main__ within each of the
		python scripts, which in turn creates audio files for use in
		automated testing based on parameters in the corresponding .csv
		file.  The audio files are stored in the test/testdata directory.
		"""
		# make testData dir if necessary
		testDataPath = os.path.normpath(
						os.path.dirname(
						os.path.abspath(__file__)) + self.testDataDir)
		if not os.path.isdir(testDataPath):
			os.mkdir(testDataPath)
		else:
			for file in os.listdir(testDataPath):
				os.remove(os.path.join(testDataPath, file))
		# next make test data
		makeTestDataDirPath = os.path.dirname(
								os.path.abspath(__file__)) + \
								self.makeTestDataDir
		for file in os.listdir(makeTestDataDirPath):
			if file.startswith(self.makeScriptPrefix):
				runpy.run_path(makeTestDataDirPath + file, 
								run_name=self.runpyRunName)
			else:
				pass
	
	def set_log_file_path(self, logName):
		"""
		Set the self.logFilePath based on logName.  First checks to see
		that the log directory exists; if not, makes it.
		"""
		logFileName = strftime("%Y-%m-%d_%H-%M-%S", gmtime()) + \
						logName + '.txt'
		logDirPath = os.path.dirname(os.path.abspath(__file__)) + \
						self.testLogDir
		if not os.path.isdir(logDirPath):
			os.mkdir(logDirPath)
		else:
			pass
		self.logFilePath = logDirPath + logFileName
		print("PATH TO LOG FILE:\n{}".format(self.logFilePath))
		

if __name__ == '__main__':
	if len(argv) > 2:
		autoTest = AutomateTesting(logName=argv[1])
	else:
		autoTest = AutomateTesting()
	autoTest.run_tests()