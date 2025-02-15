import networkx as nx
import matplotlib.pyplot as plt


# Function to build the directed graph from the AOP
def build_graph(AOP):
    G = nx.DiGraph()
    for node, details in AOP.items():
        for connection in details["connections"]:
            G.add_edge(node, connection)
    return G


# Function to assign colors to nodes based on their type
def assign_colors(AOP):
    colors = []
    for node in AOP:
        if node[0:3].lower() == "mie":  # MIE node
            colors.append("lightblue")
        elif node[0:2].lower() == "AO":  # AO node
            colors.append("red")
        else:  # KE nodes
            colors.append("orange")
    return colors


# Function to visualize the AOP
def visualize_AOP(AOP):
    G = build_graph(AOP=AOP)
    pos = nx.spring_layout(G)  # Generate positions for nodes
    node_colors = assign_colors(AOP)  # Assign colors to nodes
    nx.draw(
        G,
        pos,
        with_labels=True,
        node_size=3000,
        node_color=node_colors,  # Use assigned colors
        font_size=10,
        edge_color="gray",  # Optional: Set edge color
    )
    plt.show()


def print(*args, **kwargs):
    """My custom print() function that prints readable AOPs"""
    # Adding new arguments to the print function signature 
    # is probably a bad idea.
    # Instead consider testing if custom argument keywords
    # are present in kwarg
    there_is_a_dict = False
    for arg in args:
        if type(arg) == type({}):
            there_is_a_dict = True
    if there_is_a_dict:
        try:
            import builtins as __builtin__
            import pprint
        finally:
            left_to_print = []
            for arg in args:
                # if dict then most likely an AOP
                if type(arg) == type({}):
                    pprint.pprint(arg)
                else:
                    left_to_print.append(arg)

            if len(left_to_print) > 0:
                print_text = f"{left_to_print[0]}"
                for index, item in enumerate(left_to_print):
                    if index != 0:
                        print_text += f" {item}"

                __builtin__.print(print_text, **kwargs)
    else:
        import builtins as __builtin__
        __builtin__.print(*args, **kwargs)
