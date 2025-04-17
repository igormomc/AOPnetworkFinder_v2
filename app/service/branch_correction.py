from collections import deque
from enum import Enum

import networkx as nx
import numpy as np
import pymc as pm

from app.service.create_AOP import add_proba_by_keid, create_AOP_from_scratch, add_AOP_variable_by_keid
from app.service.visualize_AOP import build_graph


class fill_method(Enum):
    AVERAGE = 0
    CONSERVATIVE = 1
    PROTECTIVE = 2
    MEDIAN = 3
    DUMMY = 4


def hill_activation(dose, ac50, hill_coefficient=1):
    return (dose ** hill_coefficient) / ((dose ** hill_coefficient) + (ac50 ** hill_coefficient))


def calculate_node_activation_probability(AOP, dose, hill_coefficient=1):
    for KeyEvent in AOP:
        AOP[KeyEvent]["P(prior|event)"] = hill_activation(
            ac50=AOP[KeyEvent]["AC50"],
            dose=dose,
            hill_coefficient=hill_coefficient,
        )


def bayesian_update_node_probabilities(AOP):
    """
    Use Bayesian inference to update node probabilities based on prior beliefs and evidence.
    """
    for node in AOP:
        prior_prob = AOP[node]["P(prior|event)"]

        # Bayesian model for node activation
        with pm.Model() as model:
            # Define a prior
            activation_prior = pm.Beta("activation_prior", alpha=2, beta=5)

            # Observed data: use the prior as evidence for now
            observed_data = pm.Bernoulli("observed_data", p=activation_prior, observed=[prior_prob])

            # Sample posterior
            trace = pm.sample(1000, return_inferencedata=False, progressbar=False)

        # Update node with the mean posterior probability
        posterior_mean = np.mean(trace["activation_prior"])
        AOP[node]["P(prior|event)"] = posterior_mean


def calculate_cycles_equivalent_probability(posteriors):
    """
    Resolve cycles using Bayesian posterior probabilities.
    """
    combined_probability = 1 - np.prod([1 - p for p in posteriors])
    return combined_probability


def find_predecessor_nodes(AOP, target_node):
    """
    Find all predecessor nodes (nodes that point to the target node) in the AOP.

    Args:
    @param AOP (dict): A dictionary representing the AOP graph.
    @param target_node (str): The target node whose predecessors are to be found.

    Returns:
    @param list: List of predecessor nodes.
    """
    predecessors = []
    for node, details in AOP.items():
        if target_node in details["connections"]:
            predecessors.append(node)
    return predecessors


def find_critical_path(AOP, start_node="MIE0", end_node="AO0"):
    """
    Find the shortest path between two nodes in the AOP graph.

    Args:
        AOP (dict): A dictionary representing the AOP graph.
                    Each node has a "connections" key with a list of connected nodes.
        start_node (str): The starting node.
        end_node (str): The target node.

    Returns:
        list: A list of nodes representing the shortest path, or an empty list if no path exists.
    """
    if start_node not in AOP or end_node not in AOP:
        raise ValueError("Start or end node not found in the AOP graph.")

    # Queue for BFS
    queue = deque([(start_node, [start_node])])
    visited = set()

    while queue:
        current_node, path = queue.popleft()

        # If we reach the end node, return the path
        if current_node == end_node:
            return path

        # Mark the current node as visited
        visited.add(current_node)

        # Add neighbors to the queue if not visited
        for neighbor in AOP[current_node]["connections"]:
            if neighbor not in visited:
                queue.append((neighbor, path + [neighbor]))

    # If no path exists, return an empty list
    return []


def find_forks(AOP, target_node, path):
    """
    Find forks branching off the specified critical path at a target node.

    Args:
    @param AOP (dict): A dictionary representing the AOP graph.
    @param target_node (str): The target node to check for forks.
    @param path (list): The critical path used to trace forks.

    Returns:
    @param dict: A dictionary where keys are the origin nodes of forks
            and values are lists of paths branching from the critical path:
            {
                "origin_in_path": [["fork1"], ["fork2"], ...]
            }
    """

    predecessors = find_predecessor_nodes(AOP, target_node)

    # Filter predecessors not in the critical path
    predecessors = [pred for pred in predecessors if pred not in path]

    forks = {}
    for predecessor in predecessors:
        connection_to_path = find_connection_to_path(AOP, predecessor, path)
        if len(connection_to_path) > 0:
            forks[predecessor] = connection_to_path

    return forks


