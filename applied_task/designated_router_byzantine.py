import os

from .network_layer import DesignatedRouter, LinkInput, LinkOutput
from multiprocessing import Event
from time import sleep
from typing import List


class DesignatedRouterByzantine(DesignatedRouter):
    def __init__(self, id_: int, links_inputs: List[LinkInput], links_outputs: List[LinkOutput],
                 disconnection_probabilities: List[float], topology_name: str):
        logfile_path = os.path.join(os.path.dirname(__file__), f'DR_{topology_name}.log')
        super().__init__(id_, links_inputs, links_outputs, disconnection_probabilities, topology_name, logfile_path)

    def _save_topology(self, topology_index: int):
        traitors = list(map(lambda s: int(s.split('-')[0]), self._topology_name.split('_')[2:]))
        graph = self._topology.graph
        for active_node in self._active_nodes:
            graph.nodes[active_node]['title'] = 'lieutenant' if active_node > 0 else 'general'
            if active_node in traitors:
                graph.nodes[active_node]['color'] = 'red'
        self._save_graph(graph, topology_index)

    def run(self, stop_event: Event, *args):
        self._start_links()
        self._init_topology_stage(stop_event)
        is_need_set_topology = True
        is_need_sleep = True

        while not stop_event.is_set():
            if is_need_set_topology:
                self._set_topology(0)
                is_need_set_topology = False

            if is_need_sleep:
                sleep(self._sleep_time)

        self._stop_links()
