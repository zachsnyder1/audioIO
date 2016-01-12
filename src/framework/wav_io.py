"""
This module contains concrete classes that implement methods for 
reading, unpacking, [re]packing, and writing sample data to and 
from .WAV files. The concrete classes ReadWav and WriteWav 
inherit from the abstract base_io.BaseRead and base_io.BaseWrite 
classes, respectively, and from WavBase, which contains  
methods specific to .WAV files. Not all .WAV files are covered. This 
module currently only supports 8- and 16-bit PCM and 32- 
and 64-bit floating point formats.
"""

import struct
import math
from . import base_io as baseIO


# <<<----- CONSTANTS ----->>>

# WAV specific signalParams{} keys
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
WAV_CHUNK_SIZE_ADDITION = 4   # Num bytes in WAV file format header
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
		self.signalParams[KEY_STRUCT_MULTIPLIER] = '' # initialize for later
		# Supported formats:
		if self.signalParams[KEY_AUDIO_FMT] == WAV_FMT_PCM and \
			self.signalParams[baseIO.CORE_KEY_BYTE_DEPTH] == baseIO.INT8_SIZE:
			self.signalParams[KEY_STRUCT_FMT_CHAR] = 'B'
		elif self.signalParams[KEY_AUDIO_FMT] == WAV_FMT_PCM and \
			self.signalParams[baseIO.CORE_KEY_BYTE_DEPTH] == baseIO.INT16_SIZE:
			self.signalParams[KEY_STRUCT_FMT_CHAR] = 'h'
		elif self.signalParams[KEY_AUDIO_FMT] == WAV_FMT_FLOAT and \
			self.signalParams[baseIO.CORE_KEY_BYTE_DEPTH] == baseIO.FLOAT_SIZE:
			self.signalParams[KEY_STRUCT_FMT_CHAR] = 'f'
		elif self.signalParams[KEY_AUDIO_FMT] == WAV_FMT_FLOAT and \
			self.signalParams[baseIO.CORE_KEY_BYTE_DEPTH] == baseIO.DOUBLE_SIZE:
			self.signalParams[KEY_STRUCT_FMT_CHAR] = 'd'
		# Else: raise IncompatibleFileFormat with format description
		else:
			try:
				fmtStr = self.signalParams[baseIO.CORE_KEY_FMT]
			except KeyError:
				fmtStr = 'unknown'
			exStr = "{} format not supported: {}-bit {}"
			fmtdExStr = exStr.format(self.targetFile, 
								   self.signalParams[baseIO.CORE_KEY_BIT_DEPTH],
								   fmtStr)
			raise baseIO.IncompatibleFileFormat(fmtdExStr)
			
	def get_struct_fmt_str(self):
		"""
		Called in unpack and pack to determine struct formatting string based
		on buffer length.
		
		Returns the struct formatting string used during unpack()/repack().
		"""
		return '<' + str(self.signalParams[KEY_STRUCT_MULTIPLIER]) + \
			self.signalParams[KEY_STRUCT_FMT_CHAR]