def find_useless_nodes(AOP):
    """
    Identify nodes involved in useless loops in the AOP graph, ensuring nodes
    that contribute valid downstream paths are not misclassified as useless.

    Args:
    @param AOP (dict): A dictionary representing the AOP graph.

    Returns:
    @param list: List of nodes involved in useless loops.
    """
    G = build_graph(AOP)
    visited_nodes = set()
    useless_nodes = set()

    def dfs(node, path):
        if node in path:
            # If we revisit a node, determine if it is actually useless
            loop_start = path.index(node)
            loop_nodes = path[loop_start:]
            for n in loop_nodes:
                # Check if the node contributes to connections outside the loop
                if any(conn not in loop_nodes for conn in G.successors(n)):
                    # Node contributes outside the loop; skip marking it useless
                    continue
                useless_nodes.add(n)
            return

        # Mark node as visited and continue DFS
        visited_nodes.add(node)
        for neighbor in G.successors(node):
            dfs(neighbor, path + [node])

    # Perform DFS for all nodes
    for start_node in G.nodes:
        if start_node not in visited_nodes:
            dfs(start_node, [])

    return list(useless_nodes)


# Don't look it is ugly but it works fine so don't come crying
def find_useless_cycles(AOP):
    """
    Identify connections that form cycles in the AOP graph.

    Args:
    @param AOP (dict): A dictionary representing the AOP graph.

    Returns:
    @param list of tuples: connections that, when removed, will break cycles (e.g., [("KE5", "KE4")]).
    """
    G = build_graph(AOP)
    cycles = list(nx.simple_cycles(G))  # Find all cycles¨

    connections_to_break = []

    for cycle in cycles:
        # The edge to break is from the last node to the first node in the cycle
        connections_to_break.append(find_connection_to_break(cycle))

    return connections_to_break


def find_connection_to_break(cycle):
    cycle = sorted(cycle)  # Sort by length, then lexicographically
    last_node = cycle[-1]
    first_node = cycle[0]
    return (last_node, first_node)


def remove_useless_connections(AOP):
    """
    Remove specified connections (edges) from the AOP graph.

    Args:
    @param AOP (dict): A dictionary representing the AOP graph.
    @param edges_to_break (list of tuples): Edges to remove, e.g., [("KE5", "KE4")].

    Returns:
    @param dict: Updated AOP with specified edges removed.
    """
    edges_to_break = find_useless_cycles(AOP)

    for source, target in edges_to_break:
        if source in AOP and target in AOP[source]["connections"]:
            AOP[source]["connections"].remove(target)


def calculate_branch_probability(AOP, branch):
    p_activation = 1
    for node in branch:
        p_activation *= AOP[node]["P(prior|event)"]
    return p_activation


def find_nodes_between(path, startpoint, endpoint):
    """
    Returns a list of nodes between the start and end nodes in the given path.

    Args:
        path (list): The list of nodes representing the path.
        start: The starting node (included in the result).
        end: The endpoint node (excluded from the result).

    Returns:
        list: A list of nodes between the start and end nodes, including start but excluding end.
    """
    if startpoint not in path or endpoint not in path:
        raise ValueError("Start or end node not found in the path.")

    try:
        start_index = path.index(startpoint)
        end_index = path.index(endpoint)

        if start_index >= end_index:
            raise ValueError("Start node must come before the end node.")

        return path[start_index:end_index]
    except ValueError as e:
        raise ValueError(f"Invalid path or nodes: {e}")


def find_nodes_before_start(path, node):
    if node not in path:
        raise ValueError("Start or end node not found in the path.")

    try:
        index = path.index(node)

        return path[0:index]
    except ValueError as e:
        raise ValueError(f"Invalid path or nodes: {e}")


def perform_branch_correctionV1(AOP, critical_path, branch_path, endpoint):
    branched_portion_of_main_path = find_nodes_between(
        critical_path,
        branch_path[0],
        endpoint
    )

    previous_path_proba = calculate_branch_probability(
        AOP,
        branched_portion_of_main_path
    )

    branch_probability = calculate_branch_probability(AOP, branch_path)

    new_proba = 1

    for node in branch_path:
        new_proba *= AOP[node]["P(prior|event)"]
        AOP[node]["P(prior|event)"] = new_proba

    AOP[endpoint]["P(prior|event)"] = previous_path_proba + (1 - previous_path_proba) * branch_probability


