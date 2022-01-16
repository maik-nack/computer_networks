import os

from .link import LinkInput, LinkOutput
from .message import Message, MessageHelloDataT, MessageType
from .topology import Topology
from logging import FileHandler, getLogger, INFO, Logger
from multiprocessing import Event
from random import choice
from time import sleep, time
from typing import Dict, List, Optional, Set, Tuple


class Router:
    _id: int
    _dr_link_input: LinkInput
    _dr_link_output: LinkOutput
    _links_inputs: List[LinkInput]
    _links_outputs: List[LinkOutput]
    _neighbors: Dict[int, int]
    _active_neighbors: Set[int]
    _topology: Optional[Topology]
    _topology_name: str
    _ways: Optional[Dict[int, List[int]]]
    _logger: Logger
    _sleep_time: float = 0.1

    def __init__(self, id_: int, dr_link_input: LinkInput, dr_link_output: LinkOutput, links_inputs: List[LinkInput],
                 links_outputs: List[LinkOutput], topology_name: str, logfile_path: Optional[str] = None):
        self._id = id_
        self._dr_link_input = dr_link_input
        self._dr_link_output = dr_link_output
        self._links_inputs = links_inputs
        self._links_outputs = links_outputs
        self._neighbors = {}
        self._active_neighbors = set()
        self._topology = None
        self._topology_name = topology_name
        self._ways = None
        self._logger = getLogger(f'R_{self._id}')
        self._logger.setLevel(INFO)
        if logfile_path is None:
            logfile_path = os.path.join(os.path.dirname(__file__), f'R_{self._id}_{self._topology_name}.log')
        with open(logfile_path, 'w'):
            pass
        fh = FileHandler(logfile_path)
        fh.setLevel(INFO)
        self._logger.addHandler(fh)

    def _receive_hello(self, stop_event: Event) -> Dict[int, Tuple[int, float]]:
        input_neighbors: Dict[int, Tuple[int, float]] = {}

        while not stop_event.is_set() and len(input_neighbors) != len(self._links_inputs):
            is_need_sleep = True
            for i, link in enumerate(self._links_inputs):
                if link.not_empty():
                    message = link.receive()

                    if message.type == MessageType.HELLO:
                        data: MessageHelloDataT = message.data
                        input_neighbors[message.src] = (data.id, time() - data.start_time)
                        self._logger.info(f'received hello from {message.src}')

                    is_need_sleep = False

            if is_need_sleep:
                sleep(self._sleep_time)

        return input_neighbors

    def _set_topology(self, topology: Topology):
        self._topology = topology
        self._ways = self._topology.get_shortest_ways(self._id)
        self._active_neighbors = set(self._topology.get_neighbors(self._id))
        self._logger.info(f'new shortest ways: {self._ways}')

    def _init_topology(self, stop_event: Event, input_neighbors: Dict[int, Tuple[int, float]]):
        is_need_set_neighbors = False
        is_topology_set = False
        is_neighbors_set = False

        while not stop_event.is_set() and not (is_topology_set and is_neighbors_set):
            is_need_sleep = True
            if self._dr_link_input.not_empty():
                message = self._dr_link_input.receive()
                if message.type == MessageType.GET_NEIGHBORS:
                    is_need_set_neighbors = True
                elif message.type == MessageType.SET_TOPOLOGY:
                    self._logger.info('received topology')
                    self._set_topology(message.data)
                    is_topology_set = True
                elif message.type == MessageType.SET_NEIGHBORS:
                    self._neighbors = message.data
                    is_neighbors_set = True
                    self._logger.info(f'received neighbours: {list(self._neighbors)}')
                is_need_sleep = False

            if is_need_set_neighbors:
                is_need_set_neighbors = False
                self._dr_link_output.send(Message(self._id, None, MessageType.SET_NEIGHBORS, input_neighbors))

            if is_need_sleep:
                sleep(self._sleep_time)

    def _hello_stage(self, stop_event: Event):
        for i, link in enumerate(self._links_outputs):
            link.send(Message(self._id, None, MessageType.HELLO, MessageHelloDataT(i, time())))

        input_neighbors = self._receive_hello(stop_event)
        self._init_topology(stop_event, input_neighbors)

    def _start_links(self):
        for link in self._links_inputs:
            link.start_receiving()
        for link in self._links_outputs:
            link.start_sending()
        self._dr_link_input.start_receiving()
        self._dr_link_output.start_sending()

    def _stop_links(self):
        for link in self._links_outputs:
            link.stop_sending()
        for link in self._links_inputs:
            link.stop_receiving()
        self._dr_link_output.stop_sending()
        self._dr_link_input.stop_receiving()

    def run(self, stop_event: Event, send_event: Event, *args):
        self._start_links()
        self._hello_stage(stop_event)

        active = True
        is_need_sleep = True

        while not stop_event.is_set():
            for link_in in self._links_inputs:
                if link_in.not_empty():
                    message = link_in.receive()
                    if message.type == MessageType.DATA and active:
                        if message.dst == self._id:
                            self._logger.info(f'received message from {message.src}: {message.data}')
                        elif message.dst in self._ways:
                            neighbor = self._ways[message.dst][1]
                            message.data += [self._id]
                            self._links_outputs[self._neighbors[neighbor]].send(message)
                            self._logger.info(f'transferred message from {message.src} to {message.dst}: '
                                              f'{message.data}')
                        else:
                            self._logger.info(f'cannot transfer message from {message.src} to {message.dst}')
                    is_need_sleep = False

            if send_event.is_set():
                if active:
                    node = choice(list(self._ways))
                    if len(self._ways[node]) == 0:
                        self._logger.info(f'cannot send message to {node}')
                    else:
                        message = Message(self._id, node, MessageType.DATA, [self._id])
                        self._links_outputs[self._neighbors[self._ways[node][1]]].send(message)
                        self._logger.info(f'sent message to {message.dst}: {message.data}')
                send_event.clear()

            if self._dr_link_input.not_empty():
                message = self._dr_link_input.receive()
                if message.type == MessageType.SET_TOPOLOGY:
                    self._logger.info('received topology')
                    self._set_topology(message.data)
                elif message.type == MessageType.DISCONNECT:
                    active = False
                is_need_sleep = False

            if is_need_sleep:
                sleep(self._sleep_time)

        self._stop_links()
