import struct
import math
from . import audioIO as aIO



class WavBase:
	"""
	WAV base class.  Holds important constants and methods that are
	inherited into ReadWav and WriteWav classes.
	"""
	# CONSTANTS:
	
	# WAV specific headerDict{} keys
	keyRiffIdIndex = 'riffIdIndex'
	keyWaveIdIndex = 'waveIdIndex'
	keyFmtIdIndex  = 'fmtIdIndex'
	keyFactIdIndex = 'factIdIndex'
	keyDataIdIndex = 'dataIdIndex'
	keyChunkId = 'chunkID'
	keyChunkSize = 'chunkSize'
	keyFormatId = 'format'
	keySubchunk1Id = 'subchunk1ID'
	keySubchunk1Size = 'subchunk1Size'
	keyAudioFmt = 'audioFormat'
	keyByteRate = 'byteRate'
	keyBlockAlign = 'blockAlign'
	keyCbSize = 'cbSize'
	keyWValidBPS = 'wValidBitsPerSample'
	keyDwChannelMask = 'dwChannelMask'
	keySubFmtAudioFmt = 'subAudioFmt'
	keySubFormat = 'SubFormat'
	keySubchunk2Id = 'subchunk2ID'
	keySubchunk2Size = 'subchunk2Size'
	keyDwSampleLength = 'dwSampleLength'
	keySubchunk3Id = 'subchunk3ID'
	keySubchunk3Size = 'subchunk3Size'
	keyStructMultiplier = 'structMultiplier'
	keyStructFmtChar = 'structFmtChar'
	# Sizes
	wavHeaderSearchLen = 100  # Num bytes used to search for header chunk IDs
	wavChunkHeadSize = 12   # Num bytes in WAV file format header
	subChunkHeadSize = 8  # Num bytes in a subchunk header
	fmtChunkSize16 = 16  # Num bytes in PCM fmt subchunk
	fmtChunkSize18 = 18  # Num bytes in non-PCM && non-extensible fmt subchunk
	fmtChunkSize40 = 40  # Num bytes in extensible format fmt subchunk
	subformatSize = 14   # Num bytes in the SubFormat parameter
	fmtExtensionSize0 = 0  # Num bytes in extension if non-extensible
	fmtExtensionSize22 = 22 # Num bytes in extension if extensible
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
	wavFmtPCM = 1   # Standard, PCM data
	wavFmtFloat = 3 # Floating point data
	wavFmtALaw = 6  # A-law 8-bit data
	wavFmtMULaw = 7 # Mu-law 8-bit data
	wavFmtExtensible = 61183 # Extensible format
	
	def init_fmt_str(self):
		"""
		Initializes the multiplier and data type character for the struct
		format string.  Called at the end of read_header() override.
		"""
		self.headerDict[self.keyStructMultiplier] = '' # initialize for later
		if self.headerDict[self.keyAudioFmt] == self.wavFmtPCM and \
			self.headerDict[self.keyByteDepth] == self.int8Size:
			self.headerDict[self.keyStructFmtChar] = 'B'
		elif self.headerDict[self.keyAudioFmt] == self.wavFmtPCM and \
			self.headerDict[self.keyByteDepth] == self.int16Size:
			self.headerDict[self.keyStructFmtChar] = 'h'
		elif self.headerDict[self.keyAudioFmt] == self.wavFmtPCM and \
			self.headerDict[self.keyByteDepth] == self.int24Size:
			raise aIO.IncompatibleAudioFormat('24 bit wav not supported')
		elif self.headerDict[self.keyAudioFmt] == self.wavFmtPCM and \
			self.headerDict[self.keyByteDepth] == self.int32Size:
			self.headerDict[self.keyStructFmtChar] = 'i'
		elif self.headerDict[self.keyAudioFmt] == self.wavFmtFloat and \
			self.headerDict[self.keyByteDepth] == self.floatSize:
			self.headerDict[self.keyStructFmtChar] = 'f'
		elif self.headerDict[self.keyAudioFmt] == self.wavFmtFloat and \
			self.headerDict[self.keyByteDepth] == self.doubleSize:
			self.headerDict[self.keyStructFmtChar] = 'd'
		else:
			raise aIO.IncompatibleAudioFormat
			
	def struct_fmt_str(self):
		"""
		Called in unpack and pack to determine struct formatting string based
		on buffer length.
		
		Returns the struct formatting string used during unpack()/repack().
		"""
		return '<' + str(self.headerDict[self.keyStructMultiplier]) + \
			self.headerDict[self.keyStructFmtChar]



