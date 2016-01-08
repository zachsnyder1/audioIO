"""
Contains audioIO base classes, including exception classes.
"""

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


# Base classes:
class AudioIOBase:
	"""
	Base class for audio IO.  Consists of constants that are
	used in all inheriting 'read' and 'write' classes.
	"""
	# CONSTANTS:
	
	# Strings:
	# Endianness
	littleEndian = 'little'
	bigEndian = 'big'
	# Encoding
	utf8 = 'utf-8'
	# Format
	formatStringFloat = 'float'
	formatStringPCM = 'PCM'
	# Core headerDict keys
	keyAudioFmtStr = 'audioFormatStr'
	keySigned = 'signed'
	keyNumChannels = 'numChannels'
	keyBitDepth = 'bitDepth'
	keyByteDepth = 'byteDepth'
	keySampleRate = 'sampleRate'
	keySamplesPerChannel = 'samplesPerChannel'
	# Assignment and pack strings 
	# for self.read_and_assign(), self.pack_and_write()
	assignLittleUTF = 'little_utf'
	assignBigUTF = 'big_utf'
	assignLittleINT = 'little_int'
	assignBigINT = 'big_int'
	assignLittleUINT = 'little_uint'
	assignBigUINT = 'big_uint'
	assignDIRECT = 'direct'
	packLittleUTF = 'little_utf'
	packBigUTF = 'big_utf'
	packLittleINT = 'little_int'
	packBigINT = 'big_int'
	packLittleUINT = 'little_uint'
	packBigUINT = 'big_uint'
	packDIRECT = 'direct'
	# Sizes
	reset = 0       # To reset count variables / seek to beginning of file
	samplesPerBuffer = 1024   # Number of samples per buffer
	chunkIdSize = 4   # Number of bytes in chunkID
	byteSize = 8    # Number of bits per byte
	int32Size = 4   # Number of bytes in a 32-bit integer
	int24Size = 3   # Number of bytes in a 24-bit integer
	int16Size = 2   # Number of bytes in a 16-bit integer
	int8Size = 1    # Number of bytes in a 8-bit integer
	floatSize = 4   # Number of bytes in a single precision float
	doubleSize = 8  # Number of bytes in a double precision float



