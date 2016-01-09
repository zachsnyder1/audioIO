import os
import sys
import unittest
import hashlib
PACKAGE_ROOT = '../..'
SCRIPT_DIR = os.path.dirname(os.path.realpath(os.path.join(os.getcwd(), 
	os.path.expanduser(__file__))))
PACKAGE_PATH = os.path.normpath(os.path.join(SCRIPT_DIR, PACKAGE_ROOT))
sys.path.append(PACKAGE_PATH)
from src.framework import wavIO as wIO
from src.framework import audioIO as aIO
from src.framework import engine

TEST_DATA_DIR = os.path.normpath(
					os.path.dirname(
					os.path.dirname(
					os.path.abspath(__file__))) + '/testData/')
TEST_WRITE_FILE = os.path.normpath(
					os.path.abspath(
					os.path.join(TEST_DATA_DIR, 'test_write_audio_file.txt')))



class EngineInitTestMethods(unittest.TestCase):
	"""
	Methods to test the initialization of an Engine object.
	"""
	def setUp(self):
		self.testReadFile = None
		for file in os.listdir(TEST_DATA_DIR):
			if file.startswith('WAVE_'):
				self.testReadFile = os.path.join(TEST_DATA_DIR, file)
				break
			else:
				pass
		if self.testReadFile == None:
			self.fail("no 'WAVE_*' file in testData/ dir")
		else:
			pass
	
	def plugin_cb(self, engineObj, sampleNestedList):
		return sampleNestedList
	
	def test_init(self):
		"""
		Test basic initialization.
		"""
		readAudioObj = wIO.ReadWav(self.testReadFile)
		writeAudioObj = wIO.WriteWav(TEST_WRITE_FILE)
		engineObj = engine.Engine(readAudioObj, writeAudioObj, self.plugin_cb)
		self.assertIsInstance(engineObj, engine.Engine)