def run_dose_responseV1(AOP, dose, proba_provided=False, bayesian_update=False):
    # Step 1: Handle loops
    remove_useless_connections(AOP)

    if not proba_provided:
        # Step 2: calculate_node_activation_probability
        calculate_node_activation_probability(AOP, dose)

    if bayesian_update:
        # Step 3: Apply Bayesian update to probabilities
        # TODO : try with this because answer will be more accurate but it takes longer and I am lazy
        bayesian_update_node_probabilities(AOP)

    # Step 4: Calculate the probability of the critical path
    critical_path = find_critical_path(AOP)

    # Step 5: Account for the probability of branches
    # TODO make it so that this function is called again after on each branch found to elieviate embeded branches
    for node in critical_path:
        forks = find_forks(AOP, node, critical_path)

        for fork_node in forks:
            fork = forks[fork_node]
            perform_branch_correction(AOP, critical_path, fork, node)
            # recalculate the probability of the critical path with updated probability

    # Told ya I would calculate the crit path (˘³˘)♥︎
    calculate_path_probability(AOP, critical_path)
    return AOP['AO']["cumulative probability"]


def run_dose_response(AOP, dose, calculated_node, proba_provided=False, bayesian_update=False):
    # Step 1: Handle loops
    remove_useless_connections(AOP)

    if not proba_provided:
        # Step 2: calculate_node_activation_probability
        calculate_node_activation_probability(AOP, dose)

    if bayesian_update:
        # Step 3: Apply Bayesian update to probabilities
        # TODO : try with this because answer will be more accurate but it takes longer and I am lazy
        bayesian_update_node_probabilities(AOP)

    # Step 5: Account for the probability of branches with this beautiful recursive
    perform_branch_correction(AOP, node=calculated_node)

    return AOP[calculated_node]["cumulative probability"]


def perform_branch_correction(AOP, node, visited=None):
    if visited is None:
        visited = set()

    # Base case: if the node has already been visited
    if node in visited:
        return AOP[node]["cumulative probability"]

    # Mark node as visited
    visited.add(node)

    # Check if the node is an endpoint (no ancestors)
    predecessors = find_predecessor_nodes(AOP, node)

    if not predecessors:
        # If it's an endpoint, handle differently:
        if "MIE" in node:  # If it's an MIE node
            AOP[node]["cumulative probability"] = AOP[node]["P(prior|event)"]
        else:  # If it's a Key Event node
            AOP[node]["cumulative probability"] = 0
        return AOP[node]["cumulative probability"]

    # Initialize probability as 1 (for ancestor calculations)
    node_probability = 1

    # For each predecessor (ancestor) node
    for predecessor in predecessors:
        # Recursively calculate probability for each ancestor
        ancestor_probability = perform_branch_correction(AOP, node=predecessor, visited=visited)

        # Adjust the node's probability based on ancestors
        node_probability *= (1 - ancestor_probability)

    # Update the node's cumulative probability in the AOP graph
    AOP[node]["cumulative probability"] = (1 - node_probability) * AOP[node]["P(prior|event)"]

    return AOP[node]["cumulative probability"]


def calculate_path_probability(AOP, critical_path):
    for node_name in critical_path:
        AOP[node_name]["cumulative probability"] = calculate_cumulative_probability_of_node(AOP, critical_path,
                                                                                            node_name)


def calculate_cumulative_probability_of_node(AOP, critical_path, node_name):
    index_node = critical_path.index(node_name)
    node = AOP[node_name]

    if index_node == 0:
        node["cumulative probability"] = node["P(prior|event)"]
        previous_proba = 1
    else:
        previous_node = AOP[critical_path[index_node - 1]]
        previous_proba = previous_node["cumulative probability"]
    return previous_proba * node["P(prior|event)"]


