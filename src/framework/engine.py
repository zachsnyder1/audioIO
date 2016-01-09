"""
Base class for the engine.
"""
import math
import copy
from collections import deque
from . import audioIO as aIO
from . import engine_helper as helper


class Engine:
	"""
	Class for plugin algorithm objects.  Connects a ReadAudo object
	with a WriteAudio object and an audio processing algorithm, as a
	callback.
	"""
	def __init__(self, readObj, writeObj, algorithm=None, reachBack=0, 
				format=None):
		"""
		Accepts and stores:
		
		1) readObj  ==>  The initialized read audio object.
		
		2) writeObj ==>  The initialized write audio object.
		
		3) algorithm     ==>  A callback used to process the audio data.
		
		4) reachBack     ==>  The number of samples that the algorithm will
							  be able to "reach" back to for reference during
							  calculation.  This is important only if
							  processingis retrospective.  Default is 0.
		5) format        ==>  The format (either 'float' or 'PCM') in which
							  the data will be presented to the algorithm.
							  Default is that it is the same as the format
							  of the read file.
		"""
		self.readObj = readObj
		self.writeObj = writeObj
		self.reachBack = reachBack
		self.exposureFormat = format
		# Set the algorithm to input, or default if no input
		if algorithm:
			self.algorithm = algorithm
		else:
			self.algorithm = self.default_algorithm
		# If reachBack, create the reach back deque
		if self.reachBack > 0:
			reachBackDequeLength = \
				math.ceil(self.reachBack / aIO.SAMPLES_PER_BUFFER) + 1
		else:
			reachBackDequeLength = 0
		self.reachBackDeque = deque(deque(), reachBackDequeLength)
		self.bufferLenDeque = deque(deque(), reachBackDequeLength)
		
		# init file headers
		with open(self.readObj.targetFile, 'rb') as readStream:
			self.readObj.read_header(readStream)
		self.writeObj.init_header(self.readObj, self.reachBack)
		# for quick, clean access in the algorithm_wrapper_closure() function:
		self.readFormat = self.readObj.headerDict[aIO.CORE_KEY_FMT]
		self.writeFormat = self.writeObj.headerDict[aIO.CORE_KEY_FMT]
		self.readBitDepth = self.readObj.headerDict[aIO.CORE_KEY_BIT_DEPTH]
		self.writeBitDepth = self.writeObj.headerDict[aIO.CORE_KEY_BIT_DEPTH]
		self.readSigned = self.readObj.headerDict[aIO.CORE_KEY_SIGNED]
		self.writeSigned = self.writeObj.headerDict[aIO.CORE_KEY_SIGNED]
		# init self.exposureFormat, if None
		if self.exposureFormat == None:
			self.exposureFormat = self.readFormat
		else:
			pass
		# initialize the algorithm wrapper
		self.algorithm_wrapper =  self.algorithm_wrapper_closure()
	
	def process(self):
		"""
		Reads input file, exposes it to the plugin algorithm as a nested array
		of sample values, then writes the processed audio to the output
		file.
		"""
		with open(self.readObj.targetFile, 'rb') as readStream:
			with open(self.writeObj.targetFile, 'wb') as writeStream:
				# Write header of output
				self.writeObj.write_header(writeStream)
				# Set read stream to beginning of data
				readStream.seek(0)
				self.byteArray = readStream.read(self.readObj.headerLen)
					
				# Expose a nested list of samples to the callback function
				# and write the processed data:
				blockAlign = \
					self.readObj.headerDict[aIO.CORE_KEY_BYTE_DEPTH] * \
					self.readObj.headerDict[aIO.CORE_KEY_NUM_CHANNELS]
				bufferSize = aIO.SAMPLES_PER_BUFFER * blockAlign
				while True:
					byteArray = readStream.read(bufferSize)   # Read Data
					if byteArray:
						# Unpack binary
						sampleNestedList = self.readObj.unpack(byteArray)
						# EXECUTE CALLBACK
						processedSampleNestedList = \
							self.algorithm_wrapper(self, sampleNestedList)
						# Pack processed data
						processedByteArray = \
							self.writeObj.repack(processedSampleNestedList)
						# Write processed buffer to file
						writeStream.write(processedByteArray)
					else:
						break
				# Don't forget to flush()
				self.flush(writeStream)
	
	def flush(self, writeStream):
		"""
		Called at the end of the process() while loop.  Feeds the algorithm
		empty samples (value=0) so that it can finish processing any fade-out
		of the envelope.
		
		Accepts:
		
		1) writeStream  ==>  A pointer to the open write file.
		"""
		if not self.reachBack:
			return
		else:
			# Set correct zero (float, PCM signed, PCM unsigned)
			zero = None
			if self.readFormat == aIO.FLOAT:
				zero = float(0)
			elif self.readFormat == aIO.PCM and \
				self.readSigned == True:
				zero = int(0)
			elif self.readFormat == aIO.PCM and \
				self.readSigned == False:
				zero = int(2**(self.readBitDepth - 1))
			# Create a dummy nested list with all zeros
			list = []
			for i in range(self.readObj.headerDict[
							aIO.CORE_KEY_NUM_CHANNELS]):
				list.append(copy.copy(zero))
			nest = []
			for i in range(self.reachBack):
				nest.append(copy.deepcopy(list))
			# Feed the nest peacemeal into the algorith_wrapper()
			counter = 0
			while True:
				if counter > len(nest):
					break
				else:
					pass
				bufferFull = nest[counter:
								  (counter + aIO.SAMPLES_PER_BUFFER)]
				# Execute callback
				processedSampleNestedList = \
					self.algorithm_wrapper(self, bufferFull)
				# Pack processed data
				processedByteArray = \
					self.writeObj.repack(processedSampleNestedList)
				# Write processed buffer to file
				writeStream.write(processedByteArray)
				counter += aIO.SAMPLES_PER_BUFFER

	
	def default_algorithm(self, sampleNestedList):
		"""
		Default algorithm, if Engine object is instantiated without
		an algorithm callback.
		"""
		return sampleNestedList
	
	def algorithm_wrapper_closure(self):
		"""
		A closure for the algorithm_wrapper function.  Conditionally define
		the logic in the algorithm_wrapper function, so that you don't have
		to work your way through this nasty logic block every time the
		algorithm() method is called.
		"""
		# Conditionally define algorithm_wrapper() function:
		# If read format and write format are both float...
		if self.readFormat == self.writeFormat and \
			(self.readFormat == aIO.FLOAT):
			# ...and the algorithm works with floating point,
			# simply pass to the algorithm.
			if self.exposureFormat == aIO.FLOAT:
				return helper.wrapper_fff
			# ...but the algorithm works with PCM,
			# convert to PCM, pass to algorithm, convert back to float.
			elif self.exposureFormat == aIO.PCM:
				return helper.wrapper_fpf
		# If read format and write format are both PCM...
		elif self.readFormat == self.writeFormat and \
			(self.readFormat == aIO.PCM):
			# ...but the algorithm works with floating point,
			# convert to float, pass to algorithm, convert back to PCM
			if self.exposureFormat == aIO.FLOAT:
				return helper.wrapper_pfp
			# ...and the algorithm works with PCM...
			elif self.exposureFormat == aIO.PCM:
				# ...and the read data is unsigned...
				if not self.readSigned:
					return helper.wrapper_ppp_unsigned
				# ...and the read data is signed...
				else:
					# ...if there is no conversion of format or int repr,
					# simply pass to the algorithm.
					if self.readBitDepth == self.writeBitDepth and \
						self.readSigned == self.writeSigned:
						return helper.wrapper_ppp_signed_no_conversion
					# ...if there is such conversion,
					# pass to the algorithm, then perform PCM-PCM conversion.
					else:
						return helper.wrapper_ppp_signed_conversion
		# If read format is float and write format is PCM...
		elif self.readFormat != self.writeFormat and \
			(self.readFormat == aIO.FLOAT):
			# ...and the algorithm works with floating point,
			# pass to the algorithm, then convert to PCM.
			if self.exposureFormat == aIO.FLOAT:
				return helper.wrapper_ffp
			# ...and the algorithm works with PCM...
			elif self.exposureFormat == aIO.PCM:
				# ...and the write data is unsigned,
				# convert to signed PCM, pass to algorithm, then to unsigned.
				if not self.writeSigned:
					return helper.wrapper_fpp_unsigned
				# ...and the write data is signed,
				# convert to PCM, then pass to the algorithm.
				else:
					return helper.wrapper_fpp_signed
		# If read format is PCM and write format is float...
		elif self.readFormat != self.writeFormat and \
			(self.readFormat == aIO.PCM):
			# ...and the algorithm works with floating point,
			# convert to float, then pass to the algorithm.
			if self.exposureFormat == aIO.FLOAT:
				return helper.wrapper_pff
			# ...and the algorithm works with PCM...
			elif self.exposureFormat == aIO.PCM:
				# ...and the read file data is unsigned,
				# convert to 2's compliment, pass to algorithm, then
				# convert to float.
				if not self.readSigned:
					return helper.wrapper_ppf_unsigned
				# ...and the read file data is already 2's compliment,
				# pass to the algorithm, then convert to float.
				else:
					return helper.wrapper_ppf_signed
	
	def update_reachback_deques(self, sampleNestedList):
		"""
		Appends copy of nested list of samples to the reachBackDeque,
		and appends the length of the nested list to the bufferLenDeque.
		
		Accepts:
		
		1) sampleNestedList  ==>  The nested list of samples to append
								  to the reachBackDeque.
		"""
		self.reachBackDeque.append(copy.deepcopy(sampleNestedList))
		self.bufferLenDeque.append(len(sampleNestedList))
	
	
	def reach_back(self, numSamples, currBlock, currChannel):
		"""
		Returns the sample from the currentChannel that came
		numSamples beforehand, based on the currentBlock within
		the currently processing buffer-full of samples.  If the
		numSamples is greater than the number of blocks that
		precedes the current sample, then return zero.
		
		Accepts:
		
		1) numSamples  ==>  The number of samples to reach back.
		
		2) currBlock   ==>  The index of the reference block.
		
		3) currChannel ==>  The index of the reference channel.
		
		Returns the value of the reachBack sample.
		"""
		# Calculate the number of preceeding samples
		preceedingSamples = -self.bufferLenDeque[-1]
		for bufferLen in self.bufferLenDeque:
			preceedingSamples += bufferLen
		preceedingSamples += currBlock
		# If attempting to reach back further than start of file,
		# then return a value of zero
		if numSamples > preceedingSamples:
			return 0
		else:
			# *negative* reachBack total index = \
			# 	(curr *negative* position) - numSamples
			rbIndex = currBlock - self.bufferLenDeque[-1] - numSamples
			# Find the correct buffer in deque 
			index1 = 0
			for i in range(1, len(self.bufferLenDeque)+1):
				index1 -= 1
				rbIndex += self.bufferLenDeque[-i]
				if rbIndex >= 0:
					break
			# Return the desired sample
			return self.reachBackDeque[index1][rbIndex][currChannel]
	

