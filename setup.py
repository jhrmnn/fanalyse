from setuptools import setup, find_packages
import subprocess
subprocess.run([
    'curl',
    '-O',
    'https://raw.githubusercontent.com/nvbn/thefuck/82a12dda81fefa655df6daa5fe2e92c81b5c7187/fastentrypoints.py',
], check=True)
import fastentrypoints


setup(
    name='fanalyse',
    description='Fortran static analyzer',
    url='https://github.com/azag0/fanalyse',
    author='Jan Hermann',
    author_email='dev@janhermann.cz',
    license='Mozilla Public License 2.0',
    packages=find_packages(),
    install_requires=[
        'textx',
    ],
    entry_points={
        'console_scripts': ['fanalyse = fanalyse:main']
    },
)
