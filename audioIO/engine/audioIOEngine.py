import struct
from sys import argv
from datetime import datetime


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

class AssignmentError(Exception):
	"""
	Raised when the ReadAudio.read_and_assign() method or the
	WriteAudio.pack_and_write() method recieve an unexpected
	assignment or packing ID string, respectively.
	"""
	pass



class AudioIOBase:
	"""
	Base class for audio IO.  Consists of constants that are
	used in all inheriting 'read' and 'write' classes.
	"""
	# CONSTANTS:
	# Assignment and pack strings (for self.read_and_assign(), self.pack_and_write())
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
	reset = 0       # Used to reset count variables and seek to beginning of file
	samplesPerBuffer = 1024   # Number of samples per buffer
	chunkIdSize = 4   # Number of bytes in chunkID
	byteSize = 8   # Number of bits per byte
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
	
	These methods are used by an AudioIOEngine object in its process()
	method.
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

	# --------------------------------------------------------------------------
	# ----------------------------- TO BE OVERRIDEN ----------------------------
	# --------------------------------------------------------------------------
	def read_header(self, readStream):
		"""
		Called in AudioIOEngine().process() to populate the headerDict{} with values read
		from the header of the read file.  Must be overridden by the inheriting
		class.
		
		Accepts one parameter:
		
		1) readStream  ==> The open read file.
		"""
		return
	
	def unpack(self, byteArray):
		"""
		Called in self.process() to unpack the buffer binary in a way that
		is relevant to the file type.  Must be overridden by inheriting 
		file type class.
		
		Accepts:
		
		1) byteArray  ==> The buffer binary as a byte array. 
		
		Returns a nested list of sample data with the format:
		
		  [block1=[chan1, chan2, etc.], block2=[chan1, chan2, etc.], etc.]
		"""
		return [[]]
	
	# --------------------------------------------------------------------------
	# -------------------------- END:  TO BE OVERRIDDEN ------------------------
	# --------------------------------------------------------------------------
	
	def unpack_int_and_advance(self, numBytes, byteorder='little', signed=False):
		"""
		Unpacks a slice of the binary stored in self.byteArray and returns the
		integer value of that slice.  Defined to maximize code reuse.
		
		Accepts:
		
		1) numBytes   ==> The size of the binary slice in bytes.
		2) byteorder ==> The byteorder of the binary. Either 'little' or
						  'big'; default='little'.
		3) signed     ==> Bool indicates whether or not the integer is signed.
						  Default=False.
		
		Returns the unpacked integer.
		"""
		binary = self.byteArray[self.readOffset:(self.readOffset + numBytes)]
		self.readOffset += numBytes
		return int.from_bytes(binary, byteorder=byteorder, signed=signed)
	
	def unpack_utf_and_advance(self, numBytes, byteorder='big'):
		"""
		Unpacks a slice of the binary stored in self.byteArray and returns
		the decoded string based on UTF-8 encoding.
		
		Accepts:
		
		1) numBytes  ==> The size of the binary slice in bytes.
		
		Returns the decoded UTF-8 string.
		"""
		if byteorder == 'big':
			binary = self.byteArray[self.readOffset:(self.readOffset + numBytes)]
			self.readOffset += numBytes
			return binary.decode("utf-8")
		elif byteorder == 'little':
			binary = bytearray()
			for i in range(numBytes):
				binary += self.byteArray[(self.readOffset + numBytes) - (1+i):(self.readOffset + numBytes) - i]
			self.readOffset += numBytes
			return binary.decode("utf-8")
	
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
			
			  1) assignmentIdStr - (self.assignBigUTF -> unpacks bin to big-endian
			  						UTF-8 str)
			  					 - (self.assignLittleUTF -> unpacks bin to little-endian
			  					 	UTF-8 str)
					   			 - (self.assignBigUINT -> unpacks bin to big-endian
					   			 	unisgned int)
					   			 - (self.assignLittleUINT -> unpacks bin to little-endian
					   			 	unisgned int)
					   			 - (self.assignBigINT -> unpacks bin to big-endian
					   			 	signed int)
					   			 - (self.assignLittleINT -> unpacks bin to little-endian
					   			 	signed int)
					   			 - (self.assignDIRECT -> assigns val 2 directly as val 3)
			  2) headerKey  -  The key in self.headerDict{} to which the value will
			  				   be assigned.
			  3) If assignmentIdStr == self.assignDIRECT:
			  			- The value that will be assigned to headerKey in the headerDict.
			  	 else:
			  	 		- The size of the binary slice that will be interpreted as
			  	 		  either the int or UTF-8 string assigned to headerKey.
			  	 
			  	 Either way, the third value can be a lambda expression, which
			  	 can be used if you are trying to reference a headerDict{} key
			  	 before it is assigned a vlaue.
		
		Example of assignmentNestedTuple:
		
			(
				(self.assignBigUTF, 'chunkID', self.int32Size),
				(self.assignLittleUNIT, 'chunkSize', self.int16Size),
				(self.assignDIRECT, 'foo', 'bar')
			)
		"""
		self.byteArray = readStream.read(readLen)
		self.readOffset = self.reset
		if not self.byteArray:
			raise ReadFileEmpty
		else:
			for assignment in assignmentNestedTuple:
				if assignment[0] == self.assignBigUTF:
					if callable(assignment[2]):
						self.headerDict[assignment[1]] = self.unpack_utf_and_advance(assignment[2]())
					else:
						self.headerDict[assignment[1]] = self.unpack_utf_and_advance(assignment[2])
				elif assignment[0] == self.assignLittleUTF:
					if callable(assignment[2]):
						self.headerDict[assignment[1]] = self.unpack_utf_and_advance(assignment[2](), byteorder='little')
					else:
						self.headerDict[assignment[1]] = self.unpack_utf_and_advance(assignment[2], byteorder='little')
				elif assignment[0] == self.assignBigUINT:
					if callable(assignment[2]):
						self.headerDict[assignment[1]] = self.unpack_int_and_advance(assignment[2](), byteorder='big', signed=False)
					else:
						self.headerDict[assignment[1]] = self.unpack_int_and_advance(assignment[2], byteorder='big', signed=False)
				elif assignment[0] == self.assignLittleUINT:
					if callable(assignment[2]):
						self.headerDict[assignment[1]] = self.unpack_int_and_advance(assignment[2](), signed=False)
					else:
						self.headerDict[assignment[1]] = self.unpack_int_and_advance(assignment[2], signed=False)
				elif assignment[0] == self.assignBigINT:
					if callable(assignment[2]):
						self.headerDict[assignment[1]] = self.unpack_int_and_advance(assignment[2](), byteorder='big', signed=True)
					else:
						self.headerDict[assignment[1]] = self.unpack_int_and_advance(assignment[2], byteorder='big', signed=True)
				elif assignment[0] == self.assignLittleINT:
					if callable(assignment[2]):
						self.headerDict[assignment[1]] = self.unpack_int_and_advance(assignment[2](), signed=True)
					else:
						self.headerDict[assignment[1]] = self.unpack_int_and_advance(assignment[2], signed=True)
				elif assignment[0] == self.assignDIRECT:
					if callable(assignment[2]):
						self.headerDict[assignment[1]] = assignment[2]()
					else:
						self.headerDict[assignment[1]] = assignment[2]
				else:
					raise AssignmentError('unrecognized assignment string')
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
	
	These methods are used by an AudioIOEngine object in its process()
	method.
	"""
	def __init__(self, targetFile):
		"""
		self.headerDict ==> A transferred copy of the headerDict{} of
							the ReadAudio object.
		self.byteArray  ==> Used to store the binary read during the
							read_header() call.
		self.targetFile ==> The only parameter taken by the constructor,
							targetFile is the path of the file to be written.
		"""
		self.headerDict = {}
		self.byteArray = bytearray()
		self.targetFile = targetFile

	# --------------------------------------------------------------------------
	# ----------------------------- TO BE OVERRIDEN ----------------------------
	# --------------------------------------------------------------------------
	def write_header(self, writeStream):
		"""
		Used to write the header of the output file based on values in
		headerDict{}.  Must be overridden by inheriting file type class.
		
		Accepts:
		
		1) writeStream  ==> A pointer to the open output file.
		"""
		writeStream.write(bytearray())
	
	def repack(self, processedSampleNestedList):
		"""
		Called in self.process() to unpack the buffer binary in a way that
		is relevant to the file type.  Must be overridden by inheriting 
		file type class.
		
		Accepts:
		
		1) processedSampleNestedList  ==> A nested list of processed sample
										  data.
		
		Returns a bytearray of the processed audio data.
		"""
		return bytearray()
	
	# --------------------------------------------------------------------------
	# -------------------------- END:  TO BE OVERRIDDEN ------------------------
	# --------------------------------------------------------------------------
	
	def pack_and_write(self, writeStream, packNestedTuple):
		"""
		Packs/decodes input data into binary and then writes it to file.
		
		Accepts:
		
		1) writeStream  ==> The open write file.
		2) packNestedTuple
			==> a nested tuple, where each inner tuple contains 3 values,
			    unless packIdStr == self.packDIRECT or self.packBigUTF or
			    self.packLittleUTF, in which case it contains 2 values:
			
			  1) packIdStr - (self.packBigUTF -> packs big-endian UTF-8 str to bin)
			  			   - (self.packLittleUTF -> packs little-endian UTF-8 str to bin)
					   	   - (self.packBigUINT -> packs big-endian unisgned int to bin)
					   	   - (self.packLittleUINT -> packs little-endian unisgned int to bin)
					   	   - (self.packBigINT -> packs big-endian signed int to bin)
					   	   - (self.packLittleINT -> packs little-endian signed int to bin)
					   	   - (self.packDIRECT -> writes bin stored in headerDict as is)
			  2) headerKey  
			  		If packIdStr == self.packDIRECT:
			  				-  The binary string that is to be written directly to file.
			  		else:
			  				-  The key in self.headerDict{} which contains the value
			  				   that will be packed.
			  3) numBytes   - The size of the binary string into which the value is to be
			  	 		 	  packed (in bytes).
			  	 
			  	 Whether the inner tuple contains 2 or 3 values, the final value can be a
			  	 lambda expression.
		
		Example of packNestedTuple:
		
			(
				(self.packBigUTF, 'chunkID',
				(self.packUNIT, 'chunkSize', self.int16Size),
				(self.packDIRECT, b'foo')
			)
		"""
		self.byteArray = bytearray()
		for directive in packNestedTuple:
			if directive[0] == self.packBigUTF:
				self.byteArray += self.headerDict[directive[1]].encode("utf-8")
			elif directive[0] == self.packLittleUTF:
				self.byteArray += self.headerDict[directive[1]][::-1].encode("utf-8")
			elif directive[0] == self.packBigUINT:
				if callable(directive[2]):
					self.byteArray += self.headerDict[directive[1]].to_bytes(directive[2](), byteorder='big', signed=False)
				else:
					self.byteArray += self.headerDict[directive[1]].to_bytes(directive[2], byteorder='big', signed=False)
			elif directive[0] == self.packLittleUINT:
				if callable(directive[2]):
					self.byteArray += self.headerDict[directive[1]].to_bytes(directive[2](), byteorder='little', signed=False)
				else:
					self.byteArray += self.headerDict[directive[1]].to_bytes(directive[2], byteorder='little', signed=False)
			elif directive[0] == self.packBigINT:
				if callable(directive[2]):
					self.byteArray += self.headerDict[directive[1]].to_bytes(directive[2](), byteorder='big', signed=True)
				else:
					self.byteArray += self.headerDict[directive[1]].to_bytes(directive[2], byteorder='big', signed=True)
			elif directive[0] == self.packLittleINT:
				if callable(directive[2]):
					self.byteArray += self.headerDict[directive[1]].to_bytes(directive[2](), byteorder='little', signed=True)
				else:
					self.byteArray += self.headerDict[directive[1]].to_bytes(directive[2], byteorder='little', signed=True)
			elif directive[0] == self.packDIRECT:
				if callable(directive[1]):
					self.byteArray += directive[1]()
				else:
					self.byteArray += self.headerDict[directive[1]]
			else:
				raise AssignmentError('unrecognized pack type string')
		# Write to file
		writeStream.write(self.byteArray)



