"""
Contains audioIO base classes, including exception classes.
"""

# <<<------ CONSTANTS ----->>>
	
# Audio Formats
FLOAT = 'float'
PCM = 'PCM'
	
# Core headerDict keys
CORE_KEY_FMT = 'audioFormatStr'
CORE_KEY_SIGNED = 'signed'
CORE_KEY_NUM_CHANNELS = 'numChannels'
CORE_KEY_BIT_DEPTH = 'bitDepth'
CORE_KEY_BYTE_DEPTH = 'byteDepth'
CORE_KEY_SAMPLE_RATE = 'sampleRate'
CORE_KEY_SAMPLES_PER_CHANNEL = 'samplesPerChannel'
	
# Assignment and pack strings 
# for self.read_and_assign(), self.pack_and_write()
LITTLE_UTF = 'little_utf'
BIG_UTF = 'big_utf'
LITTLE_INT = 'little_int'
BIG_INT = 'big_int'
LITTLE_UINT = 'little_uint'
BIG_UINT = 'big_uint'
DIRECT = 'direct'
	
# Sizes
SAMPLES_PER_BUFFER = 1024   # Number of samples per buffer
BYTE_SIZE = 8    # Number of bits per byte
INT32_SIZE = 4   # Number of bytes in a 32-bit integer
INT24_SIZE = 3   # Number of bytes in a 24-bit integer
INT16_SIZE = 2   # Number of bytes in a 16-bit integer
INT8_SIZE = 1    # Number of bytes in a 8-bit integer
FLOAT_SIZE = 4   # Number of bytes in a single precision float
DOUBLE_SIZE = 8  # Number of bytes in a double precision float


# Exception classes:
class ReadFileEmpty(Exception):
	"""
	Raised when the read file is empty.
	"""
	pass

class IncompatibleAudioFormat(Exception):
	"""
	Raised when the format of the read file is not covered by
	the module.
	"""
	pass

class AssignmentIdError(Exception):
	"""
	Raised when the ReadAudio.read_and_assign() method recieves
	an unexpected assignment ID string.
	"""
	pass

class PackIdError(Exception):
	"""
	Raised when the ReadAudio.pack_and_write() method recieves
	an unexpected packing ID string.
	"""
	pass



