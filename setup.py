from setuptools import setup, find_packages

setup(
	name = 'signalhook',
	version = '0.1.0',
	packages = find_packages('src'),
	package_dir = {'':'src'},
	
	license = 'MIT',
	description = "A python3 framework for plugging a processing algorithm into a discrete time function signal."
)