import ast
import re

from setuptools import setup, find_packages

_version_re = re.compile(r'__version__\s+=\s+(.*)')

with open('vcli/__init__.py', 'rb') as f:
    version = str(ast.literal_eval(_version_re.search(
        f.read().decode('utf-8')).group(1)))

description = 'Vertica CLI with auto-completion and syntax highlighting'

setup(
    name='vcli',
    author='Chang-Hung Liang',
    author_email='eliang.cs@gmail.com',
    version=version,
    license='LICENSE.txt',
    url='http://github.com/dbcli/vcli',
    packages=find_packages(),
    package_data={'vcli': ['vclirc']},
    description=description,
    long_description=open('README.rst').read(),
    install_requires=[
        'click >= 4.1',
        'configobj >= 5.0.6',
        'prompt_toolkit==0.46',
        'Pygments >= 2.0',  # Pygments has to be Capitalcased. WTF?
        'sqlparse == 0.1.16',
        'vertica-python==0.5.2'
    ],
    entry_points='''
        [console_scripts]
        vcli=vcli.main:cli
    ''',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: Unix',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: SQL',
        'Topic :: Database',
        'Topic :: Database :: Front-Ends',
        'Topic :: Software Development',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ],
)
