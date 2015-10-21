import os
import sys
import unittest
PACKAGE_ROOT = '../..'
SCRIPT_DIR = os.path.dirname(os.path.realpath(os.path.join(os.getcwd(), 
	os.path.expanduser(__file__))))
PACKAGE_PATH = os.path.normpath(os.path.join(SCRIPT_DIR, PACKAGE_ROOT))
sys.path.append(PACKAGE_PATH)
from audioIO.engine import audioIOEngine as aIOe

TEST_DATA_DIR = os.path.normpath(os.path.dirname(os.path.dirname(os.path.abspath(__file__))) + '/testData/')
TEST_READ_FILE = os.path.normpath(os.path.abspath(os.path.join(TEST_DATA_DIR, 'test_read_audio_file.txt')))
TEST_WRITE_FILE = os.path.normpath(os.path.abspath(os.path.join(TEST_DATA_DIR, 'test_write_audio_file.txt')))



class AudioIOEngineInitTestMethods(unittest.TestCase):
	"""
	Methods to test the initialization of an AudioIOEngine object.
	"""
	def plugin_cb(self, engineObj, sampleNestedList):
		return sampleNestedList
	
	def test_init(self):
		"""
		Test basic initialization.
		"""
		readAudioObj = aIOe.ReadAudio(TEST_READ_FILE)
		writeAudioObj = aIOe.WriteAudio(TEST_WRITE_FILE)
		audioIOEngineObj = aIOe.AudioIOEngine(readAudioObj, writeAudioObj, self.plugin_cb)
		self.assertIsInstance(audioIOEngineObj, aIOe.AudioIOEngine)
		

class ProcessTestMethods(unittest.TestCase):
	"""
	Methods to test the AudioIOEngine.process() function.
	"""
	def plugin_cb(self, engineObj, sampleNestedList):
		return sampleNestedList
	
	def setUp(self):
		# Initialize an engine object
		self.readAudioObj = aIOe.ReadAudio(TEST_READ_FILE)
		self.writeAudioObj = aIOe.WriteAudio(TEST_WRITE_FILE)
		self.audioIOEngineObj = aIOe.AudioIOEngine(self.readAudioObj, self.writeAudioObj, self.plugin_cb)
		# Write data to the read file
		with open(TEST_READ_FILE, 'wb') as writeStream:
			writeStream.truncate()
			writeBin = bytearray()
			for i in range(self.readAudioObj.samplesPerBuffer - 1):
				writeBin += b'\x00'
			for i in range(100):
				writeStream.write(writeBin)
		# Set necessary meta info elements
		self.readAudioObj.headerLen = 0
		self.readAudioObj.headerDict['blockAlign'] = 1
	
	def tearDown(self):
		pass
	
	def test_process(self):
		self.audioIOEngineObj.process()
		self.assertTrue(True)