import pickle

from .link_layer import Connection, ProtocolT, RECEIVER, ReceiverT, SENDER, SenderT
from .message import Message
from queue import Queue
from threading import Thread
from typing import Tuple


class LinkInput:
    _connection: Connection
    _receiver: ReceiverT
    _received_messages: Queue
    _is_receiving_running: bool
    _receiving_thread: Thread

    def __init__(self, connection: Connection, protocol: ProtocolT = 'selective_repeat'):
        self._connection = connection
        self._receiver = RECEIVER[protocol]
        self._is_receiving_running = True

    def _run_receiving(self):
        while self._is_receiving_running:
            if self._connection.not_empty_send():
                bytes_ = self._receiver(0.3, self._connection)
                message = pickle.loads(bytes_)
                self._received_messages.put(message)

    def start_receiving(self):
        self._received_messages = Queue()
        self._is_receiving_running = True
        self._receiving_thread = Thread(target=self._run_receiving)
        self._receiving_thread.start()

    def stop_receiving(self):
        self._is_receiving_running = False
        self._receiving_thread.join()

    def not_empty(self) -> bool:
        return not self._received_messages.empty()

    def receive(self) -> Message:
        return self._received_messages.get()


class LinkOutput:
    _connection: Connection
    _sender: SenderT
    _messages_to_send: Queue
    _is_sending_running: bool
    _sending_thread: Thread

    def __init__(self, connection: Connection, protocol: ProtocolT = 'selective_repeat'):
        self._connection = connection
        self._sender = SENDER[protocol]
        self._is_sending_running = True

    def _run_sending(self):
        while self._is_sending_running:
            if not self._messages_to_send.empty():
                message = self._messages_to_send.get()
                bytes_ = pickle.dumps(message)
                self._sender(bytes_, 25, self._connection)

    def start_sending(self):
        self._messages_to_send = Queue()
        self._is_sending_running = True
        self._sending_thread = Thread(target=self._run_sending)
        self._sending_thread.start()

    def stop_sending(self):
        self._is_sending_running = False
        self._sending_thread.join()

    def not_empty(self) -> bool:
        return not self._messages_to_send.empty()

    def send(self, message: Message):
        self._messages_to_send.put(message)


def get_link(protocol: ProtocolT = 'selective_repeat') -> Tuple[LinkOutput, LinkInput]:
    connection = Connection()
    link_output = LinkOutput(connection, protocol)
    link_input = LinkInput(connection, protocol)
    return link_output, link_input
