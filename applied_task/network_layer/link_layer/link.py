from .connection import Connection
from .go_back_n import receiver as go_back_n_receiver, sender as go_back_n_sender
from .selective_repeat import receiver as selective_repeat_receiver, sender as selective_repeat_sender
from typing import Callable, Dict, Literal


ProtocolT = Literal['go_back_n', 'selective_repeat']
SenderT = Callable[[bytes, int, Connection], int]
ReceiverT = Callable[[float, Connection], bytes]

SENDER: Dict[ProtocolT, SenderT] = {
    'go_back_n': go_back_n_sender,
    'selective_repeat': selective_repeat_sender
}

RECEIVER: Dict[ProtocolT, ReceiverT] = {
    'go_back_n': go_back_n_receiver,
    'selective_repeat': selective_repeat_receiver
}