class ReadWav(aIO.ReadAudio, WavBase):
	"""
	WAV file reader inherits from both ReadAudio and WavBase.
	It overrides the ReadAudio.read_header() and ReadAudio.unpack()
	methods that are called in the AudioIOEngine.process() method.
	"""
	# ------------------------------------------------------------------------
	# -------------------------------- OVERRIDES -----------------------------
	# ------------------------------------------------------------------------
	def read_header(self, readStream):
		"""
		Override of ReadAudio.read_header().  Any further
		initialization is tacked onto the end.
		
		Accepts:
		
		1) readStream  ==> The open read file.
		"""
		# BIN SEARCH FOR CHUNK IDs
		self.read_and_assign(readStream, self.wavHeaderSearchLen, (
			(self.assignDIRECT, self.keyRiffIdIndex, 
			lambda: self.byteArray.find(self.riffIdHex)),
			(self.assignDIRECT, self.keyWaveIdIndex, 
			lambda: self.byteArray.find(self.waveIdHex)),
			(self.assignDIRECT, self.keyFmtIdIndex, 
			lambda: self.byteArray.find(self.fmtIdHex)),
			(self.assignDIRECT, self.keyFactIdIndex, 
			lambda: self.byteArray.find(self.factIdHex)),
			(self.assignDIRECT, self.keyDataIdIndex, 
			lambda: self.byteArray.find(self.dataIdHex))))
		# Verify file format
		if (self.headerDict[self.keyRiffIdIndex] or 
			self.headerDict[self.keyWaveIdIndex] or
			self.headerDict[self.keyFmtIdIndex] or
			self.headerDict[self.keyDataIdIndex]
		) == self.binSearchFail:
			raise aIO.IncompatibleAudioFormat('file is not RIFF WAVE type')
		else:
			pass
		# RESET CURRENT POSITION
		readStream.seek(self.reset)
		self.readOffset = self.reset
		self.headerLen = self.reset
		
		# BEGIN INIT:
		# READ AND STORE CHUNK HEADER + fmt SUBCHUNK HEADER AND BODY
		if self.headerDict[self.keyFactIdIndex] == self.binSearchFail:
			readLen1 = self.headerDict[self.keyDataIdIndex]
		else:
			readLen1 = self.headerDict[self.keyFactIdIndex]
		self.read_and_assign(readStream, readLen1, (
			(self.assignBigUTF, self.keyChunkId, self.int32Size),
			(self.assignLittleUINT, self.keyChunkSize, self.int32Size),
			(self.assignBigUTF, self.keyFormatId, self.int32Size),
			(self.assignBigUTF, self.keySubchunk1Id, self.int32Size),
			(self.assignLittleUINT, self.keySubchunk1Size, self.int32Size),
			(self.assignLittleUINT, self.keyAudioFmt, self.int16Size),
			(self.assignLittleUINT, self.keyNumChannels, self.int16Size),
			(self.assignLittleUINT, self.keySampleRate, self.int32Size),
			(self.assignLittleUINT, self.keyByteRate, self.int32Size),
			(self.assignLittleUINT, self.keyBlockAlign, self.int16Size),
			(self.assignLittleUINT, self.keyBitDepth, self.int16Size),
			(self.assignLittleUINT, self.keyCbSize, self.int16Size),
			(self.assignLittleUINT, self.keyWValidBPS, self.int16Size),
			(self.assignLittleUINT, self.keyDwChannelMask, self.int32Size),
			(self.assignLittleUINT, self.keySubFmtAudioFmt, self.int16Size),
			(self.assignLittleUINT, self.keySubFormat, self.subformatSize),
			(self.assignDIRECT, self.keyByteDepth, 
			lambda: int(self.headerDict[self.keyBitDepth] / self.byteSize))))
		# set core key self.keyAudioFormatStr
		if self.headerDict[self.keyAudioFmt] == self.wavFmtPCM:
			self.headerDict[self.keyAudioFormatStr] = self.formatStringPCM
		elif self.headerDict[self.keyAudioFmt] == self.wavFmtFloat:
			self.headerDict[self.keyAudioFormatStr] = self.formatStringFloat
		# set core key self.keySigned
		if self.headerDict[self.keyAudioFmt] == self.wavFmtPCM and \
			self.headerDict[self.keyByteDepth] == self.int8Size:
			self.headerDict[self.keySigned] = False
		else:
			self.headerDict[self.keySigned] = True
		# IF NO FACT SUBCHUNK PRESENT
		if self.headerDict[self.keyFactIdIndex] == self.binSearchFail:
			readLen2 = self.subChunkHeadSize
			self.read_and_assign(readStream, readLen2, (
				(self.assignBigUTF, self.keySubchunk2Id, self.int32Size),
				(self.assignLittleUINT, self.keySubchunk2Size, 
				self.int32Size),))
		# IF FACT SUBCHUNK PRESENT
		else:
			readLen2 = ((self.headerDict[self.keyDataIdIndex] - 
				self.headerDict[self.keyFactIdIndex]) + 
				self.subChunkHeadSize)
			self.read_and_assign(readStream, readLen2, (
				(self.assignBigUTF, self.keySubchunk2Id, self.int32Size),
				(self.assignLittleUINT, self.keySubchunk2Size, 
				self.int32Size),
				(self.assignLittleUINT, self.keyDwSampleLength, 
				lambda: self.headerDict[self.keySubchunk2Size]),
				(self.assignBigUTF, self.keySubchunk3Id, self.int32Size),
				(self.assignLittleUINT, self.keySubchunk3Size, 
				self.int32Size)))
		# ASSIGN CORE KEY samples per channel
		try:
			samplesPerChannel = self.headerDict[self.keyDwSampleLength]
		except KeyError:
			samplesPerChannel = int((self.headerDict[self.keyChunkSize] - 
									self.headerLen) / 
									self.headerDict[self.keyBlockAlign])
		self.headerDict[self.keySamplesPerChannel] = samplesPerChannel
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
		self.headerDict[self.keyStructMultiplier] = \
			int(len(byteArray) / self.headerDict[self.keyByteDepth])
		# Unpack buffer
		bufferUnpacked = struct.unpack(self.struct_fmt_str(), byteArray[:])
		# Assemble into nested list
		for block in range(int(len(bufferUnpacked)  / 
								self.headerDict[self.keyNumChannels])):
			sampleList = []
			for i in range(self.headerDict[self.keyNumChannels]):
				sampleList.append(bufferUnpacked[(block * \
					self.headerDict[self.keyNumChannels])+i])
			nestedSampleList.append(sampleList)
		return nestedSampleList
	
	# ------------------------------------------------------------------------
	# ------------------------------ END: OVERRIDES --------------------------
	# ------------------------------------------------------------------------