def find_connection_to_path(AOP, current_node, critical_path, visited=None):
    """
    Find the full path from a given node to its ancestor in the critical path.

    Args:
    @param AOP (dict): A dictionary representing the AOP graph.
    @param current_node (str): The node to start from.
    @param critical_path (list): The main critical path to connect to.
    @param visited (set): A set of visited nodes to prevent infinite loops.

    Returns:
    @param list: The path connecting the current node to the critical path, or an empty list if no connection exists.
    """
    if visited is None:
        visited = set()

    # Base case: If the current node is in the critical path, return it as the starting point
    if current_node in critical_path:
        return [current_node]

    # Mark the current node as visited
    visited.add(current_node)

    # Find all predecessors of the current node
    predecessors = [
        pred for pred, details in AOP.items() if current_node in details["connections"]
    ]

    # Recursively search through predecessors
    for predecessor in predecessors:
        if predecessor not in visited:
            sub_path = find_connection_to_path(AOP, predecessor, critical_path, visited)
            if sub_path:  # If a connection to the critical path is found, build the full path
                return sub_path + [current_node]

    # No connection found
    return []


def clean_invalid_connections(AOP):
    """
    Removes connections in the AOP graph that point to nodes not present in the AOP.

    Args:
    @param AOP (dict): A dictionary representing the AOP graph where each node has a 'connections' key.

    Returns:
    @param None: The function modifies the AOP in place.
    """
    valid_nodes = set(AOP.keys())  # Get all valid nodes in the AOP
    for node, details in AOP.items():
        # Remove connections that point to non-existent nodes
        details["connections"] = [conn for conn in details["connections"] if conn in valid_nodes]


def clean_up_AOP(AOP):
    new_AOP = {
        node: {
            "name": details["name"],
            "connections": details["connections"],
            "genes": details["genes"],
            "AC50": details["AC50"]
        } for node, details in AOP.items()
    }
    return new_AOP


def run_dose_response_on_partial_AOP(AOP, dose, calculated_node="AO0", selected_nodes=None, proba_provided=True):
    if selected_nodes is not None:
        new_AOP = {node: AOP[node] for node in AOP if node in selected_nodes}
        clean_invalid_connections(new_AOP)
        AOP = clean_up_AOP(new_AOP)
    return run_dose_response(AOP, dose, calculated_node=calculated_node, proba_provided=proba_provided)


def branch_correct_dose_response(AOP, dose, selected_nodes=None, proba_provided=True):
    # Refactor the AOP so that it is clean and you can make the calculations on different paths from the same script
    if selected_nodes is not None:
        new_AOP = {node: AOP[node] for node in AOP if node in selected_nodes}
        clean_invalid_connections(new_AOP)
        AOP = clean_up_AOP(new_AOP)

    return run_dose_response(AOP=AOP, dose=dose, proba_provided=proba_provided)


def complete_ac50_values(AOP, method=fill_method.AVERAGE, max_val=0, min_val=0):
    ac50s = []
    to_correct = []
    for node in AOP:
        try:
            if AOP[node]["AC50"]:
                ac50s.append(AOP[node]["AC50"])
            else:
                to_correct.append(node)
        except:
            to_correct.append(node)
    if len(ac50s) == 0:
        method = fill_method.DUMMY
    match method:
        case fill_method.AVERAGE:
            new_ac50 = np.mean(ac50s)
            for node in to_correct:
                AOP[node]["AC50"] = new_ac50

        case fill_method.MEDIAN:
            new_ac50 = np.median(ac50s)
            for node in to_correct:
                AOP[node]["AC50"] = new_ac50

        case fill_method.CONSERVATIVE:
            for node in to_correct:
                AOP[node]["AC50"] = max_val

        case fill_method.CONSERVATIVE:
            for node in to_correct:
                AOP[node]["AC50"] = min_val

        case fill_method.DUMMY:
            for node in to_correct:
                AOP[node]["AC50"] = 20


def run_goat_dose_response(AOP_id, dose, calculated_node="AO0", AC50_values=None, probability_values=None,
                           selected_nodes=None, method=fill_method.MEDIAN, max_ac50=0, min_ac50=0, manualKEEdges=None):
    AOP = create_AOP_from_scratch(AOP_id, manualKEEdges)

    if AC50_values:
        add_AOP_variable_by_keid(AOP, AC50_values)
        complete_ac50_values(AOP=AOP, method=method)
    else:
        complete_ac50_values(AOP=AOP, method=fill_method.DUMMY)

    if probability_values:
        add_proba_by_keid(AOP, probability_values)
        proba = run_dose_response_on_partial_AOP(AOP, dose, selected_nodes=selected_nodes,
                                                 calculated_node=calculated_node, proba_provided=True)
    else:
        proba = run_dose_response_on_partial_AOP(AOP, dose, selected_nodes=selected_nodes,
                                                 calculated_node=calculated_node, proba_provided=False)
    return AOP, proba
