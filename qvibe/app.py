import logging

import faulthandler
import numpy as np
import pyaudio
from twisted.internet import reactor
from twisted.internet.endpoints import TCP4ServerEndpoint

from qvibe.config import Config
from qvibe.handler import AsyncHandler
from qvibe.interface import CommandFactory

logger = logging.getLogger(__name__)

# register a thread dumper
faulthandler.enable()
if hasattr(faulthandler, 'register'):
    import signal

    faulthandler.register(signal.SIGUSR2, all_threads=True)


class Wrapper:
    def __init__(self, stream_cfg):
        self.stream = None
        self.__fs = int(stream_cfg['fs'])
        self.__format = stream_cfg['format']
        self.__pa_format = getattr(pyaudio, self.__format)
        self.__divisor = self.__get_divisor()
        self.__device_idx = stream_cfg.get('device_idx', None)
        self.__pyaudio = pyaudio.PyAudio()
        self.handler = AsyncHandler()

    def __get_divisor(self):
        if self.__format == 'paInt16':
            return 2**15
        elif self.__format == 'paInt24':
            return 2**23
        elif self.__format == 'paFloat32':
            return 1

    @property
    def fs(self):
        return self.__fs

    def is_active(self):
        return self.stream is not None and self.stream.is_active()

    def stop(self):
        if self.is_active():
            self.stream.stop_stream()
        self.handler.accept(None)

    def ready(self, socket_handler):
        self.handler.accept(socket_handler)

    def start(self, tokens):
        vals = tokens.split('#')
        if len(vals) == 2:
            try:
                target_fs = int(vals[0])
                batch_size = int(vals[1])
                self.open(target_fs, batch_size)
            except:
                logger.exception(f"Unable to start using {tokens}")
        else:
            logger.warning(f"Unable to start using {tokens}")

    def report(self):
        '''
        Gets the state of the stream.
        :return: the state as a dict.
        '''
        return {
            'active': self.is_active(),
            'fs': self.fs,
            'format': self.__format,
            'device_idx': self.__device_idx
        }

    def open(self, target_fs, batch_size):
        frames = int(self.fs * batch_size / target_fs)
        logger.info(f"Opening stream [fs: {self.fs}, target_fs: {target_fs}, batch: {batch_size},  frames: {frames}, "
                    f"format: {self.__format}, device: {self.__device_idx}]")
        self.stream = self.__pyaudio.open(self.__fs, 1, self.__pa_format,
                                          input=True,
                                          input_device_index=self.__device_idx,
                                          frames_per_buffer=frames,
                                          stream_callback=self.callback)

    def callback(self, in_data, frame_count, time_info, status):
        if self.handler is not None:
            self.handler.handle((in_data, frame_count, time_info, status, self.__divisor))
        return None, pyaudio.paContinue


def run(args=None):
    """ The main routine. """
    cfg = Config()
    cfg.configure_logger()
    endpoint = TCP4ServerEndpoint(reactor, cfg.port)
    logger.info(f"Listening on port {cfg.port}")
    endpoint.listen(CommandFactory(Wrapper(cfg.config['interface'])))
    reactor.run()


if __name__ == '__main__':
    run()
