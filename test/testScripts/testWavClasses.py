import os
import sys
import unittest
import hashlib
PACKAGE_ROOT = '../..'
SCRIPT_DIR = os.path.dirname(os.path.realpath(os.path.join(os.getcwd(), 
	os.path.expanduser(__file__))))
PACKAGE_PATH = os.path.normpath(os.path.join(SCRIPT_DIR, PACKAGE_ROOT))
sys.path.append(PACKAGE_PATH)
from src.framework import base_io as baseIO
from src.framework import wav_io as wavIO
from src.framework import engine

TEST_DATA_DIR = os.path.normpath(
					os.path.dirname(
					os.path.dirname(
					os.path.abspath(__file__))) + '/testData/')
TEST_READ_FILE = os.path.normpath(
					os.path.abspath(
					os.path.join(TEST_DATA_DIR, 'test_read_audio_file.txt')))
TEST_WRITE_FILE = os.path.normpath(
					os.path.abspath(
					os.path.join(TEST_DATA_DIR, 'test_write_audio_file.txt')))


class WavIOEngineInitTestMethods(unittest.TestCase):
	"""
	Methods to test the initialization of a WavIOEngine object.
	"""
	def test_basic_init(self):
		"""
		Test basic initialization of both read and write classes.
		"""
		readAudioObj = wavIO.ReadWav(TEST_READ_FILE)
		writeAudioObj = wavIO.WriteWav(TEST_WRITE_FILE, 'float', 2, 32, 44100)
		self.assertIsInstance(readAudioObj, wavIO.ReadWav)
		self.assertIsInstance(writeAudioObj, wavIO.WriteWav)
	
	def test_WriteWav_conversion_init(self):
		"""
		Test initialization of write class with conversion
		parameters set to correct values.
		"""
		writeAudioObj = wavIO.WriteWav(TEST_WRITE_FILE, 'PCM', 2, 16, 44100)
		self.assertIsInstance(writeAudioObj, wavIO.WriteWav)
		self.assertEqual(writeAudioObj.signalParams, {
			baseIO.CORE_KEY_FMT: 'PCM',
			baseIO.CORE_KEY_NUM_CHANNELS: 2,
			baseIO.CORE_KEY_BIT_DEPTH: 16,
			baseIO.CORE_KEY_BYTE_DEPTH: 2,
			baseIO.CORE_KEY_SAMPLE_RATE: 44100
		})



