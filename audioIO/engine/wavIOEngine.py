import os
import sys
import struct
from . import audioIOEngine as aIOe


class WavBase:
	"""
	WAV base class.  Holds important constants that are inherited into
	ReadWav and WriteWav classes.
	"""
	# CONSTANTS:
	
	# Sizes
	wavHeaderSearchLen = 100  # Number of bytes used to search for header chunk IDs
	wavChunkHeadSize = 12   # Number of bytes in WAV file format header
	subChunkHeadSize = 8  # Number of bytes in a subchunk header
	fmtChunkSize16 = 16  # Number of bytes in PCM fmt subchunk
	fmtChunkSize18 = 18  # Number of bytes in non-PCM && non-extensible format fmt subchunk
	fmtChunkSize40 = 40  # Number of bytes in extensible format fmt subchunk
	subformatSize = 16   # Number of bytes in the SubFormat parameter of extensible format files
	fmtExtensionSize0 = 0  # Number of bytes in extension if non-extensible
	fmtExtensionSize22 = 22 # Number of bytes in extension if extensible
	# SubchunkID Strings
	riffChunkId = 'RIFF'   # Chunk ID
	waveId = 'WAVE'        # Wave ID
	fmtSubchunkId = 'fmt ' # Fmt subchunk ID
	factSubchunkId = 'fact' # Fact subchunk ID
	dataSubchunkId = 'data' # Data subchuhnk ID
	# For bin search
	riffIdHex = b'\x52\x49\x46\x46'  # Used in bin search
	waveIdHex = b'\x57\x41\x56\x45'  # Used in bin search
	fmtIdHex = b'\x66\x6d\x74\x20'   # Used in bin search
	factIdHex = b'\x66\x61\x63\x74'  # Used in bin search
	dataIdHex = b'\x64\x61\x74\x61'  # Used in bin search
	binSearchFail = -1               # Used for bin search
	# Format codes for .WAV
	waveFormatPCM = 1   # Standard, PCM data
	waveFormatFloat = 3 # Floating point data
	waveFormatALaw = 6  # A-law 8-bit data
	waveFormatMULaw = 7 # Mu-law 8-bit data
	waveFormatExtensible = b'\xff\xee' # Extensible format


