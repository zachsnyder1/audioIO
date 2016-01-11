"""
Base class for the engine.
"""
import math
import copy
import re
import os
from collections import deque
from . import base_io as baseIO
from . import wav_io as wavIO
from . import enginehelper as helper


# <<<----- CONSTANTS: ----->>>

# options dictionary keys
OUTPUT_FMT = 'output_format'
OUTPUT_NUM_CHANNELS = 'output_num_channels'
OUTPUT_BIT_DEPTH = 'output_bit_depth'
OUTPUT_SAMPLE_RATE = 'output_sample_rate'
PLUGIN_FMT = 'plugin_format'
PLUGIN_REACH_BACK = 'plugin_reach_back'
# options default value
DEFAULT = 'default'


# <<<----- EXCEPTION CLASSES: ----->>>
class InvalidInput(Exception):
	"""
	Raised when the input entity is invalid.
	"""
	pass

class InvalidOutput(Exception):
	"""
	Raised when the output entity is invalid.
	"""
	pass



class BaseEngine:
	"""
	Abstract base class for framework engines.
	"""
	def __init__(self, 
			inputEntity, 
			outputEntity, 
			algorithm=helper.default_algorithm, 
			options=None):
		"""
		Accepts and stores:
		
		1) inputEntity   ==>  Either read file or input stream.
		
		2) outputEntity  ==>  Either write file or output stream.
		
		3) algorithm     ==>  A callback used to process the audio data.
		
		4) options       ==>  A dictionary of processing/conversion options.
		"""
		# Initialize instance vars
		self.algorithm = algorithm
		
		if not options:
			self.options = dict()
		else:
			self.options = copy.deepcopy(options)
		
		# If option not set, set to DEFAULT
		defaultKeys = [
			OUTPUT_FMT,
			OUTPUT_NUM_CHANNELS,
			OUTPUT_BIT_DEPTH,
			OUTPUT_SAMPLE_RATE,
			PLUGIN_FMT,
			PLUGIN_REACH_BACK
		]
		for key in defaultKeys:
			try:
				self.options[key]
			except KeyError:
				self.options[key] = DEFAULT
		
		# Replace defaults in self.options dictionary:
		defaultMap = {
			PLUGIN_REACH_BACK: 0,
		}
		for key in defaultMap:
			if self.options[key] == DEFAULT:
				self.options[key] = defaultMap[key]
			else:
				pass

		# Validate the input/output entities, create and initialize the input
		# and output objects
		self.initializeIO(inputEntity, outputEntity)
		
		# for quick, clean access in the select_algorithm_wrapper() function:
		self.readFormat = self.audioInput.headerDict[baseIO.CORE_KEY_FMT]
		self.writeFormat = self.audioOutput.headerDict[baseIO.CORE_KEY_FMT]
		self.readBitDepth = \
			self.audioInput.headerDict[baseIO.CORE_KEY_BIT_DEPTH]
		self.writeBitDepth = \
			self.audioOutput.headerDict[baseIO.CORE_KEY_BIT_DEPTH]
		self.readSigned = self.audioInput.headerDict[baseIO.CORE_KEY_SIGNED]
		self.writeSigned = self.audioOutput.headerDict[baseIO.CORE_KEY_SIGNED]

		# Create the reach back deque
		if self.options[PLUGIN_REACH_BACK] > 0:
			reachBackDequeLength = \
				math.ceil(self.options[PLUGIN_REACH_BACK] / \
					baseIO.SAMPLES_PER_BUFFER) + 1
		else:
			reachBackDequeLength = 0
		self.reachBackDeque = deque(deque(), reachBackDequeLength)
		self.bufferLenDeque = deque(deque(), reachBackDequeLength)
		
		# initialize the algorithm wrapper
		self.algorithm_wrapper =  self.select_algorithm_wrapper()

	# ------------------------------------------------------------------------
	# --------------------------- ABSTRACT OPERATIONS ------------------------
	# ------------------------------------------------------------------------
	
	def initializeIO(self, inputEntity, outputEntity):
		"""
		Abstract operation that validates the input/output entities, and then
		instantiates and initializes the self.audioInput and self.audioOutput
		objects.
		
		Accepts:
		
		1) inputEntity  ==>  The input entity passed to the Engine during
							 initialization.
		2) outputEntity ==>  The output entity passed to the Engine during
							 initialization.
		"""
		self.audioInput = baseIO.ReadAudio(inputEntity)
		self.audioOutput = baseIO.WriteAudio(outputEntity)
	
	def process(self):
		"""
		Abstract operation that initiates the plugin processing.
		"""
		return
	
	# ------------------------------------------------------------------------
	# ------------------------- END:  ABSTRACT OPERATIONS --------------------
	# ------------------------------------------------------------------------
	
	def select_algorithm_wrapper(self):
		"""
		The algorithm_wrapper applies approriate data conversions based on
		the readFile data format, requested plugin data format, and the
		requested writeFile data format.  This method selects the correct
		algorithm_wrapper function based on those initiation parameters.
		"""
		# Conditionally assign the algorithm_wrapper() function:
		# If read format and write format are both float...
		if self.readFormat == self.writeFormat and \
			(self.readFormat == baseIO.FLOAT):
			# ...and the algorithm works with floating point,
			# simply pass to the algorithm.
			if self.options[PLUGIN_FMT] == baseIO.FLOAT:
				return helper.wrapper_fff
			# ...but the algorithm works with PCM,
			# convert to PCM, pass to algorithm, convert back to float.
			elif self.options[PLUGIN_FMT] == baseIO.PCM:
				return helper.wrapper_fpf
		# If read format and write format are both PCM...
		elif self.readFormat == self.writeFormat and \
			(self.readFormat == baseIO.PCM):
			# ...but the algorithm works with floating point,
			# convert to float, pass to algorithm, convert back to PCM
			if self.options[PLUGIN_FMT] == baseIO.FLOAT:
				return helper.wrapper_pfp
			# ...and the algorithm works with PCM...
			elif self.options[PLUGIN_FMT] == baseIO.PCM:
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
			(self.readFormat == baseIO.FLOAT):
			# ...and the algorithm works with floating point,
			# pass to the algorithm, then convert to PCM.
			if self.options[PLUGIN_FMT] == baseIO.FLOAT:
				return helper.wrapper_ffp
			# ...and the algorithm works with PCM...
			elif self.options[PLUGIN_FMT] == baseIO.PCM:
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
			(self.readFormat == baseIO.PCM):
			# ...and the algorithm works with floating point,
			# convert to float, then pass to the algorithm.
			if self.options[PLUGIN_FMT] == baseIO.FLOAT:
				return helper.wrapper_pff
			# ...and the algorithm works with PCM...
			elif self.options[PLUGIN_FMT] == baseIO.PCM:
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
		!!! TIME ISSUE !!!
		
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
	

