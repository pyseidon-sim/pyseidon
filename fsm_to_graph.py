import os
import argparse

from enum import Enum

from components.fsm.states import TugState, VesselState, \
    AnchorageState, BerthState, PilotState

# To create a png file from the .dot file run
# dot -Tpng file.dot > file.png
parser = argparse.ArgumentParser(description="FSM Graph builder")
parser.add_argument("--out-folder", required=True, help="Output folder", type=str)

args = parser.parse_args()

# Create output folder if it does not exist
if not os.path.exists(args.out_folder):
    os.makedirs(args.out_folder)


def generate_graph(state_cls: Enum):
    graphviz_code = "digraph G {"
    initial_state = state_cls.get_state_graph()["initial"]

    for state in state_cls.all_states():
        readable_state = state.replace("_", " ").capitalize()

        if state == initial_state:
            graphviz_code = f"{graphviz_code}\n\t{state}[label=\"{readable_state}\", shape=doublecircle];"
        else:
            graphviz_code = f"{graphviz_code}\n\t{state}[label=\"{readable_state}\"];"

    graphviz_code = f"{graphviz_code}\n"

    for transition in state_cls.get_state_graph()["events"]:
        src, dst, name = transition["src"], transition["dst"], transition["name"]

        if type(src) != list: src = [src]
        if type(dst) != list: dst = [dst]

        for src_state in src:
            for dst_state in dst:
                graphviz_code = f"{graphviz_code}\n\t{src_state} -> {dst_state}[label=\"{name}\"];"

    graphviz_code += "\n}"
    return graphviz_code


state_graphs = [TugState, VesselState, AnchorageState, BerthState, PilotState]
graphs_names = ["tug.dot", "vessel.dot", "anchorage.dot", "berth.dot", "pilot.dot"]

for state_graph, graph_name in zip(state_graphs, graphs_names):
    graphviz_code = generate_graph(state_graph)

    with open(f"{args.out_folder}/{graph_name}", "w") as tmp_file:
        tmp_file.write(graphviz_code)