class ReadWav(baseIO.BaseRead, WavBase):
	"""
	The concrete class that implements methods for reading .WAV audio files. 
	Inherits from both baseIO.BaseRead and WavBase.
	"""
	# ------------------------------------------------------------------------
	# -------------------------------- OVERRIDES -----------------------------
	# ------------------------------------------------------------------------
	def read_header(self, readStream):
		"""
		An implementation, specifically for .WAV files, of the abstract 
		operation declared in baseIO.BaseRead. This method is called in 
		Engine.process(), and populates the signalParams with values read
		from the header of the input file.
		
		Accepts:
		
		1) readStream  ==> The open read file.
		"""
		# BIN SEARCH FOR CHUNK IDs
		self.read_and_assign(readStream, WAV_HEADER_SEARCH_LEN, (
			(baseIO.DIRECT, KEY_RIFF_ID_INDEX, 
			lambda: self.byteArray.find(RIFF_ID_HEX)),
			(baseIO.DIRECT, KEY_WAVE_ID_INDEX, 
			lambda: self.byteArray.find(WAVE_ID_HEX)),
			(baseIO.DIRECT, KEY_FMT_ID_INDEX, 
			lambda: self.byteArray.find(FMT_ID_HEX)),
			(baseIO.DIRECT, KEY_FACT_ID_INDEX, 
			lambda: self.byteArray.find(FACT_ID_HEX)),
			(baseIO.DIRECT, KEY_DATA_ID_INDEX, 
			lambda: self.byteArray.find(DATA_ID_HEX))))
		# Verify file format
		if (self.signalParams[KEY_RIFF_ID_INDEX] or 
			self.signalParams[KEY_WAVE_ID_INDEX] or
			self.signalParams[KEY_FMT_ID_INDEX] or
			self.signalParams[KEY_DATA_ID_INDEX]
		) == BIN_SEARCH_FAIL:
			raise baseIO.IncompatibleFileFormat('file is not RIFF WAVE type')
		else:
			pass
		# RESET CURRENT POSITION
		readStream.seek(0)
		self.readOffset = 0
		self.headerLen = 0
		
		# BEGIN INIT:
		# READ AND STORE CHUNK HEADER + fmt SUBCHUNK HEADER AND BODY
		if self.signalParams[KEY_FACT_ID_INDEX] == BIN_SEARCH_FAIL:
			readLen1 = self.signalParams[KEY_DATA_ID_INDEX]
		else:
			readLen1 = self.signalParams[KEY_FACT_ID_INDEX]
		self.read_and_assign(readStream, readLen1, (
			(baseIO.BIG_UTF, KEY_CHUNK_ID, baseIO.INT32_SIZE),
			(baseIO.LITTLE_UINT, KEY_CHUNK_SIZE, baseIO.INT32_SIZE),
			(baseIO.BIG_UTF, KEY_FMT_ID, baseIO.INT32_SIZE),
			(baseIO.BIG_UTF, KEY_SUBCHUNK1_ID, baseIO.INT32_SIZE),
			(baseIO.LITTLE_UINT, KEY_SUBCHUNK1_SIZE, baseIO.INT32_SIZE),
			(baseIO.LITTLE_UINT, KEY_AUDIO_FMT, baseIO.INT16_SIZE),
			(baseIO.LITTLE_UINT, baseIO.CORE_KEY_NUM_CHANNELS, baseIO.INT16_SIZE),
			(baseIO.LITTLE_UINT, baseIO.CORE_KEY_SAMPLE_RATE, baseIO.INT32_SIZE),
			(baseIO.LITTLE_UINT, KEY_BYTE_RATE, baseIO.INT32_SIZE),
			(baseIO.LITTLE_UINT, KEY_BLOCK_ALIGN, baseIO.INT16_SIZE),
			(baseIO.LITTLE_UINT, baseIO.CORE_KEY_BIT_DEPTH, baseIO.INT16_SIZE),
			(baseIO.LITTLE_UINT, KEY_CB_SIZE, baseIO.INT16_SIZE),
			(baseIO.LITTLE_UINT, KEY_W_VALID_BPS, baseIO.INT16_SIZE),
			(baseIO.LITTLE_UINT, KEY_DW_CHANNEL_MASK, baseIO.INT32_SIZE),
			(baseIO.LITTLE_UINT, KEY_SUBFMT_AUDIO_FMT, baseIO.INT16_SIZE),
			(baseIO.LITTLE_UINT, KEY_SUBFMT, SUBFMT_SIZE),
			(baseIO.DIRECT, baseIO.CORE_KEY_BYTE_DEPTH, 
			lambda: int(self.signalParams[baseIO.CORE_KEY_BIT_DEPTH] / baseIO.BYTE_SIZE))))
		# set core key baseIO.CORE_KEY_FMT
		if self.signalParams[KEY_AUDIO_FMT] == WAV_FMT_PCM:
			self.signalParams[baseIO.CORE_KEY_FMT] = baseIO.PCM
		elif self.signalParams[KEY_AUDIO_FMT] == WAV_FMT_FLOAT:
			self.signalParams[baseIO.CORE_KEY_FMT] = baseIO.FLOAT
		else:
			pass
		# set core key baseIO.CORE_KEY_SIGNED
		if self.signalParams[KEY_AUDIO_FMT] == WAV_FMT_PCM and \
			self.signalParams[baseIO.CORE_KEY_BYTE_DEPTH] == baseIO.INT8_SIZE:
			self.signalParams[baseIO.CORE_KEY_SIGNED] = False
		else:
			self.signalParams[baseIO.CORE_KEY_SIGNED] = True
		# IF NO FACT SUBCHUNK PRESENT
		if self.signalParams[KEY_FACT_ID_INDEX] == BIN_SEARCH_FAIL:
			readLen2 = WAV_SUBCHUNK_HEAD_SIZE
			self.read_and_assign(readStream, readLen2, (
				(baseIO.BIG_UTF, KEY_SUBCHUNK2_ID, baseIO.INT32_SIZE),
				(baseIO.LITTLE_UINT, KEY_SUBCHUNK2_SIZE, 
				baseIO.INT32_SIZE),))
		# IF FACT SUBCHUNK PRESENT
		else:
			readLen2 = ((self.signalParams[KEY_DATA_ID_INDEX] - 
				self.signalParams[KEY_FACT_ID_INDEX]) + 
				WAV_SUBCHUNK_HEAD_SIZE)
			self.read_and_assign(readStream, readLen2, (
				(baseIO.BIG_UTF, KEY_SUBCHUNK2_ID, baseIO.INT32_SIZE),
				(baseIO.LITTLE_UINT, KEY_SUBCHUNK2_SIZE, 
				baseIO.INT32_SIZE),
				(baseIO.LITTLE_UINT, KEY_DW_SAMPLE_LEN, 
				lambda: self.signalParams[KEY_SUBCHUNK2_SIZE]),
				(baseIO.BIG_UTF, KEY_SUBCHUNK3_ID, baseIO.INT32_SIZE),
				(baseIO.LITTLE_UINT, KEY_SUBCHUNK3_SIZE, 
				baseIO.INT32_SIZE)))
		# ASSIGN CORE KEY samples per channel
		try:
			sampPerChan = self.signalParams[KEY_DW_SAMPLE_LEN]
		except KeyError:
			if self.signalParams[KEY_SUBCHUNK2_ID] == DATA_SUBCHUNK_ID:
				sampPerChan = int(self.signalParams[KEY_SUBCHUNK2_SIZE] / 
					self.signalParams[KEY_BLOCK_ALIGN])
			elif self.signalParams[KEY_SUBCHUNK3_ID] == DATA_SUBCHUNK_ID:
				sampPerChan = int(self.signalParams[KEY_SUBCHUNK3_SIZE] / 
					self.signalParams[KEY_BLOCK_ALIGN])
			else:
				raise
		self.signalParams[baseIO.CORE_KEY_SAMPLES_PER_CHANNEL] = sampPerChan
		# ANY FURTHER INITIALIZATION:
		self.init_struct_fmt_str()

	def unpack(self, byteArray):
		"""
		An implementation of the abstract unpacking operation for .WAV 
		files. Unpacks a buffer-full of the signal data binary of the 
		input file.
		
		Accepts:
		
		1) byteArray  ==> a buffer-full of binary
		
		Returns a nested list of numeric-type data that can be manipulated
		algorithmicly by the plugin.
		"""
		# Setup
		nestedSampleList = []
		self.signalParams[KEY_STRUCT_MULTIPLIER] = \
			int(len(byteArray) / self.signalParams[baseIO.CORE_KEY_BYTE_DEPTH])
		# Unpack buffer
		bufferUnpacked = struct.unpack(self.get_struct_fmt_str(), byteArray[:])
		# Assemble into nested list
		for block in range(int(len(bufferUnpacked)  / 
								self.signalParams[baseIO.CORE_KEY_NUM_CHANNELS])):
			sampleList = []
			for i in range(self.signalParams[baseIO.CORE_KEY_NUM_CHANNELS]):
				sampleList.append(bufferUnpacked[(block * \
					self.signalParams[baseIO.CORE_KEY_NUM_CHANNELS])+i])
			nestedSampleList.append(sampleList)
		return nestedSampleList
	
	# ------------------------------------------------------------------------
	# ------------------------------ END: OVERRIDES --------------------------
	# ------------------------------------------------------------------------



