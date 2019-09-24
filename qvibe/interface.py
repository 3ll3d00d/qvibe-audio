import logging
from enum import Enum

import numpy as np
import resampy
from twisted.internet.protocol import Factory, connectionDone
from twisted.protocols.basic import LineReceiver

from qvibe.handler import DataHandler

logger = logging.getLogger(__name__)


class Command(Enum):
    GET = 1
    SET = 2


class SocketHandler(DataHandler):

    def __init__(self, protocol):
        self.protocol = protocol
        self.new_fs = 500
        self.fs = 48000

    def handle(self, data):
        in_data, frame_count, time_info, status, divisor = data
        try:
            decoded = np.frombuffer(in_data, dtype=np.int16) / divisor
            decimated = resampy.resample(decoded, self.fs, self.new_fs, filter=load_resampy_filter())
            logger.info(f"Decimated {decoded.size} to {decimated.size} samples")
            self.protocol.sendLine(f"DAT|{'|'.join([str(d) for d in decimated])}".encode())
        except:
            logger.exception(f"Unserialisable data type {data.__class__.__name__}")

    def on_init_fail(self, event_time, message):
        pass


class CommandProtocol(LineReceiver):

    def __init__(self, wrapper):
        self.wrapper = wrapper

    def rawDataReceived(self, data):
        pass

    def connectionLost(self, reason=connectionDone):
        self.wrapper.stop()

    def connectionMade(self):
        self.wrapper.ready(SocketHandler(self))

    def send_stream_state(self, state):
        import json
        y = json.dumps(state)
        self.sendLine(f"DST|{y}".encode())

    def lineReceived(self, line):
        tokens = line.decode().split('|')
        try:
            cmd = Command[tokens[0]]
            if cmd == Command.GET:
                self.send_stream_state(self.wrapper.report())
            elif cmd == Command.SET:
                self.wrapper.start(tokens[1])
                self.send_stream_state(self.wrapper.report())
        except KeyError as e:
            logger.info(f"Unknown command in {line}")
        except Exception as e:
            logger.exception(f"Failed to handle command - {line}")


class CommandFactory(Factory):

    def __init__(self, wrapper):
        self.wrapper = wrapper

    def buildProtocol(self, addr):
        return CommandProtocol(self.wrapper)


def load_resampy_filter():
    '''
    A replacement for resampy.load_filter that is compatible with pyinstaller.
    :return: same values as resampy.load_filter
    '''
    import sys
    if getattr(sys, 'frozen', False):
        def __load_frozen():
            import os
            data = np.load(
                os.path.join(sys._MEIPASS, '_resampy_filters', os.path.extsep.join(['kaiser_fast', 'npz'])))
            return data['half_window'], data['precision'], data['rolloff']

        return __load_frozen
    else:
        return 'kaiser_fast'

