import re
import serial
import serial.tools.list_ports

import logging
log = logging.getLogger(__name__)


def _port_sort_key(s):
    '''
    >>> _port_sort_key('COM12A')
    ('COM', 12, 'A')

    >>> _port_sort_key('abc')
    ('abc', -1, '')

    >>> sorted(['COM1', 'COM3', 'COM12', 'AA', 'AA1', 'AA1b'], key=_port_sort_key)
    ['AA', 'AA1', 'AA1b', 'COM1', 'COM3', 'COM12']
    '''
    prefix, num, suffix = re.match(r'([^\d]*)(\d*)(.*)', s).groups()
    return (prefix, int(num) if num else -1, suffix)


def best_port(ports):
    '''Attempt to sort ports numerically, expect names like COM1 but deal with other possibilities gracefully'''
    return max(ports, key=_port_sort_key)


class PortMonitor:
    def __init__(self, connection_status_changed_callback=None):
        self.connection_status_changed_callback = connection_status_changed_callback
        self.port = None
        self.ports = {}
        # after first appearing, a port is unconnectable for a while. Store this in order to keep retrying.
        self.last_seen_new_ports = {}


    def scan(self):
        self.ports = { p.device: p.description for p in serial.tools.list_ports.comports() }


    def scan_and_connect(self):
        # complicated logic!
        old_ports = self.ports
        self.scan()

        if self.port and self.port.name not in self.ports:
            self.disconnect()

        new_ports = self.ports.keys() - old_ports.keys()
        if new_ports:
            # if we get some new ports this time, forget all old stuff and try to connect to them
            self.last_seen_new_ports = new_ports
        else:
            # use previous iteration
            new_ports = self.last_seen_new_ports
        # but make sure we are not trying to connect to removed ports
        new_ports &= self.ports.keys()

        # reconnect if new port(s) have appeared
        # if no new ports appeared but we are not connected, connect to the best available port
        if not self.port and not new_ports:
            new_ports = self.ports.keys()

        if new_ports:
            log.debug(f'New ports: {list(new_ports)}')
            if self.connect(best_port(new_ports)):
                self.last_seen_new_ports = {}


    def connect(self, port_name):
        self.disconnect()
        log.info(f'Connecting to {port_name!r}')
        try:
            port = serial.Serial(port_name)
            port.timeout = 0.3
            port.write_timeout = 0.5
            self.port = port
            log.info(f'Connected to {self.port.name!r}')
            self._on_connection_status_changed(True)
            return True
        except Exception as exc:
            log.error(f'Failed to connect to {port_name!r}: {exc}')


    def disconnect(self):
        if self.port:
            self.port.close()
            self.port = None
            log.info('Disconnected')
            self._on_connection_status_changed(False)


    def _on_connection_status_changed(self, connected: bool):
        if self.connection_status_changed_callback:
            self.connection_status_changed_callback(connected)





if __name__ == '__main__':
    import doctest
    doctest.testmod(verbose=True)

