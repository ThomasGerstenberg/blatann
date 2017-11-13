
from setuptools import setup, find_packages
import sys


VERSION = "v0.1.0"

py2 = sys.version_info[0] == 2
py3 = sys.version_info[0] == 3

_install_requires = ["pc-ble-driver-py"]

if py2:
    _install_requires.extend(["enum34"])


setup(
    name="blatann",
    version=VERSION.lstrip("v"),  # Remove the leading v, pip doesn't like that
    description="API for controlling nRF52 connectivity devices through pc-ble-driver-py",
    url="https://github.com/ThomasGerstenberg/blatann",
    author="Thomas Gerstenberg",
    email="tgerst6@gmail.com",
    keywords="ble bluetooth nrf52 nordic",
    packages=find_packages(exclude=["test", "test.*"]),
    install_requires=_install_requires,
)
