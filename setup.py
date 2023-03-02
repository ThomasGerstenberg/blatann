
from setuptools import setup, find_packages
from os import path


VERSION = "v0.5.0"

HERE = path.dirname(__file__)
with open(path.join(HERE, "README.md"), "r", encoding="utf-8") as f:
    long_description = f.read().replace("\r", "")


with open("requirements.txt") as f:
    install_requires = [line.strip() for line in f if line.strip()]


setup(
    name="blatann",
    version=VERSION.lstrip("v"),  # Remove the leading v, pip doesn't like that
    description="API for controlling nRF52 connectivity devices through pc-ble-driver-py",
    url="https://github.com/ThomasGerstenberg/blatann",
    author="Thomas Gerstenberg",
    author_email="tgerst6@gmail.com",
    keywords="ble bluetooth nrf52 nordic",
    packages=find_packages(exclude=["tests", "tests.*"]),
    install_requires=install_requires,
    python_requires=">=3.7.*",
    long_description_content_type="text/markdown",
    long_description=long_description,
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: BSD License",
        "Operating System :: OS Independent",
    ],
)