class EngineConversionTestMethods(unittest.TestCase):
	"""
	Methods to test the conversion of files during processing.
	"""
	def assert_int_cb(self, engineObj, sampleNestedList):
		"""
		Assert that:
		
		1) Data is integer format
		
		2) First sample is negative
		"""
		self.assertIsInstance(sampleNestedList[0][0], int)
		self.assertTrue(sampleNestedList[0][0] < 0)
		return sampleNestedList
	
	def assert_float_cb(self, engineObj, sampleNestedList):
		"""
		Assert that data is floating point format.
		"""
		self.assertIsInstance(sampleNestedList[0][0], float)
		return sampleNestedList
			
	def test_conversions(self):
		"""
		Tests conversions in audio format by converting test data.  The test
		data first need to be made using a make*.py script and associated .csv
		file in the makeTestData/ directory.  In order for the assertions in
		the callbacks (above) to work, the first sample in each test data file
		needs to be negative (if signed), or less than half the MAX value of
		the data type (if unsigned).  Also, there should be fewer samples in
		the file than fit in the buffer size, because the assertion will
		be performed for each buffer-full of data...
		"""
		# parameter nest for subtests
		# paramList[0]  ==>  The test read file (a certain format)
		# paramList[1]  ==>  The test write file
		# paramList[2]  ==>  Format of the write file
		# paramList[3]  ==>  Bit depth of the write file
		# paramList[4]  ==>  Data format passed to algorithm
		# paramList[5]  ==>  The assertion to perform (inside the algorithm)
		# paramList[6]  ==>  The assertion to perform (testing the write data)
		paramNest = [
			[
				'ENGINE_PCM_2CH_44100SR_16BIT.wav', 
				'ENGINE_PCM16_to_FLOAT32.wav',
				'float',
				32,
				'PCM',
				self.assert_int_cb,
				self.assert_float_cb
			],
			[
				'ENGINE_PCM_2CH_44100SR_16BIT.wav', 
				'ENGINE_PCM16_to_FLOAT32.wav',
				'float',
				32,
				'float',
				self.assert_float_cb,
				self.assert_float_cb
			],
			[
				'ENGINE_PCM_2CH_44100SR_16BIT.wav', 
				'ENGINE_PCM16_to_FLOAT64.wav',
				'float',
				64,
				'PCM',
				self.assert_int_cb,
				self.assert_float_cb
			],
			[
				'ENGINE_PCM_2CH_44100SR_16BIT.wav', 
				'ENGINE_PCM16_to_FLOAT64.wav',
				'float',
				64,
				'float',
				self.assert_float_cb,
				self.assert_float_cb
			],
			[
				'ENGINE_PCM_2CH_44100SR_16BIT.wav', 
				'ENGINE_PCM16_to_PCM8.wav',
				'PCM',
				8,
				'PCM',
				self.assert_int_cb,
				self.assert_int_cb
			],
			[
				'ENGINE_PCM_2CH_44100SR_16BIT.wav', 
				'ENGINE_PCM16_to_PCM8.wav',
				'PCM',
				8,
				'float',
				self.assert_float_cb,
				self.assert_int_cb
			],
			[
				'ENGINE_PCM_2CH_44100SR_8BIT.wav', 
				'ENGINE_PCM8_to_FLOAT32.wav',
				'float',
				32,
				'PCM',
				self.assert_int_cb,
				self.assert_float_cb
			],
			[
				'ENGINE_PCM_2CH_44100SR_8BIT.wav', 
				'ENGINE_PCM8_to_FLOAT32.wav',
				'float',
				32,
				'float',
				self.assert_float_cb,
				self.assert_float_cb
			],
			[
				'ENGINE_PCM_2CH_44100SR_8BIT.wav', 
				'ENGINE_PCM8_to_FLOAT64.wav',
				'float',
				64,
				'PCM',
				self.assert_int_cb,
				self.assert_float_cb
			],
			[
				'ENGINE_PCM_2CH_44100SR_8BIT.wav', 
				'ENGINE_PCM8_to_FLOAT64.wav',
				'float',
				64,
				'float',
				self.assert_float_cb,
				self.assert_float_cb
			],
			[
				'ENGINE_PCM_2CH_44100SR_8BIT.wav', 
				'ENGINE_PCM8_to_PCM16.wav',
				'PCM',
				16,
				'PCM',
				self.assert_int_cb,
				self.assert_int_cb
			],
			[
				'ENGINE_PCM_2CH_44100SR_8BIT.wav', 
				'ENGINE_PCM8_to_PCM16.wav',
				'PCM',
				16,
				'float',
				self.assert_float_cb,
				self.assert_int_cb
			],
			[
				'ENGINE_FLOAT_2CH_44100SR_32BIT.wav',
				'ENGINE_FLOAT32_to_PCM16.wav',
				'PCM',
				16,
				'float',
				self.assert_float_cb,
				self.assert_int_cb
			],
			[
				'ENGINE_FLOAT_2CH_44100SR_32BIT.wav',
				'ENGINE_FLOAT32_to_PCM16.wav',
				'PCM',
				16,
				'PCM',
				self.assert_int_cb,
				self.assert_int_cb
			],
			[
				'ENGINE_FLOAT_2CH_44100SR_32BIT.wav',
				'ENGINE_FLOAT32_to_PCM8.wav',
				'PCM',
				8,
				'float',
				self.assert_float_cb,
				self.assert_int_cb
			],
			[
				'ENGINE_FLOAT_2CH_44100SR_32BIT.wav',
				'ENGINE_FLOAT32_to_PCM8.wav',
				'PCM',
				8,
				'PCM',
				self.assert_int_cb,
				self.assert_int_cb
			],
			[
				'ENGINE_FLOAT_2CH_44100SR_64BIT.wav',
				'ENGINE_FLOAT64_to_PCM16.wav',
				'PCM',
				16,
				'float',
				self.assert_float_cb,
				self.assert_int_cb
			],
			[
				'ENGINE_FLOAT_2CH_44100SR_64BIT.wav',
				'ENGINE_FLOAT64_to_PCM16.wav',
				'PCM',
				16,
				'PCM',
				self.assert_int_cb,
				self.assert_int_cb
			],
			[
				'ENGINE_FLOAT_2CH_44100SR_64BIT.wav',
				'ENGINE_FLOAT64_to_PCM8.wav',
				'PCM',
				8,
				'float',
				self.assert_float_cb,
				self.assert_int_cb
			],
			[
				'ENGINE_FLOAT_2CH_44100SR_64BIT.wav',
				'ENGINE_FLOAT64_to_PCM8.wav',
				'PCM',
				8,
				'PCM',
				self.assert_int_cb,
				self.assert_int_cb
			],
		]
		for paramList in paramNest:
			with self.subTest(params = paramList):
				# set read and write files	
				readFile = os.path.join(TEST_DATA_DIR, paramList[0])
				writeFile = os.path.join(TEST_DATA_DIR, paramList[1])
				postTestFile = os.path.join(TEST_DATA_DIR, 'temp1.wav')
				# init objects
				readAudioObj = wIO.ReadWav(readFile)
				writeAudioObj = wIO.WriteWav(writeFile, 
												format=paramList[2], 
												bitDepth=paramList[3])
				engineObj = engine.Engine(readAudioObj, writeAudioObj, 
									  paramList[5], format=paramList[4])
				engineObj.process()
				# Test the wrapper function
				readAudioObj = wIO.ReadWav(writeFile)
				writeAudioObj = wIO.WriteWav(postTestFile)
				engineObj = engine.Engine(readAudioObj, writeAudioObj, 
										paramList[6])
				engineObj.process()
		
		
		
