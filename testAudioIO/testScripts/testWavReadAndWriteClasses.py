import os
import sys
import unittest
import hashlib
PACKAGE_ROOT = '../..'
SCRIPT_DIR = os.path.dirname(os.path.realpath(os.path.join(os.getcwd(), 
	os.path.expanduser(__file__))))
PACKAGE_PATH = os.path.normpath(os.path.join(SCRIPT_DIR, PACKAGE_ROOT))
sys.path.append(PACKAGE_PATH)
from audioIO.engine import audioIOEngine as aIOe
from audioIO.engine import wavIOEngine as wIOe

TEST_DATA_DIR = os.path.normpath(os.path.dirname(os.path.dirname(os.path.abspath(__file__))) + '/testData/')
TEST_READ_FILE = os.path.normpath(os.path.abspath(os.path.join(TEST_DATA_DIR, 'test_read_audio_file.txt')))
TEST_WRITE_FILE = os.path.normpath(os.path.abspath(os.path.join(TEST_DATA_DIR, 'test_write_audio_file.txt')))


class WavIOEngineInitTestMethods(unittest.TestCase):
	"""
	Methods to test the initialization of a WavIOEngine object.
	"""
	def test_init(self):
		"""
		Test basic initialization.
		"""
		readAudioObj = wIOe.ReadWav(TEST_READ_FILE)
		writeAudioObj = wIOe.WriteWav(TEST_WRITE_FILE)
		self.assertIsInstance(readAudioObj, wIOe.ReadWav)
		self.assertIsInstance(writeAudioObj, wIOe.WriteWav)


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
			if readFile.startswith('WAVE_'):
				# Perform copy
				self.readAudioObj = wIOe.ReadWav(os.path.join(TEST_DATA_DIR, readFile))
				writeFile = readFile.split('.')[0] + '_AFTER.py'
				self.writeAudioObj = wIOe.WriteWav(os.path.join(TEST_DATA_DIR, writeFile))
				self.audioIOEngineObj = aIOe.AudioIOEngine(self.readAudioObj, self.writeAudioObj, self.plugin_cb)
				self.audioIOEngineObj.process()
				# Test that copy was successful
				readSha1 = hashlib.sha1()
				writeSha1 = hashlib.sha1()
				with open(os.path.join(TEST_DATA_DIR, readFile), 'rb') as readStream:
					readSha1.update(readStream.read())
				with open(os.path.join(TEST_DATA_DIR, writeFile), 'rb') as writeStream:
					writeSha1.update(writeStream.read())
				self.assertEqual(readSha1.hexdigest(), writeSha1.hexdigest())
			else:
				pass
				
		
		
		