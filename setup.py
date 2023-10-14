from setuptools import setup
import setuptools
import re

with open("requirements.txt", encoding="utf-8") as r:
    requires = [i.strip() for i in r]

with open("bcnadds/__init__.py", encoding="utf-8") as f:
    ver = re.findall(r"__version__ = \"(.+)\"", f.read())[0]

with open('README.md', 'r', encoding='utf-8') as fh:
    long_description = fh.read()
    
setup(
    name='bcnadds',
    version=ver,
    description='This package for blackcat userbot adds',
    author='santhosh',
    author_email='yumikoapi@gmail.com',
    package_data={"bcnadds": ["py.typed"]},
    url='https://github.com/bcncalling/bcnadds',
    long_description=long_description,
    long_description_content_type='text/markdown',
    packages=setuptools.find_packages(),
    keywords=['bcnadds', 'telegram', 'telegram-bots', 'bcn userbot', 'telegram bots library'],
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "Natural Language :: English",
        "License :: OSI Approved :: GNU Lesser General Public License v3 (LGPLv3)",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: Implementation",
        "Programming Language :: Python :: Implementation :: CPython",
        "Programming Language :: Python :: Implementation :: PyPy",
        "Topic :: Internet",
        "Topic :: Communications",
        "Topic :: Communications :: Chat",
        "Topic :: Software Development :: Libraries",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Software Development :: Libraries :: Application Frameworks"
    ],
    python_requires='>=3.6',
    install_requires=["pyrogram==2.0.106", "TgCrypto", "requests==2.28.2", "asyncio==3.4.3"],
)
