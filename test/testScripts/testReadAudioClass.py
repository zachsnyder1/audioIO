import os
import sys
import unittest
import time
PACKAGE_ROOT = '../..'
SCRIPT_DIR = os.path.dirname(os.path.realpath(os.path.join(os.getcwd(), 
	os.path.expanduser(__file__))))
PACKAGE_PATH = os.path.normpath(os.path.join(SCRIPT_DIR, PACKAGE_ROOT))
sys.path.append(PACKAGE_PATH)
from src.framework import base_io as baseIO

# Set a read file for testing
TEST_DATA_DIR = os.path.normpath(
					os.path.dirname(
					os.path.dirname(
					os.path.abspath(__file__))) + '/testData/')
TEST_READ_FILE = TEST_DATA_DIR + '/test_read_file.txt'


class ReadAudioInitTestMethods(unittest.TestCase):
	"""
	Methods to test the initialization of a ReadAudio object.
	"""
	def setUp(self):
		with open(TEST_READ_FILE, 'wb') as writeStream:
			writeStream.write(bytearray(1))
	
	def test_init(self):
		audioInput = baseIO.ReadAudio(TEST_READ_FILE)
		self.assertIsInstance(audioInput, baseIO.ReadAudio)

class UnpackIntAndAdvanceTestMethods(unittest.TestCase):
	"""
	Methods to test the ReadAudio.unpack_int() method.
	"""
	
	def setUp(self):
		self.audioInput = baseIO.ReadAudio(TEST_READ_FILE)
	
	def tearDown(self):
		pass
	
	def test_unpack_value_with_correct_data(self):
		"""
		Tests the unpacked integer value of ReadAudio.unpack_int()
		method.
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
			with self.subTest(numBytes_endianness_signed = parameterList):
				numbytes = parameterList[0]
				integer = (2**(parameterList[0] - 1) -1)
				
				self.audioInput.readOffset = 0
				self.audioInput.byteArray = bytearray()
				self.audioInput.byteArray += \
					(integer).to_bytes(numbytes, 
										byteorder=parameterList[1], 
										signed=parameterList[2])
				unpackedInt = \
					self.audioInput.unpack_int(numbytes, 
												 byteorder=parameterList[1], 
												 signed=parameterList[2])
				self.assertEqual(integer, unpackedInt)
	
	def test_readOffset_value_with_correct_data(self):
		"""
		Tests the ReadAudio object's readOffset value after calling
		ReadAudio.unpack_int() method.
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
			with self.subTest(numBytes_endianness_signed = parameterList):
				numbytes = parameterList[0]
				integer = (2**(parameterList[0] - 1) -1)
				
				self.audioInput.readOffset = 0
				self.audioInput.byteArray = bytearray()
				self.audioInput.byteArray += \
					(integer).to_bytes(numbytes, 
										byteorder=parameterList[1], 
										signed=parameterList[2])
				unpackedInt = \
					self.audioInput.unpack_int(numbytes, 
												 byteorder=parameterList[1], 
												 signed=parameterList[2])
				self.assertEqual(self.audioInput.readOffset, numbytes)
		
	def test_unpack_value_is_zero_beyond_readLen(self):
		"""
		Tests that the read value is zero if the readOffset is greater
		than the length of the bytearray being read.  This is necessary
		for variable length headers (the missing values should be set
		to zero).
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
			with self.subTest(numBytes_endianness_signed = parameterList):
				numbytes = parameterList[0]
				integer = (2**(parameterList[0] - 1) -1)
				
				self.audioInput.readOffset = numbytes + 1
				self.audioInput.byteArray = bytearray()
				self.audioInput.byteArray += \
					(integer).to_bytes(numbytes, 
										byteorder=parameterList[1], 
										signed=parameterList[2])
				unpackedInt = \
					self.audioInput.unpack_int(numbytes, 
												 byteorder=parameterList[1], 
												 signed=parameterList[2])
				self.assertEqual(0, unpackedInt)


class UnpackUtfAndAdvanceTestMethods(unittest.TestCase):
	"""
	Methods to test the ReadAudio.unpack_utf() method.
	"""
	def setUp(self):
		self.audioInput = baseIO.ReadAudio(TEST_READ_FILE)
	
	def tearDown(self):
		pass
		
	def test_unpack_value_with_correct_data(self):
		"""
		Tests the unpacked UTF-8 string value of ReadAudio.unpack_utf()
		method.
		"""
		paramList = ['RIFF', 'WAVE', 'foo', 'bar', 'arandomstring']
		
		for parameter in paramList:
			with self.subTest(utf_str = parameter):
				numbytes = len(parameter)
				stringBin = parameter.encode("utf-8")
				
				self.audioInput.readOffset = 0
				self.audioInput.byteArray = bytearray()
				self.audioInput.byteArray += stringBin
				unpackedString = self.audioInput.unpack_utf(numbytes)
				self.assertEqual(parameter, unpackedString)

	def test_readOffset_value_with_correct_data(self):
		"""
		Tests the ReadAudio object's readOffset value after calling
		ReadAudio.unpack_utf() method.
		"""
		paramList = ['RIFF', 'WAVE', 'foo', 'bar', 'arandomstring']
		
		for parameter in paramList:
			with self.subTest(utf_str = parameter):
				numbytes = len(parameter)
				stringBin = parameter.encode("utf-8")
				
				self.audioInput.readOffset = 0
				self.audioInput.byteArray = bytearray()
				self.audioInput.byteArray += stringBin
				unpackedString = self.audioInput.unpack_utf(numbytes)
				self.assertEqual(self.audioInput.readOffset, numbytes)
	
	def test_unpack_value_is_zero_beyond_readLen(self):
		"""
		Tests that the read value is zero if the readOffset is greater
		than the length of the bytearray being read.  This is necessary
		for variable length headers (the missing values should be set
		to zero).
		"""
		paramList = ['RIFF', 'WAVE', 'foo', 'bar', 'arandomstring']
		
		for parameter in paramList:
			with self.subTest(utf_str = parameter):
				numbytes = len(parameter)
				stringBin = parameter.encode("utf-8")
				
				self.audioInput.readOffset = numbytes + 1
				self.audioInput.byteArray = bytearray()
				self.audioInput.byteArray += stringBin
				unpackedString = self.audioInput.unpack_utf(numbytes)
				self.assertEqual(unpackedString, '')



class ReadAndAssignTestMethods(unittest.TestCase):
	"""
	Methods to test the ReadAudio.read_and_assign() method.
	"""
	def setUp(self):
		self.audioInput = baseIO.ReadAudio(TEST_READ_FILE)
	
	def tearDown(self):
		pass
	
	def test_assign_utf(self):
		"""
		Test that ReadAudio.read_and_assign() correctly reads and
		assigns UTF-8 strings of various length and endianness.
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
				# handle endianness
				if parameterList[1] == 'little':
					assignStr = baseIO.LITTLE_UTF
				elif parameterList[1] == 'big':
					assignStr = baseIO.BIG_UTF
				# write utf to file
				with open(TEST_DATA_DIR + 
						  '/test_read_and_assign.txt', 'wb') as writeStream:
					writeStream.truncate()
					writeStream.write(parameterList[0].encode('utf-8'))
				# read utf
				with open(TEST_DATA_DIR + 
						  '/test_read_and_assign.txt', 'rb') as readStream:
					self.audioInput.read_and_assign(readStream, 
												 len(parameterList[0]), 
												 ((assignStr, 
												 'test', 
												 len(parameterList[0])),))
				if assignStr == baseIO.BIG_UTF:
					self.assertEqual(self.audioInput.headerDict['test'], 
									 parameterList[0])
				elif assignStr == baseIO.LITTLE_UTF:
					self.assertEqual(self.audioInput.headerDict['test'], 
									 parameterList[0][::-1])
	
	def test_assign_int(self):
		"""
		Test that ReadAudio.read_and_assign() correctly reads and assigns
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
			with self.subTest(numBytes_signed = parameterList):
				integer = int(2**((parameterList[0] * 8) - 1) - 1)
				# handle assign string
				if parameterList[1] == 'little' and parameterList[2] == True:
					assignStr = baseIO.LITTLE_INT
				elif parameterList[1] == 'little' and \
					parameterList[2] == False:
					assignStr = baseIO.LITTLE_UINT
				elif parameterList[1] == 'big' and parameterList[2] == True:
					assignStr = baseIO.BIG_INT
				elif parameterList[1] == 'big' and parameterList[2] == False:
					assignStr = baseIO.BIG_UINT
				else:
					raise
				# write int to file
				with open(TEST_DATA_DIR + 
						  '/test_read_and_assign.txt', 'wb') as writeStream:
					writeStream.truncate()
					writeStream.write(integer.to_bytes(parameterList[0], 
												byteorder=parameterList[1], 
												signed=parameterList[2]))
				# read int
				with open(TEST_DATA_DIR + 
						  '/test_read_and_assign.txt', 'rb') as readStream:
					self.audioInput.read_and_assign(readStream, 
												 parameterList[0], 
												 ((assignStr, 
												  'test', 
												  parameterList[0]),))
				self.assertEqual(self.audioInput.headerDict['test'], integer)

	def test_multiple_assignments(self):
		"""
		Test that ReadAudio.read_and_assign() correctly reads and assigns
		multiple values from a read.
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
		
		totalLen = 0
		with open(TEST_DATA_DIR + 
				  '/test_read_and_assign.txt', 'wb') as writeStream:
			writeStream.truncate()
			for parameterList in paramNestedList:
				if isinstance(parameterList[0], int):
					integer = int(2**((parameterList[0] * 8) - 1) - 1)
					# write int to file
					writeStream.write(integer.to_bytes(parameterList[0], 
												byteorder=parameterList[1], 
												signed=parameterList[2]))
					totalLen += parameterList[0]
				elif isinstance(parameterList[0], str):
					if parameterList[1] == 'little':
						writeStream.write(parameterList[0][::-1].\
											encode('utf-8'))
					elif parameterList[1] == 'big':
						writeStream.write(parameterList[0].encode('utf-8'))
					else:
						raise
					totalLen += len(parameterList[0])
				else:
					raise
		# read
		nList = []
		assignmentList = []
		
		for parameterList in paramNestedList:
				leng = 0
				if isinstance(parameterList[0], int):
					leng = parameterList[0]
					integer = int(2**((parameterList[0] * 8) - 1) - 1)
					# handle assign string
					if parameterList[1] == 'little' and \
						parameterList[2] == True:
						assignStr = baseIO.LITTLE_INT
					elif parameterList[1] == 'little' and \
						parameterList[2] == False:
						assignStr = baseIO.LITTLE_UINT
					elif parameterList[1] == 'big' and \
						parameterList[2] == True:
						assignStr = baseIO.BIG_INT
					elif parameterList[1] == 'big' and \
						parameterList[2] == False:
						assignStr = baseIO.BIG_UINT
					else:
						raise
				elif isinstance(parameterList[1], str):
					leng = len(parameterList[0])
					# handle endianness
					if parameterList[1] == 'little':
						assignStr = baseIO.LITTLE_UTF
					elif parameterList[1] == 'big':
						assignStr = baseIO.BIG_UTF
					else:
						raise
				else:
					raise
				nList.append((assignStr, repr(parameterList), leng))
				assignmentList.append(repr(parameterList))
		
		nestedTuple = (nList[:])
		with open(TEST_DATA_DIR + 
				  '/test_read_and_assign.txt', 'rb') as readStream:
			self.audioInput.read_and_assign(readStream, totalLen, nestedTuple)
		for i in range(len(nList)):
			with self.subTest(assignment=assignmentList[i]):
				originalValue = None
				if isinstance(paramNestedList[i][0], int):
					originalValue = \
						int(2**((paramNestedList[i][0] * 8) - 1) - 1)
				elif isinstance(paramNestedList[i][0], str):
					originalValue = paramNestedList[i][0]
				else:
					raise
				self.assertEqual(self.audioInput.headerDict[assignmentList[i]], 
								 originalValue)
		
	def test_assign_past_read_len(self):
		"""
		Test that ReadAudio.read_and_assign() all assignments past the
		read length are assigned as zero (numeric type) or '' (string type).
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
		
		totalLen = 0
		with open(TEST_DATA_DIR + 
				  '/test_read_and_assign.txt', 'wb') as writeStream:
			writeStream.truncate()
			writeStream.write(b'\x00')
			for parameterList in paramNestedList:
				if isinstance(parameterList[0], int):
					integer = int(2**((parameterList[0] * 8) - 1) - 1)
					# write int to file
					writeStream.write(integer.to_bytes(parameterList[0], 
												byteorder=parameterList[1], 
												signed=parameterList[2]))
					totalLen += parameterList[0]
				elif isinstance(parameterList[0], str):
					if parameterList[1] == 'little':
						writeStream.write(parameterList[0][::-1].\
											encode('utf-8'))
					elif parameterList[1] == 'big':
						writeStream.write(parameterList[0].encode('utf-8'))
					else:
						raise
					totalLen += len(parameterList[0])
				else:
					raise
		# read
		nList = []
		assignmentList = []
		
		for parameterList in paramNestedList:
				leng = 0
				if isinstance(parameterList[0], int):
					leng = parameterList[0]
					integer = int(2**((parameterList[0] * 8) - 1) - 1)
					# handle assign string
					if parameterList[1] == 'little' and \
						parameterList[2] == True:
						assignStr = baseIO.LITTLE_UINT
					elif parameterList[1] == 'little' and \
						parameterList[2] == False:
						assignStr = baseIO.LITTLE_INT
					elif parameterList[1] == 'big' and \
						parameterList[2] == True:
						baseIO.BIG_UINT
					elif parameterList[1] == 'big' and \
						parameterList[2] == False:
						baseIO.BIG_INT
					else:
						raise
				elif isinstance(parameterList[1], str):
					leng = len(parameterList[0])
					# handle endianness
					if parameterList[1] == 'little':
						assignStr = baseIO.LITTLE_UTF
					elif parameterList[1] == 'big':
						assignStr = baseIO.BIG_UTF
					else:
						raise
				else:
					raise
				nList.append((assignStr, repr(parameterList), leng))
				assignmentList.append(repr(parameterList))
		
		nestedTuple = (nList[:])
		with open(TEST_DATA_DIR + 
				  '/test_read_and_assign.txt', 'rb') as readStream:
			self.audioInput.read_and_assign(readStream, 1, nestedTuple)
		for i in range(len(nList)):
			with self.subTest(assignment=assignmentList[i]):
				expectedValue = None
				if isinstance(paramNestedList[i][0], int):
					expectedValue = 0
				elif isinstance(paramNestedList[i][0], str):
					expectedValue = ''
				else:
					raise
				self.assertEqual(self.audioInput.headerDict[assignmentList[i]], 
								 expectedValue)