class FileToFileEngine(BaseEngine):
	"""
	"""
	def initializeIO(self, inputEntity, outputEntity):
		"""
		Concrete operation that validates the input/output entities, and then
		instantiates and initializes the self.audioInput and self.audioOutput
		objects.
		
		Accepts:
		
		1) inputEntity  ==>  The input entity passed to the Engine during
							 initialization.
		2) outputEntity ==>  The output entity passed to the Engine during
							 initialization.
		"""
		# <<<--- VALIDATION --->>>
		# make sure I/O entities are valid file paths
		# input entity:
		if isinstance(inputEntity, str):
			if not os.path.exists(inputEntity):
				raise InvalidInput("readFile needs to be valid path")
			else:
				pass
		else:
			raise InvalidInput("readFile needs to be valid path")
		# Output entity:
		if not isinstance(outputEntity, str):
			raise InvalidOutput("writeFile needs to be valid path")
		else:
			pass
		
		# Make sure extensions are supported by the framework
		inputValid = False  # BOOL: validity of input file extension
		outputValid = False # BOOL: validity of output file extension
		# regex search patterns for all valid file extensions
		validFileExt = [
			r'.*[.]wav$',
		]
		# search paths for extensions
		for extension in validFileExt:
			if re.search(extension, inputEntity):
				inputValid = True
			else:
				pass
			if re.search(extension, outputEntity):
				outputValid = True
			else:
				pass
		
		# raise exceptions if input/output entities not valid
		if inputValid:
			pass
		else:
			errorMsg = "{} file type not supported".format(inputEntity)
			raise InvalidInput(errorMsg)
		if outputValid:
			pass
		else:
			errorMsg = "{} file type not supported".format(outputEntity)
			raise InvalidOutput(errorMsg)
		
		# <<<--- INSTANTIATION, INITIALIZATION --->>>
		# Audio input object first:
		self.audioInput = wavIO.ReadWav(inputEntity)
		with open(inputEntity, 'rb') as readStream:
			self.audioInput.read_header(readStream)

		# Replace defaults in self.options dictionary:
		defaultMap = {
			PLUGIN_FMT: baseIO.CORE_KEY_FMT,
			OUTPUT_FMT: baseIO.CORE_KEY_FMT,
			OUTPUT_NUM_CHANNELS: baseIO.CORE_KEY_NUM_CHANNELS,
			OUTPUT_BIT_DEPTH: baseIO.CORE_KEY_BIT_DEPTH,
			OUTPUT_SAMPLE_RATE: baseIO.CORE_KEY_SAMPLE_RATE
		}
		for key in defaultMap:
			if self.options[key] == DEFAULT:
				self.options[key] = self.audioInput.headerDict[defaultMap[key]]
			else:
				pass
		
		# Now create audio output object:
		self.audioOutput = wavIO.WriteWav(
			outputEntity, 
			format=self.options[OUTPUT_FMT],
			numChannels=self.options[OUTPUT_NUM_CHANNELS],
			bitDepth=self.options[OUTPUT_BIT_DEPTH],
			sampleRate=self.options[OUTPUT_SAMPLE_RATE])
		# and initialize:
		self.audioOutput.init_header(
			self.audioInput, self.options[PLUGIN_REACH_BACK])

	def process(self):
		"""
		Reads input file, exposes it to the plugin algorithm as a nested array
		of sample values, then writes the processed audio to the output
		file.
		"""
		with open(self.audioInput.targetFile, 'rb') as readStream:
			with open(self.audioOutput.targetFile, 'wb') as writeStream:
				# Write header of output
				self.audioOutput.write_header(writeStream)
				# Set read stream to beginning of data
				readStream.seek(0)
				self.byteArray = readStream.read(self.audioInput.headerLen)
					
				# Expose a nested list of samples to the callback function
				# and write the processed data:
				blockAlign = \
					self.audioInput.headerDict[baseIO.CORE_KEY_BYTE_DEPTH] * \
					self.audioInput.headerDict[baseIO.CORE_KEY_NUM_CHANNELS]
				bufferSize = baseIO.SAMPLES_PER_BUFFER * blockAlign
				while True:
					byteArray = readStream.read(bufferSize)   # Read Data
					if byteArray:
						# Unpack binary
						sampleNestedList = self.audioInput.unpack(byteArray)
						# EXECUTE CALLBACK
						processedSampleNestedList = \
							self.algorithm_wrapper(self, sampleNestedList)
						# Pack processed data
						processedByteArray = \
							self.audioOutput.repack(processedSampleNestedList)
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
		if not self.options[PLUGIN_REACH_BACK]:
			return
		else:
			# Set correct zero (float, PCM signed, PCM unsigned)
			zero = None
			if self.readFormat == baseIO.FLOAT:
				zero = float(0)
			elif self.readFormat == baseIO.PCM and \
				self.readSigned == True:
				zero = int(0)
			elif self.readFormat == baseIO.PCM and \
				self.readSigned == False:
				zero = int(2**(self.readBitDepth - 1))
			# Create a dummy nested list with all zeros
			list = []
			for i in range(self.audioInput.headerDict[
							baseIO.CORE_KEY_NUM_CHANNELS]):
				list.append(copy.copy(zero))
			nest = []
			for i in range(self.options[PLUGIN_REACH_BACK]):
				nest.append(copy.deepcopy(list))
			# Feed the nest peacemeal into the algorith_wrapper()
			counter = 0
			while True:
				if counter > len(nest):
					break
				else:
					pass
				bufferFull = nest[counter:
								  (counter + baseIO.SAMPLES_PER_BUFFER)]
				# Execute callback
				processedSampleNestedList = \
					self.algorithm_wrapper(self, bufferFull)
				# Pack processed data
				processedByteArray = \
					self.audioOutput.repack(processedSampleNestedList)
				# Write processed buffer to file
				writeStream.write(processedByteArray)
				counter += baseIO.SAMPLES_PER_BUFFER


class StreamToFileEngine(BaseEngine):
	"""
	"""
	def process(self):
		"""
		"""
		pass


class StreamToStreamEngine(BaseEngine):
	"""
	"""
	def process(self):
		"""
		"""
		pass

