"""
TODO:  Refactor
"""

import os
import sys
from sys import argv
import struct

class CreateTestFile:
	
	def __init__(self, testDataDir, argList):
		self.testDataDir = testDataDir
		self.testFileName = 'WAVE_' + argList[0]
		self.chunkID = argList[1]
		self.chunkSize = argList[2]
		self.waveID = argList[3]
		self.fmtChunkId = argList[4]
		self.fmtChunkSize = argList[5]
		self.audioFormat = argList[6]
		self.numChannels = argList[7]
		self.sampleRate = argList[8]
		self.bytesPerSec = argList[9]
		self.blockAlign = argList[10]
		self.bitsPerSample = argList[11]
		self.cbSize = argList[12]
		self.wValidBitsPerSample = argList[13]
		self.dwChannelMask = argList[14]
		self.subFormat = argList[15]
		self.factChunkId = argList[16]
		self.factChunkSize = argList[17]
		self.dwSampleLength = argList[18]
		self.dataChunkId = argList[19]
		self.dataChunkSize = argList[20]
		self.data = argList[21].split(',')
	
	def conditional_write_utf(self, parameterStr):
		if parameterStr == 'None':
			return
		else:
			self.writeStream.write(bytes(parameterStr, 'utf-8'))
	
	def conditional_write_int(self, parameterInt, byteorder='little', signed=False, intLen=4):
		if parameterInt == 'None':
			return
		else:
			self.writeStream.write(int(parameterInt).to_bytes(intLen, byteorder=byteorder, signed=signed))
	
	def write_test_file(self):
		with open(self.testDataDir + self.testFileName, 'wb') as writeStream:
			self.writeStream = writeStream
			self.conditional_write_utf(self.chunkID)
			self.conditional_write_int(self.chunkSize)
			self.conditional_write_utf(self.waveID)
			self.conditional_write_utf(self.fmtChunkId)
			self.conditional_write_int(self.fmtChunkSize)
			self.conditional_write_int(self.audioFormat, intLen=2)
			self.conditional_write_int(self.numChannels, intLen=2)
			self.conditional_write_int(self.sampleRate)
			self.conditional_write_int(self.bytesPerSec)
			self.conditional_write_int(self.blockAlign, intLen=2)
			self.conditional_write_int(self.bitsPerSample, intLen=2)
			# Extension
			self.conditional_write_int(self.cbSize, intLen=2)
			self.conditional_write_int(self.wValidBitsPerSample, intLen=2)
			self.conditional_write_int(self.dwChannelMask, intLen=4)
			self.conditional_write_int(self.subFormat, intLen=16)
			# Fact chunk
			self.conditional_write_utf(self.factChunkId)
			self.conditional_write_int(self.factChunkSize, intLen=4)
			try:
				self.conditional_write_int(self.dwSampleLength, intLen=(int(self.factChunkSize)))
			except:
				pass
			# Data chunk
			self.conditional_write_utf(self.dataChunkId)
			self.conditional_write_int(self.dataChunkSize, intLen=4)
			# DATA
			if int(self.audioFormat) == 3:
				if int(self.bitsPerSample) == 32:
					for sample in self.data:
						self.writeStream.write(struct.pack('<f', int(sample)/1))
				elif int(self.bitsPerSample) == 24:
					pass
				elif int(self.bitsPerSample) == 64:
					for sample in self.data:
						self.writeStream.write(struct.pack('<d', int(sample)/1))
			elif int(self.audioFormat) == 1:
				for sample in self.data:
					if self.bitsPerSample == '8':
						self.writeStream.write(int(sample).to_bytes(int(int(self.bitsPerSample) / 8), byteorder='little', signed=False))
					else:
						self.writeStream.write(int(sample).to_bytes(int(int(self.bitsPerSample) / 8), byteorder='little', signed=True))
			else:
				pass  # ADD FUNCTIONALITY LATER
			# Pad:
			if (int(self.dataChunkSize) % 2) == 1:
				self.conditional_write_int('0', intLen=1)

if __name__ == '__main__':
	# get necessary file/dir names
	# NOTE: can't use os.getcwd() because this file is run using runpy
	#       inside the runtests.py, so os.getcwd() would return the
	#       working directory of that file.
	currentFile = __file__.split('/')[-1]
	currentWorkingDir = '/'.join(__file__.split('/')[0:-1])
	testDataCsvFile = currentFile.split('make')[1].split('.')[0] + '.csv'
	testDataCsvPath = currentWorkingDir + '/' + testDataCsvFile
	testDataDir = os.path.abspath(os.path.join(currentWorkingDir, os.pardir)) + '/testData/'
	# read test data csv file
	lines = []
	with open(testDataCsvPath, 'r') as readStream:
		lines = readStream.readlines()
	# make the test files based on info from the csv file
	for line in lines:
		if line[0] == '#':
			continue
		else:
			pass
		args = line.split(';')
		testObj = CreateTestFile(testDataDir, args)
		testObj.write_test_file()
		
	
	
				
				
				
				
				