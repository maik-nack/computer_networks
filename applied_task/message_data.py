from typing import List


class MessageData:
    m: int
    value: bool
    path: List[int]

    def __init__(self, m: int, value: bool, path: List[int]):
        self.m = m
        self.value = value
        self.path = path
