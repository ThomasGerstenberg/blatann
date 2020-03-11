import os
import logging
from typing import Optional
from unittest import TestCase, SkipTest

from blatann import BleDevice
from blatann.gap.default_bond_db import DefaultBondDatabaseLoader
from blatann.utils import setup_logger

HERE = os.path.dirname(__file__)

BLATANN_QUICK_ENVKEY = "BLATANN_TEST_QUICK"
BLATANN_DEV_ENVKEY_FORMAT = "BLATANN_DEV_{}"
BOND_DB_FILE_FMT = os.path.join(HERE, "bond_db{}.pkl")


def _configure_device(dev_number, config, optional=False):
    env_key = BLATANN_DEV_ENVKEY_FORMAT.format(dev_number)
    comport = os.environ.get(env_key, None)
    if not comport:
        if optional:
            return None
        raise EnvironmentError(f"Environment variable {env_key} must be defined with the device's comport")
    dev = BleDevice(comport)
    dev.bond_db_loader = DefaultBondDatabaseLoader(BOND_DB_FILE_FMT.format(dev_number))
    dev.configure(**config)
    return dev


class BlatannTestCase(TestCase):
    dev1: BleDevice
    dev2: BleDevice
    dev3: Optional[BleDevice]
    logger: logging.Logger = None
    bond_db_file_fmt = os.path.join(HERE, "bond_db{}.pkl")

    requires_3_devices = False
    dev1_config = {}
    dev2_config = {}
    dev3_config = {}

    @classmethod
    def setUpClass(cls) -> None:
        if BlatannTestCase.logger is None:
            BlatannTestCase.logger = setup_logger()

        cls.dev1 = _configure_device(1, cls.dev1_config)
        cls.dev2 = _configure_device(2, cls.dev2_config)

        if cls.requires_3_devices:
            cls.dev3 = _configure_device(3, cls.dev3_config)
            if not cls.dev3:
                raise SkipTest("Need third device for this TestCase")
        else:
            cls.dev3 = None

        cls.dev1.open(True)
        cls.dev2.open(True)
        if cls.dev3:
            cls.dev3.open(True)

    @classmethod
    def tearDownClass(cls) -> None:
        cls.dev1.close()
        cls.dev2.close()
        if cls.dev3:
            cls.dev3.close()


class TestParams(object):
    def __init__(self, test_params, setup=None, teardown=None):
        self.test_params = test_params
        self._setup = setup
        self._teardown = teardown

    def __call__(self, func):
        def subtest_runner(test_case: BlatannTestCase):
            try:
                self.setup(test_case)

                for tc in self.test_params:
                    with test_case.subTest(**tc):
                        param_s = ", ".join("{}={!r}".format(k, v) for k, v in tc.items())
                        test_case.logger.info(
                            "Running {}.{}({})".format(self.__class__.__name__, func.__name__, param_s))
                        func(test_case, **tc)
            finally:
                self.teardown(test_case)

        return subtest_runner

    def setup(self, test_case: BlatannTestCase):
        if self._setup and callable(self._setup):
            instancemethod = getattr(test_case, self._setup.__name__, None)
            if instancemethod:
                instancemethod()
            else:
                self._setup()

    def teardown(self, test_case: BlatannTestCase):
        if self._teardown and callable(self._teardown):
            instancemethod = getattr(test_case, self._teardown.__name__, None)
            if instancemethod:
                instancemethod()
            else:
                self._teardown()


def long_running(func):
    def f(self: TestCase, *args, **kwargs):
        quick_tests = int(os.environ.get(BLATANN_QUICK_ENVKEY, 0))
        if quick_tests:
            name = "{}.{}".format(self.__class__.__name__, func.__name__)
            self.skipTest("Skipping {} because it's a long-running test ({}={})".format(name, BLATANN_QUICK_ENVKEY, quick_tests))
        func(self, *args, **kwargs)
    return f
