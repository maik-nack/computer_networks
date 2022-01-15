from .connection import Connection
from .packet import Packet
from random import random
from time import time


def sender(bytes_to_send: bytes, window_size: int, connection: Connection) -> int:
    timeout = 0.2
    strong_timeout = 10
    packets_count_to_send = len(bytes_to_send)

    last_sent_packet_id = min(window_size, packets_count_to_send) - 1
    connection.send_packets((Packet(i, bytes_to_send[i:i + 1]) for i in range(last_sent_packet_id + 1)))
    sent_packets = last_sent_packet_id + 1
    window = dict.fromkeys(range(0, last_sent_packet_id + 1), time())

    start = time()
    while not connection.not_empty_ack():
        if time() - start > strong_timeout:
            for packet_id, start in window.items():
                connection.send(Packet(packet_id, bytes_to_send[packet_id:packet_id + 1]))
                window[packet_id] = time()
            start = time()
            sent_packets += len(window)

    while len(window) > 0:
        if connection.not_empty_ack():
            packet_id = connection.receive_ack()
            window.pop(packet_id, None)

        for packet_id, start in window.items():
            current = time()
            if current - start > timeout:
                connection.send(Packet(packet_id, bytes_to_send[packet_id:packet_id + 1]))
                window[packet_id] = current
                sent_packets += 1

        while len(window) < window_size and last_sent_packet_id < packets_count_to_send - 1:
            last_sent_packet_id += 1
            sent_packets += 1
            connection.send(Packet(last_sent_packet_id, bytes_to_send[last_sent_packet_id:last_sent_packet_id + 1]))
            window[last_sent_packet_id] = time()

    connection.send(Packet(-1, b''))
    return sent_packets


def receiver(transmission_error_probability: float, connection: Connection) -> bytes:
    bytes_ = b''

    while True:
        if connection.not_empty_send():
            packet: Packet = connection.receive_send()
            if packet.id == -1:
                break

            if random() > transmission_error_probability:
                connection.ack(packet.id)
                if len(bytes_) == packet.id:
                    bytes_ += packet.data
                elif len(bytes_) > packet.id:
                    bytes_ = bytes_[:packet.id] + packet.data + bytes_[packet.id + 1:]
                else:
                    bytes_ = bytes_ + b''.join(b' ' for _ in range(packet.id - len(bytes_))) + packet.data

    return bytes_
