from setuptools import setup, find_packages

setup(
    name='presentation-clicker-client',
    version='0.1.0',
    packages=find_packages(),
    install_requires=[
        'paho-mqtt',
        'cryptography',
        'ttkbootstrap',
        'pyyaml',
    ],
    entry_points={
        'console_scripts': [
            'presentation-clicker-client=presentation_clicker_client.ui_client:main',
        ],
    },
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
    description='Presentation Clicker Client',
    include_package_data=True,
    long_description=open('README.md').read() if __import__('os').path.exists('README.md') else '',
    long_description_content_type='text/markdown',
    python_requires='>=3.8',
)
