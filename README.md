# audioIO
Read audio from file, expose to a custom plugin algorithm, rewrite processed audio to file.

## What?

A python3 package that aims to provide a simple interface for applying a custom audio
processing algorithm to an audio file.  In its present, nascent form it only works for
8- and 16--bit PCM and 32- and 64-bit floating point .WAV files.  More to come.

## Why?

Maybe you want to get your feet wet writing digital audio effects, but you find the
overhead of learning the VST3 API unnecessary while you are still just in the tinkering
stage.  Why not keep it simple for now?

## How?

```python
from audioIO.plugins import plugin
from audioIO.io import wavIO as wIO

def my_algorithm(pluginObj, sampleNestedList):
  # Do something with the samples...
	return processedSampleNestedList
	
readObj = wIO.ReadWav('readFile.wav')
writeObj = wIO.WriteWav('writeFile.wav')
pluginObj = plugin.Plugin(readObj, writeObj, my_algorithm)
pluginObj.process()
```

Your effect callback accepts:

- *pluginObj*		 ==>  Pointer to the Plugin object.  Allows you access to meta info from the header of the read file, as well as to a convenient and simple helper API.
- *sampleNestedList* ==>  A nested list of sample values read from each buffer.  Each item is itself a list, which contains the sample value of each channel at that point in time.  The actual value of each sample can be either an integer or a float, depending on how you set the format of the Plugin object upon init.  For example:

<dl>
	<dd>                        
&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp[[channel1, channel2], [channel1, channel2], etc...]<br>
                            
&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbspi.e.<br>
                                    
&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp[[-0.8, -0.7], [-0.2, -0.15], etc...]<br><br>
	</dd>
</dl>
                        

Your effect callback returns:

- *processedSampleNestedList*  ==>  The nested list of processed samples.

Your effect callback is called once each time a new buffer is read from file.

##API?

Here's the gist:

<dl>
	<dt><i>class</i> wavIO.<b>ReadWav</b>(<i>targetFile</i>)</dt>
		<dd>Reads and stores the header info from <i>targetFile</i> for use during processing by<br>
			a plugin.Plugin() object.
		</dd>
	<dt><i>class</i> wavIO.<b>WriteWav</b>(<i>targetFile</i>, <i>format=None</i>, <i>numChannels=None</i>, <i>bitDepth=None</i>, <i>sampleRate=None</i>)</dt>
		<dd>Initializes and stores the header info for <i>targetFile</i> for use during processing<br>
			by a plugin.Plugin() object.  To apply a conversion to the format of the audio<br>
			file during processing, optional initialization arguments are set.<br><br>

			To change the file from PCM to floating point (or vice versa), set <i>format</i> to<br>
			a string indicating the target format (<i>'float'</i> or <i>'PCM'</i>).  Likewise, <i>numChannels</i><br>
			is an integer value indicating that the write file should be either stereo (2) or<br>
			mono (1); <i>bitDepth</i> is an integer value indicating the target bitDepth; and<br>
			<i>sampleRate</i> is an integer value indicating the target sample rate.<br><br>
	
			NOTES:<br>
			a) Currently supported bit depths are<br>
				&nbsp&nbsp&nbsp&nbsp&nbsp&nbspPCM:    8-bit,  16-bit<br>
				&nbsp&nbsp&nbsp&nbsp&nbsp&nbspFloat:  32-bit, 64-bit<br>
			b) Sample rate conversions perform neither interpolation or decimation at this point.
		</dd>
	<dt><i>class</i> plugin.<b>Plugin</b>(<i>readObj</i>, <i>writeObj</i>, <i>algorithm=None</i>, <i>reachBack=0</i>, <i>format=None</i>)</dt>
		<dd>Connects the read file with the write file via an audio processing <i>algorithm</i>,<br>
			which is implemented as a user-defined callback function. <i>readObj</i> and <i>writeObj</i><br>
			are an initialized wavIO.ReadWav() and an initialized wavIO.WriteWav() object, <br>
			respectively.  If the <i>algorithm</i> callback function performs calculations of samples<br>
			based on the values of previous samples, <i>reachBack</i> can be defined as the maximum<br>
			number of samples that the <i>algorithm</i> needs to be able to 'peek back at'.  If the<br>
			<i>algorithm</i> is written to process samples in a specific format (PCM vs. floating <br>
			point), the <i>format</i> of the samples can be designated by a string (either <i>'PCM'</i> or<br>
			<i>'float'</i>).  Otherwise the algorithm will be presented the samples in whatever format<br>
			they occur in the read file, with the caveat that PCM values will always be signed,<br>
			even if they occur as unsigned in binary form--e.g. 8-bit PCM .wav files.<br><br>
			
			Method(s):<br><br>
			
			<b><i>.process()</i></b><br>
			&nbsp&nbsp&nbsp&nbspReads the input file data, passes it through the algorithm callback function,<br>
			&nbsp&nbsp&nbsp&nbspand writes the processed audio to the output file.<br><br>
	
			<b><i>.reach_back<(numSamples, currBlock, currChannel)</i></b><br>
			&nbsp&nbsp&nbsp&nbspCan be called within the algorithm callback function in order to reference<br>
			&nbsp&nbsp&nbsp&nbspthe value of a sample of the same channel (<i>currChannel</i>) that occurred<br>
			&nbsp&nbsp&nbsp&nbsp<i>numSamples</i> samples previously to a sample at <i>currBlock</i> index in the<br>
			&nbsp&nbsp&nbsp&nbsppresently executing nested list of samples.  What?<br><br>

			&nbsp&nbsp&nbsp&nbspRemember what the nested list of samples looked like:<br><br>
	
			&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp[[channel1, channel2], [channel1, channel2], etc...]<br>
                            
            &nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbspi.e.<br>
                                    
            &nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp[[-0.8, -0.7], [-0.2, -0.15], etc...]<br><br>

			&nbsp&nbsp&nbsp&nbspSo, if you are working with floating point values you could process<br>
			&nbsp&nbsp&nbsp&nbspthe samples with something like this:<br>
		</dd>
	</dt>
</dl>
   
```python
def my_algorithm(pluginObj, sampleNestedList):
    for block in range(len(sampleNestedList)):
		for channel in range(len(sampleNestedList[block])):
			sampleNestedList[block][channel] += \
				pIObj.reach_back(44100, block, channel) * 0.35
	return sampleNestedList
```
    
<dl>
		<dd>	
			&nbsp&nbsp&nbsp&nbspThis gives you an extremely simple delay algorithm that repeats<br>
			&nbsp&nbsp&nbsp&nbspthe signal once at a 44100 sample delay, and at 35% the signal volume.<br>
		</dd>
</dl>

##Testing?

If you adjusted the source and you want to see if everything is still working as
before, just run 

```$ python3 runtests.py```

from the testAudioIO/ directory.

## License

```
The MIT License

Copyright (c) 2015, Zach

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.
```
