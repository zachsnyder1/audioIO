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
	
	def init_struct_fmt_str(self):
		"""
		Initializes the multiplier and data type character for the struct
		format string.  Called at the end of read_header() override.
		"""
		self.headerDict[self.keyStructMultiplier] = '' # initialize for later
		# Supported formats:
		if self.headerDict[self.keyAudioFmt] == self.wavFmtPCM and \
			self.headerDict[aIO.CORE_KEY_BYTE_DEPTH] == aIO.INT8_SIZE:
			self.headerDict[self.keyStructFmtChar] = 'B'
		elif self.headerDict[self.keyAudioFmt] == self.wavFmtPCM and \
			self.headerDict[aIO.CORE_KEY_BYTE_DEPTH] == aIO.INT16_SIZE:
			self.headerDict[self.keyStructFmtChar] = 'h'
		elif self.headerDict[self.keyAudioFmt] == self.wavFmtFloat and \
			self.headerDict[aIO.CORE_KEY_BYTE_DEPTH] == aIO.FLOAT_SIZE:
			self.headerDict[self.keyStructFmtChar] = 'f'
		elif self.headerDict[self.keyAudioFmt] == self.wavFmtFloat and \
			self.headerDict[aIO.CORE_KEY_BYTE_DEPTH] == aIO.DOUBLE_SIZE:
			self.headerDict[self.keyStructFmtChar] = 'd'
		# Else: raise IncompatibleAudioFormat with format description
		else:
			try:
				fmtStr = self.headerDict[aIO.CORE_KEY_FMT]
			except KeyError:
				fmtStr = 'unknown'
			exStr = "{} format not supported: {}-bit {}"
			fmtdExStr = exStr.format(self.targetFile, 
								   self.headerDict[aIO.CORE_KEY_BIT_DEPTH],
								   fmtStr)
			raise aIO.IncompatibleAudioFormat(fmtdExStr)
			
	def get_struct_fmt_str(self):
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
			(aIO.DIRECT, self.keyRiffIdIndex, 
			lambda: self.byteArray.find(self.riffIdHex)),
			(aIO.DIRECT, self.keyWaveIdIndex, 
			lambda: self.byteArray.find(self.waveIdHex)),
			(aIO.DIRECT, self.keyFmtIdIndex, 
			lambda: self.byteArray.find(self.fmtIdHex)),
			(aIO.DIRECT, self.keyFactIdIndex, 
			lambda: self.byteArray.find(self.factIdHex)),
			(aIO.DIRECT, self.keyDataIdIndex, 
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
		readStream.seek(0)
		self.readOffset = 0
		self.headerLen = 0
		
		# BEGIN INIT:
		# READ AND STORE CHUNK HEADER + fmt SUBCHUNK HEADER AND BODY
		if self.headerDict[self.keyFactIdIndex] == self.binSearchFail:
			readLen1 = self.headerDict[self.keyDataIdIndex]
		else:
			readLen1 = self.headerDict[self.keyFactIdIndex]
		self.read_and_assign(readStream, readLen1, (
			(aIO.BIG_UTF, self.keyChunkId, aIO.INT32_SIZE),
			(aIO.LITTLE_UINT, self.keyChunkSize, aIO.INT32_SIZE),
			(aIO.BIG_UTF, self.keyFormatId, aIO.INT32_SIZE),
			(aIO.BIG_UTF, self.keySubchunk1Id, aIO.INT32_SIZE),
			(aIO.LITTLE_UINT, self.keySubchunk1Size, aIO.INT32_SIZE),
			(aIO.LITTLE_UINT, self.keyAudioFmt, aIO.INT16_SIZE),
			(aIO.LITTLE_UINT, aIO.CORE_KEY_NUM_CHANNELS, aIO.INT16_SIZE),
			(aIO.LITTLE_UINT, aIO.CORE_KEY_SAMPLE_RATE, aIO.INT32_SIZE),
			(aIO.LITTLE_UINT, self.keyByteRate, aIO.INT32_SIZE),
			(aIO.LITTLE_UINT, self.keyBlockAlign, aIO.INT16_SIZE),
			(aIO.LITTLE_UINT, aIO.CORE_KEY_BIT_DEPTH, aIO.INT16_SIZE),
			(aIO.LITTLE_UINT, self.keyCbSize, aIO.INT16_SIZE),
			(aIO.LITTLE_UINT, self.keyWValidBPS, aIO.INT16_SIZE),
			(aIO.LITTLE_UINT, self.keyDwChannelMask, aIO.INT32_SIZE),
			(aIO.LITTLE_UINT, self.keySubFmtAudioFmt, aIO.INT16_SIZE),
			(aIO.LITTLE_UINT, self.keySubFormat, self.subformatSize),
			(aIO.DIRECT, aIO.CORE_KEY_BYTE_DEPTH, 
			lambda: int(self.headerDict[aIO.CORE_KEY_BIT_DEPTH] / aIO.BYTE_SIZE))))
		# set core key aIO.CORE_KEY_FMT
		if self.headerDict[self.keyAudioFmt] == self.wavFmtPCM:
			self.headerDict[aIO.CORE_KEY_FMT] = aIO.PCM
		elif self.headerDict[self.keyAudioFmt] == self.wavFmtFloat:
			self.headerDict[aIO.CORE_KEY_FMT] = aIO.FLOAT
		# set core key aIO.CORE_KEY_SIGNED
		if self.headerDict[self.keyAudioFmt] == self.wavFmtPCM and \
			self.headerDict[aIO.CORE_KEY_BYTE_DEPTH] == aIO.INT8_SIZE:
			self.headerDict[aIO.CORE_KEY_SIGNED] = False
		else:
			self.headerDict[aIO.CORE_KEY_SIGNED] = True
		# IF NO FACT SUBCHUNK PRESENT
		if self.headerDict[self.keyFactIdIndex] == self.binSearchFail:
			readLen2 = self.subChunkHeadSize
			self.read_and_assign(readStream, readLen2, (
				(aIO.BIG_UTF, self.keySubchunk2Id, aIO.INT32_SIZE),
				(aIO.LITTLE_UINT, self.keySubchunk2Size, 
				aIO.INT32_SIZE),))
		# IF FACT SUBCHUNK PRESENT
		else:
			readLen2 = ((self.headerDict[self.keyDataIdIndex] - 
				self.headerDict[self.keyFactIdIndex]) + 
				self.subChunkHeadSize)
			self.read_and_assign(readStream, readLen2, (
				(aIO.BIG_UTF, self.keySubchunk2Id, aIO.INT32_SIZE),
				(aIO.LITTLE_UINT, self.keySubchunk2Size, 
				aIO.INT32_SIZE),
				(aIO.LITTLE_UINT, self.keyDwSampleLength, 
				lambda: self.headerDict[self.keySubchunk2Size]),
				(aIO.BIG_UTF, self.keySubchunk3Id, aIO.INT32_SIZE),
				(aIO.LITTLE_UINT, self.keySubchunk3Size, 
				aIO.INT32_SIZE)))
		# ASSIGN CORE KEY samples per channel
		try:
			samplesPerChannel = self.headerDict[self.keyDwSampleLength]
		except KeyError:
			samplesPerChannel = int((self.headerDict[self.keyChunkSize] - 
									self.headerLen) / 
									self.headerDict[self.keyBlockAlign])
		self.headerDict[aIO.CORE_KEY_SAMPLES_PER_CHANNEL] = samplesPerChannel
		# ANY FURTHER INITIALIZATION:
		self.init_struct_fmt_str()

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
			int(len(byteArray) / self.headerDict[aIO.CORE_KEY_BYTE_DEPTH])
		# Unpack buffer
		bufferUnpacked = struct.unpack(self.get_struct_fmt_str(), byteArray[:])
		# Assemble into nested list
		for block in range(int(len(bufferUnpacked)  / 
								self.headerDict[aIO.CORE_KEY_NUM_CHANNELS])):
			sampleList = []
			for i in range(self.headerDict[aIO.CORE_KEY_NUM_CHANNELS]):
				sampleList.append(bufferUnpacked[(block * \
					self.headerDict[aIO.CORE_KEY_NUM_CHANNELS])+i])
			nestedSampleList.append(sampleList)
		return nestedSampleList
	
	# ------------------------------------------------------------------------
	# ------------------------------ END: OVERRIDES --------------------------
	# ------------------------------------------------------------------------



class WriteWav(aIO.WriteAudio, WavBase):
	"""
	WAV file writer class inherits from both WriteAudio and WavBase.  It 
	overrides the WriteAudio.init_header(), WriteAudio.write_header(), and 
	WriteAudio.repack() methods that are called in the AudioIOEngine.process() 
	method.
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
				if key == aIO.CORE_KEY_FMT:
					if value == aIO.FLOAT:
						self.headerDict[self.keyAudioFmt] = \
							self.wavFmtFloat
					elif value == aIO.PCM:
						self.headerDict[self.keyAudioFmt] = \
							self.wavFmtPCM
				else:
					pass
				self.headerDict[key] = value
			# Fill in the remaining core headerDict{} info
			# based on readObj.headerDict{}
			coreKeys = [
				aIO.CORE_KEY_FMT, 
				aIO.CORE_KEY_NUM_CHANNELS, 
				aIO.CORE_KEY_BIT_DEPTH, 
				aIO.CORE_KEY_BYTE_DEPTH, 
				aIO.CORE_KEY_SAMPLE_RATE, 
				aIO.CORE_KEY_SAMPLES_PER_CHANNEL
			]
			for key in coreKeys:
				try:
					if key == aIO.CORE_KEY_FMT:
						self.headerDict[self.keyAudioFmt]
					else:
						self.headerDict[key]
				except KeyError:
					if key == aIO.CORE_KEY_FMT:
						if readObj.headerDict[aIO.CORE_KEY_FMT] == \
							aIO.FLOAT:
							self.headerDict[self.keyAudioFmt] = \
								self.wavFmtFloat
						elif readObj.headerDict[aIO.CORE_KEY_FMT] == \
							aIO.PCM:
							self.headerDict[self.keyAudioFmt] = \
								self.wavFmtPCM
					else:
						pass
					self.headerDict[key] = readObj.headerDict[key]
			# Calculate fields from above
			self.headerDict[self.keyBlockAlign] = \
				self.headerDict[aIO.CORE_KEY_BYTE_DEPTH] * \
				self.headerDict[aIO.CORE_KEY_NUM_CHANNELS]
			self.headerDict[self.keyByteRate] = \
				self.headerDict[self.keyBlockAlign] * \
				self.headerDict[aIO.CORE_KEY_SAMPLE_RATE]
			# set core key aIO.CORE_KEY_SIGNED
			if self.headerDict[self.keyAudioFmt] == self.wavFmtPCM and \
				self.headerDict[aIO.CORE_KEY_BYTE_DEPTH] == aIO.INT8_SIZE:
				self.headerDict[aIO.CORE_KEY_SIGNED] = False
			else:
				self.headerDict[aIO.CORE_KEY_SIGNED] = True
			# init the struct fmt string
			self.init_struct_fmt_str()
			
			# Populate the remaining fields:
			# CALCULATE INTERMEDIATE VALUES
			factChunkSizeMultiplier = \
				math.ceil(self.headerDict[aIO.CORE_KEY_SAMPLES_PER_CHANNEL] / 
						  (2**32))
			dataChunkSize = \
				int((self.headerDict[aIO.CORE_KEY_SAMPLES_PER_CHANNEL] + \
				reachBack) * \
				self.headerDict[aIO.CORE_KEY_BYTE_DEPTH] * \
				self.headerDict[aIO.CORE_KEY_NUM_CHANNELS])
			# SET ID STRINGS
			self.headerDict[self.keyChunkId] = self.riffChunkId
			self.headerDict[self.keyFormatId] = self.waveId
			self.headerDict[self.keySubchunk1Id] = self.fmtSubchunkId
			# IF AUDIO FORMAT = PCM, BIT-DEPTH <= 16
			if (self.headerDict[self.keyAudioFmt] == 
				self.wavFmtPCM) and (self.headerDict[aIO.CORE_KEY_BYTE_DEPTH] <= 
										 aIO.INT16_SIZE):
				self.headerDict[self.keySubchunk1Size] = self.fmtChunkSize16
				self.headerDict[self.keySubchunk2Id] = self.dataSubchunkId
				self.headerDict[self.keySubchunk2Size] = dataChunkSize
			# IF AUDIO FORMAT = PCM, BIT-DEPTH = 24
			# IN PROGRESS !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
			elif (self.headerDict[self.keyAudioFmt] == 
				  self.wavFmtPCM) and (self.headerDict[aIO.CORE_KEY_BYTE_DEPTH] == 
				  					   aIO.INT24_SIZE):
				pass
			# IF AUDIO FORMAT = FLOAT
			elif self.headerDict[self.keyAudioFmt] == self.wavFmtFloat:
				self.headerDict[self.keySubchunk1Size] = self.fmtChunkSize18
				self.headerDict[self.keyCbSize] = self.fmtExtensionSize0
				self.headerDict[self.keySubchunk2Id] = self.factSubchunkId
				self.headerDict[self.keySubchunk2Size] = \
					int(aIO.INT32_SIZE * factChunkSizeMultiplier)
				self.headerDict[self.keyDwSampleLength] = \
					self.headerDict[aIO.CORE_KEY_SAMPLES_PER_CHANNEL] + \
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
				self.headerDict[aIO.CORE_KEY_BYTE_DEPTH] * \
				self.headerDict[aIO.CORE_KEY_NUM_CHANNELS])
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
			(aIO.BIG_UTF, self.keyChunkId),
			(aIO.LITTLE_UINT, self.keyChunkSize, aIO.INT32_SIZE),
			(aIO.BIG_UTF, self.keyFormatId),
			(aIO.BIG_UTF, self.keySubchunk1Id),
			(aIO.LITTLE_UINT, self.keySubchunk1Size, aIO.INT32_SIZE),
			(aIO.LITTLE_UINT, self.keyAudioFmt, aIO.INT16_SIZE),
			(aIO.LITTLE_UINT, aIO.CORE_KEY_NUM_CHANNELS, aIO.INT16_SIZE),
			(aIO.LITTLE_UINT, aIO.CORE_KEY_SAMPLE_RATE, aIO.INT32_SIZE),
			(aIO.LITTLE_UINT, self.keyByteRate, aIO.INT32_SIZE),
			(aIO.LITTLE_UINT, self.keyBlockAlign, aIO.INT16_SIZE),
			(aIO.LITTLE_UINT, aIO.CORE_KEY_BIT_DEPTH, aIO.INT16_SIZE)))
		# Handle format subchunk extension
		if self.headerDict[self.keySubchunk1Size] == self.fmtChunkSize18:
			self.pack_and_write(writeStream, (
				(aIO.LITTLE_UINT, self.keyCbSize, aIO.INT16_SIZE),))
		elif self.headerDict[self.keySubchunk1Size] == self.fmtChunkSize40:
			self.pack_and_write(writeStream, (
				(aIO.LITTLE_UINT, self.keyCbSize, aIO.INT16_SIZE),
				(aIO.LITTLE_UINT, self.keyWValidBPS, aIO.INT16_SIZE),
				(aIO.LITTLE_UINT, self.keyDwChannelMask, aIO.INT32_SIZE),
				(aIO.LITTLE_UINT, self.keySubFmtAudioFmt, aIO.INT16_SIZE),
				(aIO.DIRECT, self.keySubFormat)))
		else:
			pass
		self.pack_and_write(writeStream, (
			(aIO.BIG_UTF, self.keySubchunk2Id),
			(aIO.LITTLE_UINT, self.keySubchunk2Size, aIO.INT32_SIZE)))
		# Conditionally handle fact subchunk, write data subchunk
		# If fact subchunk is present
		if self.headerDict[self.keySubchunk2Id] != self.dataSubchunkId:
			self.pack_and_write(writeStream, (
				(aIO.LITTLE_UINT, self.keyDwSampleLength, 
				lambda: self.headerDict[self.keySubchunk2Size]),
				(aIO.BIG_UTF, self.keySubchunk3Id),
				(aIO.LITTLE_UINT, self.keySubchunk3Size, aIO.INT32_SIZE)))
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
			for channel in range(self.headerDict[aIO.CORE_KEY_NUM_CHANNELS]):
				intTupleList.append(processedSampleNestedList[block][channel])
		intTuple = tuple(intTupleList)
		self.headerDict[self.keyStructMultiplier] = len(intTuple)
		# Pack
		processedByteArray = struct.pack(self.get_struct_fmt_str(), *intTuple)
		return processedByteArray
	
	# ------------------------------------------------------------------------
	# ------------------------------ END: OVERRIDES --------------------------
	# ------------------------------------------------------------------------
	