class FloatPcmConversionsTestMethods(unittest.TestCase):
	"""
	Methods to test the Engine helper methods that convert a nested array
	of data between float and PCM.
	"""
	def plugin_cb(self, engineObj, sampleNestedList):
		return sampleNestedList
	
	def setUp(self):
		self.testReadFile = None
		for file in os.listdir(TEST_DATA_DIR):
			if file.startswith('WAVE_'):
				self.testReadFile = os.path.join(TEST_DATA_DIR, file)
				break
			else:
				pass
		if self.testReadFile == None:
			self.fail("no 'WAVE_*' file in testData/ dir")
		else:
			pass
		readAudioObj = wIO.ReadWav(self.testReadFile)
		writeAudioObj = wIO.WriteWav(TEST_WRITE_FILE)
		self.engineObj = engine.Engine(readAudioObj, writeAudioObj, 
									self.plugin_cb)
	
	def test_float_to_pcm(self):
		"""
		Test the float to PCM conversion method.
		"""
		paramNest = [
			[
				[[-1.0], [-0.5], [0.0], [0.5], [1.0]], 
				16, 
				True, 
				[[-32768], [-16384], [0], [16383], [32767]]
			],
			[
				[[-1.0], [-0.5], [0.0], [0.5], [1.0]], 
				16, 
				False, 
				[[0], [16383], [32767], [49151], [65535]]
			],
			[
				[[-1.0], [-0.5], [0.0], [0.5], [1.0]], 
				8, 
				True, 
				[[-128], [-64], [0], [63], [127]]
			],
			[
				[[-1.0], [-0.5], [0.0], [0.5], [1.0]], 
				8, 
				False, 
				[[0], [63], [127], [191], [255]]
			]
		]
		for paramList in paramNest:
			converted = self.engineObj.float_to_pcm(paramList[0], 
													paramList[1], 
													paramList[2])
			for i in range(len(converted)):
				with self.subTest(params=paramList):
					tolerance = 0
					self.assertTrue(tolerance >= 
									abs(converted[i][0] - paramList[3][i][0]))
	
	def test_pcm_to_float(self):
		"""
		Test the PCM to float conversion method.
		"""
		paramNest = [
			[
				[[-32768], [-16384], [0], [16383], [32767]], 
				16, 
				True, 
				[[-1.0], [-0.5], [0.0], [0.5], [1.0]]
			],
			[
				[[0], [16383], [32767], [49151], [65535]],
				16, 
				False, 
				[[-1.0], [-0.5], [0.0], [0.5], [1.0]]
			],
			[
				[[-128], [-64], [0], [63], [127]],
				8, 
				True, 
				[[-1.0], [-0.5], [0.0], [0.5], [1.0]]
			],
			[
				[[0], [63], [127], [191], [255]], 
				8, 
				False, 
				[[-1.0], [-0.5], [0.0], [0.5], [1.0]]
			]
		]
		for paramList in paramNest:
			converted = self.engineObj.pcm_to_float(paramList[0], 
													paramList[1], 
													paramList[2])
			for i in range(len(converted)):
				reference = (paramList[3][i][0], converted[1][0])
				with self.subTest(expected_actual=reference):
					tolerance = 0.01
					self.assertTrue(tolerance > 
									abs(converted[i][0] - paramList[3][i][0]))
	
	
