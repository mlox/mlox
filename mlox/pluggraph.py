from pprint import PrettyPrinter
import logging

pluggraph_logger = logging.getLogger('mlox.pluggraph')

class pluggraph:
    """A graph structure built from ordering rules which specify plugin load (partial) order"""
    def __init__(self):
        # nodes is a dictionary of lists, where each key is a plugin, and each
        # value is a list of the children of that plugin in the graph
        # that is, if we have "foo.esp" -> "bar.esp" and "foo.esp" -> "baz.esp"
        # where "->" is read "is a parent of" and means "preceeds in load order"
        # the data structure will contain: {"foo.esp": ["bar.esp", "baz.esp"]}
        self.nodes = {}
        # incoming_count is a dictionary of that keeps track of the count of
        # how many incoming edges a plugin node in the graph has.
        # incoming_count["bar.esp"] == 1 means that bar.esp only has one parent
        # incoming_count["foo.esp"] == 0 means that foo.esp is a root node
        self.incoming_count = {}
        # nodes (plugins) that should be pulled nearest to top of load order,
        # if possible.
        self.nearstart = []
        # nodes (plugins) that should be pushed nearest to bottom of load order,
        # if possible.
        self.nearend = []

    def can_reach(self, startnode, plugin):
        """Return True if startnode can reach plugin in the graph, False otherwise."""
        stack = [startnode]
        seen = {}
        while stack != []:
            p = stack.pop()
            if p == plugin:
                return(True)
            seen[p] = True
            if p in self.nodes:
                stack.extend([child for child in self.nodes[p] if not child in seen])
        return(False)

    def add_edge(self, where, plug1, plug2):
        """Add an edge to our graph connecting plug1 to plug2, which means
        that plug2 follows plug1 in the load order. Since we check every new
        edge to see if it will make a cycle, the process of adding all edges
        will be O(square(n)/2) in the worst case of a totally ordered
        set. This could mean a long run-time for the Oblivion data, which
        is currently a total order of a set of about 5000 plugins."""
        # before adding edge from plug1 to plug2 (meaning plug1 is parent of plug2),
        # we look to see if plug2 is already a parent of plug1, if so, we have
        # detected a cycle, which we disallow.
        if self.can_reach(plug2, plug1):
            # (where == "") when adding edges from psuedo-rules we
            # create from our current plugin list, We ignore cycles in
            # this case because they do not matter.
            # (where != "") when it is an edge from a rules file, and in
            # that case we do want to see cycle errors.
            cycle_detected = "%s: Cycle detected, not adding: \"%s\" -> \"%s\"" % (where, plug1, plug2)
            if where == "":
                pluggraph_logger.debug(cycle_detected)
            else:
                pluggraph_logger.warning(cycle_detected)
            return False
        self.nodes.setdefault(plug1, [])
        if plug2 in self.nodes[plug1]: # edge already exists
            pluggraph_logger.debug("%s: Not adding duplicate Edge: \"%s\" -> \"%s\"", where, plug1, plug2)
            return True
        # add plug2 to the graph as a child of plug1
        self.nodes[plug1].append(plug2)
        self.incoming_count[plug2] = self.incoming_count.setdefault(plug2, 0) + 1
        pluggraph_logger.debug("adding edge: %s -> %s" % (plug1, plug2))
        return(True)

    def get_dot_graph(self):
        """
        Produce a graphviz dot graph.

        This is mostly a novelty to visualize what's going on
        """
        buffer = "digraph plugins {\n"
        for (node, plugins) in self.nodes.items():
            for a_plugin in plugins:
                buffer += "\""+ node + "\" -> \"" + a_plugin + "\"\n"
        buffer += "}\n"
        return buffer

    def explain(self, what, active_plugins):
        """
        Tell the user all the plugins mlox thinks should follow <what>
        """
        seen = {}
        output = ""
        output += "This is a picture of all the plugins mlox thinks should follow {0}\n".format(what)
        output += "Child plugins are indented with respect to their parents\n"
        output += "Lines beginning with '=' are plugins you don't have.\n"
        output += "Lines beginning with '+' are plugins you do have.\n"
        def explain_rec(indent, n):
            output = ""
            if n in seen:
                return
            seen[n] = True
            if n in self.nodes:
                for child in self.nodes[n]:
                    prefix = indent.replace(" ", "+") if child in active_plugins else indent.replace(" ", "=")
                    output += "%s%s\n" % (prefix, child)
                    explain_rec(" " + indent, child)
            return output
        output += explain_rec(" ", what.lower())
        return output

    def topo_sort(self):
        """topological sort"""

        def remove_roots(roots, which):
            """This function is used to yank roots out of the main list of graph roots to
            support the NearStart and NearEnd rules."""
            removed = []
            for p in which:
                leftover = []
                while len(roots) > 0:
                    r = roots.pop(0)
                    if self.can_reach(r, p):
                        removed.append(r)
                    else:
                        leftover.append(r)
                roots = leftover
            return(removed, roots)

        # find the roots of the graph
        roots = [node for node in self.nodes if self.incoming_count.get(node, 0) == 0]
        pluggraph_logger.debug("========== BEGIN TOPOLOGICAL SORT DEBUG INFO ==========")
        pluggraph_logger.debug("graph before sort (node: children)")
        pluggraph_logger.debug(PrettyPrinter(indent=4).pformat(self.nodes))
        pluggraph_logger.debug("roots:\n  %s" % ("\n  ".join(roots)))
        if len(roots) > 0:
            # use the nearstart information to pull preferred plugins to top of load order
            (top_roots, roots) = remove_roots(roots, self.nearstart)
            bottom_roots = roots        # any leftovers go at the end
            roots = top_roots + bottom_roots
            pluggraph_logger.debug("nearstart:\n  %s" % ("\n  ".join(self.nearstart)))
            pluggraph_logger.debug("top roots:\n  %s" % ("\n  ".join(top_roots)))
            pluggraph_logger.debug("nearend:\n  %s" % ("\n  ".join(self.nearend)))
            pluggraph_logger.debug("bottom roots:\n  %s" % ("\n  ".join(bottom_roots)))
            pluggraph_logger.debug("newroots:\n  %s" % ("\n  ".join(roots)))
        pluggraph_logger.debug("========== END TOPOLOGICAL SORT DEBUG INFO ==========\n")
        # now do the actual topological sort
        # based on http://www.bitformation.com/art/python_toposort.html
        roots.reverse()
        sorted_items = []
        while len(roots) != 0:
            root = roots.pop()
            sorted_items.append(root)
            if not root in self.nodes:
                continue
            for child in self.nodes[root]:
                self.incoming_count[child] -= 1
                if self.incoming_count[child] == 0:
                    roots.append(child)
            del self.nodes[root]
        if len(self.nodes.items()) != 0:
            pluggraph_logger.error("Topological Sort Failed!")
            pluggraph_logger.debug(PrettyPrinter(indent=4).pformat(self.nodes.items()))
            return None
        return sorted_items
