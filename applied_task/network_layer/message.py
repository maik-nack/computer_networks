from enum import Enum
from typing import Any, Optional


class MessageType(Enum):
    HELLO = 'HELLO'
    GET_NEIGHBORS = 'GET_NEIGHBORS'
    SET_NEIGHBORS = 'SET_NEIGHBORS'
    SET_TOPOLOGY = 'SET_TOPOLOGY'
    DATA = 'DATA'
    DISCONNECT = 'DISCONNECT'


class Message:
    src: int
    dst: Optional[int]
    type: MessageType
    data: Any

    def __init__(self, src: int, dst: Optional[int], type_: MessageType, data: Any):
        self.src = src
        self.dst = dst
        self.type = type_
        self.data = data


class MessageHelloDataT:
    id: int
    start_time: float

    def __init__(self, id_: int, start_time: float):
        self.id = id_
        self.start_time = start_time