class ReadAudio:
	"""
	This base class for reading audio provides a template and helper
	functions for inheriting classes.  Each file type that is supported
	consists of a read class and a write class, which iherit from 
	ReadAudio and WriteAudio respectively.  Two methods of ReadAudio
	need to be overridden for in the inheriting class:
	
	1) read_header(self, readStream)
	2) unpack(self)
	
	These methods are used by a Engine object in its process() method.
	"""
	def __init__(self, targetFile):
		"""
		self.readOffset ==> Used in helper functions to keep track of the
							current position for future reads.
		self.headerLen  ==> Used to find the beginning of the audio data
							during processing.
		self.headerDict ==> Used to store the values read from the header
							of the audio file being read.
		self.byteArray  ==> Used to store the binary read during the
							read_header() call.
		self.targetFile ==> The only parameter taken by the constructor,
							targetFile is the path of the file to be read.
		"""
		self.readOffset = 0
		self.headerLen = 0
		self.headerDict = {}
		self.byteArray = bytearray()
		self.targetFile = targetFile

	# ------------------------------------------------------------------------
	# --------------------------- ABSTRACT OPERATIONS ------------------------
	# ------------------------------------------------------------------------
	def read_header(self, readStream):
		"""
		Called in Engine().process() to populate the headerDict{} with
		values read from the header of the read file.  Must be overridden by
		the inheriting class.
		
		Accepts one parameter:
		
		1) readStream  ==> The open read file.
		"""
		return
	
	def unpack(self, byteArray):
		"""
		Called in Engine().process() to unpack the buffer binary in a way
		that is relevant to the file type.  Must be overridden by inheriting 
		file type class.
		
		Accepts:
		
		1) byteArray  ==> The buffer binary as a byte array. 
		
		Returns a nested list of sample data with the format:
		
		  [block1=[chan1, chan2, etc.], block2=[chan1, chan2, etc.], etc.]
		"""
		return [[]]
	
	# ------------------------------------------------------------------------
	# ------------------------- END:  ABSTRACT OPERATIONS --------------------
	# ------------------------------------------------------------------------
	
	def unpack_int(self, numBytes, byteorder='little', signed=False):
		"""
		Unpacks a slice of the binary stored in self.byteArray and returns the
		integer value of that slice.  Defined to maximize code reuse.
		
		Accepts:
		
		1) numBytes   ==> The size of the binary slice in bytes.
		2) byteorder ==> The byteorder of the binary. Either 'little'
						  or 'big'; default='little'.
		3) signed     ==> Bool indicates whether or not the integer is signed.
						  Default=False.
		
		Returns the unpacked integer.
		"""
		binary = self.byteArray[self.readOffset:(self.readOffset + numBytes)]
		self.readOffset += numBytes
		return int.from_bytes(binary, byteorder=byteorder, signed=signed)
	
	def unpack_utf(self, numBytes, byteorder='big'):
		"""
		Unpacks a slice of the binary stored in self.byteArray and returns
		the decoded string based on UTF-8 encoding.
		
		Accepts:
		
		1) numBytes  ==> The size of the binary slice in bytes.
		
		Returns the decoded UTF-8 string.
		"""
		if byteorder == 'big':
			binary = self.byteArray[self.readOffset:
									(self.readOffset + numBytes)]
			self.readOffset += numBytes
			return binary.decode('utf-8')
		elif byteorder == 'little':
			binary = bytearray()
			for i in range(numBytes):
				binary += self.byteArray[(self.readOffset + numBytes) - (1+i):
											(self.readOffset + numBytes) - i]
			self.readOffset += numBytes
			return binary.decode('utf-8')
	
	def read_and_assign(self, readStream, readLen, assignmentNestedTuple):
		"""
		Reads readLen bytes from readStream and makes assignments to the
		headerDict{} based on the information in the assignmentNestedTuple.
		
		Accepts:
		
		1) readStream  ==> The open read file.
		2) readLen     ==> The amount of binary to read from the file in
						   bytes.  Equal to the sum of the length of all
						   assignment values, but can be less if you want
						   to assign values from a variable-length header
						   section.  In that case, include assignment
						   parametes for every value in the maximum
						   length header section, and assign the readLen
						   to be only the actual length of the section.
						   That way, if the extension is missing, the values
						   are assigned as zero (numeric-type) or '' (string-
						   type) by default.
		3) assignmentNestedTuple
			==> a nested tuple, where each inner tuple contains 3 values:
			
			  1) assignmentIdStr - (BIG_UTF -> unpacks bin to
			  						big-endian UTF-8 str)
			  					 - (LITTLE_UTF -> unpacks bin to
			  					 	little-endian UTF-8 str)
					   			 - (BIG_UINT -> unpacks bin to
					   			 	big-endian unisgned int)
					   			 - (LITTLE_UINT -> unpacks bin to
					   			 	little-endian unisgned int)
					   			 - (BIG_INT -> unpacks bin to
					   			 	big-endian signed int)
					   			 - (LITTLE_INT -> unpacks bin to
					   			 	little-endian signed int)
					   			 - (DIRECT -> assigns val 2 
					   			 	directly as val 3)
			  2) headerKey  -  The key in self.headerDict{} to which the value
			  				   will be assigned.
			  3) If assignmentIdStr == DIRECT:
			  			- The value that will be assigned to headerKey in the
			  			  headerDict.
			  	 else:
			  	 		- The size of the binary slice that will be 
			  	 		  interpreted as either the int or UTF-8 string 
			  	 		  assigned to headerKey.
			  	 
			  	 Either way, the third value can be a lambda expression, which
			  	 can be used if you are trying to reference a headerDict{} key
			  	 before it is assigned a vlaue.
		
		Example of assignmentNestedTuple:
		
			(
				(BIG_UTF, self.keyChunkId, INT32_SIZE),
				(self.assignLittleUNIT, self.keyChunkSize, INT16_SIZE),
				(DIRECT, 'foo', 'bar')
			)
		"""
		# Read from file
		self.byteArray = readStream.read(readLen)
		self.readOffset = 0
		# Assert that the read worked
		if not self.byteArray:
			raise ReadFileEmpty
		else:
			# For each separate assignment tuple, take action based on 
			# assignment string, and on whether or not the third value
			# is a lambda expression:
			for assignment in assignmentNestedTuple:
				if assignment[0] == BIG_UTF:
					if callable(assignment[2]):
						self.headerDict[assignment[1]] = \
							self.unpack_utf(assignment[2]())
					else:
						self.headerDict[assignment[1]] = \
							self.unpack_utf(assignment[2])
				elif assignment[0] == LITTLE_UTF:
					if callable(assignment[2]):
						self.headerDict[assignment[1]] = \
							self.unpack_utf(assignment[2](), 
											byteorder='little')
					else:
						self.headerDict[assignment[1]] = \
							self.unpack_utf(assignment[2], 
											byteorder='little')
				elif assignment[0] == BIG_UINT:
					if callable(assignment[2]):
						self.headerDict[assignment[1]] = \
							self.unpack_int(assignment[2](), 
											byteorder='big', 
											signed=False)
					else:
						self.headerDict[assignment[1]] = \
							self.unpack_int(assignment[2], 
											byteorder='big', 
											signed=False)
				elif assignment[0] == LITTLE_UINT:
					if callable(assignment[2]):
						self.headerDict[assignment[1]] = \
							self.unpack_int(assignment[2](), 
											signed=False)
					else:
						self.headerDict[assignment[1]] = \
							self.unpack_int(assignment[2], 
											signed=False)
				elif assignment[0] == BIG_INT:
					if callable(assignment[2]):
						self.headerDict[assignment[1]] = \
							self.unpack_int(assignment[2](), 
											byteorder='big', 
											signed=True)
					else:
						self.headerDict[assignment[1]] = \
							self.unpack_int(assignment[2], 
											byteorder='big', 
											signed=True)
				elif assignment[0] == LITTLE_INT:
					if callable(assignment[2]):
						self.headerDict[assignment[1]] = \
							self.unpack_int(assignment[2](),
											 signed=True)
					else:
						self.headerDict[assignment[1]] = \
							self.unpack_int(assignment[2], 
											signed=True)
				elif assignment[0] == DIRECT:
					if callable(assignment[2]):
						self.headerDict[assignment[1]] = assignment[2]()
					else:
						self.headerDict[assignment[1]] = assignment[2]
				# If there is an unrecognized assignment string:
				else:
					raise AssignmentIdError('unrecognized assignment string')
		self.headerLen += readLen


