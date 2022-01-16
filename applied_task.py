from applied_task import DesignatedRouterByzantine, RouterGeneral, RouterLieutenant
from applied_task.network_layer import get_link, LinkInput, LinkOutput
from functools import partial
from multiprocessing import Event, Process, Value
from multiprocessing.sharedctypes import Synchronized
from typing import List, Tuple


def run_router_general(stop_event: Event, m: int, topology_name: str, id_: int, dr_link_input: LinkInput,
                       dr_link_output: LinkOutput, lieutenants_links_outputs: List[LinkOutput], is_traitor: bool,
                       value: Synchronized):
    router = RouterGeneral(id_, dr_link_input, dr_link_output, lieutenants_links_outputs, is_traitor, topology_name)
    router.run(stop_event, m)
    value.value = int(router.value)


def run_router_lieutenant(stop_event: Event, m: int, topology_name: str, id_: int, dr_link_input: LinkInput,
                          dr_link_output: LinkOutput, general_link_input: LinkInput,
                          lieutenants_links_inputs: List[LinkInput], lieutenants_links_outputs: List[LinkOutput],
                          is_traitor: bool, value: Synchronized):
    router = RouterLieutenant(id_, dr_link_input, dr_link_output, general_link_input, lieutenants_links_inputs,
                              lieutenants_links_outputs, is_traitor, topology_name)
    router.run(stop_event, m)
    value.value = int(router.value)


def run_designated_router(stop_event: Event, topology_name: str, links_inputs: List[LinkInput],
                          links_outputs: List[LinkOutput], disconnection_probabilities: List[float]):
    router = DesignatedRouterByzantine(-1, links_inputs, links_outputs, disconnection_probabilities, topology_name)
    router.run(stop_event)


def byzantine(n: int, m: int, traitors: List[bool], name: str):
    stop_event = Event()
    values = [Value('i', 0) for _ in range(n)]

    general_runner = partial(run_router_general, stop_event, m, name)
    lieutenant_runner = partial(run_router_lieutenant, stop_event, m, name)
    dr_runner = partial(run_designated_router, stop_event, name)

    dr_router_links: List[Tuple[LinkOutput, LinkInput]] = [get_link() for _ in range(n)]
    router_dr_links: List[Tuple[LinkOutput, LinkInput]] = [get_link() for _ in range(n)]

    general_lieutenant_links: List[Tuple[LinkOutput, LinkInput]] = [get_link() for _ in range(n - 1)]

    lieutenants_links_inputs: List[List[LinkInput]] = [[] for _ in range(n - 1)]
    lieutenants_links_outputs: List[List[LinkOutput]] = [[] for _ in range(n - 1)]

    for lieutenant in range(n - 1):
        for lieutenant_neighbor in filter(lambda l: l != lieutenant, range(n - 1)):
            lieutenant_link_output, lieutenant_link_input = get_link()
            lieutenants_links_outputs[lieutenant].append(lieutenant_link_output)
            lieutenants_links_inputs[lieutenant_neighbor].append(lieutenant_link_input)

    disconnection_probabilities = [0.0 for _ in range(n)]

    general_process = Process(target=general_runner,
                              args=(0, dr_router_links[0][1], router_dr_links[0][0],
                                    [general_lieutenant_links[i][0] for i in range(n - 1)], traitors[0], values[0]))
    lieutenants_processes = [Process(target=lieutenant_runner,
                                     args=(i + 1, dr_router_links[i + 1][1], router_dr_links[i + 1][0],
                                           general_lieutenant_links[i][1], lieutenants_links_inputs[i],
                                           lieutenants_links_outputs[i], traitors[i + 1], values[i + 1]))
                             for i in range(n - 1)]
    dr_process = Process(target=dr_runner,
                         args=([router_dr_links[i][1] for i in range(n)], [dr_router_links[i][0] for i in range(n)],
                               disconnection_probabilities))
    processes = [general_process] + lieutenants_processes + [dr_process]

    for process in processes:
        process.daemon = True
    for process in processes:
        process.start()
    general_process.join()
    for lieutenant_process in lieutenants_processes:
        lieutenant_process.join()
    stop_event.set()
    dr_process.join()

    values_ = [bool(value.value) for value in values]
    non_traitors_values = [values_[i + 1] for i in range(n - 1) if not traitors[i + 1]]
    if all(non_traitors_values) or not any(non_traitors_values):
        print('all loyal lieutenants have the same values')
        if not traitors[0]:
            if values_[0] == non_traitors_values[0]:
                print('all loyal lieutenants have the same value as a loyal general')
            else:
                print('traitors have won')
    else:
        print('traitors have won')


def main():
    byzantines = {
        '4_1_0-t': dict(n=4, m=1, traitors=[True, False, False, False]),
        '4_1_1-t': dict(n=4, m=1, traitors=[False, True, False, False]),
        '7_2_0-t_4-t': dict(n=7, m=2, traitors=[True, False, False, False, True, False, False]),
        '7_2_1-t_4-t': dict(n=7, m=2, traitors=[False, True, False, False, True, False, False])
    }
    for name, topology in byzantines.items():
        print(name)
        byzantine(**topology, name=name)


if __name__ == '__main__':
    main()
