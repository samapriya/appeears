import setuptools
from setuptools import find_packages


def readme():
    with open("README.md") as f:
        return f.read()


setuptools.setup(
    name="appeears",
    version="0.0.3",
    packages=find_packages(),
    url="https://github.com/samapriya/appeears",
    install_requires=[
        "tqdm >= 4.56.0",
        "requests >= 2.28.1",
        "natsort >= 8.1.0",
        "beautifulsoup4>=4.11.1",
        "PyGeoj==1.0.0"
    ],
    license="Apache 2.0",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    classifiers=[
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research",
        "Natural Language :: English",
        "License :: OSI Approved :: Apache Software License",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Operating System :: OS Independent",
        "Topic :: Scientific/Engineering :: GIS",
    ],
    author="Samapriya Roy",
    author_email="samapriya.roy@gmail.com",
    description="Simple CLI for NASA AppEEARS API",
    entry_points={
        "console_scripts": [
            "appeears=appeears.appeears:main",
        ],
    },
)
