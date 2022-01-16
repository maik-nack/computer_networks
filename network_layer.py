from applied_task.network_layer import DesignatedRouter, get_link, LinkInput, LinkOutput, Router
from functools import partial
from multiprocessing import Event, Process
from time import sleep
from typing import List, Tuple


SLEEP_TIME = 180


def run_router(stop_event: Event, topology_name: str, id_: int, dr_link_input: LinkInput,
               dr_link_output: LinkOutput, links_inputs: List[LinkInput], links_outputs: List[LinkOutput],
               send_event: Event):
    router = Router(id_, dr_link_input, dr_link_output, links_inputs, links_outputs, topology_name)
    router.run(stop_event, send_event)


def run_designated_router(stop_event: Event, connection_off_event: Event, topology_name: str,
                          links_inputs: List[LinkInput], links_outputs: List[LinkOutput],
                          disconnection_probabilities: List[float]):
    router = DesignatedRouter(-1, links_inputs, links_outputs, disconnection_probabilities, topology_name)
    router.run(stop_event, connection_off_event)


def ospf(topology: List[Tuple[List[int], float]], name: str):
    stop_event = Event()
    send_events = [Event() for _ in range(len(topology))]
    connection_off_event = Event()

    router_runner = partial(run_router, stop_event, name)
    dr_runner = partial(run_designated_router, stop_event, connection_off_event, name)

    dr_router_links: List[Tuple[LinkOutput, LinkInput]] = [get_link() for _ in range(len(topology))]
    router_dr_links: List[Tuple[LinkOutput, LinkInput]] = [get_link() for _ in range(len(topology))]

    links_inputs: List[List[LinkInput]] = [[] for _ in range(len(topology))]
    links_outputs: List[List[LinkOutput]] = [[] for _ in range(len(topology))]

    for node, (neighbors, _) in enumerate(topology):
        for neighbor in neighbors:
            link_output, link_input = get_link()
            links_outputs[node].append(link_output)
            links_inputs[neighbor].append(link_input)

    disconnection_probabilities = [disconnection_probability for (_, disconnection_probability) in topology]

    routers_processes = [Process(target=router_runner,
                                 args=(node, dr_router_links[node][1], router_dr_links[node][0], links_inputs[node],
                                       links_outputs[node], send_events[node]))
                         for node in range(len(topology))]
    dr_process = Process(target=dr_runner,
                         args=([router_dr_links[i][1] for i in range(len(topology))],
                               [dr_router_links[i][0] for i in range(len(topology))], disconnection_probabilities))
    processes = routers_processes + [dr_process]

    for process in processes:
        process.daemon = True
    for process in processes:
        process.start()
    sleep(SLEEP_TIME)
    for node in range(len(topology)):
        send_events[node].set()
    sleep(SLEEP_TIME)
    connection_off_event.set()
    sleep(SLEEP_TIME)
    for node in range(len(topology)):
        send_events[node].set()
    sleep(SLEEP_TIME)
    stop_event.set()
    for process in processes:
        process.join()


def main():
    topologies = {
        'line': [([1], 0.9), ([0, 2], 0.1), ([1, 3], 0.9), ([2, 4], 0.9), ([3], 0.9)],
        'circle': [([1], 0.9), ([2], 0.1), ([3], 0.9), ([4], 0.9), ([0], 0.9)],
        'star': [([1, 2, 3, 4], 0.1), ([0], 0.9), ([0], 0.9), ([0], 0.9), ([0], 0.9)]
    }
    for name, topology in topologies.items():
        print(name)
        ospf(topology, name)


if __name__ == '__main__':
    main()