class ReadWav(aIOe.ReadAudio, WavBase):
	"""
	WAV file reader inherits from both ReadAudio and WavBase.
	It overrides the ReadAudio.read_header() and ReadAudio.unpack()
	methods that are called in the AudioIOEngine.process() method.
	"""
	# --------------------------------------------------------------------------
	# -------------------------------- OVERRIDES -------------------------------
	# --------------------------------------------------------------------------
	def read_header(self, readStream):
		"""
		Override of ReadAudio.read_header().  Any further initialization is
		tacked onto the end.
		
		Accepts:
		
		1) readStream  ==> The open read file.
		"""
		# BIN SEARCH FOR CHUNK IDs
		self.read_and_assign(readStream, self.wavHeaderSearchLen, (
			(self.assignDIRECT, 'riffIdIndex', 
				lambda: self.byteArray.find(self.riffIdHex)
			),
			(self.assignDIRECT, 'waveIdIndex', 
				lambda: self.byteArray.find(self.waveIdHex)
			),
			(self.assignDIRECT, 'fmtIdIndex', 
				lambda: self.byteArray.find(self.fmtIdHex)
			),
			(self.assignDIRECT, 'factIdIndex', 
				lambda: self.byteArray.find(self.factIdHex)
			),
			(self.assignDIRECT, 'dataIdIndex', 
				lambda: self.byteArray.find(self.dataIdHex)
			)
		))
		# Verify file format
		if (self.headerDict['riffIdIndex'] or 
			self.headerDict['waveIdIndex'] or
			self.headerDict['fmtIdIndex'] or
			self.headerDict['dataIdIndex']
		) == self.binSearchFail:
			raise aIOe.IncompatibleAudioFormat('file is not RIFF WAVE type')
		else:
			pass
		# RESET CURRENT POSITION
		readStream.seek(self.reset)
		self.readOffset = self.reset
		self.headerLen = self.reset
		
		# BEGIN INIT:
		# READ AND STORE CHUNK HEADER + fmt SUBCHUNK HEADER AND BODY
		if self.headerDict['factIdIndex'] == self.binSearchFail:
			readLen1 = self.headerDict['dataIdIndex']
		else:
			readLen1 = self.headerDict['factIdIndex']
		self.read_and_assign(readStream, readLen1, (
			(self.assignBigUTF, 'chunkID', self.int32Size),
			(self.assignLittleUINT, 'chunkSize', self.int32Size),
			(self.assignBigUTF, 'format', self.int32Size),
			(self.assignBigUTF, 'subchunk1ID', self.int32Size),
			(self.assignLittleUINT, 'subchunk1Size', self.int32Size),
			(self.assignLittleUINT, 'audioFormat', self.int16Size),
			(self.assignLittleUINT, 'numChannels', self.int16Size),
			(self.assignLittleUINT, 'sampleRate', self.int32Size),
			(self.assignLittleUINT, 'byteRate', self.int32Size),
			(self.assignLittleUINT, 'blockAlign', self.int16Size),
			(self.assignLittleUINT, 'bitsPerSample', self.int16Size),
			(self.assignLittleUINT, 'cbSize', self.int16Size),
			(self.assignLittleUINT, 'dwChannelMask', self.int32Size),
			(self.assignLittleUINT, 'SubFormat', self.subformatSize),
			(self.assignDIRECT, 'bytesPerSample', 
				lambda: int(self.headerDict['bitsPerSample'] / self.byteSize)
			)
		))
		# IF NO FACT SUBCHUNK PRESENT
		if self.headerDict['factIdIndex'] == self.binSearchFail:
			readLen2 = self.subChunkHeadSize
			self.read_and_assign(readStream, readLen2, (
				(self.assignBigUTF, 'subchunk2ID', self.int32Size),
				(self.assignLittleUINT, 'subchunk2Size', self.int32Size),
			))
		# IF FACT SUBCHUNK PRESENT
		else:
			readLen2 = ((self.headerDict['dataIdIndex'] - 
				self.headerDict['factIdIndex']) + 
				self.subChunkHeadSize
			)
			self.read_and_assign(readStream, readLen2, (
				(self.assignBigUTF, 'subchunk2ID', self.int32Size),
				(self.assignLittleUINT, 'subchunk2Size', self.int32Size),
				(self.assignLittleUINT, 'dwSampleLength', 
					lambda: self.headerDict['subchunk2Size']
				),
				(self.assignBigUTF, 'subchunk3ID', self.int32Size),
				(self.assignLittleUINT, 'subchunk3Size', self.int32Size)
			))
		# ANY FURTHER INITIALIZATION:
		self.init_fmt_str()

	def unpack(self, byteArray):
		"""
		Override of ReadAudio.unpack().
		
		Accepts:
		
		1) byteArray  ==> a buffer-full of binary
		
		Returns a nested list of numeric-type data that can be manipulated
		algorithmicly by the plugin.
		"""
		# Setup
		nestedSampleList = []
		self.headerDict['structMultiplier'] = int(len(byteArray) / self.headerDict['bytesPerSample'])
		# Unpack buffer
		bufferUnpacked = struct.unpack(self.struct_fmt_str(), byteArray[:])
		# Assemble into nested list
		for block in range(int( len(bufferUnpacked)  / self.headerDict['numChannels'])):
			sampleList = []
			for i in range(self.headerDict['numChannels']):
				sampleList.append(bufferUnpacked[(block*self.headerDict['numChannels'])+i])
			nestedSampleList.append(sampleList)
		return nestedSampleList
	
	# --------------------------------------------------------------------------
	# ------------------------------ END: OVERRIDES ----------------------------
	# --------------------------------------------------------------------------
	
	def init_fmt_str(self):
		"""
		Initializes the multiplier and data type character for the struct
		format string.  Called at the end of read_header() override.
		"""
		self.headerDict['structMultiplier'] = '' # initialize for later
		if self.headerDict['audioFormat'] == self.waveFormatPCM and self.headerDict['bytesPerSample'] == self.int8Size:
			self.headerDict['structFmtChar'] = 'B'
		elif self.headerDict['audioFormat'] == self.waveFormatPCM and self.headerDict['bytesPerSample'] == self.int16Size:
			self.headerDict['structFmtChar'] = 'h'
		elif self.headerDict['audioFormat'] == self.waveFormatPCM and self.headerDict['bytesPerSample'] == self.int24Size:
			raise aIOe.IncompatibleAudioFormat('24 bit wav not supported')
		elif self.headerDict['audioFormat'] == self.waveFormatPCM and self.headerDict['bytesPerSample'] == self.int32Size:
			self.headerDict['structFmtChar'] = 'i'
		elif self.headerDict['audioFormat'] == self.waveFormatFloat and self.headerDict['bytesPerSample'] == self.floatSize:
			self.headerDict['structFmtChar'] = 'f'
		elif self.headerDict['audioFormat'] == self.waveFormatFloat and self.headerDict['bytesPerSample'] == self.doubleSize:
			self.headerDict['structFmtChar'] = 'd'
		else:
			raise aIOe.IncompatibleAudioFormat
	
	def struct_fmt_str(self):
		"""
		Called in unpack and pack to determine struct formatting string based
		on buffer length.
		"""
		return '<' + str(self.headerDict['structMultiplier']) + self.headerDict['structFmtChar']

