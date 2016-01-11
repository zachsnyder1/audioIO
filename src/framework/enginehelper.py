import math

def clip_pcm(sampleNestedList, bitDepth):
	"""
	Clip the (PCM) audio signal -- make sure it does not exceed the
	range of values dictated by its numeric format and bit depth.
		
	Accepts:
		
	1) sampleNestedList  ==>  The nested list of samples to clip.
		
	2) bitDepth          ==>  The bit depth of the samples.
	"""
	for i in range(len(sampleNestedList)):
		for x in range(len(sampleNestedList[i])):
			if sampleNestedList[i][x] > ((2**(bitDepth - 1)) - 1):
				sampleNestedList[i][x] = ((2**(bitDepth - 1)) - 1)
			elif sampleNestedList[i][x] < -(2**(bitDepth - 1)):
				sampleNestedList[i][x] = -(2**(bitDepth - 1))
			else:
				pass
	return sampleNestedList
	
def clip_float(sampleNestedList):
	"""
	Clip the (float) audio signal -- make sure it does not exceed the
	range of values dictated by its numeric format and bit depth.
	
	Accepts:
	
	1) sampleNestedList  ==>  The nested list of samples to clip.
	"""
	for i in range(len(sampleNestedList)):
		for x in range(len(sampleNestedList[i])):
			if sampleNestedList[i][x] > 1.0:
				sampleNestedList[i][x] = 1.0
			elif sampleNestedList[i][x] < -1.0:
				sampleNestedList[i][x] = -1.0
			else:
				pass
	return sampleNestedList

def float_to_pcm(sampleNestedList, bitDepth, signed):
	"""
	Converts nested sample list from floating point to PCM.
	
	Accepts:
	
	1) sampleNestedList  ==>  The nested list of samles to convert.
	
	2) bitDepth          ==>  The desired bit depth of PCM values.
	
	3) signed            ==>  A boolean indicating whether to
							  convert to signed or unsigned PCM.
	
	Returns the converted nested list of samples.
	"""
	if signed:
		for block in range(len(sampleNestedList)):
			for channel in range(len(sampleNestedList[block])):
				sampleNestedList[block][channel] = \
					math.floor(sampleNestedList[block][channel] * \
						(((2**bitDepth) - 1) / 2))
	else:
		for block in range(len(sampleNestedList)):
			for channel in range(len(sampleNestedList[block])):
				sampleNestedList[block][channel] = \
					math.floor((sampleNestedList[block][channel]+1) *
						(((2**(bitDepth))-1)/2))
	return sampleNestedList

def pcm_to_float(sampleNestedList, bitDepth, signed):
	"""
	Converts nested sample list from PCM to floating point.
	
	Accepts:
	
	1) sampleNestedList  ==>  The nested list of samles to convert.
	
	2) bitDepth          ==>  The bit depth of the input PCM.
	
	3) signed            ==>  A boolean indicating whether or not
							  the input values are signed.
	
	Returns the converted nested list of samples.
	"""
	if signed:
		for block in range(len(sampleNestedList)):
			for channel in range(len(sampleNestedList[block])):
				if sampleNestedList[block][channel] <= 0:
					sampleNestedList[block][channel] = \
						sampleNestedList[block][channel] / \
						(2**(bitDepth - 1))
				else:
					sampleNestedList[block][channel] = \
						(sampleNestedList[block][channel] / 
						(2**(bitDepth - 1))) + \
						(1 / (2**(bitDepth-1)))
	else:
		for block in range(len(sampleNestedList)):
			for channel in range(len(sampleNestedList[block])):
				sampleNestedList[block][channel] = \
					(((sampleNestedList[block][channel]) / 
					(((2**(bitDepth))-1)/2)) - 1)
	return sampleNestedList

