
import os         #To calculate the amount remaining to parse (os.path.getsize)
import re
import logging
from pprint import PrettyPrinter
import pluggraph
import fileFinder

# comments start with ';'
re_comment = re.compile(r'(?:^|\s);.*$')
# re_rule matches the start of a rule.
# TBD: check end-bracket pattern
re_rule = re.compile(r'^\[(version|order|nearend|nearstart|conflict|note|patch|requires)((?:\s+.[^\]]*)?)\](.*)$', re.IGNORECASE)


# line for multiline messages
re_message = re.compile(r'^\s')
# pattern used to match a string that should only contain a plugin name, no slop
re_plugin = re.compile(r'^(\S.*?\.es[mp]\b)([\s]*)', re.IGNORECASE)
# metacharacters for filename expansion
re_plugin_meta = re.compile(r'([*?])')
re_plugin_metaver = re.compile(r'(<VER>)', re.IGNORECASE)
re_escape_meta = re.compile(r'([()+.])')
# for recognizing our functions:
re_fun = re.compile(r'^\[(ALL|ANY|NOT|DESC|VER|SIZE)\s*', re.IGNORECASE)
re_end_fun = re.compile(r'^\]\s*')
re_desc_fun = re.compile(r'\[DESC\s*(!?)/([^/]+)/\s+([^\]]+)\]', re.IGNORECASE)
# for parsing a size predicate
re_size_fun = re.compile(r'\[SIZE\s*(!?)(\d+)\s+(\S.*?\.es[mp]\b)\s*\]', re.IGNORECASE)

# for parsing a version number
ver_delim = r'[_.-]'
re_ver_delim = re.compile(ver_delim)
plugin_version = r'(\d+(?:%s?\d+)*[a-zA-Z]?)' % ver_delim
re_alpha_tail = re.compile(r'(\d+)([a-z])', re.IGNORECASE)
re_ver_fun = re.compile(r'\[VER\s*([=<>])\s*%s\s*([^\]]+)\]' % plugin_version, re.IGNORECASE)
# for grabbing version numbers from filenames
re_filename_version = re.compile(r'\D%s\D*\.es[mp]' % plugin_version, re.IGNORECASE)
# for grabbing version numbers from plugin header description fields
re_header_version = re.compile(r'\b(?:version\b\D+|v(?:er)?\.?\s*)%s' % plugin_version, re.IGNORECASE)

# for cleaning up pretty printer
re_notstr = re.compile(r"\s*'NOT',")
re_anystr = re.compile(r"\s*'ANY',")
re_allstr = re.compile(r"\s*'ALL',")
re_indented = re.compile(r'^', re.MULTILINE)

# set of characters that are not allowed to occur in plugin names. (we allow '*' and '?' for filename matching).
# Not actually used anywhere
re_plugin_illegal = re.compile(r'[\"\\/=+<>:;|\^]')


version_operators = {'=': True, '<': True, '>': True}

tes3_min_plugin_size = 362

parse_logger = logging.getLogger('mlox.parser')

#Get the version information from a plugin
def get_version(plugin,data_dir = None):
    match = re_filename_version.search(plugin)
    file_ver = match.group(1) if match else None
    desc_ver = None
    if isinstance(data_dir,str):
        data_dir = fileFinder.caseless_dirlist(data_dir)
    if isinstance(data_dir,fileFinder.caseless_dirlist) != False:
        desc = plugin_description(data_dir.find_path(plugin))
        if desc != None:
            match = re_header_version.search(desc)
            desc_ver = match.group(1) if match else None
    if file_ver != None:
        file_ver = format_version(file_ver)
    if desc_ver != None:
        desc_ver = format_version(desc_ver)
    return (file_ver, desc_ver)

def format_version(ver):
    """convert something we think is a version number into a canonical form that can be used for comparison"""
    v = re_ver_delim.split(ver, 3)
    match = re_alpha_tail.match(v[-1])
    alpha = "_"
    if match:
        v[-1] = match.group(1)
        alpha = match.group(2)
    for i in range(0, len(v)):
        v[i] = int(v[i])
    while len(v) < 3:
        v.append(0)
    return("%05d.%05d.%05d.%s" % (v[0], v[1], v[2], alpha))