class WriteWav(aIOe.WriteAudio, WavBase):
	"""
	WAV file writer inherits from both WriteAudio and WavBase.
	It overrides the WriteAudio.read_header() and WriteAudio.unpack()
	methods that are called in the AudioIOEngine.process() method.
	"""
	def write_header(self, writeStream):
		"""
		Override of WriteAudio.write_header()
		
		Accepts:
		
		1) writeStream  ==> A pointer to the open output file.
		"""
		# Write chunk header and fmt subchunk
		self.pack_and_write(writeStream, (
			(self.packBigUTF, 'chunkID'),
			(self.packLittleUINT, 'chunkSize', self.int32Size),
			(self.packBigUTF, 'format'),
			(self.packBigUTF, 'subchunk1ID'),
			(self.packLittleUINT, 'subchunk1Size', self.int32Size),
			(self.packLittleUINT, 'audioFormat', self.int16Size),
			(self.packLittleUINT, 'numChannels', self.int16Size),
			(self.packLittleUINT, 'sampleRate', self.int32Size),
			(self.packLittleUINT, 'byteRate', self.int32Size),
			(self.packLittleUINT, 'blockAlign', self.int16Size),
			(self.packLittleUINT, 'bitsPerSample', self.int16Size)
		))
		# Handle format subchunk extension
		if self.headerDict['subchunk1Size'] == self.fmtChunkSize18:
			self.pack_and_write(writeStream, (
				(self.packLittleUINT, 'cbSize', self.int16Size),
			))
		elif self.headerDict['subchunk1Size'] == self.fmtChunkSize40:
			self.pack_and_write(writeStream, (
				(self.packLittleUINT, 'cbSize', self.int16Size),
				(self.packLittleUINT, 'dwChannelMask', self.int32Size),
				(self.packLittleUINT, 'SubFormat', self.subformatSize)
			))
		else:
			pass
		self.pack_and_write(writeStream, (
			(self.packBigUTF, 'subchunk2ID'),
			(self.packLittleUINT, 'subchunk2Size', self.int32Size)
		))
		# Conditionally handle fact subchunk, write data subchunk
		# If no fact subchunk present
		if self.headerDict['factIdIndex'] != self.binSearchFail:
			self.pack_and_write(writeStream, (
				(self.packLittleUINT, 'dwSampleLength', 
					lambda: self.headerDict['subchunk2Size']
				),
				(self.packBigUTF, 'subchunk3ID'),
				(self.packLittleUINT, 'subchunk3Size', self.int32Size)
			))
		else:
			pass
	
	def repack(self, processedSampleNestedList):
		"""
		Override of WriteAudio.repack()
		
		Accepts:
		
		1) processedSampleNestedList  ==> A nested list of processed sample
										  data.
		
		Returns a bytearray of the processed audio data.
		"""
		# Setup
		intTupleList = []
		processedByteArray = bytearray()
		# Disassemble nested list into tuple
		for block in range(len(processedSampleNestedList)):
			for channel in range(self.headerDict['numChannels']):
				intTupleList.append(processedSampleNestedList[block][channel])
		intTuple = tuple(intTupleList)
		self.headerDict['structMultiplier'] = len(intTuple)
		# Pack
		processedByteArray = struct.pack(self.struct_fmt_str(), *intTuple)
		return processedByteArray
	
	def struct_fmt_str(self):
		"""
		Called in unpack and pack to determine struct formatting string based
		on buffer length.
		"""
		return '<' + str(self.headerDict['structMultiplier']) + self.headerDict['structFmtChar']