class ClipTestMethods(unittest.TestCase):
	"""
	Methods to test the Engine.clip_float() and Engine.clip_pcm()
	functions.
	"""
	def plugin_cb(self, engineObj, sampleNestedList):
		return sampleNestedList
	
	def setUp(self):
		self.testReadFile = None
		for file in os.listdir(TEST_DATA_DIR):
			if file.startswith('WAVE_'):
				self.testReadFile = os.path.join(TEST_DATA_DIR, file)
				break
			else:
				pass
		if self.testReadFile == None:
			self.fail("no 'WAVE_*' file in testData/ dir")
		else:
			pass
		readAudioObj = wIO.ReadWav(self.testReadFile)
		writeAudioObj = wIO.WriteWav(TEST_WRITE_FILE)
		self.engineObj = engine.Engine(readAudioObj, writeAudioObj, 
									self.plugin_cb)
	
	def test_clip_float(self):
		"""
		Test that Engine.clip_float() properly clips a nested list
		of float values.
		"""
		nest = [
			[-10.0, 10.0],
			[-2.0, 2.0],
			[-1.0000000001, 1.0000000001],
			[-1.0, 1],
			[-0.5, 0.5],
			[0.0, 0.0]
		]
		expected = [
			[-1.0, 1.0],
			[-1.0, 1.0],
			[-1.0, 1.0],
			[-1.0, 1.0],
			[-0.5, 0.5],
			[0.0, 0.0]
		]
		clippedNest = self.engineObj.clip_float(nest)
		self.assertEqual(clippedNest, expected)
	
	def test_clip_pcm(self):
		"""
		Test that Engine.clip_pcm() properly clips a nested list
		of PCM values of various bit depth.
		"""
		paramNest = [
			[
				8,
				[
					[-4253, 4253],
					[-255, 255],
					[-129, 128],
					[-64, 63],
					[0, 0]
				],
				[
					[-128, 127],
					[-128, 127],
					[-128, 127],
					[-64, 63],
					[0, 0]
				],
			],
			[
				16,
				[
					[-425326, 425326],
					[-65536, 65536],
					[-32769, 32768],
					[-16384, 16383],
					[0, 0]
				],
				[
					[-32768, 32767],
					[-32768, 32767],
					[-32768, 32767],
					[-16384, 16383],
					[0, 0]
				],
			],
			[
				24,
				[
					[-1677721642, 1677721642],
					[-16777216, 16777216],
					[-8388609, 8388608],
					[-16384, 16383],
					[0, 0]
				],
				[
					[-8388608, 8388607],
					[-8388608, 8388607],
					[-8388608, 8388607],
					[-16384, 16383],
					[0, 0]
				],
			],
		]
		
		for paramList in paramNest:
			with self.subTest(params=paramList):
				clippedNest = self.engineObj.clip_pcm(paramList[1], 
														paramList[0])
				self.assertEqual(clippedNest, paramList[2])
	
	
