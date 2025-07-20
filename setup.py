"""
Setup configuration for Presentation Clicker.
"""
from setuptools import setup, find_packages
import os

# Read README if it exists
def read_readme():
    readme_path = os.path.join(os.path.dirname(__file__), 'README.md')
    if os.path.exists(readme_path):
        with open(readme_path, 'r', encoding='utf-8') as f:
            return f.read()
    return ""

# Read requirements if it exists
def read_requirements():
    req_path = os.path.join(os.path.dirname(__file__), 'requirements.txt')
    if os.path.exists(req_path):
        with open(req_path, 'r', encoding='utf-8') as f:
            return [line.strip() for line in f if line.strip() and not line.startswith('#')]
    return [
        'paho-mqtt>=1.6.0',
        'PyYAML>=6.0',
        'Pillow>=10.0.0',
        'ttkbootstrap>=1.10.0',
        'cryptography>=41.0.0',
        'keyboard>=0.13.5',
    ]

setup(
    name="presentation-clicker",
    version="0.3.0",
    description="Wireless presentation remote control system using MQTT",
    long_description=read_readme(),
    long_description_content_type="text/markdown",
    author="GameOver94",
    url="https://github.com/GameOver94/Presentation-Clicker-Development",
    packages=find_packages(),
    include_package_data=True,
    package_data={
        'presentation_clicker.client': ['*.yaml'],
        'presentation_clicker.server': ['*.yaml'],
    },
    install_requires=read_requirements(),
    python_requires='>=3.8',
    entry_points={
        'console_scripts': [
            'presentation-clicker=presentation_clicker.cli:main',
        ],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: End Users/Desktop",
        "Topic :: Multimedia :: Graphics :: Presentation",
        "Topic :: System :: Networking",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Operating System :: OS Independent",
    ],
    keywords="presentation remote control mqtt wireless",
    project_urls={
        "Bug Reports": "https://github.com/GameOver94/Presentation-Clicker-Development/issues",
        "Source": "https://github.com/GameOver94/Presentation-Clicker-Development",
    },
)
