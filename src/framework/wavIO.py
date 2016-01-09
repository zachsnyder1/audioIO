import struct
import math
from . import audioIO as aIO


# <<<----- CONSTANTS ----->>>

# WAV specific headerDict{} keys
KEY_RIFF_ID_INDEX = 'riffIdIndex'
KEY_WAVE_ID_INDEX = 'WAVE_IDIndex'
KEY_FMT_ID_INDEX  = 'fmtIdIndex'
KEY_FACT_ID_INDEX = 'factIdIndex'
KEY_DATA_ID_INDEX = 'dataIdIndex'
KEY_CHUNK_ID = 'chunkID'
KEY_CHUNK_SIZE = 'chunkSize'
KEY_FMT_ID = 'format'
KEY_SUBCHUNK1_ID = 'subchunk1ID'
KEY_SUBCHUNK1_SIZE = 'subchunk1Size'
KEY_AUDIO_FMT = 'audioFormat'
KEY_BYTE_RATE = 'byteRate'
KEY_BLOCK_ALIGN = 'blockAlign'
KEY_CB_SIZE = 'cbSize'
KEY_W_VALID_BPS = 'wValidBitsPerSample'
KEY_DW_CHANNEL_MASK = 'dwChannelMask'
KEY_SUBFMT_AUDIO_FMT = 'subAudioFmt'
KEY_SUBFMT = 'SubFormat'
KEY_SUBCHUNK2_ID = 'subchunk2ID'
KEY_SUBCHUNK2_SIZE = 'subchunk2Size'
KEY_DW_SAMPLE_LEN = 'dwSampleLength'
KEY_SUBCHUNK3_ID = 'subchunk3ID'
KEY_SUBCHUNK3_SIZE = 'subchunk3Size'
KEY_STRUCT_MULTIPLIER = 'structMultiplier'
KEY_STRUCT_FMT_CHAR = 'structFmtChar'
# Sizes
WAV_HEADER_SEARCH_LEN = 100  # Num bytes used to search for header chunk IDs
WAV_CHUNK_HEAD_SIZE = 12   # Num bytes in WAV file format header
WAV_SUBCHUNK_HEAD_SIZE = 8  # Num bytes in a subchunk header
FMT_CHUNK_SIZE_16 = 16  # Num bytes in PCM fmt subchunk
FMT_CHUNK_SIZE_18 = 18  # Num bytes in non-PCM && non-extensible fmt subchunk
FMT_CHUNK_SIZE_40 = 40  # Num bytes in extensible format fmt subchunk
SUBFMT_SIZE = 14   # Num bytes in the SubFormat parameter
FMT_EXT_SIZE_0 = 0  # Num bytes in extension if non-extensible
FMT_EXT_SIZE_22 = 22 # Num bytes in extension if extensible
# SubchunkID Strings
RIFF_CHUNK_ID = 'RIFF'   # Chunk ID
WAVE_ID = 'WAVE'        # Wave ID
FMT_SUBCHUNK_ID = 'fmt ' # Fmt subchunk ID
FACT_SUBCHUNK_ID = 'fact' # Fact subchunk ID
DATA_SUBCHUNK_ID = 'data' # Data subchuhnk ID
# For bin search
RIFF_ID_HEX = b'\x52\x49\x46\x46'  # Used in bin search
WAVE_ID_HEX = b'\x57\x41\x56\x45'  # Used in bin search
FMT_ID_HEX = b'\x66\x6d\x74\x20'   # Used in bin search
FACT_ID_HEX = b'\x66\x61\x63\x74'  # Used in bin search
DATA_ID_HEX = b'\x64\x61\x74\x61'  # Used in bin search
BIN_SEARCH_FAIL = -1               # Used for bin search
# Format codes for .WAV
WAV_FMT_PCM = 1   # Standard, PCM data
WAV_FMT_FLOAT = 3 # Floating point data
WAV_FMT_ALAW = 6  # A-law 8-bit data
WAV_FMT_MULAW = 7 # Mu-law 8-bit data
WAV_FMT_EXTENSIBLE = 61183 # Extensible format


