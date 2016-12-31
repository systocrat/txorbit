from setuptools import setup

setup(
    name='txorbit',
    use_incremental=True,
    setup_requires=['incremental'],
    install_requires=['incremental', 'twisted'],
    description='Transactional WebSockets library for the Twisted networking framework',
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
