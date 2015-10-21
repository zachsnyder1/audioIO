"""
A place for trying things out, performing manual testing, etc.
"""

import os
import sys
import datetime
from sys import argv

SCRIPT_DIR = os.path.dirname(os.path.realpath(os.path.abspath(__file__)))
sys.path.append(SCRIPT_DIR)
from audioIO.engine import audioIOEngine as aIOe
from audioIO.engine import wavIOEngine as wIOe

if __name__ == '__main__':

	def cb(processorObject, sampleNestedList):
		print('\nDATA: {}\n\n'.format(sampleNestedList))
		return sampleNestedList
	
	readObj = wIOe.ReadWav(argv[1])
	writeObj = wIOe.WriteWav(argv[2])
	processor = aIOe.AudioIOEngine(readObj, writeObj, cb)
	processor.process()