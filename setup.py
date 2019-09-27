import os
from setuptools import setup, find_packages

with open('README.md') as f:
    readme = f.read()

version = os.environ.get('TRAVIS_TAG', '0.0.1-alpha.1+dirty')

setup(name='qvibe-audio',
      version=version,
      description='Bridges data to/from a pyaudio device to a tcp socket decimating before sending to reduce load',
      long_description=readme,
      long_description_content_type='text/markdown',
      classifiers=[
          'License :: OSI Approved :: MIT License',
          'Programming Language :: Python :: 3.7',
          'Development Status :: 4 - Beta',
      ],
      url='http://github.com/3ll3d00d/qvibe-audio',
      author='Matt Khan',
      author_email='mattkhan+qvibe-audio@gmail.com',
      license='MIT',
      packages=find_packages(exclude=('test', 'docs')),
      python_requires='>=3.7',
      entry_points={
          'console_scripts': [
              'qvibe-audio = qvibe.app:run',
          ],
      },
      install_requires=[
          'pyaudio',
          'pyyaml',
          'twisted',
          'numpy',
          'resampy'
      ],
      include_package_data=False,
      zip_safe=False)
