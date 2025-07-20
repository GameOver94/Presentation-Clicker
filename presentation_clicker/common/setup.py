from setuptools import setup, find_packages

setup(
    name='presentation-clicker-common',
    version='0.1.0',
    packages=find_packages(),
    install_requires=[
        'cryptography',
        'ttkbootstrap',
        'pyyaml',
    ],
    author='Patrick Harrer',
    author_email='patrick.harrer94@hotmail.com',
    url='https://github.com/GameOver94/Presentation-Clicker-Development/',
    license='MIT',
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Intended Audience :: End Users/Desktop',
        'Topic :: Utilities',
    ],
    description='Presentation Clicker Common Library',
    include_package_data=True,
    python_requires='>=3.8',
)
