import os

from .link import LinkInput, LinkOutput
from .message import Message, MessageType
from .topology import Topology
from logging import FileHandler, getLogger, INFO, Logger
from multiprocessing import Event
from networkx import DiGraph
from pyvis.network import Network
from random import random
from time import sleep
from typing import Dict, List, Optional, Set, Tuple


class DesignatedRouter:
    _id: int
    _links_inputs: List[LinkInput]
    _links_outputs: List[LinkOutput]
    _nodes: Dict[int, int]
    _active_nodes: Set[int]
    _disconnection_probabilities: List[float]
    _topology: Optional[Topology]
    _topology_name: str
    _logger: Logger
    _sleep_time: float = 0.1

    def __init__(self, id_: int, links_inputs: List[LinkInput], links_outputs: List[LinkOutput],
                 disconnection_probabilities: List[float], topology_name: str, logfile_path: Optional[str] = None):
        self._id = id_
        self._links_inputs = links_inputs
        self._links_outputs = links_outputs
        self._nodes = {}
        self._active_nodes = set()
        self._disconnection_probabilities = disconnection_probabilities
        self._topology = None
        self._topology_name = topology_name
        self._logger = getLogger('DR')
        self._logger.setLevel(INFO)
        if logfile_path is None:
            logfile_path = os.path.join(os.path.dirname(__file__), f'DR_{self._topology_name}.log')
        with open(logfile_path, 'w'):
            pass
        fh = FileHandler(logfile_path)
        fh.setLevel(INFO)
        self._logger.addHandler(fh)

    def _init_topology_stage(self, stop_event: Event):
        for link in self._links_outputs:
            link.send(Message(self._id, None, MessageType.GET_NEIGHBORS, None))

        self._topology = Topology()
        neighbors: Dict[int, Dict[int, int]] = {}
        is_need_sleep = True

        while not stop_event.is_set() and len(self._nodes) != len(self._links_outputs):
            for i, link in enumerate(self._links_inputs):
                if link.not_empty():
                    message = link.receive()

                    if message.type == MessageType.SET_NEIGHBORS:
                        self._nodes[message.src] = i
                        input_neighbors: Dict[int, Tuple[int, float]] = message.data
                        for neighbor, (link_id, weight) in input_neighbors.items():
                            self._topology.add_edge(neighbor, message.src, weight)
                            neighbors[neighbor] = neighbors.get(neighbor, {})
                            neighbors[neighbor][message.src] = link_id
                    is_need_sleep = False

            if is_need_sleep:
                sleep(self._sleep_time)

        self._active_nodes = set(self._nodes)

        for active_node in self._active_nodes:
            link = self._links_outputs[self._nodes[active_node]]
            link.send(Message(self._id, active_node, MessageType.SET_NEIGHBORS, neighbors.get(active_node, {})))

    def _save_graph(self, graph: DiGraph, topology_index: int):
        network = Network(directed=True)
        network.from_nx(graph)
        base_path = os.path.dirname(self._logger.handlers[0].baseFilename)  # type: ignore
        filename = f'topology_{self._topology_name}_{topology_index}.html'
        network.save_graph(os.path.join(base_path, filename))
        self._logger.info(f'saved topology graph in file {filename}')

    def _save_topology(self, topology_index: int):
        graph = self._topology.graph
        graph.add_node(-1, color='red', title='designated_router')
        for active_node in self._active_nodes:
            graph.nodes[active_node]['title'] = 'router'
            graph.add_edge(-1, active_node, color='red')
            graph.add_edge(active_node, -1, color='red')
        self._save_graph(graph, topology_index)

    def _set_topology(self, topology_index: int):
        for active_node in self._active_nodes:
            link = self._links_outputs[self._nodes[active_node]]
            link.send(Message(self._id, active_node, MessageType.SET_TOPOLOGY, self._topology))
        self._save_topology(topology_index)

    def _start_links(self):
        for link in self._links_inputs:
            link.start_receiving()
        for link in self._links_outputs:
            link.start_sending()

    def _stop_links(self):
        for link in self._links_outputs:
            link.stop_sending()
        for link in self._links_inputs:
            link.stop_receiving()

    def run(self, stop_event: Event, connection_off_event: Event, *args):
        self._start_links()
        self._init_topology_stage(stop_event)
        is_need_set_topology = True
        topology_index = 0
        is_need_sleep = True

        while not stop_event.is_set():
            if connection_off_event.is_set():
                for active_node in self._active_nodes:
                    if random() < self._disconnection_probabilities[active_node]:
                        is_need_set_topology = True
                        connection_off_event.clear()
                        self._topology.remove_node(active_node)
                        self._active_nodes.remove(active_node)
                        link = self._links_outputs[self._nodes[active_node]]
                        link.send(Message(self._id, active_node, MessageType.DISCONNECT, None))
                        self._logger.info(f'lost connection to node {active_node}')
                        break

            if is_need_set_topology:
                self._set_topology(topology_index)
                is_need_set_topology = False
                topology_index += 1

            if is_need_sleep:
                sleep(self._sleep_time)

        self._stop_links()
