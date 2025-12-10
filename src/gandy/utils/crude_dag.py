# Rather than using networkx, let's just implement our own DAG since we only need a simple topological sort (for speech_sort).
# Partly vibe-coded because this is really just basic boilerplate stuff.

class CrudeDAG():
    def __init__(self):
        self.adj_list = {}
        self.in_degree = {}

    def add_node(self, node):
        if node not in self.adj_list:
            self.adj_list[node] = []
            self.in_degree[node] = 0

    def _reachable(self, start, target):
        # Return True if `target` is reachable from `start` (DFS).
        if start == target:
            return True
        visited = set()
        stack = [start]
        while stack:
            node = stack.pop()
            if node == target:
                return True
            if node in visited:
                continue
            visited.add(node)
            for neighbor in self.adj_list.get(node, []):
                if neighbor not in visited:
                    stack.append(neighbor)
        return False

    def add_edge(self, from_node, to_node):
        self.add_node(from_node)
        self.add_node(to_node)

        # If there is already a path from `to_node` back to `from_node`,
        # adding `from_node -> to_node` would create a cycle. Do a no-op.
        if self._reachable(to_node, from_node):
            return False

        self.adj_list[from_node].append(to_node)
        self.in_degree[to_node] += 1
        return True

    def topological_sort(self):
        zero_in_degree = [node for node in self.in_degree if self.in_degree[node] == 0]
        sorted_nodes = []

        while zero_in_degree:
            node = zero_in_degree.pop()

            sorted_nodes.append(node)

            for neighbor in self.adj_list[node]:
                self.in_degree[neighbor] -= 1
                if self.in_degree[neighbor] == 0:
                    zero_in_degree.append(neighbor)

        if len(sorted_nodes) != len(self.adj_list):
            # Notice the vibe-coding?
            # In our use case (speech_sort), cycles shouldn't ever even happen, so this check is kinda redundant.
            raise ValueError("Graph has at least one cycle, topological sort not possible.")

        return sorted_nodes