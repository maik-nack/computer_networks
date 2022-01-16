import os

from .message_data import MessageData
from .network_layer import LinkInput, LinkOutput, Message, MessageType, Router
from .tree import TreeNode
from collections import Counter
from multiprocessing import Event
from random import randint
from time import sleep
from typing import List, Tuple


class RouterLieutenant(Router):
    _is_traitor: bool
    _value: bool

    def __init__(self, id_: int, dr_link_input: LinkInput, dr_link_output: LinkOutput, general_link_input: LinkInput,
                 lieutenants_links_inputs: List[LinkInput], lieutenants_links_outputs: List[LinkOutput],
                 is_traitor: bool, topology_name: str):
        logfile_path = os.path.join(os.path.dirname(__file__), f'R-Lieutenant_{id_}_{topology_name}.log')
        super().__init__(id_, dr_link_input, dr_link_output, [general_link_input] + lieutenants_links_inputs,
                         lieutenants_links_outputs, topology_name, logfile_path)
        self._is_traitor = is_traitor
        self._logger.info(f"I'm{' ' if self._is_traitor else ' not '}a traitor")

    @property
    def value(self) -> bool:
        return self._value

    def _send_value(self, m: int, received_value: bool, received_path: List[int]):
        for lieutenant in filter(lambda l: l not in received_path, self._neighbors):
            value = bool(randint(0, 1)) if self._is_traitor else received_value
            data_out = MessageData(m, value, received_path + [lieutenant])
            message_out = Message(self._id, lieutenant, MessageType.DATA, data_out)
            self._links_outputs[self._neighbors[lieutenant]].send(message_out)
            self._logger.info(f'sent message to {lieutenant}: {value}, {data_out.path}')

    def _receive_general_value(self) -> Tuple[int, bool]:
        while True:
            general_message = self._links_inputs[0].receive()
            if general_message.type == MessageType.DATA:
                general_id = general_message.src
                general_data: MessageData = general_message.data
                general_value = general_data.value
                self._logger.info(f'received value from general: {general_value}')
                break
        return general_id, general_value

    def _create_tree(self, stop_event: Event, m: int, general_id: int, general_value: bool) -> TreeNode:
        tree = TreeNode(general_id, general_value, {self._id: TreeNode(self._id, general_value)})

        neighbors_lieutenants_count = len(self._neighbors)
        neighbors_lieutenants_count_ = neighbors_lieutenants_count
        messages_count = 0
        for i in range(1, min(m, neighbors_lieutenants_count) + 1):
            messages_count += neighbors_lieutenants_count_
            neighbors_lieutenants_count_ *= neighbors_lieutenants_count - i

        self._send_value(m - 2, general_value, [general_id, self._id])

        received_messages = 0
        while not stop_event.is_set() and received_messages < messages_count:
            for lieutenant_link_input in self._links_inputs[1:]:
                if lieutenant_link_input.not_empty():
                    message = lieutenant_link_input.receive()
                    if message.type == MessageType.DATA:
                        received_messages += 1
                        data: MessageData = message.data
                        self._logger.info(f'received message ({received_messages}) from {message.src}: {data.value}, '
                                          f'{data.path}')
                        subtree = tree
                        for lieutenant in data.path[1:]:
                            subtree[lieutenant] = subtree.get(lieutenant, TreeNode(lieutenant, data.value))
                            subtree = subtree[lieutenant]

                        if data.m >= 0:
                            self._send_value(data.m - 1, data.value, data.path)

        self._logger.info('received all messages')
        return tree

    def _calculate_value(self, stop_event: Event, tree: TreeNode):
        self._logger.info('started to calculate value')
        stack: List[Tuple[TreeNode, int]] = [(tree, 0)]
        while not stop_event.is_set() and len(stack) > 0:
            subtree, i = stack.pop()
            if i == 0 and subtree.children_count > 1:
                subtrees = [(subtree_child, 0) for subtree_child in subtree if subtree_child.id != self._id]
                stack += [(subtree, 1)] + subtrees
            elif subtree.children_count == 1:
                subtree[self._id].output_value = subtree[self._id].input_value
            elif i > 0:
                values = [subtree_child[self._id].output_value
                          for subtree_child in subtree if subtree_child.id != self._id]
                values.append(subtree[self._id].input_value)
                counter = Counter(values)
                true_count = counter.get(True, 0)
                false_count = counter.get(False, 0)
                if false_count >= true_count:
                    value = False
                else:
                    value = True
                subtree[self._id].output_value = value
        self._value = tree[self._id].output_value
        self._logger.info(f'calculated tree:\n{tree}')
        self._logger.info(f'calculated value {self._value}')

    def run(self, stop_event: Event, m: int, *args):
        self._start_links()
        self._hello_stage(stop_event)

        general_id, general_value = self._receive_general_value()
        if m == 0:
            self._value = general_value
            return

        tree = self._create_tree(stop_event, m, general_id, general_value)
        self._calculate_value(stop_event, tree)

        while not stop_event.is_set() and any(link_output.not_empty() for link_output in self._links_outputs):
            sleep(self._sleep_time)

        self._stop_links()