class WriteAudio:
	"""
	This base class for writing audio provides a template and helper
	functions for inheriting classes.  Each file type that is supported
	consists of a read class and a write class, which iherit from 
	ReadAudio and WriteAudio respectively.  Two methods of WriteAudio
	need to be overridden for in the inheriting class:
	
	1) write_header(self, readStream)
	2) repack(self)
	
	These methods are used by a Engine object in its process() method.
	"""
	def __init__(self, targetFile, format=None, numChannels=None, 
					bitDepth=None, sampleRate=None):
		"""
		Constructor initializes:
		
		1) self.headerDict ==> A transferred copy of the headerDict{} of
							the ReadAudio object.
		2) self.byteArray  ==> Used to store the binary read during the
							read_header() call.
		3) self.conversion ==> A boolean used to indicate whether the output
							file has a different format than the input file.
		4) self.conversionParameters
						   ==> The ways in which the output file differs in
						   	format from the input file.
		
		Constructor accepts:
		
		1) targetFile  ==> The path of the file to be written.
		
		2) format 	   ==> The audio format of the ouput file, if different
						   from that of the input file.
		3) numChannels ==> The number of channels of the ouput file, if
						   different from that of the input file.
		4) bitDepth    ==> The bit depth of the ouput file, if different
						   from that of the input file.
		5) sampleRate  ==> The sample rate of the ouput file, if different
						   from that of the input file.
		"""
		# Handle Conversion Parameters
		self.conversionParameters = {}
		self.conversion = False
		if format:
			self.conversionParameters[CORE_KEY_FMT] = format
		if numChannels:
			self.conversionParameters[CORE_KEY_NUM_CHANNELS] = int(numChannels)
		if bitDepth:
			self.conversionParameters[CORE_KEY_BIT_DEPTH] = int(bitDepth)
			self.conversionParameters[CORE_KEY_BYTE_DEPTH] = \
				int(self.conversionParameters[CORE_KEY_BIT_DEPTH] / 
					BYTE_SIZE)
		if sampleRate:
			self.conversionParameters[CORE_KEY_SAMPLE_RATE] = int(sampleRate)
		if self.conversionParameters:
			self.conversion = True
		# Init other vars
		self.headerDict = {}
		self.byteArray = bytearray()
		self.targetFile = targetFile

	# ------------------------------------------------------------------------
	# --------------------------- ABSTRACT OPERATIONS ------------------------
	# ------------------------------------------------------------------------
	def init_header(self, audioInput, reachBack):
		"""
		If no file conversion, simply copy header from audioInput.  Else, 
		populate based on conversion parameters, as well as audioInput and 
		engineObj.  Must be overridden by inheriting file-type  write
		class.
		
		Accepts:
		
		1) audioInput    ==>  A pointer to the open read file.
		
		2) reachBack  ==>  The number of samples that the plugin 
						   algorithm will add to the file.
		"""
		return
	
	def write_header(self, writeStream):
		"""
		Used to write the header of the output file based on values in
		headerDict{}.  Must be overridden by inheriting file-type write
		class.
		
		Accepts:
		
		1) writeStream  ==>  A pointer to the open write file.
		"""
		writeStream.write(bytearray())
	
	def repack(self, processedSampleNestedList):
		"""
		Called in Engine().process() to unpack the buffer binary in a way 
		that is relevant to the file type.  Must be overridden by
		inheriting file-type write class.
		
		Accepts:
		
		1) processedSampleNestedList  ==> A nested list of processed sample
										  data.
		
		Returns a bytearray of the processed audio data.
		"""
		return bytearray()
	
	# ------------------------------------------------------------------------
	# ------------------------- END:  ABSTRACT OPERATIONS --------------------
	# ------------------------------------------------------------------------
	
	def pack_and_write(self, writeStream, packNestedTuple):
		"""
		Packs/decodes input data into binary and then writes it to file.
		
		Accepts:
		
		1) writeStream  ==> The open write file.
		2) packNestedTuple
			==> a nested tuple, where each inner tuple contains 3 values,
			    unless packIdStr == DIRECT or BIG_UTF or
			    LITTLE_UTF, in which case it contains 2 values:
			
			  1) packIdStr - (BIG_UTF -> 
			  					packs big-endian UTF-8 str to bin)
			  			   - (LITTLE_UTF -> 
			  			   		packs little-endian UTF-8 str to bin)
					   	   - (BIG_UINT -> 
					   	   		packs big-endian unisgned int to bin)
					   	   - (LITTLE_UINT -> 
					   	   		packs little-endian unisgned int to bin)
					   	   - (BIG_INT -> 
					   	   		packs big-endian signed int to bin)
					   	   - (LITTLE_INT -> 
					   	   		packs little-endian signed int to bin)
					   	   - (DIRECT -> 
					   	   		writes bin stored in headerDict as is)
			  2) headerKey  
			  		If packIdStr == DIRECT:
			  				-  The binary string that is to be written
			  				   directly to file.
			  		elif packIdStr == BIG_UTF:
			  				-  The UTF string to be written to file in
			  					big-endian byte order.
			  		elif packIdStr == LITTLE_UTF:
			  				-  The UTF string to be written to file in
			  					little-endian byte order.
			  		else:
			  				-  The key in self.headerDict{} which contains
			  				   the value that will be packed.
			  3) numBytes   - The size of the binary string into which the
			  				  value is to be packed (in bytes).
			  	 
			  	 Whether the inner tuple contains 2 or 3 values, the final
			  	 value can be a lambda expression.
		
		Example of packNestedTuple:
		
			(
				(BIG_UTF, 'RIFF',
				(self.packUNIT, self.keyChunkSize, INT16_SIZE),
				(DIRECT, b'foo')
			)
		"""
		# Init an empty bytearray object
		self.byteArray = bytearray()
		# For each tuple 'directive', pack the input into binary
		# and assign to the bytearray
		for directive in packNestedTuple:
			if directive[0] == BIG_UTF:
				self.byteArray += \
					self.headerDict[directive[1]].encode('utf-8')
			elif directive[0] == LITTLE_UTF:
				self.byteArray += \
					self.headerDict[directive[1]][::-1].encode('utf-8')
			elif directive[0] == BIG_UINT:
				if callable(directive[2]):
					self.byteArray += \
						self.headerDict[directive[1]].\
							to_bytes(directive[2](), 
										byteorder='big', 
										signed=False)
				else:
					self.byteArray += \
						self.headerDict[directive[1]].\
							to_bytes(directive[2], 
										byteorder='big', 
										signed=False)
			elif directive[0] == LITTLE_UINT:
				if callable(directive[2]):
					self.byteArray += \
						self.headerDict[directive[1]].\
							to_bytes(directive[2](), 
										byteorder='little', 
										signed=False)
				else:
					self.byteArray += \
						self.headerDict[directive[1]].\
							to_bytes(directive[2], 
										byteorder='little', 
										signed=False)
			elif directive[0] == BIG_INT:
				if callable(directive[2]):
					self.byteArray += \
						self.headerDict[directive[1]].\
							to_bytes(directive[2](), 
										byteorder='big', 
										signed=True)
				else:
					self.byteArray += \
						self.headerDict[directive[1]].\
							to_bytes(directive[2], 
										byteorder='big', 
										signed=True)
			elif directive[0] == LITTLE_INT:
				if callable(directive[2]):
					self.byteArray += \
						self.headerDict[directive[1]].\
							to_bytes(directive[2](), 
										byteorder='little', 
										signed=True)
				else:
					self.byteArray += \
						self.headerDict[directive[1]].\
							to_bytes(directive[2], 
										byteorder='little', 
										signed=True)
			elif directive[0] == DIRECT:
				if callable(directive[1]):
					self.byteArray += directive[1]()
				else:
					self.byteArray += self.headerDict[directive[1]]
			else:
				raise PackIdError('unrecognized pack type string')
		# Write binary in bytearray to file
		writeStream.write(self.byteArray)

