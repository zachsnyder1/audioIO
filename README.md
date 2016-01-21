# signalhook
Read audio from file, expose to a custom plugin algorithm, rewrite processed audio to file.

## What?

A developing python3 framework for exposing a discrete-time signal to a custom 
processing or analyzing plugin. Currently, 'signal' means sample data read from 
and written to file, although the goal is to eventually implement the same 
functionality for real-time data being read from and written to ring buffers. 
In its present, nascent form it only works for 8- and 16-bit PCM and 32- and 
64-bit floating point .WAV audio files. Much more to come.


## Why?

Maybe you want to get your feet wet writing digital audio effects, but you find the
overhead of learning the VST3 API unnecessary while you are still just in the tinkering
stage.  Why not keep it simple for now?

## How?

```python
# Everything you will need here is located in the engine module.  Don't forget
# to install the signalhook package first (see Installation section...)
from signalhook import engine

# Define your plugin callback function:
def my_plugin(engObj, sampleNestedList):
	# Do something with the samples...
	return sampleNestedList

# Set some options:
optionsDict = {
	# present the plugin with
	# floating point samples:
	engine.PLUGIN_FMT: 'float',
	
	# write the output file
	# as PCM data:
	engine.OUTPUT_FMT: 'PCM'
}

# Instantiate an engine:
engObj = engine.FileToFileEngine(
	'path/to/input.wav',
	'path/to/output.wav',
	algorithm=my_plugin,
	options=optionsDict
)

# Initiate the signal processing:
engObj.process()
```

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