def pcm_to_pcm(sampleNestedList, inBitDepth, outBitDepth, inSigned, 
				outSigned):
	"""
	Converts to float, then converts pack to PCM at desired bit depth.
	
	Accepts:
	
	1) sampleNestedList  ==>  The nested list of samles to convert.
	
	2) inBitDepth        ==>  The bit depth of the input PCM.
	
	3) outBitDepth       ==>  The desired bit depth of the output
							  PCM.
	
	4) inSigned          ==>  A boolean indicating whether or not
							  the input values are signed.
	
	5) outSigned         ==>  A boolean indicating whether or not
							  the output values are signed.
	
	Returns the converted nested list of samples.
	"""
	pcm_to_float(sampleNestedList, inBitDepth, inSigned)
	return float_to_pcm(sampleNestedList, outBitDepth, outSigned)


def default_algorithm(self, sampleNestedList):
	"""
	Default algorithm, if Engine object is instantiated without
	an algorithm callback.
	"""
	return sampleNestedList

# --------------------------------------------------------------
# ---------------------- ALGORITHM WRAPPERS: -------------------
# --------------------------------------------------------------

def wrapper_fff(engineObj, sampleNestedList):
	"""
	Read fmt = float, 
	Plugin fmt = float,
	write fmt = float
	"""
	engineObj.update_reachback_deques(sampleNestedList)
	processedNest = engineObj.algorithm(engineObj, sampleNestedList)
	return clip_float(processedNest)

def wrapper_fpf(engineObj, sampleNestedList):
	"""
	Read fmt = float, 
	Plugin fmt = PCM,
	write fmt = float
	"""
	preProcessedNest = float_to_pcm(sampleNestedList, 32, True)
	engineObj.update_reachback_deques(preProcessedNest)
	processedNest = engineObj.algorithm(engineObj, preProcessedNest)
	clippedNest = clip_pcm(processedNest, 32)
	return pcm_to_float(clippedNest, 32, True)

def wrapper_pfp(engineObj, sampleNestedList):
	"""
	Read fmt = PCM, 
	Plugin fmt = Float,
	write fmt = PCM
	"""
	preProcessedNest = pcm_to_float(sampleNestedList, 
									engineObj.readBitDepth, 
									engineObj.readSigned)
	engineObj.update_reachback_deques(preProcessedNest)
	processedNest = engineObj.algorithm(engineObj, preProcessedNest)
	clippedNest = clip_float(processedNest)
	return float_to_pcm(clippedNest, 
						engineObj.writeBitDepth, 
						engineObj.writeSigned)
	
def wrapper_ppp_unsigned(engineObj, sampleNestedList):
	"""
	Read fmt = PCM, 
	Plugin fmt = PCM,
	write fmt = PCM
	
	Read data is unsigned.
	"""
	preProcessedNest = pcm_to_pcm(sampleNestedList,
								  engineObj.readBitDepth,
								  engineObj.readBitDepth,
								  engineObj.readSigned,
								  True)
	engineObj.update_reachback_deques(preProcessedNest)
	processedNest = engineObj.algorithm(engineObj, preProcessedNest)
	clippedNest = clip_pcm(processedNest, engineObj.readBitDepth)
	return pcm_to_pcm(clippedNest, 
						   engineObj.readBitDepth,
						   engineObj.writeBitDepth, 
						   True,
						   engineObj.writeSigned)
	
def wrapper_ppp_signed_no_conversion(engineObj, sampleNestedList):
	"""
	Read fmt = PCM, 
	Plugin fmt = PCM,
	write fmt = PCM
	
	Read and write data are signed, and read bit depth == write bit depth.
	"""
	engineObj.update_reachback_deques(sampleNestedList)
	processedNest = engineObj.algorithm(engineObj, sampleNestedList)
	return clip_pcm(processedNest, engineObj.readBitDepth)
	
