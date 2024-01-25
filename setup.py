from setuptools import setup, find_packages

setup(
    name='pyqual',
    version='0.0.1',
    packages=find_packages(),
    package_dir={'': 'src'},
    url='',
    license='MIT',
    author='sebastian',
    author_email='sebastian.fest@gmail.com',
    description='A simple client for Qualtrics.',
    classifiers=[
        'Development Status :: 1 - Planning',
        'Intended Audience :: Science/Research',
        'License :: OSI Approved :: MIT License',
        'Operating System :: POSIX :: Linux',
        'Programming Language :: Python :: 3.11',
    ],
)
