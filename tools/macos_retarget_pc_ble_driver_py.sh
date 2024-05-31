#!/usr/bin/env bash

# Script to retarget the pc-ble-driver-py dependencies to a different python install.
# The shared object in the library is linked against the system-installed python, which is not
# ideal since people commonly use brew-installed python instead (or anaconda).
#
# This script should be run within the python environment you want to use,
# and blatann + pc-ble-driver-py should already be pip-installed into the environment.
# This script also need the "Command Line Tools for Xcode" to use xcrun command
# You can find it here: https://developer.apple.com/download/all/?q=command%20line%20tools
#
# NOTE: This will need to be run any time pc-ble-driver-py is installed or updated, even virtual environments.
#       Easy test to see if it needs to be run: `import blatann` will fail

# Python executable to use. Change this out if something other than python3 should be used
PYTHON=python3

# Get the location
PYTHON_LOC=`which $PYTHON`

if [[ -z $PYTHON_LOC ]]
then
	echo "ERROR: Unable to find python location"
	exit -1
fi

echo "targeting python @ $PYTHON_LOC"
echo

# Ensure blatann and pc-ble-driver-py are already installed
BLATANN=`$PYTHON -m pip list | grep blatann`
PC_BLE_DRIVER_PY=`$PYTHON -m pip list | grep "pc_ble_driver_py\|pc-ble-driver-py"

if [[ -z $BLATANN ]]
then
	echo "ERROR: unable to find blatann install. Run 'pip install blatann' prior to running this script"
	exit -1
fi

echo "found lib: $BLATANN"

if [[ -z $PC_BLE_DRIVER_PY ]]
then
	echo "ERROR: unable to find pc-ble-driver-py install. Run 'pip install pc-ble-driver-py' prior to running this script"
	exit -1
fi

echo "found lib: $PC_BLE_DRIVER_PY"

# Get the location of pc-ble-driver-py by importing the lib and printing out its directory
PC_BLE_DRIVER_LOC=`$PYTHON -c "import os, pc_ble_driver_py; print(os.path.dirname(pc_ble_driver_py.__file__))"`
# For the python2.7 version change the path to 'lib/macos_osx/_pc_ble_driver_sd_api_v3.so'
PC_BLE_DRIVER_LIB=$PC_BLE_DRIVER_LOC/lib/_nrf_ble_driver_sd_api_v5.so

echo "pc-ble-driver location: $PC_BLE_DRIVER_LOC"
echo "library to patch:       $PC_BLE_DRIVER_LIB"
echo

# Determine the location of the Python libraries for the target python and currently-linked python.
# Output of otool -L is:
# path/to/lib
#    path/to/dependency1 (version compat info)
#    path/to/dependency2 (version compat info)
#    ...
#
# We need to find the Python.framework dependency so we can switch it out using install_name_tool
#
# Command breakdown:
#    otool -L : Print out library dependencies (above)
#    tail -n +2 : Skip the first line (path of the library itself), in case it also includes 'Python.framework'
#    grep : Find the entry with the path to the Python framework dependency
#    cut : Cut on spaces and take only the first part (the path)
#    xargs : strip off whitespace from the otool output
TARGET_LIB=`otool -L $PYTHON_LOC | tail -n +2 | grep Python.framework | cut -d " " -f 1 | xargs`
CURRENT_LIB=`otool -L $PC_BLE_DRIVER_LIB | tail -n +2 | grep Python.framework | cut -d " " -f 1 | xargs`

# Sanity-check both paths are found
if [[ -z $TARGET_LIB || -z $CURRENT_LIB ]]
then
	echo "ERROR: unable to find paths in otool!"
	exit -1
fi

echo "re-linking library"
echo "old:    $CURRENT_LIB"
echo "new:    $TARGET_LIB"
echo

# Change out the current lib with the target
install_name_tool -change $CURRENT_LIB $TARGET_LIB $PC_BLE_DRIVER_LIB

# Verify the change worked
echo "testing that blatann can be imported..."
if $PYTHON -c "import blatann"
then
	echo "Success!"
else
	echo "Re-target failed!"
	exit -1
fi