class WavInitHeaderTestMethods(unittest.TestCase):
	"""
	Methods to test the WriteWav.init_header() function.
	"""
	def test_valid_conversion_parameters_PCM(self):
		"""
		Test with valid conversion parameters, converting to a PCM file.
		"""
		readAudioObj = wavIO.ReadWav(TEST_READ_FILE)
		reachBack = 0
		writeAudioObj = wavIO.WriteWav(TEST_WRITE_FILE, 'PCM', 2, 16, 44100)
		
		readAudioObj.signalParams[baseIO.CORE_KEY_SAMPLES_PER_CHANNEL] = 100
		writeAudioObj.init_header(readAudioObj, reachBack)
		
		self.assertEqual(writeAudioObj.signalParams, {
			baseIO.CORE_KEY_SAMPLES_PER_CHANNEL: 100,
			wavIO.KEY_CHUNK_ID: wavIO.RIFF_CHUNK_ID,
			wavIO.KEY_CHUNK_SIZE: 436,
			wavIO.KEY_FMT_ID: wavIO.WAVE_ID,
			wavIO.KEY_SUBCHUNK1_ID: wavIO.FMT_SUBCHUNK_ID,
			wavIO.KEY_SUBCHUNK1_SIZE: wavIO.FMT_CHUNK_SIZE_16,
			wavIO.KEY_AUDIO_FMT: wavIO.WAV_FMT_PCM,
			baseIO.CORE_KEY_NUM_CHANNELS: 2,
			baseIO.CORE_KEY_SAMPLE_RATE: 44100,
			wavIO.KEY_BYTE_RATE: 4*44100,
			wavIO.KEY_BLOCK_ALIGN: 4,
			baseIO.CORE_KEY_BIT_DEPTH: 16,
			baseIO.CORE_KEY_BYTE_DEPTH: 2,
			wavIO.KEY_SUBCHUNK2_ID: wavIO.DATA_SUBCHUNK_ID,
			wavIO.KEY_SUBCHUNK2_SIZE: 400,
			wavIO.KEY_STRUCT_MULTIPLIER: '',
			wavIO.KEY_STRUCT_FMT_CHAR: 'h',
			baseIO.CORE_KEY_SIGNED: True,
			baseIO.CORE_KEY_FMT: 'PCM'
		})
	
	def test_valid_conversion_parameters_float(self):
		"""
		Test with valid conversion parameters, converting to a float file.
		"""
		readAudioObj = wavIO.ReadWav(TEST_READ_FILE)
		reachBack = 0
		writeAudioObj = wavIO.WriteWav(TEST_WRITE_FILE, 'float', 2, 32, 44100)
		
		readAudioObj.signalParams[baseIO.CORE_KEY_SAMPLES_PER_CHANNEL] = 100
		writeAudioObj.init_header(readAudioObj, reachBack)
		
		self.assertEqual(writeAudioObj.signalParams, {
			baseIO.CORE_KEY_SAMPLES_PER_CHANNEL: 100,
			wavIO.KEY_CHUNK_ID: wavIO.RIFF_CHUNK_ID,
			wavIO.KEY_CHUNK_SIZE: 850,
			wavIO.KEY_FMT_ID: wavIO.WAVE_ID,
			wavIO.KEY_SUBCHUNK1_ID: wavIO.FMT_SUBCHUNK_ID,
			wavIO.KEY_SUBCHUNK1_SIZE: wavIO.FMT_CHUNK_SIZE_18,
			wavIO.KEY_AUDIO_FMT: wavIO.WAV_FMT_FLOAT,
			baseIO.CORE_KEY_NUM_CHANNELS: 2,
			baseIO.CORE_KEY_SAMPLE_RATE: 44100,
			wavIO.KEY_BYTE_RATE: 8*44100,
			wavIO.KEY_BLOCK_ALIGN: 8,
			baseIO.CORE_KEY_BIT_DEPTH: 32,
			baseIO.CORE_KEY_BYTE_DEPTH: 4,
			wavIO.KEY_CB_SIZE: 0,
			wavIO.KEY_SUBCHUNK2_ID: wavIO.FACT_SUBCHUNK_ID,
			wavIO.KEY_SUBCHUNK2_SIZE: 4,
			wavIO.KEY_DW_SAMPLE_LEN: 100,
			wavIO.KEY_SUBCHUNK3_ID: wavIO.DATA_SUBCHUNK_ID,
			wavIO.KEY_SUBCHUNK3_SIZE: 800,
			wavIO.KEY_STRUCT_MULTIPLIER: '',
			wavIO.KEY_STRUCT_FMT_CHAR: 'f',
			baseIO.CORE_KEY_SIGNED: True,
			baseIO.CORE_KEY_FMT: 'float'
		})


class CopyTestFilesTestMethods(unittest.TestCase):
	"""
	Methods to test WavIOEngine read and write classes by performing a simple
	copy operation on the WAVE_ test files.
	"""
	def plugin_cb(self, engineObj, sampleNestedList):
		return sampleNestedList
	
	def setUp(self):
		pass
	
	def tearDown(self):
		pass
	
	def test_copy_files(self):
		"""
		Copy each test file and test that copys match using sha1 hash.
		"""
		for readFile in os.listdir(TEST_DATA_DIR):
			with self.subTest(readFile=readFile):
				if readFile.startswith('WAVE_'):
					# override test of 8-bit, because it goes through
					# unsigned -> signed -> unsigned conversion
					if readFile == 'WAVE_PCM_2CH_44100SR_8BIT.wav':
						continue
					else:
						pass
					# Perform copy
					readFilePath = os.path.join(TEST_DATA_DIR, readFile)
					writeFile = readFile.split('.')[0] + '_AFTER.wav'
					writeFilePath = os.path.join(TEST_DATA_DIR, writeFile)
					options = {}
					self.engineObj = engine.FileToFileEngine(
												readFilePath, 
												writeFilePath, 
												algorithm=self.plugin_cb,
												options=options)
					self.engineObj.process()
					# Test that copy was successful
					readSha1 = hashlib.sha1()
					writeSha1 = hashlib.sha1()
					with open(readFilePath, 'rb') as readStream:
						readSha1.update(readStream.read())
					with open(writeFilePath, 'rb') as writeStream:
						writeSha1.update(writeStream.read())
					self.assertEqual(readSha1.hexdigest(), 
										writeSha1.hexdigest())
				else:
					pass
				
		
		
		