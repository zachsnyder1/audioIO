import os
import sys
import unittest
import hashlib
PACKAGE_ROOT = '../..'
SCRIPT_DIR = os.path.dirname(os.path.realpath(os.path.join(os.getcwd(), 
	os.path.expanduser(__file__))))
PACKAGE_PATH = os.path.normpath(os.path.join(SCRIPT_DIR, PACKAGE_ROOT))
sys.path.append(PACKAGE_PATH)
from src.framework import audioIO as aIO
from src.framework import wavIO as wIO
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
		readAudioObj = wIO.ReadWav(TEST_READ_FILE)
		writeAudioObj = wIO.WriteWav(TEST_WRITE_FILE)
		self.assertIsInstance(readAudioObj, wIO.ReadWav)
		self.assertIsInstance(writeAudioObj, wIO.WriteWav)
	
	def test_WriteWav_conversion_init(self):
		"""
		Test initialization of write class with conversion
		parameters set to correct values.
		"""
		writeAudioObj = wIO.WriteWav(TEST_WRITE_FILE, format='PCM', 
										numChannels=2, bitDepth=16, 
										sampleRate=44100)
		self.assertIsInstance(writeAudioObj, wIO.WriteWav)
		self.assertEqual(writeAudioObj.conversion, True)
		self.assertEqual(writeAudioObj.conversionParameters, {
			aIO.CORE_KEY_FMT: 'PCM',
			aIO.CORE_KEY_NUM_CHANNELS: 2,
			aIO.CORE_KEY_BIT_DEPTH: 16,
			aIO.CORE_KEY_BYTE_DEPTH: 2,
			aIO.CORE_KEY_SAMPLE_RATE: 44100
		})



class WavInitHeaderTestMethods(unittest.TestCase):
	"""
	Methods to test the WriteWav.init_header() function.
	"""
	def test_valid_conversion_parameters_PCM(self):
		"""
		Test with valid conversion parameters, converting to a PCM file.
		"""
		readAudioObj = wIO.ReadWav(TEST_READ_FILE)
		reachBack = 0
		writeAudioObj = wIO.WriteWav(TEST_WRITE_FILE, format='PCM', 
										numChannels=2, bitDepth=16, 
										sampleRate=44100)
		
		readAudioObj.headerDict[aIO.CORE_KEY_SAMPLES_PER_CHANNEL] = 100
		writeAudioObj.init_header(readAudioObj, reachBack)
		
		self.assertEqual(writeAudioObj.headerDict, {
			aIO.CORE_KEY_SAMPLES_PER_CHANNEL: 100,
			writeAudioObj.keyChunkId: writeAudioObj.riffChunkId,
			writeAudioObj.keyChunkSize: 444,
			writeAudioObj.keyFormatId: writeAudioObj.waveId,
			writeAudioObj.keySubchunk1Id: writeAudioObj.fmtSubchunkId,
			writeAudioObj.keySubchunk1Size: writeAudioObj.fmtChunkSize16,
			writeAudioObj.keyAudioFmt: writeAudioObj.wavFmtPCM,
			aIO.CORE_KEY_NUM_CHANNELS: 2,
			aIO.CORE_KEY_SAMPLE_RATE: 44100,
			writeAudioObj.keyByteRate: 4*44100,
			writeAudioObj.keyBlockAlign: 4,
			aIO.CORE_KEY_BIT_DEPTH: 16,
			aIO.CORE_KEY_BYTE_DEPTH: 2,
			writeAudioObj.keySubchunk2Id: writeAudioObj.dataSubchunkId,
			writeAudioObj.keySubchunk2Size: 400,
			writeAudioObj.keyStructMultiplier: '',
			writeAudioObj.keyStructFmtChar: 'h',
			aIO.CORE_KEY_SIGNED: True,
			aIO.CORE_KEY_FMT: 'PCM'
		})
	
	def test_valid_conversion_parameters_float(self):
		"""
		Test with valid conversion parameters, converting to a float file.
		"""
		readAudioObj = wIO.ReadWav(TEST_READ_FILE)
		reachBack = 0
		writeAudioObj = wIO.WriteWav(TEST_WRITE_FILE, format='float', 
										numChannels=2, bitDepth=32, 
										sampleRate=44100)
		
		readAudioObj.headerDict[aIO.CORE_KEY_SAMPLES_PER_CHANNEL] = 100
		writeAudioObj.init_header(readAudioObj, reachBack)
		
		self.assertEqual(writeAudioObj.headerDict, {
			aIO.CORE_KEY_SAMPLES_PER_CHANNEL: 100,
			writeAudioObj.keyChunkId: writeAudioObj.riffChunkId,
			writeAudioObj.keyChunkSize: 858,
			writeAudioObj.keyFormatId: writeAudioObj.waveId,
			writeAudioObj.keySubchunk1Id: writeAudioObj.fmtSubchunkId,
			writeAudioObj.keySubchunk1Size: writeAudioObj.fmtChunkSize18,
			writeAudioObj.keyAudioFmt: writeAudioObj.wavFmtFloat,
			aIO.CORE_KEY_NUM_CHANNELS: 2,
			aIO.CORE_KEY_SAMPLE_RATE: 44100,
			writeAudioObj.keyByteRate: 8*44100,
			writeAudioObj.keyBlockAlign: 8,
			aIO.CORE_KEY_BIT_DEPTH: 32,
			aIO.CORE_KEY_BYTE_DEPTH: 4,
			writeAudioObj.keyCbSize: 0,
			writeAudioObj.keySubchunk2Id: writeAudioObj.factSubchunkId,
			writeAudioObj.keySubchunk2Size: 4,
			writeAudioObj.keyDwSampleLength: 100,
			writeAudioObj.keySubchunk3Id: writeAudioObj.dataSubchunkId,
			writeAudioObj.keySubchunk3Size: 800,
			writeAudioObj.keyStructMultiplier: '',
			writeAudioObj.keyStructFmtChar: 'f',
			aIO.CORE_KEY_SIGNED: True,
			aIO.CORE_KEY_FMT: 'float'
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
					self.readAudioObj = wIO.ReadWav(os.path.join(
															TEST_DATA_DIR, 
															readFile))
					writeFile = readFile.split('.')[0] + '_AFTER.py'
					self.writeAudioObj = wIO.WriteWav(os.path.join(
															TEST_DATA_DIR, 
															writeFile))
					self.engineObj = engine.Engine(self.readAudioObj, 
												self.writeAudioObj, 
												self.plugin_cb)
					self.engineObj.process()
					# Test that copy was successful
					readSha1 = hashlib.sha1()
					writeSha1 = hashlib.sha1()
					with open(os.path.join(TEST_DATA_DIR, 
											readFile), 'rb') as readStream:
						readSha1.update(readStream.read())
					with open(os.path.join(TEST_DATA_DIR, 
											writeFile), 'rb') as writeStream:
						writeSha1.update(writeStream.read())
					self.assertEqual(readSha1.hexdigest(), 
										writeSha1.hexdigest())
				else:
					pass
				
		
		
		