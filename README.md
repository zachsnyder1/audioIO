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
from audioIO.src.framework import engine

def my_algorithm(engineObj, sampleNestedList):
  # Do something with the samples...
	return processedSampleNestedList

options = {
	engine.OUTPUT_FMT: 'float',
	engine.OUTPUT_BIT_DEPTH: 32
}
	
processor = engine.FileToFileEngine('readFile.wav', 
									'writeFile.wav', 
                                    algorithm=my_algorithm, 
                                    options=options)
processor.process()
```

Your effect callback accepts:

- *engineObj*		 ==>  Pointer to the Engine object.  Allows you access to meta info from the header of the read file, as well as to a convenient and simple helper API.
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

##Testing?

If you adjusted the source and you want to see if everything is still working as
before, just run 

```$ python3 runtests.py```

from the test/ directory.

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
