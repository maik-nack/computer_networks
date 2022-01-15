import numpy as np
import os
import pandas as pd
import pickle
import plotly.express as px

from applied_task.network_layer.link_layer import Connection, ProtocolT, RECEIVER, SENDER
from multiprocessing import Array, Process, Value
from multiprocessing.sharedctypes import Synchronized, SynchronizedString
from time import time
from typing import List, Tuple


def sender(message_to_send: str, window_size: int, connection: Connection, protocol: ProtocolT, k: Synchronized):
    function = SENDER[protocol]
    bytes_to_send = pickle.dumps(message_to_send)
    sent_bytes = function(bytes_to_send, window_size, connection)
    k.value = len(bytes_to_send) / sent_bytes


def receiver(transmission_error_probability: float, connection: Connection, protocol: ProtocolT,
             received_message: SynchronizedString):
    function = RECEIVER[protocol]
    received_bytes = function(transmission_error_probability, connection)
    received_message.value = pickle.loads(received_bytes).encode()


def run(message_to_send: str, window_size: int, transmission_error_probability: float,
        protocol: ProtocolT) -> Tuple[float, float]:
    connection = Connection()
    k = Value('d')
    received_message = Array('c', len(message_to_send))

    sender_process = Process(target=sender, args=(message_to_send, window_size, connection, protocol, k))
    sender_process.daemon = True
    receiver_process = Process(target=receiver,
                               args=(transmission_error_probability, connection, protocol, received_message))
    receiver_process.daemon = True

    start = time()
    sender_process.start()
    receiver_process.start()
    sender_process.join()
    receiver_process.join()
    end = time()

    print(f'Message to send and received message are equal: {message_to_send == received_message.value.decode()}')

    return k.value, end - start


def main():
    message_to_send = 'It is a very long long message to send throw channel in bytes with pickle transformation'
    protocols: List[ProtocolT] = ['go_back_n', 'selective_repeat']
    transmission_error_probabilities = np.linspace(0, 0.9, 20)
    transmission_error_probability = 0.3
    window_sizes = list(range(1, 26))
    window_size = 3
    df_ws = pd.DataFrame(columns=['protocol', 'window_size', 'k', 'elapsed_time'])
    df_tep = pd.DataFrame(columns=['protocol', 'transmission_error_probability', 'k', 'elapsed_time'])

    for protocol in protocols:
        for window_size in window_sizes:
            k, elapsed_time = run(message_to_send, window_size, transmission_error_probability, protocol)
            df_ws = df_ws.append(dict(protocol=protocol, window_size=window_size, k=k, elapsed_time=elapsed_time),
                                 ignore_index=True)

    for protocol in protocols:
        for transmission_error_probability in transmission_error_probabilities:
            k, elapsed_time = run(message_to_send, window_size, transmission_error_probability, protocol)
            df_tep = df_tep.append(dict(protocol=protocol, k=k, elapsed_time=elapsed_time,
                                        transmission_error_probability=transmission_error_probability),
                                   ignore_index=True)

    base_path = os.path.join('applied_task', 'network_layer', 'link_layer')
    fig_ws_k = px.line(df_ws[['protocol', 'window_size', 'k']], x='window_size', y='k', color='protocol')
    fig_ws_k.write_html(os.path.join(base_path, 'window_size_k.html'))

    fig_ws_elapsed_time = px.line(df_ws[['protocol', 'window_size', 'elapsed_time']], x='window_size', y='elapsed_time',
                                  color='protocol')
    fig_ws_elapsed_time.write_html(os.path.join(base_path, 'window_size_elapsed_time.html'))

    fig_tep_k = px.line(df_tep[['protocol', 'transmission_error_probability', 'k']], x='transmission_error_probability',
                        y='k', color='protocol')
    fig_tep_k.write_html(os.path.join(base_path, 'transmission_error_probability_k.html'))

    fig_tep_elapsed_time = px.line(df_tep[['protocol', 'transmission_error_probability', 'elapsed_time']],
                                   x='transmission_error_probability', y='elapsed_time', color='protocol')
    fig_tep_elapsed_time.write_html(os.path.join(base_path, 'transmission_error_probability_elapsed_time.html'))


if __name__ == '__main__':
    main()