class AudioIOEngine:
	"""
	Connects the read and write classes to the plugin algorithm, and executes
	the processing of the audio data.
	"""
	def __init__(self, audioReadObj, audioWriteObj, pluginFunction):
		"""
		self.audioReadObj  ==> An initialized object that inherits from
							   ReadAudio base class.
		self.audioWriteObj ==> An initialized object that inherits from
							   WriteAudio base class.
		self.callback      ==> The audio plugin algorithm.
		"""
		self.audioReadObj = audioReadObj
		self.audioWriteObj = audioWriteObj
		self.callback = pluginFunction
	
	def process(self):
		"""
		Reads input file, exposes it to the plugin algorithm as a nested array
		of sample values, then writes the processed audio to the output
		file.
		"""
		with open(self.audioReadObj.targetFile, 'rb') as readStream:
			with open(self.audioWriteObj.targetFile, 'wb') as writeStream:
				# Read header of input, write header of output
				self.audioReadObj.read_header(readStream)
				self.audioWriteObj.headerDict = self.audioReadObj.headerDict
				self.audioWriteObj.write_header(writeStream)
				# Set read stream to beginning of data
				readStream.seek(AudioIOBase.reset)
				self.byteArray = readStream.read(self.audioReadObj.headerLen)
					
				# Expose a nested list of samples to the callback function
				# and write the processed data:
				bufferSize = AudioIOBase.samplesPerBuffer * self.audioReadObj.headerDict['blockAlign']
				while True:
					byteArray = readStream.read(bufferSize)   # Data read from file
					if byteArray:
						# Unpack binary
						sampleNestedList = self.audioReadObj.unpack(byteArray)
						# EXECUTE CALLBACK
						processedSampleNestedList = self.callback(self, sampleNestedList)
						# Pack processed data
						processedByteArray = self.audioWriteObj.repack(processedSampleNestedList)
						# Write processed buffer to file
						writeStream.write(processedByteArray)
					else:
						break