class ReadAudio(AudioIOBase):
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
	# ----------------------------- TO BE OVERRIDEN --------------------------
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
	# -------------------------- END:  TO BE OVERRIDDEN ----------------------
	# ------------------------------------------------------------------------
	
	def unpack_int(self, numBytes, byteorder='little', signed=False):
		"""
		Unpacks a slice of the binary stored in self.byteArray and returns the
		integer value of that slice.  Defined to maximize code reuse.
		
		Accepts:
		
		1) numBytes   ==> The size of the binary slice in bytes.
		2) byteorder ==> The byteorder of the binary. Either self.littleEndian
						  or self.bigEndian; default=self.littleEndian.
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
		if byteorder == self.bigEndian:
			binary = self.byteArray[self.readOffset:
									(self.readOffset + numBytes)]
			self.readOffset += numBytes
			return binary.decode(self.utf8)
		elif byteorder == self.littleEndian:
			binary = bytearray()
			for i in range(numBytes):
				binary += self.byteArray[(self.readOffset + numBytes) - (1+i):
											(self.readOffset + numBytes) - i]
			self.readOffset += numBytes
			return binary.decode(self.utf8)
	
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
			
			  1) assignmentIdStr - (self.assignBigUTF -> unpacks bin to
			  						big-endian UTF-8 str)
			  					 - (self.assignLittleUTF -> unpacks bin to
			  					 	little-endian UTF-8 str)
					   			 - (self.assignBigUINT -> unpacks bin to
					   			 	big-endian unisgned int)
					   			 - (self.assignLittleUINT -> unpacks bin to
					   			 	little-endian unisgned int)
					   			 - (self.assignBigINT -> unpacks bin to
					   			 	big-endian signed int)
					   			 - (self.assignLittleINT -> unpacks bin to
					   			 	little-endian signed int)
					   			 - (self.assignDIRECT -> assigns val 2 
					   			 	directly as val 3)
			  2) headerKey  -  The key in self.headerDict{} to which the value
			  				   will be assigned.
			  3) If assignmentIdStr == self.assignDIRECT:
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
				(self.assignBigUTF, self.keyChunkId, self.int32Size),
				(self.assignLittleUNIT, self.keyChunkSize, self.int16Size),
				(self.assignDIRECT, 'foo', 'bar')
			)
		"""
		# Read from file
		self.byteArray = readStream.read(readLen)
		self.readOffset = self.reset
		# Assert that the read worked
		if not self.byteArray:
			raise ReadFileEmpty
		else:
			# For each separate assignment tuple, take action based on 
			# assignment string, and on whether or not the third value
			# is a lambda expression:
			for assignment in assignmentNestedTuple:
				if assignment[0] == self.assignBigUTF:
					if callable(assignment[2]):
						self.headerDict[assignment[1]] = \
							self.unpack_utf(assignment[2]())
					else:
						self.headerDict[assignment[1]] = \
							self.unpack_utf(assignment[2])
				elif assignment[0] == self.assignLittleUTF:
					if callable(assignment[2]):
						self.headerDict[assignment[1]] = \
							self.unpack_utf(assignment[2](), 
											byteorder=self.littleEndian)
					else:
						self.headerDict[assignment[1]] = \
							self.unpack_utf(assignment[2], 
											byteorder=self.littleEndian)
				elif assignment[0] == self.assignBigUINT:
					if callable(assignment[2]):
						self.headerDict[assignment[1]] = \
							self.unpack_int(assignment[2](), 
											byteorder=self.bigEndian, 
											signed=False)
					else:
						self.headerDict[assignment[1]] = \
							self.unpack_int(assignment[2], 
											byteorder=self.bigEndian, 
											signed=False)
				elif assignment[0] == self.assignLittleUINT:
					if callable(assignment[2]):
						self.headerDict[assignment[1]] = \
							self.unpack_int(assignment[2](), 
											signed=False)
					else:
						self.headerDict[assignment[1]] = \
							self.unpack_int(assignment[2], 
											signed=False)
				elif assignment[0] == self.assignBigINT:
					if callable(assignment[2]):
						self.headerDict[assignment[1]] = \
							self.unpack_int(assignment[2](), 
											byteorder=self.bigEndian, 
											signed=True)
					else:
						self.headerDict[assignment[1]] = \
							self.unpack_int(assignment[2], 
											byteorder=self.bigEndian, 
											signed=True)
				elif assignment[0] == self.assignLittleINT:
					if callable(assignment[2]):
						self.headerDict[assignment[1]] = \
							self.unpack_int(assignment[2](),
											 signed=True)
					else:
						self.headerDict[assignment[1]] = \
							self.unpack_int(assignment[2], 
											signed=True)
				elif assignment[0] == self.assignDIRECT:
					if callable(assignment[2]):
						self.headerDict[assignment[1]] = assignment[2]()
					else:
						self.headerDict[assignment[1]] = assignment[2]
				# If there is an unrecognized assignment string:
				else:
					raise AssignmentIdError('unrecognized assignment string')
		self.headerLen += readLen


