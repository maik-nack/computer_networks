from copy import deepcopy
from queue import PriorityQueue
from networkx import DiGraph
from typing import Dict, List


class Topology:
    _graph: DiGraph

    def __init__(self):
        self._graph = DiGraph()

    @property
    def graph(self) -> DiGraph:
        return deepcopy(self._graph)

    def add_node(self, node_to_add: int):
        self._graph.add_node(node_to_add)

    def remove_node(self, node_to_del: int):
        self._graph.remove_node(node_to_del)

    def add_edge(self, src: int, dst: int, weight: float):
        self._graph.add_edge(src, dst, weight=weight)

    def remove_edge(self, src: int, dst: int):
        self._graph.remove_edge(src, dst)

    def get_neighbors(self, node: int) -> List[int]:
        return list(self._graph.neighbors(node))

    def has_edge(self, src: int, dst: int) -> bool:
        return self._graph.has_edge(src, dst)

    def get_weight(self, src: int, dst: int) -> float:
        return self._graph[src][dst]['weight']

    def get_shortest_ways(self, root_node: int) -> Dict[int, List[int]]:
        ways = {node: [] for node in self._graph}
        ways[root_node] = [root_node]

        distances = {node: float('inf') for node in self._graph}
        distances[root_node] = 0

        queue = PriorityQueue()
        queue.put((0, root_node))

        unvisited = set(self._graph)

        while not queue.empty():
            (distance, node) = queue.get()
            if node not in unvisited:
                continue
            unvisited.remove(node)

            for neighbor, attrs in self._graph[node].items():
                if neighbor in unvisited:
                    new_cost = distance + attrs['weight']
                    if new_cost < distances[neighbor]:
                        queue.put((new_cost, neighbor))
                        distances[neighbor] = new_cost
                        ways[neighbor] = ways[node] + [neighbor]

        ways.pop(root_node)
        return ways
