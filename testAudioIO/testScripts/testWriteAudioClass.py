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
TEST_WRITE_FILE = os.path.normpath(os.path.abspath(os.path.join(TEST_DATA_DIR, 'test_write_audio_file.txt')))



class WriteAudioInitTestMethods(unittest.TestCase):
	"""
	Methods to test the initialization of a WriteAudio object.
	"""
	def test_init(self):
		writeAudioObj = aIOe.WriteAudio(TEST_WRITE_FILE)
		self.assertIsInstance(writeAudioObj, aIOe.WriteAudio)


class PackAndWriteTestMethods(unittest.TestCase):
	"""
	Methods to test the WriteAudio.pack_and_write() funciton.
	"""
	def setUp(self):
		self.writeAudioObj = aIOe.WriteAudio(TEST_WRITE_FILE)
	
	def tearDown(self):
		pass
	
	def test_pack_and_write_utf(self):
		"""
		Test that WriteAudio.pack_and_write() correctly packs and
		writes UTF-8 strings of various length and endianness.
		"""
		paramNestedList = [
			['RIFF', 'little'],
			['RIFF', 'big'],
			['WAVE', 'little'],
			['WAVE', 'big'],
			['foo', 'little'],
			['foo', 'big'],
			['bar', 'little'], 
			['bar', 'little'],
			['arandomstring', 'little'],
			['arandomstring', 'big']
		]
		
		for parameterList in paramNestedList:
			with self.subTest(utf_str = parameterList):
				# set headerDict['test']
				self.writeAudioObj.headerDict['test'] = parameterList[0]
				# handle endianness
				if parameterList[1] == 'little':
					packStr = self.writeAudioObj.packLittleUTF
				elif parameterList[1] == 'big':
					packStr = self.writeAudioObj.packBigUTF
				# write utf to file
				with open(TEST_WRITE_FILE, 'wb') as writeStream:
					writeStream.truncate()
					self.writeAudioObj.pack_and_write(writeStream, (
						(packStr, 'test', len(parameterList[0])),
					))
				# read utf
				binary = bytearray()
				with open(TEST_WRITE_FILE, 'rb') as readStream:
					binary += readStream.read(len(parameterList[0]))
				if packStr == self.writeAudioObj.packBigUTF:
					self.assertEqual(self.writeAudioObj.headerDict['test'], binary.decode('utf-8'))
				elif packStr == self.writeAudioObj.packLittleUTF:
					self.assertEqual(self.writeAudioObj.headerDict['test'], binary.decode('utf-8')[::-1])
					
	def test_pack_and_write_int(self):
		"""
		Test that WriteAudio.pack_and_write() correctly packs and writes
		integers of various length, endianness, and signed/not-signed.
		"""
		paramNestedList = [
			[1, 'little', True],
			[1, 'little', False],
			[1, 'big', True],
			[1, 'big', False],
			[2, 'little', True],
			[2, 'little', False],
			[2, 'big', True],
			[2, 'big', False],
			[4, 'little', True],
			[4, 'little', False],
			[4, 'big', True],
			[4, 'big', False]
		]
		
		for parameterList in paramNestedList:
			with self.subTest(numBytes_byteorder_signed = parameterList):
				# set headerDict['test']
				self.writeAudioObj.headerDict['test'] = int((2**((parameterList[0]*8) - 1)) - 1)
				# handle endianness
				if parameterList[1] == 'little' and parameterList[2] == True:
					packStr = self.writeAudioObj.packLittleINT
				elif parameterList[1] == 'little' and parameterList[2] == False:
					packStr = self.writeAudioObj.packLittleUINT
				elif parameterList[1] == 'big' and parameterList[2] == True:
					packStr = self.writeAudioObj.packBigINT
				elif parameterList[1] == 'big' and parameterList[2] == False:
					packStr = self.writeAudioObj.packBigUINT
				# write utf to file
				with open(TEST_WRITE_FILE, 'wb') as writeStream:
					writeStream.truncate()
					self.writeAudioObj.pack_and_write(writeStream, (
						(packStr, 'test', parameterList[0]),
					))
				# read int
				binary = bytearray()
				with open(TEST_WRITE_FILE, 'rb') as readStream:
					binary += readStream.read(parameterList[0])
				# assert
				if packStr == self.writeAudioObj.packLittleINT:
					self.assertEqual(self.writeAudioObj.headerDict['test'], int.from_bytes(binary, byteorder='little', signed=True))
				elif packStr == self.writeAudioObj.packLittleUINT:
					self.assertEqual(self.writeAudioObj.headerDict['test'], int.from_bytes(binary, byteorder='little', signed=False))
				elif packStr == self.writeAudioObj.packBigINT:
					self.assertEqual(self.writeAudioObj.headerDict['test'], int.from_bytes(binary, byteorder='big', signed=True))
				elif packStr == self.writeAudioObj.packBigUINT:
					self.assertEqual(self.writeAudioObj.headerDict['test'], int.from_bytes(binary, byteorder='big', signed=False))

	def test_pack_multiple(self):
		"""
		Test that WriteAudio.pack_and_write() correctly packs and writes
		multiple values.
		"""
		paramNestedList = [
			[1, 'little', True],
			[1, 'little', False],
			[1, 'big', True],
			[1, 'big', False],
			[2, 'little', True],
			[2, 'little', False],
			[2, 'big', True],
			[2, 'big', False],
			[4, 'little', True],
			[4, 'little', False],
			[4, 'big', True],
			[4, 'big', False],
			['RIFF', 'little'],
			['RIFF', 'big'],
			['WAVE', 'little'],
			['WAVE', 'big'],
			['foo', 'little'],
			['foo', 'big'],
			['bar', 'little'], 
			['bar', 'little'],
			['arandomstring', 'little'],
			['arandomstring', 'big']
		]
		
		# Load the headerDict{}
		keyList = []
		for i in range(len(paramNestedList)):
			key = 'key' + str(i)
			if isinstance(paramNestedList[i][0], int):
				self.writeAudioObj.headerDict[key] = int(2**((paramNestedList[i][0] * 8) - 1) - 1)
			elif isinstance(paramNestedList[i][0], str):
				self.writeAudioObj.headerDict[key] = paramNestedList[i][0]
			else:
				raise
			keyList.append(key)
		# Write to test file
		totalLen = 0
		tupleList = []
		with open(TEST_WRITE_FILE, 'wb') as writeStream:
			writeStream.truncate()
			for i in range(len(paramNestedList)):
				leng = 0
				if isinstance(paramNestedList[i][0], int):
					leng = paramNestedList[i][0]
					integer = int(2**((paramNestedList[i][0] * 8) - 1) - 1)
					# handle pack string
					if paramNestedList[i][1] == 'little' and paramNestedList[i][2] == True:
						tupleList.append((self.writeAudioObj.packLittleINT, keyList[i], leng))
					elif paramNestedList[i][1] == 'little' and paramNestedList[i][2] == False:
						tupleList.append((self.writeAudioObj.packLittleUINT, keyList[i], leng))
					elif paramNestedList[i][1] == 'big' and paramNestedList[i][2] == True:
						tupleList.append((self.writeAudioObj.packBigINT, keyList[i], leng))
					elif paramNestedList[i][1] == 'big' and paramNestedList[i][2] == False:
						tupleList.append((self.writeAudioObj.packBigUINT, keyList[i], leng))
					else:
						raise
				elif isinstance(paramNestedList[i][0], str):
					leng = len(paramNestedList[i][0])
					# handle endianness
					if paramNestedList[i][1] == 'little':
						tupleList.append((self.writeAudioObj.packLittleUTF, keyList[i]))
					elif paramNestedList[i][1] == 'big':
						tupleList.append((self.writeAudioObj.packBigUTF, keyList[i]))
					else:
						raise
				else:
					raise
			nestedTuple = (tupleList[:])
			self.writeAudioObj.pack_and_write(writeStream, nestedTuple)	
		# Read and test
		with open(TEST_WRITE_FILE, 'rb') as readStream:
			for i in range(len(paramNestedList)):
				with self.subTest(pack=paramNestedList[i]):
					leng = 0
					if isinstance(paramNestedList[i][0], int):
						leng = paramNestedList[i][0]
						originalValue = int(2**((paramNestedList[i][0] * 8) - 1) - 1)
						binary = readStream.read(leng)
						readValue = int.from_bytes(binary, byteorder=paramNestedList[i][1], signed=paramNestedList[i][2])
						self.assertEqual(originalValue, readValue)
					elif isinstance(paramNestedList[i][0], str):
						leng = len(paramNestedList[i][0])
						originalValue = paramNestedList[i][0]
						binary = readStream.read(leng)
						readValue = binary.decode('utf-8')
						# handle endianness
						if paramNestedList[i][1] == 'little':
							self.assertEqual(originalValue, readValue[::-1])
						elif paramNestedList[i][1] == 'big':
							self.assertEqual(originalValue, readValue)
						else:
							raise
					else:
						raise


