from dataclasses import dataclass
from pathlib import Path

from port_monitor import PortMonitor
from comms import Message, send_receive, pretty_hexlify
import intelhex


def main():
    f = Path(__file__).parent.joinpath('example.hex').read_text()
    messages = intelhex.parse_text(f)

    port_monitor = PortMonitor()
    port_monitor.scan_and_connect()
    print(port_monitor.ports, port_monitor.port)

    for msg in messages:
        r = send_receive(port_monitor.port, msg)
        if r:
           print(r, pretty_hexlify(r.data))


if __name__ == '__main__':
    main()
