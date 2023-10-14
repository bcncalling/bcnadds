from setuptools import setup, find_packages

with open('README.md', encoding='utf-8') as f:
    long_description = f.read()

with open('requirements.txt') as f:
    requirements = f.read().splitlines()

setup(
    name='bcnadds',
    version='0.0.5',
    description='The package for bcnuserbot to addons',
    long_description=long_description,
    long_description_content_type='text/markdown',
    author='santhu',
    license='GNU General Public License (GPL)', 
    classifiers=[
        'License :: OSI Approved :: GNU General Public License (GPL)',
        'Programming Language :: Python :: 3',
    ],
    packages=find_packages(),
    install_requires=requirements,
)
