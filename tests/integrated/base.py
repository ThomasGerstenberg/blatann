import os
import logging
from unittest import TestCase
from blatann import BleDevice
from blatann.gap.default_bond_db import DefaultBondDatabaseLoader
from blatann.utils import setup_logger

HERE = os.path.dirname(__file__)

BLATANN_QUICK_ENVKEY = "BLATANN_TEST_QUICK"
BLATANN_DEV1_ENVKEY = "BLATANN_DEV_1"
BLATANN_DEV2_ENVKEY = "BLATANN_DEV_2"
BLATANN_DEV3_ENVKEY = "BLATANN_DEV_3"


class BlatannTestCase(TestCase):
    dev1: BleDevice
    dev2: BleDevice
    logger: logging.Logger = None
    bond_db_file = os.path.join(HERE, "bond_db.pkl")

    @classmethod
    def setUpClass(cls) -> None:
        if BlatannTestCase.logger is None:
            BlatannTestCase.logger = setup_logger()
        cls.dev1: BleDevice = BleDevice(os.environ[BLATANN_DEV1_ENVKEY])
        cls.dev1.bond_db_loader = DefaultBondDatabaseLoader(cls.bond_db_file)
        # cls.dev2: BleDevice = BleDevice(os.environ[BLATANN_DEV2_ENVKEY])
        # cls.dev2.bond_db_loader = DefaultBondDatabaseLoader(cls.bond_db_file)

        cls.dev1.open(True)
        # cls.dev2.open(True)

    @classmethod
    def tearDownClass(cls) -> None:
        cls.dev1.close()
        # cls.dev2.close()


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
