"""
A place for trying things out, performing exploratory testing, etc.
"""

import os
import sys
import time
from sys import argv

SCRIPT_DIR = os.path.dirname(os.path.realpath(os.path.abspath(__file__)))
sys.path.append(SCRIPT_DIR)
from src.framework import engine
from src.framework import wav_io as wavIO

if __name__ == '__main__':

	# With reach_back() call 121 seconds
	def cb(pIObj, sampleNestedList):
		for block in range(len(sampleNestedList)):
			for channel in range(len(sampleNestedList[block])):
					pIObj.reach_back(44100, block, channel)
		return sampleNestedList
	
	# No reach_back() call: 30 seconds
	def test_time(pIObj, sampleNestedList):
		for block in range(len(sampleNestedList)):
			for channel in range(len(sampleNestedList[block])):
				pass
		return sampleNestedList
	
	options = {
		engine.OUTPUT_FMT: 'float',
		engine.OUTPUT_BIT_DEPTH: 32
	}
	
	processor = engine.FileToFileEngine(argv[1], argv[2], options=options)
	processor.process()

	endTime = time.clock()
	print("ELAPSED TIME: {}".format(endTime))