class WavBase:
	"""
	WAV base class.  Holds important methods that are
	inherited into ReadWav and WriteWav classes.
	"""
	
	def init_struct_fmt_str(self):
		"""
		Initializes the multiplier and data type character for the struct
		format string.  Called at the end of read_header() override.
		"""
		self.headerDict[KEY_STRUCT_MULTIPLIER] = '' # initialize for later
		# Supported formats:
		if self.headerDict[KEY_AUDIO_FMT] == WAV_FMT_PCM and \
			self.headerDict[aIO.CORE_KEY_BYTE_DEPTH] == aIO.INT8_SIZE:
			self.headerDict[KEY_STRUCT_FMT_CHAR] = 'B'
		elif self.headerDict[KEY_AUDIO_FMT] == WAV_FMT_PCM and \
			self.headerDict[aIO.CORE_KEY_BYTE_DEPTH] == aIO.INT16_SIZE:
			self.headerDict[KEY_STRUCT_FMT_CHAR] = 'h'
		elif self.headerDict[KEY_AUDIO_FMT] == WAV_FMT_FLOAT and \
			self.headerDict[aIO.CORE_KEY_BYTE_DEPTH] == aIO.FLOAT_SIZE:
			self.headerDict[KEY_STRUCT_FMT_CHAR] = 'f'
		elif self.headerDict[KEY_AUDIO_FMT] == WAV_FMT_FLOAT and \
			self.headerDict[aIO.CORE_KEY_BYTE_DEPTH] == aIO.DOUBLE_SIZE:
			self.headerDict[KEY_STRUCT_FMT_CHAR] = 'd'
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
		return '<' + str(self.headerDict[KEY_STRUCT_MULTIPLIER]) + \
			self.headerDict[KEY_STRUCT_FMT_CHAR]



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
		self.read_and_assign(readStream, WAV_HEADER_SEARCH_LEN, (
			(aIO.DIRECT, KEY_RIFF_ID_INDEX, 
			lambda: self.byteArray.find(RIFF_ID_HEX)),
			(aIO.DIRECT, KEY_WAVE_ID_INDEX, 
			lambda: self.byteArray.find(WAVE_ID_HEX)),
			(aIO.DIRECT, KEY_FMT_ID_INDEX, 
			lambda: self.byteArray.find(FMT_ID_HEX)),
			(aIO.DIRECT, KEY_FACT_ID_INDEX, 
			lambda: self.byteArray.find(FACT_ID_HEX)),
			(aIO.DIRECT, KEY_DATA_ID_INDEX, 
			lambda: self.byteArray.find(DATA_ID_HEX))))
		# Verify file format
		if (self.headerDict[KEY_RIFF_ID_INDEX] or 
			self.headerDict[KEY_WAVE_ID_INDEX] or
			self.headerDict[KEY_FMT_ID_INDEX] or
			self.headerDict[KEY_DATA_ID_INDEX]
		) == BIN_SEARCH_FAIL:
			raise aIO.IncompatibleAudioFormat('file is not RIFF WAVE type')
		else:
			pass
		# RESET CURRENT POSITION
		readStream.seek(0)
		self.readOffset = 0
		self.headerLen = 0
		
		# BEGIN INIT:
		# READ AND STORE CHUNK HEADER + fmt SUBCHUNK HEADER AND BODY
		if self.headerDict[KEY_FACT_ID_INDEX] == BIN_SEARCH_FAIL:
			readLen1 = self.headerDict[KEY_DATA_ID_INDEX]
		else:
			readLen1 = self.headerDict[KEY_FACT_ID_INDEX]
		self.read_and_assign(readStream, readLen1, (
			(aIO.BIG_UTF, KEY_CHUNK_ID, aIO.INT32_SIZE),
			(aIO.LITTLE_UINT, KEY_CHUNK_SIZE, aIO.INT32_SIZE),
			(aIO.BIG_UTF, KEY_FMT_ID, aIO.INT32_SIZE),
			(aIO.BIG_UTF, KEY_SUBCHUNK1_ID, aIO.INT32_SIZE),
			(aIO.LITTLE_UINT, KEY_SUBCHUNK1_SIZE, aIO.INT32_SIZE),
			(aIO.LITTLE_UINT, KEY_AUDIO_FMT, aIO.INT16_SIZE),
			(aIO.LITTLE_UINT, aIO.CORE_KEY_NUM_CHANNELS, aIO.INT16_SIZE),
			(aIO.LITTLE_UINT, aIO.CORE_KEY_SAMPLE_RATE, aIO.INT32_SIZE),
			(aIO.LITTLE_UINT, KEY_BYTE_RATE, aIO.INT32_SIZE),
			(aIO.LITTLE_UINT, KEY_BLOCK_ALIGN, aIO.INT16_SIZE),
			(aIO.LITTLE_UINT, aIO.CORE_KEY_BIT_DEPTH, aIO.INT16_SIZE),
			(aIO.LITTLE_UINT, KEY_CB_SIZE, aIO.INT16_SIZE),
			(aIO.LITTLE_UINT, KEY_W_VALID_BPS, aIO.INT16_SIZE),
			(aIO.LITTLE_UINT, KEY_DW_CHANNEL_MASK, aIO.INT32_SIZE),
			(aIO.LITTLE_UINT, KEY_SUBFMT_AUDIO_FMT, aIO.INT16_SIZE),
			(aIO.LITTLE_UINT, KEY_SUBFMT, SUBFMT_SIZE),
			(aIO.DIRECT, aIO.CORE_KEY_BYTE_DEPTH, 
			lambda: int(self.headerDict[aIO.CORE_KEY_BIT_DEPTH] / aIO.BYTE_SIZE))))
		# set core key aIO.CORE_KEY_FMT
		if self.headerDict[KEY_AUDIO_FMT] == WAV_FMT_PCM:
			self.headerDict[aIO.CORE_KEY_FMT] = aIO.PCM
		elif self.headerDict[KEY_AUDIO_FMT] == WAV_FMT_FLOAT:
			self.headerDict[aIO.CORE_KEY_FMT] = aIO.FLOAT
		# set core key aIO.CORE_KEY_SIGNED
		if self.headerDict[KEY_AUDIO_FMT] == WAV_FMT_PCM and \
			self.headerDict[aIO.CORE_KEY_BYTE_DEPTH] == aIO.INT8_SIZE:
			self.headerDict[aIO.CORE_KEY_SIGNED] = False
		else:
			self.headerDict[aIO.CORE_KEY_SIGNED] = True
		# IF NO FACT SUBCHUNK PRESENT
		if self.headerDict[KEY_FACT_ID_INDEX] == BIN_SEARCH_FAIL:
			readLen2 = WAV_SUBCHUNK_HEAD_SIZE
			self.read_and_assign(readStream, readLen2, (
				(aIO.BIG_UTF, KEY_SUBCHUNK2_ID, aIO.INT32_SIZE),
				(aIO.LITTLE_UINT, KEY_SUBCHUNK2_SIZE, 
				aIO.INT32_SIZE),))
		# IF FACT SUBCHUNK PRESENT
		else:
			readLen2 = ((self.headerDict[KEY_DATA_ID_INDEX] - 
				self.headerDict[KEY_FACT_ID_INDEX]) + 
				WAV_SUBCHUNK_HEAD_SIZE)
			self.read_and_assign(readStream, readLen2, (
				(aIO.BIG_UTF, KEY_SUBCHUNK2_ID, aIO.INT32_SIZE),
				(aIO.LITTLE_UINT, KEY_SUBCHUNK2_SIZE, 
				aIO.INT32_SIZE),
				(aIO.LITTLE_UINT, KEY_DW_SAMPLE_LEN, 
				lambda: self.headerDict[KEY_SUBCHUNK2_SIZE]),
				(aIO.BIG_UTF, KEY_SUBCHUNK3_ID, aIO.INT32_SIZE),
				(aIO.LITTLE_UINT, KEY_SUBCHUNK3_SIZE, 
				aIO.INT32_SIZE)))
		# ASSIGN CORE KEY samples per channel
		try:
			samplesPerChannel = self.headerDict[KEY_DW_SAMPLE_LEN]
		except KeyError:
			samplesPerChannel = int((self.headerDict[KEY_CHUNK_SIZE] - 
									self.headerLen) / 
									self.headerDict[KEY_BLOCK_ALIGN])
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
		self.headerDict[KEY_STRUCT_MULTIPLIER] = \
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
						self.headerDict[KEY_AUDIO_FMT] = \
							WAV_FMT_FLOAT
					elif value == aIO.PCM:
						self.headerDict[KEY_AUDIO_FMT] = \
							WAV_FMT_PCM
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
						self.headerDict[KEY_AUDIO_FMT]
					else:
						self.headerDict[key]
				except KeyError:
					if key == aIO.CORE_KEY_FMT:
						if readObj.headerDict[aIO.CORE_KEY_FMT] == \
							aIO.FLOAT:
							self.headerDict[KEY_AUDIO_FMT] = \
								WAV_FMT_FLOAT
						elif readObj.headerDict[aIO.CORE_KEY_FMT] == \
							aIO.PCM:
							self.headerDict[KEY_AUDIO_FMT] = \
								WAV_FMT_PCM
					else:
						pass
					self.headerDict[key] = readObj.headerDict[key]
			# Calculate fields from above
			self.headerDict[KEY_BLOCK_ALIGN] = \
				self.headerDict[aIO.CORE_KEY_BYTE_DEPTH] * \
				self.headerDict[aIO.CORE_KEY_NUM_CHANNELS]
			self.headerDict[KEY_BYTE_RATE] = \
				self.headerDict[KEY_BLOCK_ALIGN] * \
				self.headerDict[aIO.CORE_KEY_SAMPLE_RATE]
			# set core key aIO.CORE_KEY_SIGNED
			if self.headerDict[KEY_AUDIO_FMT] == WAV_FMT_PCM and \
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
			self.headerDict[KEY_CHUNK_ID] = RIFF_CHUNK_ID
			self.headerDict[KEY_FMT_ID] = WAVE_ID
			self.headerDict[KEY_SUBCHUNK1_ID] = FMT_SUBCHUNK_ID
			# IF AUDIO FORMAT = PCM, BIT-DEPTH <= 16
			if (self.headerDict[KEY_AUDIO_FMT] == 
				WAV_FMT_PCM) and (self.headerDict[aIO.CORE_KEY_BYTE_DEPTH] <= 
										 aIO.INT16_SIZE):
				self.headerDict[KEY_SUBCHUNK1_SIZE] = FMT_CHUNK_SIZE_16
				self.headerDict[KEY_SUBCHUNK2_ID] = DATA_SUBCHUNK_ID
				self.headerDict[KEY_SUBCHUNK2_SIZE] = dataChunkSize
			# IF AUDIO FORMAT = PCM, BIT-DEPTH = 24
			# IN PROGRESS !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
			elif (self.headerDict[KEY_AUDIO_FMT] == 
				  WAV_FMT_PCM) and (self.headerDict[aIO.CORE_KEY_BYTE_DEPTH] == 
				  					   aIO.INT24_SIZE):
				pass
			# IF AUDIO FORMAT = FLOAT
			elif self.headerDict[KEY_AUDIO_FMT] == WAV_FMT_FLOAT:
				self.headerDict[KEY_SUBCHUNK1_SIZE] = FMT_CHUNK_SIZE_18
				self.headerDict[KEY_CB_SIZE] = FMT_EXT_SIZE_0
				self.headerDict[KEY_SUBCHUNK2_ID] = FACT_SUBCHUNK_ID
				self.headerDict[KEY_SUBCHUNK2_SIZE] = \
					int(aIO.INT32_SIZE * factChunkSizeMultiplier)
				self.headerDict[KEY_DW_SAMPLE_LEN] = \
					self.headerDict[aIO.CORE_KEY_SAMPLES_PER_CHANNEL] + \
					reachBack
				self.headerDict[KEY_SUBCHUNK3_ID] = DATA_SUBCHUNK_ID
				self.headerDict[KEY_SUBCHUNK3_SIZE] = dataChunkSize
			# CALCULATE CHUNK SIZE:
			if self.headerDict[KEY_SUBCHUNK2_ID] == DATA_SUBCHUNK_ID:
				self.headerDict[KEY_CHUNK_SIZE] = \
					int((2 * WAV_SUBCHUNK_HEAD_SIZE) + \
					WAV_CHUNK_HEAD_SIZE + \
					self.headerDict[KEY_SUBCHUNK1_SIZE] + \
					self.headerDict[KEY_SUBCHUNK2_SIZE])
			else:
				self.headerDict[KEY_CHUNK_SIZE] = \
					int((3 * WAV_SUBCHUNK_HEAD_SIZE) + \
					WAV_CHUNK_HEAD_SIZE + \
					self.headerDict[KEY_SUBCHUNK1_SIZE] + \
					self.headerDict[KEY_SUBCHUNK2_SIZE] + \
					self.headerDict[KEY_SUBCHUNK3_SIZE])
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
			self.headerDict[KEY_CHUNK_SIZE] += reachBackAdd
			if self.headerDict[KEY_SUBCHUNK2_ID] == DATA_SUBCHUNK_ID:
				self.headerDict[KEY_SUBCHUNK2_SIZE] += reachBackAdd
			else:
				self.headerDict[KEY_SUBCHUNK3_SIZE] += reachBackAdd
		return
	
	def write_header(self, writeStream):
		"""
		Override of WriteAudio.write_header()
		
		Accepts:
		
		1) writeStream  ==> A pointer to the open output file.
		"""
		# Write chunk header and fmt subchunk
		self.pack_and_write(writeStream, (
			(aIO.BIG_UTF, KEY_CHUNK_ID),
			(aIO.LITTLE_UINT, KEY_CHUNK_SIZE, aIO.INT32_SIZE),
			(aIO.BIG_UTF, KEY_FMT_ID),
			(aIO.BIG_UTF, KEY_SUBCHUNK1_ID),
			(aIO.LITTLE_UINT, KEY_SUBCHUNK1_SIZE, aIO.INT32_SIZE),
			(aIO.LITTLE_UINT, KEY_AUDIO_FMT, aIO.INT16_SIZE),
			(aIO.LITTLE_UINT, aIO.CORE_KEY_NUM_CHANNELS, aIO.INT16_SIZE),
			(aIO.LITTLE_UINT, aIO.CORE_KEY_SAMPLE_RATE, aIO.INT32_SIZE),
			(aIO.LITTLE_UINT, KEY_BYTE_RATE, aIO.INT32_SIZE),
			(aIO.LITTLE_UINT, KEY_BLOCK_ALIGN, aIO.INT16_SIZE),
			(aIO.LITTLE_UINT, aIO.CORE_KEY_BIT_DEPTH, aIO.INT16_SIZE)))
		# Handle format subchunk extension
		if self.headerDict[KEY_SUBCHUNK1_SIZE] == FMT_CHUNK_SIZE_18:
			self.pack_and_write(writeStream, (
				(aIO.LITTLE_UINT, KEY_CB_SIZE, aIO.INT16_SIZE),))
		elif self.headerDict[KEY_SUBCHUNK1_SIZE] == FMT_CHUNK_SIZE_40:
			self.pack_and_write(writeStream, (
				(aIO.LITTLE_UINT, KEY_CB_SIZE, aIO.INT16_SIZE),
				(aIO.LITTLE_UINT, KEY_W_VALID_BPS, aIO.INT16_SIZE),
				(aIO.LITTLE_UINT, KEY_DW_CHANNEL_MASK, aIO.INT32_SIZE),
				(aIO.LITTLE_UINT, KEY_SUBFMT_AUDIO_FMT, aIO.INT16_SIZE),
				(aIO.DIRECT, KEY_SUBFMT)))
		else:
			pass
		self.pack_and_write(writeStream, (
			(aIO.BIG_UTF, KEY_SUBCHUNK2_ID),
			(aIO.LITTLE_UINT, KEY_SUBCHUNK2_SIZE, aIO.INT32_SIZE)))
		# Conditionally handle fact subchunk, write data subchunk
		# If fact subchunk is present
		if self.headerDict[KEY_SUBCHUNK2_ID] != DATA_SUBCHUNK_ID:
			self.pack_and_write(writeStream, (
				(aIO.LITTLE_UINT, KEY_DW_SAMPLE_LEN, 
				lambda: self.headerDict[KEY_SUBCHUNK2_SIZE]),
				(aIO.BIG_UTF, KEY_SUBCHUNK3_ID),
				(aIO.LITTLE_UINT, KEY_SUBCHUNK3_SIZE, aIO.INT32_SIZE)))
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
		self.headerDict[KEY_STRUCT_MULTIPLIER] = len(intTuple)
		# Pack
		processedByteArray = struct.pack(self.get_struct_fmt_str(), *intTuple)
		return processedByteArray
	
	# ------------------------------------------------------------------------
	# ------------------------------ END: OVERRIDES --------------------------
	# ------------------------------------------------------------------------
	
