from .packet import Packet
from multiprocessing import Queue
from typing import Iterable


class Connection:
    _queue_to_send: Queue
    _queue_to_ack: Queue

    def __init__(self):
        self._queue_to_send = Queue()
        self._queue_to_ack = Queue()

    def send(self, packet: Packet):
        self._queue_to_send.put(packet)

    def send_packets(self, packets: Iterable[Packet]):
        for packet in packets:
            self._queue_to_send.put(packet)

    def ack(self, packet_id: int):
        self._queue_to_ack.put(packet_id)

    def not_empty_send(self) -> bool:
        return not self._queue_to_send.empty()

    def not_empty_ack(self) -> bool:
        return not self._queue_to_ack.empty()

    def receive_send(self) -> Packet:
        return self._queue_to_send.get()

    def receive_ack(self) -> int:
        return self._queue_to_ack.get()
