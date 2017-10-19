import logging
import sys


LOG_FORMAT = "[%(asctime)s] [%(threadName)s] [%(name)s.%(funcName)s:%(lineno)s] [%(levelname)s]: %(message)s"


def setup_logger(name=None, level="DEBUG"):
    logger = logging.getLogger(name)
    logger.setLevel(level)
    formatter = logging.Formatter(LOG_FORMAT)
    stream_handler = logging.StreamHandler(sys.stderr)
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)
    return logger


def find_target_device(ble_device, name):
    scan_report = ble_device.scanner.start_scan().wait()

    for report in scan_report.advertising_peers_found:
        if report.advertise_data.local_name == name:
            return report.peer_address