class ReachBackTestMethods(unittest.TestCase):
	"""
	Methods to test the reach back functionality of the Engine
	class.
	"""
	dataNest = []  # For accumulating nested sample data over
				   # multiple algorithm calls
	
	def plugin_cb(self, pIObj, sampleNestedList):
		return sampleNestedList
	
	def reachback_cb_closure(self, reachBack):
		"""
		For testing the Engine.reach_back() function.  Closure
		allows assignment of the reachBack value.
		"""
		def cb(pIObj, sampleNestedList):
			for block in range(len(sampleNestedList)):
				for channel in range(len(sampleNestedList[block])):
					sampleNestedList[block][channel] += \
						pIObj.reach_back(reachBack, block, channel)
				self.dataNest.append(sampleNestedList[block])
			return sampleNestedList
		self.reachback_cb = cb		
	
	def test_wav_size_adjustment(self):
		"""
		Test that WriteWav.init_header() function properly
		augments the RIFF chunk size and Data subchunk size
		according to the reachBack size.
		"""
		paramNest = [
			[
				'ENGINE_FLOAT_2CH_44100SR_64BIT.wav',
				1000
			],
			[
				'ENGINE_FLOAT_2CH_44100SR_64BIT.wav',
				10
			],
			[
				'ENGINE_FLOAT_2CH_44100SR_32BIT.wav',
				1000
			],
			[
				'ENGINE_FLOAT_2CH_44100SR_32BIT.wav',
				10
			],
			[
				'ENGINE_PCM_2CH_44100SR_8BIT.wav',
				1000
			],
			[
				'ENGINE_PCM_2CH_44100SR_8BIT.wav',
				10
			],
			[
				'ENGINE_PCM_2CH_44100SR_16BIT.wav',
				1000
			],
			[
				'ENGINE_PCM_2CH_44100SR_16BIT.wav',
				10
			],
		]
		for paramList in paramNest:
			with self.subTest(params = paramList):
				# set read and write files	
				readFile = os.path.join(TEST_DATA_DIR, paramList[0])
				writeFile = os.path.join(TEST_DATA_DIR, 'temp1.wav')
				# init objects
				readAudioObj = wIO.ReadWav(readFile)
				writeAudioObj = wIO.WriteWav(writeFile)
				engineObj = engine.Engine(readAudioObj, writeAudioObj, 
									  self.plugin_cb, reachBack=paramList[1])
				
				# Expected difference in size
				sizeDiff = paramList[1] * \
					engineObj.readObj.headerDict[
						aIO.CORE_KEY_BYTE_DEPTH] * \
					engineObj.readObj.headerDict[
						aIO.CORE_KEY_NUM_CHANNELS]
				# Store read/write chunk size
				readChunkSize = \
					engineObj.readObj.headerDict[
						wIO.KEY_CHUNK_SIZE]
				writeChunkSize = \
					engineObj.writeObj.headerDict[
						wIO.KEY_CHUNK_SIZE]
				# Store read/write data subchunk size
				if engineObj.readObj.headerDict[
						wIO.KEY_SUBCHUNK2_ID] == \
						wIO.DATA_SUBCHUNK_ID:
					readDataSubChunkSize = \
						engineObj.readObj.headerDict[
							wIO.KEY_SUBCHUNK2_SIZE]
				else:
					readDataSubChunkSize = \
						engineObj.readObj.headerDict[
							wIO.KEY_SUBCHUNK3_SIZE]
				if engineObj.writeObj.headerDict[
						wIO.KEY_SUBCHUNK2_ID] == \
						wIO.DATA_SUBCHUNK_ID:
					writeDataSubChunkSize = \
						engineObj.writeObj.headerDict[
							wIO.KEY_SUBCHUNK2_SIZE]
				else:
					writeDataSubChunkSize = \
						engineObj.writeObj.headerDict[
							wIO.KEY_SUBCHUNK3_SIZE]
				# ASSERTIONS:
				self.assertEqual(writeChunkSize, 
								 (readChunkSize + sizeDiff))
				self.assertEqual(writeDataSubChunkSize,
								 (readDataSubChunkSize + sizeDiff))
				
				
	def test_reach_back(self):
		"""
		Test the reach_back() method.
		"""
		self.maxDiff = None
		paramNest = [
			[
				'ENGINE_PCM_2CH_44100SR_16BIT.wav',
				'reachBack16bit_2.wav',
				2,
				[
					[-1, 0],
					[1, 1],
					[1, 2],
					[4, 4],
					[6, 6],
					[8, 8],
					[4, 9],
					[6, 9],
					[2, 8],
					[4, 6],
					[6, 4],
					[8, 2],
					[4, 1],
					[5, 0]
				]
			],
			[
				'ENGINE_PCM_2CH_44100SR_16BIT.wav',
				'reachBack16bit_5.wav',
				5,
				[
					[-1, 0],
					[1, 1],
					[2, 2],
					[3, 3],
					[4, 4],
					[4, 5],
					[1, 6],
					[3, 6],
					[5, 6],
					[7, 6],
					[9, 6],
					[5, 5],
					[1, 4],
					[2, 3],
					[3, 2],
					[4, 1],
					[5, 0]
				]
			],
			[
				'ENGINE_PCM_2CH_44100SR_16BIT.wav',
				'reachBack16bit_20.wav',
				20,
				[
					[-1, 0],
					[1, 1],
					[2, 2],
					[3, 3],
					[4, 4],
					[5, 5],
					[0, 5],
					[1, 4],
					[2, 3],
					[3, 2],
					[4, 1],
					[5, 0],
					[0, 0],
					[0, 0],
					[0, 0],
					[0, 0],
					[0, 0],
					[0, 0],
					[0, 0],
					[0, 0],
					[-1, 0],
					[1, 1],
					[2, 2],
					[3, 3],
					[4, 4],
					[5, 5],
					[0, 5],
					[1, 4],
					[2, 3],
					[3, 2],
					[4, 1],
					[5, 0]
				]
			],
			[
				'ENGINE_FLOAT_2CH_44100SR_32BIT.wav',
				'reachBack32bit_2.wav',
				2,
				[
					[-0.10000000149011612, 0.0],
					[0.10000000149011612, 0.10000000149011612],
					[0.10000000149011612, 0.20000000298023224],
					[0.4000000134110451, 0.4000000134110451],
					[0.6000000089406967, 0.6000000089406967],
					[0.800000011920929, 0.800000011920929],
					[0.4000000059604645, 0.9000000059604645],
					[0.6000000014901161, 0.9000000059604645],
					[0.20000000298023224, 0.800000011920929],
					[0.4000000134110451, 0.6000000089406967],
					[0.6000000089406967, 0.4000000134110451],
					[0.800000011920929, 0.20000000298023224],
					[0.4000000059604645, 0.10000000149011612],
					[0.5, 0.0]
				]
			],
			[
				'ENGINE_FLOAT_2CH_44100SR_32BIT.wav',
				'reachBack32bit_5.wav',
				5,
				[
					[-0.10000000149011612, 0.0],
					[0.10000000149011612, 0.10000000149011612],
					[0.20000000298023224, 0.20000000298023224],
					[0.30000001192092896, 0.30000001192092896],
					[0.4000000059604645, 0.4000000059604645],
					[0.3999999985098839, 0.5],
					[0.10000000149011612, 0.6000000014901161],
					[0.30000000447034836, 0.6000000089406967],
					[0.5000000149011612, 0.6000000238418579],
					[0.7000000178813934, 0.6000000089406967],
					[0.9000000059604645, 0.6000000014901161],
					[0.5, 0.5],
					[0.10000000149011612, 0.4000000059604645],
					[0.20000000298023224, 0.30000001192092896],
					[0.30000001192092896, 0.20000000298023224],
					[0.4000000059604645, 0.10000000149011612],
					[0.5, 0.0]
				]
			],
			[
				'ENGINE_FLOAT_2CH_44100SR_32BIT.wav',
				'reachBack32bit_20.wav',
				20,
				[
					[-0.10000000149011612, 0.0],
					[0.10000000149011612, 0.10000000149011612],
					[0.20000000298023224, 0.20000000298023224],
					[0.30000001192092896, 0.30000001192092896],
					[0.4000000059604645, 0.4000000059604645],
					[0.5, 0.5],
					[0.0, 0.5],
					[0.10000000149011612, 0.4000000059604645],
					[0.20000000298023224, 0.30000001192092896],
					[0.30000001192092896, 0.20000000298023224],
					[0.4000000059604645, 0.10000000149011612],
					[0.5, 0.0],
					[0.0, 0.0],
					[0.0, 0.0],
					[0.0, 0.0],
					[0.0, 0.0],
					[0.0, 0.0],
					[0.0, 0.0],
					[0.0, 0.0],
					[0.0, 0.0],
					[-0.10000000149011612, 0.0],
					[0.10000000149011612, 0.10000000149011612],
					[0.20000000298023224, 0.20000000298023224],
					[0.30000001192092896, 0.30000001192092896],
					[0.4000000059604645, 0.4000000059604645],
					[0.5, 0.5],
					[0.0, 0.5],
					[0.10000000149011612, 0.4000000059604645],
					[0.20000000298023224, 0.30000001192092896],
					[0.30000001192092896, 0.20000000298023224],
					[0.4000000059604645, 0.10000000149011612],
					[0.5, 0.0]
				]
			]
		]
		for paramList in paramNest:
			with self.subTest(params = paramList):
				# set read and write files	
				readFile = os.path.join(TEST_DATA_DIR, paramList[0])
				writeFile = os.path.join(TEST_DATA_DIR, paramList[1])
				# set reachback_cb using closure
				self.reachback_cb_closure(paramList[2])
				# init objects
				readAudioObj = wIO.ReadWav(readFile)
				writeAudioObj = wIO.WriteWav(writeFile)
				engineObj = engine.Engine(readAudioObj, writeAudioObj, 
									  self.reachback_cb, 
									  reachBack=paramList[2])
				engineObj.process()
				# Assertion:
				self.assertEqual(self.dataNest, paramList[3])
				self.dataNest.clear()
		
		
		
	
	
	