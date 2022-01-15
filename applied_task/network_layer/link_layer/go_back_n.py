from .connection import Connection
from .packet import Packet
from random import random
from time import time


def sender(bytes_to_send: bytes, window_size: int, connection: Connection) -> int:
    timeout = 0.2
    strong_timeout = 10
    last_acked_packet_id = -1
    packets_count_to_send = len(bytes_to_send)

    last_sent_packet_id = min(window_size, packets_count_to_send) - 1
    connection.send_packets((Packet(i, bytes_to_send[i:i + 1]) for i in range(last_sent_packet_id + 1)))
    start = time()
    sent_packets = last_sent_packet_id + 1

    while not connection.not_empty_ack():
        if time() - start > strong_timeout:
            connection.send_packets((Packet(i, bytes_to_send[i:i + 1]) for i in range(last_sent_packet_id + 1)))
            start = time()
            sent_packets += last_sent_packet_id + 1

    while last_acked_packet_id < packets_count_to_send - 1:
        if connection.not_empty_ack():
            packet_id = connection.receive_ack()
            if packet_id == last_acked_packet_id + 1:
                last_acked_packet_id += 1
                if last_sent_packet_id < packets_count_to_send - 1:
                    last_sent_packet_id += 1
                    sent_packets += 1
                    connection.send(Packet(last_sent_packet_id,
                                           bytes_to_send[last_sent_packet_id:last_sent_packet_id + 1]))
                start = time()

        if time() - start > timeout:
            packet_id = last_acked_packet_id + 1
            last_sent_packet_id = min(packet_id + window_size, packets_count_to_send) - 1
            connection.send_packets((Packet(i, bytes_to_send[i:i + 1])
                                     for i in range(packet_id, last_sent_packet_id + 1)))
            sent_packets += last_sent_packet_id - packet_id + 1
            start = time()

    connection.send(Packet(-1, b''))
    return sent_packets


def receiver(transmission_error_probability: float, connection: Connection) -> bytes:
    last_acked_packet_id = -1
    bytes_ = b''

    while True:
        if connection.not_empty_send():
            packet: Packet = connection.receive_send()
            if packet.id == -1:
                break

            if packet.id == last_acked_packet_id + 1 and random() > transmission_error_probability:
                last_acked_packet_id += 1
                connection.ack(packet.id)
                bytes_ += packet.data

    return bytes_