def wrapper_ppp_signed_conversion(engineObj, sampleNestedList):
	"""
	Read fmt = PCM, 
	Plugin fmt = PCM,
	write fmt = PCM
	
	Some data format conversion is necessary.
	"""
	engineObj.update_reachback_deques(sampleNestedList)
	processedNest = engineObj.algorithm(engineObj, sampleNestedList)
	clippedNest = clip_pcm(processedNest, engineObj.readBitDepth)
	return pcm_to_pcm(clippedNest, 
					  engineObj.readBitDepth, 
					  engineObj.writeBitDepth, 
					  engineObj.readSigned, 
					  engineObj.writeSigned)
	
def wrapper_ffp(engineObj, sampleNestedList):
	"""
	Read fmt = Float, 
	Plugin fmt = Float,
	write fmt = PCM
	"""
	engineObj.update_reachback_deques(sampleNestedList)
	processedNest = engineObj.algorithm(engineObj, sampleNestedList)
	clippedNest = clip_float(processedNest)
	return float_to_pcm(clippedNest, 
						engineObj.writeBitDepth, 
						engineObj.writeSigned)
	

def wrapper_fpp_unsigned(engineObj, sampleNestedList):
	"""
	Read fmt = Float, 
	Plugin fmt = PCM,
	write fmt = PCM
	
	Write data is unsigned.
	"""
	preProcessedNest = float_to_pcm(sampleNestedList,
									engineObj.writeBitDepth,
									True)
	engineObj.update_reachback_deques(preProcessedNest)
	processedNest = engineObj.algorithm(engineObj, preProcessedNest)
	clippedNest = clip_pcm(processedNest, engineObj.writeBitDepth)
	return pcm_to_pcm(clippedNest, 
					  engineObj.writeBitDepth,
					  engineObj.writeBitDepth, 
					  True,
					  engineObj.writeSigned)
	
def wrapper_fpp_signed(engineObj, sampleNestedList):
	"""
	Read fmt = Float, 
	Plugin fmt = PCM,
	write fmt = PCM
	
	Write data is signed.
	"""
	preProcessedNest = float_to_pcm(sampleNestedList, 
									engineObj.writeBitDepth, 
									engineObj.writeSigned)
	engineObj.update_reachback_deques(preProcessedNest)
	processedNest = engineObj.algorithm(engineObj, preProcessedNest)
	return clip_pcm(processedNest, engineObj.writeBitDepth)
	
def wrapper_pff(engineObj, sampleNestedList):
	"""
	Read fmt = PCM, 
	Plugin fmt = Float,
	write fmt = Float
	"""
	preProcessedNest = pcm_to_float(sampleNestedList, 
									engineObj.readBitDepth, 
									engineObj.readSigned)
	engineObj.update_reachback_deques(preProcessedNest)
	processedNest = engineObj.algorithm(engineObj, preProcessedNest)
	return clip_float(processedNest)
	
def wrapper_ppf_unsigned(engineObj, sampleNestedList):
	"""
	Read fmt = PCM, 
	Plugin fmt = Float,
	write fmt = Float
	
	Read data is unsigned.
	"""
	preProcessedNest = pcm_to_pcm(sampleNestedList, 
								  engineObj.readBitDepth, 
								  engineObj.readBitDepth, 
								  engineObj.readSigned, 
								  True)
	engineObj.update_reachback_deques(preProcessedNest)
	processedNest = engineObj.algorithm(engineObj, sampleNestedList)
	clippedNest = clip_pcm(processedNest, engineObj.readBitDepth)
	return pcm_to_float(clippedNest, engineObj.readBitDepth, True)
	
def wrapper_ppf_signed(engineObj, sampleNestedList):
	"""
	Read fmt = PCM, 
	Plugin fmt = Float,
	write fmt = Float
	
	Read data is signed.
	"""	
	engineObj.update_reachback_deques(sampleNestedList)
	processedNest = engineObj.algorithm(engineObj, sampleNestedList)
	clippedNest = clip_pcm(processedNest, engineObj.readBitDepth)
	return pcm_to_float(processedNest, engineObj.readBitDepth, engineObj.readSigned)