def plugin_description(plugin):
    """Read the description field of a TES3/TES4 plugin file header"""
    try:
        inp = open(plugin, 'rb')
    except IOError:
        logging.warn("Unable to open plugin file:  {0}".format(plugin))
        return("")
    block = inp.read(4096)
    inp.close()
    if block[0:4] == "TES3":    # Morrowind
        if len(block) < tes3_min_plugin_size:
            logging.warn("Cannot read plugin description(%s): file too short, returning NULL string" % plugin)
            return("")
        desc = block[64:block.find("\x00", 64)]
        return(desc)
    elif block[0:4] == "TES4":  # Oblivion
        # This is very cheesy.
        pos = block.find("SNAM", 0)
        if pos == -1: return("")
        desc_start = block.find("\x00", pos) + 1
        if desc_start == -1: return("")
        desc_end = block.find("\x00", desc_start)
        if desc_end == -1: return("")
        desc = block[desc_start:desc_end]
        return(desc)
    else:
        return("")

class rule_parser:
    """A simple recursive descent rule parser, for evaluating rule statements containing nested boolean expressions."""
    def __init__(self, active, graph, datadir,out_stream,name_converter):
        self.active = active
        self.graph = graph
        self.datadir = datadir
        self.line_num = 0
        self.rule_file = None
        self.bytesread = 0
        self.input_handle = None
        self.buffer = ""        # the parsing buffer
        self.message = []       # the comment for the current rule
        self.curr_rule = ""     # name of the current rule we are parsing
        self.parse_dbg_indent = ""
        self.out_stream = out_stream
        self.name_converter = name_converter

    def readline(self):
        """reads a line into the current parsing buffer"""
        if self.input_handle == None:
            return(False)
        try:
            while True:
                line = self.input_handle.next()
                self.bytesread += len(line)
                self.line_num += 1
                line = re_comment.sub('', line) # remove comments
                line = line.rstrip() # strip whitespace from end of line, include CRLF
                if line != "":
                    self.buffer = line
                    parse_logger.debug("readline returns: %s" % line)
                    return(True)
        except StopIteration:
            parse_logger.debug("EOF")
            self.buffer = ""
            self.input_handle.close()
            self.input_handle = None
            return(False)

    def where(self):
        return("%s:%d" % (self.rule_file, self.line_num))

    def parse_error(self, what):
        """print a message about current parsing error, and blow away the
        current parse buffer so next parse starts on next input line."""
        parse_logger("%s: Parse Error(%s), %s [Buffer=%s]" % (self.where(), self.curr_rule, what, self.buffer))
        self.buffer = ""
        self.parse_dbg_indent = self.parse_dbg_indent[:-2]

    def parse_message_block(self):
        while self.readline():
            if re_message.match(self.buffer):
                self.message.append(self.buffer)
            else:
                return

    def expand_filename(self, plugin):
        parse_logger.debug("expand_filename, plugin=%s" % plugin)
        pat = "^%s$" % re_escape_meta.sub(r'\\\1', plugin)
        # if the plugin name contains metacharacters, do filename expansion
        subbed = False
        if re_plugin_meta.search(plugin) != None:
            parse_logger.debug("expand_filename name has META: %s" % pat)
            pat = re_plugin_meta.sub(r'.\1', pat)
            subbed = True
        if re_plugin_metaver.search(plugin) != None:
            parse_logger.debug("expand_filename name has METAVER: %s" % pat)
            pat = re_plugin_metaver.sub(plugin_version, pat)
            subbed = True
        if not subbed:        # no expansions made
            return([plugin] if plugin.lower() in self.active else [])
        parse_logger.debug("expand_filename new RE pat: %s" % pat)
        matches = []
        re_namepat = re.compile(pat, re.IGNORECASE)
        for p in self.active:
            if re_namepat.match(p):
                matches.append(p)
                parse_logger.debug("expand_filename: %s expands to: %s" % (plugin, p))
        return(matches)

    def parse_plugin_name(self):
        self.parse_dbg_indent += "  "
        buff = self.buffer.strip()
        parse_logger.debug("parse_plugin_name buff=%s" % buff)
        plugin_match = re_plugin.match(buff)
        if plugin_match:
            plugin_name = self.name_converter.cname(plugin_match.group(1))
            parse_logger.debug("parse_plugin_name name=%s" % plugin_name)
            pos = plugin_match.span(2)[1]
            self.buffer = buff[pos:].lstrip()
            matches = self.expand_filename(plugin_name)
            if matches != []:
                plugin_name = matches.pop(0)
                parse_logger.debug("parse_plugin_name new name=%s" % plugin_name)
                if len(matches) > 0:
                    self.buffer = " ".join(matches) + " " + self.buffer
                return(True, plugin_name)
            self.parse_dbg_indent = self.parse_dbg_indent[:-2]
            return(False, plugin_name)
        else:
            self.parse_error("expected a plugin name")
            self.parse_dbg_indent = self.parse_dbg_indent[:-2]
            return(None, None)

    def parse_ordering(self, rule):
        self.parse_dbg_indent += "  "
        prev = None
        n_order = 0
        while self.readline():
            if re_rule.match(self.buffer):
                self.parse_dbg_indent = self.parse_dbg_indent[:-2]
                return
            p = self.parse_plugin_name()[1]
            if p == None:
                continue
            n_order += 1
            if rule == "ORDER":
                if prev != None:
                    self.graph.add_edge(self.where(), prev, p)
                prev = p
            elif rule == "NEARSTART":
                self.graph.nearstart.append(p)
                self.graph.nodes.setdefault(p, [])
            elif rule == "NEAREND":
                self.graph.nearend.append(p)
                self.graph.nodes.setdefault(p, [])
        if rule == "ORDER":
            if n_order == 0:
                parse_logger.warning("%s: ORDER rule has no entries" % (self.where()))
            elif n_order == 1:
                parse_logger.warning("%s: ORDER rule skipped because it only has one entry: %s" % (self.where(), self.name_converter.truename(prev)))

    def parse_ver(self):
        self.parse_dbg_indent += "  "
        match = re_ver_fun.match(self.buffer)
        if match:
            p = match.span(0)[1]
            self.buffer = self.buffer[p:]
            parse_logger.debug("parse_ver new buffer = %s" % self.buffer)
            op = match.group(1)
            if op not in version_operators:
                self.parse_error("Invalid [VER] operator")
                return(None, None)
            orig_ver = match.group(2)
            ver = format_version(orig_ver)
            plugin_name = match.group(3)
            expanded = self.expand_filename(plugin_name)
            expr = "[VER %s %s %s]" % (op, orig_ver, plugin_name)
            parse_logger.debug("parse_ver, expr=%s ver=%s" % (expr, ver))
            if len(expanded) == 1:
                expr = "[VER %s %s %s]" % (op, orig_ver, expanded[0])
            elif expanded == []:
                parse_logger.debug("parse_ver [VER] \"%s\" not active" % plugin_name)
                self.parse_dbg_indent = self.parse_dbg_indent[:-2]
                return(False, expr) # file does not exist
            if self.datadir == None:
                # this case is reached when doing fromfile checks
                # and we do not have the actual plugin to check, so
                # we assume that the plugin matches the given version
                if op == '=':
                    self.parse_dbg_indent = self.parse_dbg_indent[:-2]
                    return(True, expr)
                else:
                    self.parse_dbg_indent = self.parse_dbg_indent[:-2]
                    return(False, expr)
            for xp in expanded:
                plugin = self.name_converter.cname(xp)
                plugin_t = self.name_converter.truename(plugin)
                desc = plugin_description(self.datadir.find_path(plugin))
                match = re_header_version.search(desc)
                if match:
                    p_ver_orig = match.group(1)
                    p_ver = format_version(p_ver_orig)
                    parse_logger.debug("parse_ver (header) version(%s) = %s (%s)" % (plugin_t, p_ver_orig, p_ver))
                else:
                    match = re_filename_version.search(plugin)
                    if match:
                        p_ver_orig = match.group(1)
                        p_ver = format_version(p_ver_orig)
                        parse_logger.debug("parse_ver (filename) version(%s) = %s (%s)" % (plugin_t, p_ver_orig, p_ver))
                    else:
                        parse_logger.debug("parse_ver no version for %s" % plugin_t)
                        return(False, expr)
                parse_logger.debug("parse_ver compare  p_ver=%s %s ver=%s" % (p_ver, op, ver))
                result = True
                if op == '=':
                    result = (p_ver == ver)
                elif op == '<':
                    result = (p_ver < ver)
                elif op == '>':
                    result = (p_ver > ver)
                if result:
                    self.parse_dbg_indent = self.parse_dbg_indent[:-2]
                    return(True, "[VER %s %s %s]" % (op, orig_ver, plugin))
            self.parse_dbg_indent = self.parse_dbg_indent[:-2]
            return(False, expr)
        self.parse_dbg_indent = self.parse_dbg_indent[:-2]
        self.parse_error("Invalid [VER] function")
        return(None, None)

    def parse_desc(self):
        """match patterns against the description string in the plugin header."""
        self.parse_dbg_indent += "  "
        match = re_desc_fun.match(self.buffer)
        if match:
            p = match.span(0)[1]
            self.buffer = self.buffer[p:]
            parse_logger.debug("parse_desc new buffer = %s" % self.buffer)
            bang = match.group(1) # means to invert the meaning of the match
            pat = match.group(2)
            plugin_name = match.group(3)
            expr = "[DESC %s/%s/ %s]" % (bang, pat, plugin_name)
            parse_logger.debug("parse_desc, expr=%s" % expr)
            expanded = self.expand_filename(plugin_name)
            if len(expanded) == 1:
                expr = "[DESC %s/%s/ %s]" % (bang, pat, expanded[0])
            elif expanded == []:
                parse_logger.debug("parse_desc [DESC] \"%s\" not active" % plugin_name)
                self.parse_dbg_indent = self.parse_dbg_indent[:-2]
                return(False, expr) # file does not exist
            if self.datadir == None:
                # this case is reached when doing fromfile checks,
                # which do not have access to the actual plugin, so we
                # always assume the test is merely for file existence,
                # to err on the side of caution
                self.parse_dbg_indent = self.parse_dbg_indent[:-2]
                return(True, expr)
            for xp in expanded:
                plugin = self.name_converter.cname(xp)
                plugin_t = self.name_converter.truename(plugin)
                re_pat = re.compile(pat)
                desc = plugin_description(self.datadir.find_path(plugin))
                bool = (re_pat.search(desc) != None)
                if bang == "!": bool = not bool
                parse_logger.debug("parse_desc [DESC] returning: (%s, %s)" % (bool, expr))
                if bool:
                    self.parse_dbg_indent = self.parse_dbg_indent[:-2]
                    return(True, "[DESC %s/%s/ %s]" % (bang, pat, plugin_t))
            self.parse_dbg_indent = self.parse_dbg_indent[:-2]
            return(False, expr)
        self.parse_dbg_indent = self.parse_dbg_indent[:-2]
        self.parse_error("Invalid [DESC] function")
        return(None, None)

    def parse_size(self):
        """check the given size of the plugin."""
        self.parse_dbg_indent += "  "
        match = re_size_fun.match(self.buffer)
        if match:
            p = match.span(0)[1]
            self.buffer = self.buffer[p:]
            parse_logger.debug("parse_size new buffer = %s" % self.buffer)
            bang = match.group(1) # means "is not this size"
            wanted_size = int(match.group(2))
            plugin_name = match.group(3)
            expr = "[SIZE %s%d %s]" % (bang, wanted_size, plugin_name)
            parse_logger.debug("parse_size, expr=%s" % expr)
            expanded = self.expand_filename(plugin_name)
            if len(expanded) == 1:
                expr = "[SIZE %s%d %s]" % (bang, wanted_size, expanded[0])
            elif expanded == []:
                parse_logger.debug("parse_size [SIZE] \"%s\" not active" % match.group(3))
                self.parse_dbg_indent = self.parse_dbg_indent[:-2]
                return(False, expr) # file does not exist
            if self.datadir == None:
                # this case is reached when doing fromfile checks,
                # which do not have access to the actual plugin, so we
                # always assume the test is merely for file existence,
                # to err on the side of caution
                self.parse_dbg_indent = self.parse_dbg_indent[:-2]
                return(True, expr)
            for xp in expanded:
                plugin = self.name_converter.cname(xp)
                plugin_t = self.name_converter.truename(plugin)
                actual_size = os.path.getsize(self.datadir.find_path(plugin))
                bool = (actual_size == wanted_size)
                if bang == "!": bool = not bool
                parse_logger.debug("parse_size [SIZE] returning: (%s, %s)" % (bool, expr))
                self.parse_dbg_indent = self.parse_dbg_indent[:-2]
                if bool:
                    self.parse_dbg_indent = self.parse_dbg_indent[:-2]
                    return(True, "[SIZE %s%d %s]" % (bang, wanted_size, plugin_t))
            self.parse_dbg_indent = self.parse_dbg_indent[:-2]
            return(False, expr)
        self.parse_dbg_indent = self.parse_dbg_indent[:-2]
        self.parse_error("Invalid [SIZE] function")
        return(None, None)

    def parse_expression(self, prune=False):
        self.parse_dbg_indent += "  "
        self.buffer = self.buffer.strip()
        if self.buffer == "":
            if self.readline():
                if re_rule.match(self.buffer):
                    parse_logger.debug("parse_expression new line started new rule, returning None")
                    self.parse_dbg_indent = self.parse_dbg_indent[:-2]
                    return(None, None)
                self.buffer = self.buffer.strip()
            else:
                parse_logger.debug("parse_expression EOF, returning None")
                self.parse_dbg_indent = self.parse_dbg_indent[:-2]
                return(None, None)
        parse_logger.debug("parse_expression, start buffer: \"%s\"" % self.buffer)
        match = re_fun.match(self.buffer)
        if match:
            fun = match.group(1).upper()
            if fun == "DESC":
                parse_logger.debug("parse_expression calling parse_desc()")
                self.parse_dbg_indent = self.parse_dbg_indent[:-2]
                return(self.parse_desc())
            elif fun == "VER":
                parse_logger.debug("parse_expression calling parse_ver()")
                self.parse_dbg_indent = self.parse_dbg_indent[:-2]
                return(self.parse_ver())
            elif fun == "SIZE":
                parse_logger.debug("parse_expression calling parse_size()")
                self.parse_dbg_indent = self.parse_dbg_indent[:-2]
                return(self.parse_size())
            # otherwise it's a boolean function ...
            parse_logger.debug("parse_expression parsing expression: \"%s\"" % self.buffer)
            p = match.span(0)[1]
            self.buffer = self.buffer[p:]
            parse_logger.debug("fun = %s" % fun)
            vals = []
            exprs = []
            bool_end = re_end_fun.match(self.buffer)
            parse_logger.debug("self.buffer 1 =\"%s\"" % self.buffer)
            while not bool_end:
                (bool, expr) = self.parse_expression(prune)
                if bool == None:
                    self.parse_error("[%s] Invalid boolean arguments" % fun)
                    return(None, None)
                exprs.append(expr)
                vals.append(bool)
                parse_logger.debug("self.buffer 2 =\"%s\"" % self.buffer)
                bool_end = re_end_fun.match(self.buffer)
            pos = bool_end.span(0)[1]
            self.buffer = self.buffer[pos:]
            parse_logger.debug("self.buffer 3 =\"%s\"" % self.buffer)
            if fun == "ALL":
                # prune out uninteresting expressions from ANY results
                exprs = [e for e in exprs if not(isinstance(e, list) and e == [])]
                self.parse_dbg_indent = self.parse_dbg_indent[:-2]
                return(all(vals), exprs[0] if len(exprs) == 1 else ["ALL"] + exprs)
            if fun == "ANY":
                # prune out uninteresting expressions from ANY results
                if prune:
                    exprs = [e for e in exprs if not(isinstance(e, str) and e[0:8] == "MISSING(")]
                self.parse_dbg_indent = self.parse_dbg_indent[:-2]
                self.parse_dbg_indent = self.parse_dbg_indent[:-2]
                return(any(vals), exprs[0] if len(exprs) == 1 else ["ANY"] + exprs)
            if fun == "NOT":
                self.parse_dbg_indent = self.parse_dbg_indent[:-2]
                return(not(all(vals)), ["NOT"] + exprs)
            else:
                # should not be reached due to match on re_fun
                self.parse_error("Expected Boolean function (ALL, ANY, NOT)")
                return(None, None)
            parse_logger.debug("parse_expression NOTREACHED")
        else:
            if re_fun.match(self.buffer):
                self.parse_error("Invalid function expression")
                return(None, None)
            parse_logger.debug("parse_expression parsing plugin: \"%s\"" % self.buffer)
            (exists, p) = self.parse_plugin_name()
            if exists != None and p != None:
                p = self.name_converter.truename(p) if exists else ("MISSING(%s)" % self.name_converter.truename(p))
            self.parse_dbg_indent = self.parse_dbg_indent[:-2]
            return(exists, p)
        parse_logger.debug("parse_expression NOTREACHED(2)")

    def pprint(self, expr, prefix):
        """pretty printer for parsed expressions"""
        formatted = PrettyPrinter(indent=2).pformat(expr)
        formatted = re_notstr.sub("NOT", formatted)
        formatted = re_anystr.sub("ANY", formatted)
        formatted = re_allstr.sub("ALL", formatted)
        return(re_indented.sub(prefix, formatted))

    #Remove the missing plugins from the 'ANY' expression
    def _prune_any(self,item):
        #Don't operate on simple strings
        if isinstance(item,list) == False:
            return item
        #Recursive search to make sure we get any nested expressions
        for i in range(0,len(item)):
            item[i] = self._prune_any(item[i])
        #Prune all the missing plugins
        if item[0] == 'ANY':
            return filter(lambda x: x.find('MISSING(') == -1, item)
        return item

    def parse_statement(self, rule, msg, expr):
        self.parse_dbg_indent += "  "
        parse_logger.debug("parse_statement(%s, %s, %s)" % (rule, msg, expr))
        expr = expr.strip()
        if msg == "":
            if expr == "":
                self.parse_message_block()
                expr = self.buffer
        else:
            self.message = [msg]
        if expr == "":
            if not self.readline():
                self.parse_dbg_indent = self.parse_dbg_indent[:-2]
                return
        else:
            self.buffer = expr
        msg = "" if self.message == [] else " |" + "\n |".join(self.message) # no ending LF
        if rule == "CONFLICT":  # takes any number of exprs
            exprs = []
            parse_logger.debug("before conflict parse_expr() expr=%s line=%s" % (expr, self.buffer))
            (bool, expr) = self.parse_expression()
            parse_logger.debug("conflict parse_expr()1 bool=%s bool=%s" % (bool, expr))
            while bool != None:
                if bool:
                    exprs.append(expr)
                (bool, expr) = self.parse_expression()
                parse_logger.debug("conflict parse_expr()N bool=%s bool=%s" % ("True" if bool else "False", expr))
            if len(exprs) > 1:
                self.out_stream.write("[CONFLICT]")
                for e in exprs:
                    self.out_stream.write(self.pprint(self._prune_any(e), " > "))
                if msg != "": self.out_stream.write(msg)
        elif rule == "NOTE":    # takes any number of exprs
            parse_logger.debug("function NOTE: %s" % msg)
            exprs = []
            (bool, expr) = self.parse_expression(prune=True)
            while bool != None:
                if bool:
                    exprs.append(expr)
                (bool, expr) = self.parse_expression(prune=True)
            if len(exprs) > 0:
                self.out_stream.write("[NOTE]")
                for e in exprs:
                    self.out_stream.write(self.pprint(e, " > "))
                if msg != "": self.out_stream.write(msg)
        elif rule == "PATCH":   # takes 2 exprs
            (bool1, expr1) = self.parse_expression()
            if bool1 == None:
                parse_logger.warning("%s: PATCH rule invalid first expression" % (self.where()))
                self.parse_dbg_indent = self.parse_dbg_indent[:-2]
                return
            (bool2, expr2) = self.parse_expression()
            if bool2 == None:
                parse_logger.warning("%s: PATCH rule invalid second expression" % (self.where()))
                self.parse_dbg_indent = self.parse_dbg_indent[:-2]
                return
            if bool1 and not bool2:
                # case where the patch is present but the thing to be patched is missing
                self.out_stream.write("[PATCH]\n%s is missing some pre-requisites:\n%s" %
                        (self.pprint(expr1, " !!"), self.pprint(expr2, " ")))
                if msg != "": self.out_stream.write(msg)
            if bool2 and not bool1:
                # case where the patch is missing for the thing to be patched
                self.out_stream.write("[PATCH]\n%s for:\n%s" %
                        (self.pprint(expr1, " !!"), self.pprint(expr2, " ")))
                if msg != "": self.out_stream.write(msg)
        elif rule == "REQUIRES": # takes 2 exprs
            (bool1, expr1) = self.parse_expression(prune=True)
            if bool1 == None:
                parse_logger.warning("%s: REQUIRES rule invalid first expression" % (self.where()))
                self.parse_dbg_indent = self.parse_dbg_indent[:-2]
                return
            (bool2, expr2) = self.parse_expression()
            if bool2 == None:
                parse_logger.warning("%s: REQUIRES rule invalid second expression" % (self.where()))
                self.parse_dbg_indent = self.parse_dbg_indent[:-2]
                return
            if bool1 and not bool2:
                expr2_str = self.pprint(expr2, " > ")
                self.out_stream.write("[REQUIRES]\n%s Requires:\n%s" %
                        (self.pprint(expr1, " !!!"), expr2_str))
                if msg != "": self.out_stream.write(msg)
                match = re_filename_version.search(expr2_str)
                if match:
                    self.out_stream.write(" | [Note that you may see this message if you have an older version of one\n | of the pre-requisites. In that case, it is suggested that you upgrade\n | to the newer version].")
        self.parse_dbg_indent = self.parse_dbg_indent[:-2]
        parse_logger.debug("parse_statement RETURNING")

    def read_rules(self, rule_file, progress = None):
        """Read rules from rule files (e.g., mlox_user.txt or mlox_base.txt),
        add order rules to graph, and print warnings."""
        n_rules = 0
        self.rule_file = rule_file

        pmsg = "Loading: %s" % rule_file

        parse_logger.debug("Reading rules from: \"{0}\"".format(self.rule_file))
        try:
            self.input_handle = open(self.rule_file, 'r')
            inputsize = os.path.getsize(self.rule_file)
        except IOError, OSError:
            #This can't be too important, because we try to read the user rules file, and it doesn't exist for most people (TODO:  Move file existance checking somewhere else, and change this from info to error)
            parse_logger.info("Unable to open rules file:  {0}".format(self.rule_file))
            return False

        self.line_num = 0
        while True:
            if self.buffer == "":
                if not self.readline():
                    break
            if progress != None and inputsize > 0:
                pct = int(100*self.bytesread/inputsize)
                if pct % 3 == 0 and pct < 100:
                    progress.Update(pct, pmsg)
            self.parse_dbg_indent = ""
            self.curr_rule = ""
            new_rule = re_rule.match(self.buffer)
            if new_rule:        # start a new rule
                n_rules += 1
                self.curr_rule = new_rule.group(1).upper()
                self.message = []
                if self.curr_rule == "VERSION":
                    self.buffer = ""
                elif self.curr_rule in ("ORDER", "NEAREND", "NEARSTART"):
                    self.parse_ordering(self.curr_rule)
                elif self.curr_rule in ("CONFLICT", "NOTE", "PATCH", "REQUIRES"):
                    self.parse_statement(self.curr_rule, new_rule.group(2), new_rule.group(3))
                else:
                    # we should never reach here, since re_rule only matches known rules
                    self.parse_error("read_rules failed sanity check, unknown rule")
            else:
                self.parse_error("expected start of rule")
        parse_logger.info("Read {0} rules from: \"{1}\"".format(n_rules, self.rule_file))
        return True
