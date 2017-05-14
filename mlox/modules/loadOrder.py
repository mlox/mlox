import os
import sys
import StringIO
import logging
import modules.fileFinder as fileFinder
import modules.pluggraph as pluggraph
import modules.configHandler as configHandler
import modules.ruleParser as ruleParser

#Resource files
program_path = os.path.realpath(sys.path[0])
base_file = os.path.join(program_path,"mlox_base.txt")
user_file = os.path.join(program_path,"mlox_user.txt")

old_loadorder_output = "current_loadorder.out"
new_loadorder_output = "mlox_new_loadorder.out"

order_logger = logging.getLogger('mlox.loadorder')

class loadorder:
    """Class for reading plugin mod times (load order), and updating them based on rules"""
    def __init__(self):
        # order is the list of plugins in Data Files, ordered by mtime
        self.active = {}                   # current active plugins
        self.order = []                    # the load order
        self.new_order = []                # the new load order
        self.datadir = None                # where plugins live
        self.plugin_file = None            # Path to the file containing the plugin list
        self.graph = pluggraph.pluggraph()
        self.is_sorted = False
        self.origin = None                 # where plugins came from (active, installed, file)
        self.game_type = None              # 'Morrowind', 'Oblivion', or None for unknown
        self.caseless = fileFinder.caseless_filenames()

        self.game_type, self.plugin_file, self.datadir = fileFinder.find_game_dirs()

    def get_active_plugins(self):
        """Get the active list of plugins from the game configuration. Updates self.active and self.order."""
        if self.plugin_file == None:
            order_logger.warning("{0} config file not found!".format(self.game_type))
            return

        # Get all the plugins
        configFiles = configHandler.configHandler(self.plugin_file,self.game_type).read()
        dirFiles = configHandler.dataDirHandler(self.datadir).read()

        # Remove plugins not in the data directory (and correct capitalization)
        configFiles = map(str.lower, configFiles)
        self.order = filter(lambda x: x.lower() in configFiles, dirFiles)

        #Convert the files to lowercase, while storing them in a dict
        self.order = map(self.caseless.cname,self.order)

        order_logger.info("Found {0} plugins in: \"{1}\"".format(len(self.order), self.plugin_file))
        for p in self.order:
            self.active[p] = True
        self.origin = "Active Plugins"

    def get_data_files(self):
        """Get the load order from the data files directory. Updates self.active and self.order."""
        self.order = configHandler.dataDirHandler(self.datadir).read()

        #Convert the files to lowercase, while storing them in a dict
        self.order = map(self.caseless.cname,self.order)

        order_logger.info("Found {0} plugins in: \"{1}\"".format(len(self.order), self.datadir.dirpath()))
        for p in self.order:
            self.active[p] = True
        self.origin = "Installed Plugins"

    #List the versions of all plugins in the current load order
    def listversions(self):
        out = "{0:20} {1:20} {2}\n".format("Name", "Description", "Plugin Name")
        for p in self.order:
            (file_ver, desc_ver) = ruleParser.get_version(p,self.datadir)
            out += "{0:20} {1:20} {2}\n".format(file_ver, desc_ver, self.caseless.truename(p))
        return out

    def read_from_file(self, fromfile):
        """Get the load order by reading an input file.
        Clears self.game_type and self.datadir.
        Updates self.plugin_file, self.active, and self.order."""
        self.game_type = None
        self.datadir = None         #This tells the parser to not worry about things like [SIZE] checks, or trying to read the plugin descriptions
        self.plugin_file = fromfile

        self.order = configHandler.configHandler(fromfile).read()
        if len(self.order) == 0:
            order_logger.warning("No plugins detected.\nmlox understands lists of plugins in the format used by Morrowind.ini or Wrye Mash.\nIs that what you used for input?")

        #Convert the files to lowercase, while storing them in a dict
        self.order = map(self.caseless.cname,self.order)

        order_logger.info("Found {0} plugins in: \"{1}\"".format(len(self.order), self.plugin_file))
        for p in self.order:
            self.active[p] = True
        self.origin = "Plugin List from %s" % os.path.basename(fromfile)
        order_logger.info("(Note: When the load order input is from an external source, the [SIZE] predicate cannot check the plugin filesizes, so it defaults to True).")

    def add_current_order(self):
        """We treat the current load order as a sort of preferred order in
        the case where there are no rules. However, we have to be careful
        when there exists a [NEARSTART] or [NEAREND] rule for a plugin,
        that we do not introduce a new edge, we only add the node itself.
        This allows us to move unconnected nodes to the top or bottom of
        the roots calculated in the topo_sort routine, depending on
        whether they show up in [NEARSTART] or [NEAREND] rules,
        respectively"""
        if len(self.order) < 2:
            return
        order_logger.debug("adding edges from CURRENT ORDER")
        # make ordering pseudo-rules for esms to follow official .esms
        if self.game_type == "Morrowind":
            self.graph.add_edge("", "morrowind.esm", "tribunal.esm")
            self.graph.add_edge("", "tribunal.esm", "bloodmoon.esm")
            for p in self.active: # foreach of the user's .esms
                if p[-4:] == ".esm":
                    if p not in ("morrowind.esm", "tribunal.esm", "bloodmoon.esm"):
                        self.graph.add_edge("", "bloodmoon.esm", p)
        # make ordering pseudo-rules from nearend info
        kingyo_fun = [x for x in self.graph.nearend if x in self.active]
        for p_end in kingyo_fun:
            for p in [x for x in self.order if x != p_end]:
                self.graph.add_edge("", p, p_end)
        # make ordering pseudo-rules from current load order.
        prev_i = 0
        self.graph.nodes.setdefault(self.order[prev_i], [])
        for curr_i in range(1, len(self.order)):
            self.graph.nodes.setdefault(self.order[curr_i], [])
            if (self.order[curr_i] not in self.graph.nearstart and
                self.order[curr_i] not in self.graph.nearend):
                # add an edge, on any failure due to cycle detection, we try
                # to make an edge between the current plugin and the first
                # previous ancestor we can succesfully link and edge from.
                for i in range(prev_i, 0, -1):
                    if (self.order[i] not in self.graph.nearstart and
                        self.order[i] not in self.graph.nearend):
                        if self.graph.add_edge("", self.order[i], self.order[curr_i]):
                            break
            prev_i = curr_i

    def save_order(self, filename, order, what):
        try:
            out = open(filename, 'w')
        except IOError:
            order_logger.error("Unable to write to {0} file:  {1}".format(what,filename))
            return
        for p in order:
            print >> out, p
        out.close()
        order_logger.info("%s saved to: %s" % (what, filename))

    def get_original_order(self):
        """Get the original plugin order in a nice printable format"""
        formatted = []
        for n in range(1,len(self.order)+1):
            formatted.append("{0:0>3} {1}".format(n, self.caseless.truename(self.order[n-1])))
        return formatted

    def get_new_order(self):
        """Get the new plugin order in a nice printable format.
        Also, highlight mods that have moved up in the load order."""
        formatted = []
        orig_index = {}
        for n in range(1,len(self.order)+1):
            orig_index[self.order[n-1]] = n
        highlight = "_"
        for i in range(0, len(self.new_order)):
            p = self.new_order[i]
            curr = p.lower()
            if (orig_index[curr] - 1) > i: highlight = "*"
            formatted.append("%s%03d%s %s" % (highlight, orig_index[curr], highlight, p))
            if highlight == "*":
                if i < len(self.new_order) - 1:
                    next = self.new_order[i+1].lower()
                if (orig_index[curr] > orig_index[next]):
                    highlight = "_"
        return formatted

    def explain(self,plugin_name,base_only = False):
        """Expalin why a mod is in it's current position"""
        original_graph = self.graph
        self.graph = pluggraph.pluggraph()

        parser = ruleParser.rule_parser(self.active, self.graph, self.datadir,StringIO.StringIO(),self.caseless)
        if os.path.exists(user_file):
            parser.read_rules(user_file)
        parser.read_rules(base_file)

        if not base_only:
            self.add_current_order() # tertiary order "pseudo-rules" from current load order
        output = self.graph.explain(plugin_name, self.active)

        self.graph = original_graph
        return output

    def update(self,parser_out_stream = sys.stdout,progress = None):
        """Update the load order based on input rules."""
        self.is_sorted = False
        self.graph = pluggraph.pluggraph()
        if self.order == []:
            order_logger.error("No plugins detected! mlox needs to run somewhere under where the game is installed.")
            return
        order_logger.debug("Initial load order:")
        for p in self.get_original_order():
            order_logger.debug("  " + p)


        # read rules from various sources, and add orderings to graph
        # if any subsequent rule causes a cycle in the current graph, it is discarded
        parser = ruleParser.rule_parser(self.active, self.graph, self.datadir,parser_out_stream,self.caseless)
        if os.path.exists(user_file):
            parser.read_rules(user_file, progress)
        if not parser.read_rules(base_file, progress):
            order_logger.error("Unable to parse 'mlox_base.txt', load order NOT sorted!")
            self.new_order = []
            return

        # now do the topological sort of all known plugins (rules + load order)
        self.add_current_order() # tertiary order "pseudo-rules" from current load order
        sorted = self.graph.topo_sort()

        # the "sorted" list will be a superset of all known plugin files,
        # inluding those in our Data Files directory.
        # but we only want to update plugins that are in our current "Data Files"
        sorted_datafiles = [f for f in sorted if f in self.active]
        (esm_files, esp_files) = configHandler.partition_esps_and_esms(sorted_datafiles)
        new_order_cname = [p for p in esm_files + esp_files]
        self.new_order = [self.caseless.truename(p) for p in new_order_cname]

        order_logger.debug("New load order:")
        for p in self.get_new_order():
            order_logger.debug("  " + p)

        if len(self.new_order) != len(self.order):
            order_logger.error("sanity check: len(self.new_order %d) != len(self.order %d)" % (len(self.new_order), len(self.order)))
            self.new_order = []
            return

        if self.order == new_order_cname:
            order_logger.info("[Plugins already in sorted order. No sorting needed!]")
            self.is_sorted = True

        if self.datadir != None:
            # these are things we do not want to do if just testing a load order from a file
            # save the load orders to file for future reference
            self.save_order(old_loadorder_output, [self.caseless.truename(p) for p in self.order], "current")
            self.save_order(new_loadorder_output, self.new_order, "mlox sorted")
        return

    def write_new_order(self):
        if self.new_order == [] or not isinstance(self.new_order,list):
            order_logger.error("Unable to save new load order.")
            return
        if configHandler.dataDirHandler(self.datadir).write(self.new_order):
            self.is_sorted = True
        else:
            order_logger.error("Unable to save new load order.")
