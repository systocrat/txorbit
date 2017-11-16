from setuptools import setup

from txorbit import __version__

setup(
	name='txorbit',
	install_requires=['six', 'twisted'],
	description='Transactional WebSockets library for the Twisted networking framework',
	version=__version__,
	author='systocrat',
	author_email='systocrat@outlook.com',
	maintainer='systocrat',
	maintainer_email='systocrat@outlook.com',
	url='https://github.com/systocrat/txorbit',
	packages=['txorbit'],
	license='MIT',
	classifiers=[
		'Framework :: Twisted',
		'License :: OSI Approved :: MIT License',
		'Framework :: Flask',
		'Framework :: Django'
	],
	keywords='performance websockets transactional dynamic web app flask twisted'
)
