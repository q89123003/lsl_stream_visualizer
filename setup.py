from setuptools import setup

setup(name='lsl_stream_visualizer',
      version='0.1',
      description='LSL Stream Visualizer',
      author='Kuan-Jung Chiang',
      author_email='kuchiang@eng.ucsd.edu',
      url='https://www.python.org/sigs/distutils-sig/',
      install_requires=['pylsl', 'matplotlib', 'numpy', 'PyQt5', 'pyqtgraph', 'pyopengl'],
     )