class WriteWav(baseIO.BaseWrite, WavBase):
	"""
	The concrete class that implements methods for writing .WAV audio files. 
	Inherits from both baseIO.BaseWrite and WavBase.
	"""
	# ------------------------------------------------------------------------
	# -------------------------------- OVERRIDES -----------------------------
	# ------------------------------------------------------------------------
	
	def init_header(self, inputSignal, reachBack):
		"""
		The .WAV implementation of the abstract .init_header() operation, 
		which initializes the signalParams with values based on the read 
		file and any conversion parameters that are passed as options 
		during initialization of the Engine object.
		
		Accepts:
		
		1) inputSignal    ==>  A pointer to the open read file.
		
		2) reachBack  ==>  The number of samples available to the plugin
						   algorithm for reachBack.
		"""
		# Set audio format code based on CORE_KEY_FMT
		if self.signalParams[baseIO.CORE_KEY_FMT] == baseIO.FLOAT:
			self.signalParams[KEY_AUDIO_FMT] =  WAV_FMT_FLOAT
		elif self.signalParams[baseIO.CORE_KEY_FMT] == baseIO.PCM:
			self.signalParams[KEY_AUDIO_FMT] = WAV_FMT_PCM
		# Copy samples per channel from inputSignal.signalParams
		self.signalParams[baseIO.CORE_KEY_SAMPLES_PER_CHANNEL] = \
			inputSignal.signalParams[baseIO.CORE_KEY_SAMPLES_PER_CHANNEL]
		# Calculate fields from above
		self.signalParams[KEY_BLOCK_ALIGN] = \
			self.signalParams[baseIO.CORE_KEY_BYTE_DEPTH] * \
			self.signalParams[baseIO.CORE_KEY_NUM_CHANNELS]
		self.signalParams[KEY_BYTE_RATE] = \
			self.signalParams[KEY_BLOCK_ALIGN] * \
			self.signalParams[baseIO.CORE_KEY_SAMPLE_RATE]
		# set core key baseIO.CORE_KEY_SIGNED
		if self.signalParams[KEY_AUDIO_FMT] == WAV_FMT_PCM and \
				self.signalParams[baseIO.CORE_KEY_BYTE_DEPTH] == \
				baseIO.INT8_SIZE:
			self.signalParams[baseIO.CORE_KEY_SIGNED] = False
		else:
			self.signalParams[baseIO.CORE_KEY_SIGNED] = True
		# init the struct fmt string
		self.init_struct_fmt_str()
		
		# Populate the remaining fields:
		# CALCULATE INTERMEDIATE VALUES
		factChunkSizeMultiplier = \
			math.ceil(self.signalParams[baseIO.CORE_KEY_SAMPLES_PER_CHANNEL] / 
					  (2**32))
		dataChunkSize = \
			int((self.signalParams[baseIO.CORE_KEY_SAMPLES_PER_CHANNEL] + \
			reachBack) * \
			self.signalParams[baseIO.CORE_KEY_BYTE_DEPTH] * \
			self.signalParams[baseIO.CORE_KEY_NUM_CHANNELS])
		# SET ID STRINGS
		self.signalParams[KEY_CHUNK_ID] = RIFF_CHUNK_ID
		self.signalParams[KEY_FMT_ID] = WAVE_ID
		self.signalParams[KEY_SUBCHUNK1_ID] = FMT_SUBCHUNK_ID
		# IF AUDIO FORMAT = PCM, BIT-DEPTH <= 16
		if (self.signalParams[KEY_AUDIO_FMT] == 
			WAV_FMT_PCM) and (self.signalParams[baseIO.CORE_KEY_BYTE_DEPTH] <= 
								baseIO.INT16_SIZE):
			self.signalParams[KEY_SUBCHUNK1_SIZE] = FMT_CHUNK_SIZE_16
			self.signalParams[KEY_SUBCHUNK2_ID] = DATA_SUBCHUNK_ID
			self.signalParams[KEY_SUBCHUNK2_SIZE] = dataChunkSize
		# IF AUDIO FORMAT = PCM, BIT-DEPTH = 24
		# IN PROGRESS !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
		elif (self.signalParams[KEY_AUDIO_FMT] == 
			  WAV_FMT_PCM) and (self.signalParams[baseIO.CORE_KEY_BYTE_DEPTH] == 
			  					baseIO.INT24_SIZE):
			pass
		# IF AUDIO FORMAT = FLOAT
		elif self.signalParams[KEY_AUDIO_FMT] == WAV_FMT_FLOAT:
			self.signalParams[KEY_SUBCHUNK1_SIZE] = FMT_CHUNK_SIZE_18
			self.signalParams[KEY_CB_SIZE] = FMT_EXT_SIZE_0
			self.signalParams[KEY_SUBCHUNK2_ID] = FACT_SUBCHUNK_ID
			self.signalParams[KEY_SUBCHUNK2_SIZE] = \
				int(baseIO.INT32_SIZE * factChunkSizeMultiplier)
			self.signalParams[KEY_DW_SAMPLE_LEN] = \
				self.signalParams[baseIO.CORE_KEY_SAMPLES_PER_CHANNEL] + \
				reachBack
			self.signalParams[KEY_SUBCHUNK3_ID] = DATA_SUBCHUNK_ID
			self.signalParams[KEY_SUBCHUNK3_SIZE] = dataChunkSize
		# CALCULATE CHUNK SIZE:
		if self.signalParams[KEY_SUBCHUNK2_ID] == DATA_SUBCHUNK_ID:
			self.signalParams[KEY_CHUNK_SIZE] = \
				int((2 * WAV_SUBCHUNK_HEAD_SIZE) + \
					WAV_CHUNK_SIZE_ADDITION + \
					self.signalParams[KEY_SUBCHUNK1_SIZE] + \
					self.signalParams[KEY_SUBCHUNK2_SIZE])
		else:
			self.signalParams[KEY_CHUNK_SIZE] = \
				int((3 * WAV_SUBCHUNK_HEAD_SIZE) + \
					WAV_CHUNK_SIZE_ADDITION + \
					self.signalParams[KEY_SUBCHUNK1_SIZE] + \
					self.signalParams[KEY_SUBCHUNK2_SIZE] + \
					self.signalParams[KEY_SUBCHUNK3_SIZE])
		return
	
	def write_header(self, writeStream):
		"""
		The .WAV implementation of the abstract .write_header() 
		operation, which writes the header of the output file based 
		on values in the signalParams, after it is initialized by an 
		.init_header() call.
		
		Accepts:
		
		1) writeStream  ==> A pointer to the open output file.
		"""
		# Write chunk header and fmt subchunk
		self.pack_and_write(writeStream, (
			(baseIO.BIG_UTF, KEY_CHUNK_ID),
			(baseIO.LITTLE_UINT, KEY_CHUNK_SIZE, baseIO.INT32_SIZE),
			(baseIO.BIG_UTF, KEY_FMT_ID),
			(baseIO.BIG_UTF, KEY_SUBCHUNK1_ID),
			(baseIO.LITTLE_UINT, KEY_SUBCHUNK1_SIZE, baseIO.INT32_SIZE),
			(baseIO.LITTLE_UINT, KEY_AUDIO_FMT, baseIO.INT16_SIZE),
			(baseIO.LITTLE_UINT, baseIO.CORE_KEY_NUM_CHANNELS, baseIO.INT16_SIZE),
			(baseIO.LITTLE_UINT, baseIO.CORE_KEY_SAMPLE_RATE, baseIO.INT32_SIZE),
			(baseIO.LITTLE_UINT, KEY_BYTE_RATE, baseIO.INT32_SIZE),
			(baseIO.LITTLE_UINT, KEY_BLOCK_ALIGN, baseIO.INT16_SIZE),
			(baseIO.LITTLE_UINT, baseIO.CORE_KEY_BIT_DEPTH, baseIO.INT16_SIZE)))
		# Handle format subchunk extension
		if self.signalParams[KEY_SUBCHUNK1_SIZE] == FMT_CHUNK_SIZE_18:
			self.pack_and_write(writeStream, (
				(baseIO.LITTLE_UINT, KEY_CB_SIZE, baseIO.INT16_SIZE),))
		elif self.signalParams[KEY_SUBCHUNK1_SIZE] == FMT_CHUNK_SIZE_40:
			self.pack_and_write(writeStream, (
				(baseIO.LITTLE_UINT, KEY_CB_SIZE, baseIO.INT16_SIZE),
				(baseIO.LITTLE_UINT, KEY_W_VALID_BPS, baseIO.INT16_SIZE),
				(baseIO.LITTLE_UINT, KEY_DW_CHANNEL_MASK, baseIO.INT32_SIZE),
				(baseIO.LITTLE_UINT, KEY_SUBFMT_AUDIO_FMT, baseIO.INT16_SIZE),
				(baseIO.DIRECT, KEY_SUBFMT)))
		else:
			pass
		self.pack_and_write(writeStream, (
			(baseIO.BIG_UTF, KEY_SUBCHUNK2_ID),
			(baseIO.LITTLE_UINT, KEY_SUBCHUNK2_SIZE, baseIO.INT32_SIZE)))
		# Conditionally handle fact subchunk, write data subchunk
		# If fact subchunk is present
		if self.signalParams[KEY_SUBCHUNK2_ID] != DATA_SUBCHUNK_ID:
			self.pack_and_write(writeStream, (
				(baseIO.LITTLE_UINT, KEY_DW_SAMPLE_LEN, 
				lambda: self.signalParams[KEY_SUBCHUNK2_SIZE]),
				(baseIO.BIG_UTF, KEY_SUBCHUNK3_ID),
				(baseIO.LITTLE_UINT, KEY_SUBCHUNK3_SIZE, baseIO.INT32_SIZE)))
		else:
			pass
	
	def repack(self, processedSampleNestedList):
		"""
		The .WAV implementation of the abstract .repack() operation, which 
		accepts a nested list of processed samples and repacks them back 
		into binary in the correct format, based on values in the
		signalParams. This method is called once per buffer-full of data.
		
		Accepts:
		
		1) processedSampleNestedList  ==> A nested list of processed sample
										  data.
		
		Returns a bytearray of the processed signal data.
		"""
		# Setup
		intTupleList = []
		processedByteArray = bytearray()
		# Disassemble nested list into tuple
		for block in range(len(processedSampleNestedList)):
			for channel in range(self.signalParams[baseIO.CORE_KEY_NUM_CHANNELS]):
				intTupleList.append(processedSampleNestedList[block][channel])
		intTuple = tuple(intTupleList)
		self.signalParams[KEY_STRUCT_MULTIPLIER] = len(intTuple)
		# Pack
		processedByteArray = struct.pack(self.get_struct_fmt_str(), *intTuple)
		return processedByteArray
	
	# ------------------------------------------------------------------------
	# ------------------------------ END: OVERRIDES --------------------------
	# ------------------------------------------------------------------------
	