class WriteAudio(AudioIOBase):
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
			self.conversionParameters[self.keyAudioFmtStr] = format
		if numChannels:
			self.conversionParameters[self.keyNumChannels] = int(numChannels)
		if bitDepth:
			self.conversionParameters[self.keyBitDepth] = int(bitDepth)
			self.conversionParameters[self.keyByteDepth] = \
				int(self.conversionParameters[self.keyBitDepth] / 
					self.byteSize)
		if sampleRate:
			self.conversionParameters[self.keySampleRate] = int(sampleRate)
		if self.conversionParameters:
			self.conversion = True
		# Init other vars
		self.headerDict = {}
		self.byteArray = bytearray()
		self.targetFile = targetFile

	# ------------------------------------------------------------------------
	# ----------------------------- TO BE OVERRIDEN --------------------------
	# ------------------------------------------------------------------------
	def init_header(self, readObj, reachBack):
		"""
		If no file conversion, simply copy header from readObj.  Else, 
		populate based on conversion parameters, as well as readObj and 
		engineObj.  Must be overridden by inheriting file-type  write
		class.
		
		Accepts:
		
		1) readObj    ==>  A pointer to the open read file.
		
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
	# -------------------------- END:  TO BE OVERRIDDEN ----------------------
	# ------------------------------------------------------------------------
	
	def pack_and_write(self, writeStream, packNestedTuple):
		"""
		Packs/decodes input data into binary and then writes it to file.
		
		Accepts:
		
		1) writeStream  ==> The open write file.
		2) packNestedTuple
			==> a nested tuple, where each inner tuple contains 3 values,
			    unless packIdStr == self.packDIRECT or self.packBigUTF or
			    self.packLittleUTF, in which case it contains 2 values:
			
			  1) packIdStr - (self.packBigUTF -> 
			  					packs big-endian UTF-8 str to bin)
			  			   - (self.packLittleUTF -> 
			  			   		packs little-endian UTF-8 str to bin)
					   	   - (self.packBigUINT -> 
					   	   		packs big-endian unisgned int to bin)
					   	   - (self.packLittleUINT -> 
					   	   		packs little-endian unisgned int to bin)
					   	   - (self.packBigINT -> 
					   	   		packs big-endian signed int to bin)
					   	   - (self.packLittleINT -> 
					   	   		packs little-endian signed int to bin)
					   	   - (self.packDIRECT -> 
					   	   		writes bin stored in headerDict as is)
			  2) headerKey  
			  		If packIdStr == self.packDIRECT:
			  				-  The binary string that is to be written
			  				   directly to file.
			  		elif packIdStr == self.packBigUTF:
			  				-  The UTF string to be written to file in
			  					big-endian byte order.
			  		elif packIdStr == self.packLittleUTF:
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
				(self.packBigUTF, 'RIFF',
				(self.packUNIT, self.keyChunkSize, self.int16Size),
				(self.packDIRECT, b'foo')
			)
		"""
		# Init an empty bytearray object
		self.byteArray = bytearray()
		# For each tuple 'directive', pack the input into binary
		# and assign to the bytearray
		for directive in packNestedTuple:
			if directive[0] == self.packBigUTF:
				self.byteArray += \
					self.headerDict[directive[1]].encode(self.utf8)
			elif directive[0] == self.packLittleUTF:
				self.byteArray += \
					self.headerDict[directive[1]][::-1].encode(self.utf8)
			elif directive[0] == self.packBigUINT:
				if callable(directive[2]):
					self.byteArray += \
						self.headerDict[directive[1]].\
							to_bytes(directive[2](), 
										byteorder=self.bigEndian, 
										signed=False)
				else:
					self.byteArray += \
						self.headerDict[directive[1]].\
							to_bytes(directive[2], 
										byteorder=self.bigEndian, 
										signed=False)
			elif directive[0] == self.packLittleUINT:
				if callable(directive[2]):
					self.byteArray += \
						self.headerDict[directive[1]].\
							to_bytes(directive[2](), 
										byteorder=self.littleEndian, 
										signed=False)
				else:
					self.byteArray += \
						self.headerDict[directive[1]].\
							to_bytes(directive[2], 
										byteorder=self.littleEndian, 
										signed=False)
			elif directive[0] == self.packBigINT:
				if callable(directive[2]):
					self.byteArray += \
						self.headerDict[directive[1]].\
							to_bytes(directive[2](), 
										byteorder=self.bigEndian, 
										signed=True)
				else:
					self.byteArray += \
						self.headerDict[directive[1]].\
							to_bytes(directive[2], 
										byteorder=self.bigEndian, 
										signed=True)
			elif directive[0] == self.packLittleINT:
				if callable(directive[2]):
					self.byteArray += \
						self.headerDict[directive[1]].\
							to_bytes(directive[2](), 
										byteorder=self.littleEndian, 
										signed=True)
				else:
					self.byteArray += \
						self.headerDict[directive[1]].\
							to_bytes(directive[2], 
										byteorder=self.littleEndian, 
										signed=True)
			elif directive[0] == self.packDIRECT:
				if callable(directive[1]):
					self.byteArray += directive[1]()
				else:
					self.byteArray += self.headerDict[directive[1]]
			else:
				raise PackIdError('unrecognized pack type string')
		# Write binary in bytearray to file
		writeStream.write(self.byteArray)

