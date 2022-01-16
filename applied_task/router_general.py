import os

from .message_data import MessageData
from .network_layer import LinkInput, LinkOutput, Message, MessageType, Router
from multiprocessing import Event
from random import randint
from time import sleep
from typing import List


class RouterGeneral(Router):
    _is_traitor: bool
    _value: bool

    def __init__(self, id_: int, dr_link_input: LinkInput, dr_link_output: LinkOutput,
                 lieutenants_links_outputs: List[LinkOutput], is_traitor: bool, topology_name: str):
        logfile_path = os.path.join(os.path.dirname(__file__), f'R-General_{id_}_{topology_name}.log')
        super().__init__(id_, dr_link_input, dr_link_output, [], lieutenants_links_outputs, topology_name, logfile_path)
        self._is_traitor = is_traitor
        self._logger.info(f"I'm{' ' if self._is_traitor else ' not '}a traitor")

    @property
    def value(self) -> bool:
        return self._value

    def run(self, stop_event: Event, m: int, *args):
        self._start_links()
        self._hello_stage(stop_event)

        self._value = bool(randint(0, 1))
        self._logger.info(f'my value is {self._value}')

        for lieutenant_id, lieutenant_link_id in self._neighbors.items():
            lieutenant_link = self._links_outputs[lieutenant_link_id]
            value = bool(randint(0, 1)) if self._is_traitor else self._value
            data = MessageData(m - 1, value, [self._id, lieutenant_id])
            message = Message(self._id, lieutenant_id, MessageType.DATA, data)
            lieutenant_link.send(message)
            self._logger.info(f'sent {value} to lieutenant {lieutenant_id}')

        while not stop_event.is_set() and any(link_output.not_empty() for link_output in self._links_outputs):
            sleep(self._sleep_time)

        self._stop_links()
