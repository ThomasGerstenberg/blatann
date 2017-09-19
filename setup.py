
from setuptools import setup, find_packages
from os import path


VERSION = "v0.1.0"


setup(
    name="blatann",
    version=VERSION.lstrip("v"),  # Remove the leading v, pip doesn't like that
    description="API for controlling nRF52 connectivity devices through pc-ble-driver-py",
    url="https://github.com/ThomasGerstenberg/blatann",
    packages=find_packages(exclude=["test", "test.*"]),
    install_requires=[
        "pc-ble-driver-py",
        "enum34"
    ],
)
