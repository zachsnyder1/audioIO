"""
A place for trying things out, performing exploratory testing, etc.
"""

import os
import sys
import time
from sys import argv

SCRIPT_DIR = os.path.dirname(os.path.realpath(os.path.abspath(__file__)))
sys.path.append(SCRIPT_DIR)
from audioIO.plugins import plugin
from audioIO.io import wavIO as wIO

if __name__ == '__main__':

	def cb(pIObj, sampleNestedList):
		for block in range(len(sampleNestedList)):
			for channel in range(len(sampleNestedList[block])):
				sampleNestedList[block][channel] += \
					pIObj.reach_back(44100, block, channel) * 0.35
		return sampleNestedList
	
	readObj = wIO.ReadWav(argv[1])
	writeObj = wIO.WriteWav(argv[2], format='PCM', bitDepth=16)
	processor = plugin.Plugin(readObj, writeObj, cb, format='float', 
							reachBack=44100)
	processor.process()
	endTime = time.clock()
	print("ELAPSED TIME: {}".format(endTime))