class WriteWav(aIO.WriteAudio, WavBase):
	"""
	WAV file writer inherits from both WriteAudio and WavBase.
	It overrides the WriteAudio.read_header() and WriteAudio.unpack()
	methods that are called in the AudioIOEngine.process() method.
	"""
	# ------------------------------------------------------------------------
	# -------------------------------- OVERRIDES -----------------------------
	# ------------------------------------------------------------------------
	
	def init_header(self, readObj, reachBack):
		"""
		If no file conversion, simply copy header from readObj.
		Else, populate based on conversion parameters, as well as the
		file size info caclulated from readObj and reachBack info.
		
		Accepts:
		
		1) readObj    ==>  A pointer to the open read file.
		
		2) reachBack  ==>  The number of samples available to the plugin
						   algorithm for reachBack.
		"""
		if self.conversion or (not isinstance(readObj, ReadWav)):
			# Populate core headerDict{} info based on conversion parameters
			for key, value in self.conversionParameters.items():
				if key == self.keyAudioFormatStr:
					if value == self.formatStringFloat:
						self.headerDict[self.keyAudioFmt] = \
							self.wavFmtFloat
					elif value == self.formatStringPCM:
						self.headerDict[self.keyAudioFmt] = \
							self.wavFmtPCM
				else:
					pass
				self.headerDict[key] = value
			# Fill in the remaining core headerDict{} info
			# based on readObj.headerDict{}
			coreKeys = [
				self.keyAudioFormatStr, 
				self.keyNumChannels, 
				self.keyBitDepth, 
				self.keyByteDepth, 
				self.keySampleRate, 
				self.keySamplesPerChannel
			]
			for key in coreKeys:
				try:
					if key == self.keyAudioFormatStr:
						self.headerDict[self.keyAudioFmt]
					else:
						self.headerDict[key]
				except KeyError:
					if key == self.keyAudioFormatStr:
						if readObj.headerDict[self.keyAudioFormatStr] == \
							self.formatStringFloat:
							self.headerDict[self.keyAudioFmt] = \
								self.wavFmtFloat
						elif readObj.headerDict[self.keyAudioFormatStr] == \
							self.formatStringPCM:
							self.headerDict[self.keyAudioFmt] = \
								self.wavFmtPCM
					else:
						pass
					self.headerDict[key] = readObj.headerDict[key]
			# Calculate fields from above
			self.headerDict[self.keyBlockAlign] = \
				self.headerDict[self.keyByteDepth] * \
				self.headerDict[self.keyNumChannels]
			self.headerDict[self.keyByteRate] = \
				self.headerDict[self.keyBlockAlign] * \
				self.headerDict[self.keySampleRate]
			# set core key self.keySigned
			if self.headerDict[self.keyAudioFmt] == self.wavFmtPCM and \
				self.headerDict[self.keyByteDepth] == self.int8Size:
				self.headerDict[self.keySigned] = False
			else:
				self.headerDict[self.keySigned] = True
			# init the struct fmt string
			self.init_fmt_str()
			
			# Populate the remaining fields:
			# CALCULATE INTERMEDIATE VALUES
			factChunkSizeMultiplier = \
				math.ceil(self.headerDict[self.keySamplesPerChannel] / 
						  (2**32))
			dataChunkSize = \
				int((self.headerDict[self.keySamplesPerChannel] + \
				reachBack) * \
				self.headerDict[self.keyByteDepth] * \
				self.headerDict[self.keyNumChannels])
			# SET ID STRINGS
			self.headerDict[self.keyChunkId] = self.riffChunkId
			self.headerDict[self.keyFormatId] = self.waveId
			self.headerDict[self.keySubchunk1Id] = self.fmtSubchunkId
			# IF AUDIO FORMAT = PCM, BIT-DEPTH <= 16
			if (self.headerDict[self.keyAudioFmt] == 
				self.wavFmtPCM) and (self.headerDict[self.keyByteDepth] <= 
										 self.int16Size):
				self.headerDict[self.keySubchunk1Size] = self.fmtChunkSize16
				self.headerDict[self.keySubchunk2Id] = self.dataSubchunkId
				self.headerDict[self.keySubchunk2Size] = dataChunkSize
			# IF AUDIO FORMAT = PCM, BIT-DEPTH = 24
			# IN PROGRESS !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
			elif (self.headerDict[self.keyAudioFmt] == 
				  self.wavFmtPCM) and (self.headerDict[self.keyByteDepth] == 
				  					   self.int24Size):
				pass
			# IF AUDIO FORMAT = FLOAT
			elif self.headerDict[self.keyAudioFmt] == self.wavFmtFloat:
				self.headerDict[self.keySubchunk1Size] = self.fmtChunkSize18
				self.headerDict[self.keyCbSize] = self.fmtExtensionSize0
				self.headerDict[self.keySubchunk2Id] = self.factSubchunkId
				self.headerDict[self.keySubchunk2Size] = \
					int(self.int32Size * factChunkSizeMultiplier)
				self.headerDict[self.keyDwSampleLength] = \
					self.headerDict[self.keySamplesPerChannel] + \
					reachBack
				self.headerDict[self.keySubchunk3Id] = self.dataSubchunkId
				self.headerDict[self.keySubchunk3Size] = dataChunkSize
			# CALCULATE CHUNK SIZE:
			if self.headerDict[self.keySubchunk2Id] == self.dataSubchunkId:
				self.headerDict[self.keyChunkSize] = \
					int((2 * self.subChunkHeadSize) + \
					self.wavChunkHeadSize + \
					self.headerDict[self.keySubchunk1Size] + \
					self.headerDict[self.keySubchunk2Size])
			else:
				self.headerDict[self.keyChunkSize] = \
					int((3 * self.subChunkHeadSize) + \
					self.wavChunkHeadSize + \
					self.headerDict[self.keySubchunk1Size] + \
					self.headerDict[self.keySubchunk2Size] + \
					self.headerDict[self.keySubchunk3Size])
			return
		# Else simply copy entire headerDict{}, then adjust chunk
		# and data chunk sizes based on reachBack:
		else:
			for key, value in readObj.headerDict.items():
				self.headerDict[key] = value
			# Calculate the size increase of file based on reachBack
			reachBackAdd = int(reachBack * \
				self.headerDict[self.keyByteDepth] * \
				self.headerDict[self.keyNumChannels])
			self.headerDict[self.keyChunkSize] += reachBackAdd
			if self.headerDict[self.keySubchunk2Id] == self.dataSubchunkId:
				self.headerDict[self.keySubchunk2Size] += reachBackAdd
			else:
				self.headerDict[self.keySubchunk3Size] += reachBackAdd
		return
	
	def write_header(self, writeStream):
		"""
		Override of WriteAudio.write_header()
		
		Accepts:
		
		1) writeStream  ==> A pointer to the open output file.
		"""
		# Write chunk header and fmt subchunk
		self.pack_and_write(writeStream, (
			(self.packBigUTF, self.keyChunkId),
			(self.packLittleUINT, self.keyChunkSize, self.int32Size),
			(self.packBigUTF, self.keyFormatId),
			(self.packBigUTF, self.keySubchunk1Id),
			(self.packLittleUINT, self.keySubchunk1Size, self.int32Size),
			(self.packLittleUINT, self.keyAudioFmt, self.int16Size),
			(self.packLittleUINT, self.keyNumChannels, self.int16Size),
			(self.packLittleUINT, self.keySampleRate, self.int32Size),
			(self.packLittleUINT, self.keyByteRate, self.int32Size),
			(self.packLittleUINT, self.keyBlockAlign, self.int16Size),
			(self.packLittleUINT, self.keyBitDepth, self.int16Size)))
		# Handle format subchunk extension
		if self.headerDict[self.keySubchunk1Size] == self.fmtChunkSize18:
			self.pack_and_write(writeStream, (
				(self.packLittleUINT, self.keyCbSize, self.int16Size),))
		elif self.headerDict[self.keySubchunk1Size] == self.fmtChunkSize40:
			self.pack_and_write(writeStream, (
				(self.packLittleUINT, self.keyCbSize, self.int16Size),
				(self.packLittleUINT, self.keyWValidBPS, self.int16Size),
				(self.packLittleUINT, self.keyDwChannelMask, self.int32Size),
				(self.packLittleUINT, self.keySubFmtAudioFmt, self.int16Size),
				(self.packDIRECT, self.keySubFormat)))
		else:
			pass
		self.pack_and_write(writeStream, (
			(self.packBigUTF, self.keySubchunk2Id),
			(self.packLittleUINT, self.keySubchunk2Size, self.int32Size)))
		# Conditionally handle fact subchunk, write data subchunk
		# If fact subchunk is present
		if self.headerDict[self.keySubchunk2Id] != self.dataSubchunkId:
			self.pack_and_write(writeStream, (
				(self.packLittleUINT, self.keyDwSampleLength, 
				lambda: self.headerDict[self.keySubchunk2Size]),
				(self.packBigUTF, self.keySubchunk3Id),
				(self.packLittleUINT, self.keySubchunk3Size, self.int32Size)))
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
			for channel in range(self.headerDict[self.keyNumChannels]):
				intTupleList.append(processedSampleNestedList[block][channel])
		intTuple = tuple(intTupleList)
		self.headerDict[self.keyStructMultiplier] = len(intTuple)
		# Pack
		processedByteArray = struct.pack(self.struct_fmt_str(), *intTuple)
		return processedByteArray
	
	# ------------------------------------------------------------------------
	# ------------------------------ END: OVERRIDES --------------------------
	# ------------------------------------------------------------------------
	
