import sys
import subprocess
import re
import os
import queue

class bcolors:
    PURPLE = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

class Analyzer:
    ASSIGNMENT_OPS = ["+=", "-=", "=", "++", "--"]
    COMPARE_OPS = ["<=", ">=", "<", ">"]

    def __init__(self, cfg_str, name_str):
        self.functions = []
        self.cfg = {}
        self.back_edges = {}
        self.loops = {}
        self.definitions = {}
        self.variables = {}
        self.count = {}
        self.reachability = {}
        self.names = name_str.splitlines()
        function = ""
        block = ""
        for line in cfg_str.splitlines():
            line = line.strip() #removes whitespace on either end of line
            if len(line) == 0:
                continue
            if bool(re.match("\[", line)):
                block = int(re.search("\d+", line)[0])
                self.cfg[function][block] = {}
            elif bool(re.match("\d+", line)):
                elements = line.split(":", maxsplit=1)
                self.cfg[function][block][int(elements[0])] = elements[1].strip()
            elif bool(re.match("T", line)):
                elements = line.split(":", maxsplit=1)
                self.cfg[function][block]["T"] = elements[1].strip()
            elif bool(re.match("Preds", line)):
                elements = line.split(":", maxsplit=1)
                self.cfg[function][block]["Preds"] = list(map(int, re.findall("\d+", elements[1])))
            elif bool(re.match("Succs", line)):
                elements = line.split(":", maxsplit=1)
                self.cfg[function][block]["Succs"] = list(map(int, re.findall("\d+", elements[1])))
            else:
                function = line
                self.cfg[function] = {}
                self.back_edges[function] = {}
                self.loops[function] = []
                self.definitions[function] = {}
                self.variables[function] = {}
                self.count[function] = 0
                self.functions.append(function)
                self.reachability[function] = {}
        for function, blocks in self.cfg.items():
            self.cfg[function] = dict(sorted(blocks.items(), key=lambda kv: kv[0], reverse=True))

    def __str__(self):
        #print data structure
        string = "\nCFG:\n"
        for function in self.functions:
            string += "\n" + function + "\n"
            for block, lines in self.cfg[function].items():
                string += bcolors.YELLOW + "  " + str(block) + "\n" + bcolors.ENDC
                if isinstance(lines, list):
                    for item in lines:
                        string += ("    " + str(item) + "\n")
                elif isinstance(lines, dict):
                    for key, value in lines.items():
                        if "Dom" == key:
                            string += bcolors.RED
                        elif "T" == key:
                            string += bcolors.CYAN
                        elif "Preds" == key:
                            string += bcolors.PURPLE
                        elif "Succs" == key:
                            string += bcolors.PURPLE
                        string += ("    " + str(key) + ":" + str(value) + "\n")
                else:
                    string += ("    " + lines + "\n")
                string += bcolors.ENDC

            string += "\nBack Edges:\n" + bcolors.GREEN
            for key, value in self.back_edges[function].items():
                string += "    " + str(key) + ":" + str(value) + "\n"
            string += bcolors.ENDC

            string += "\nLoops:\n" + bcolors.GREEN
            for loop in self.loops[function]:
                string += "    " + str(loop) + "\n"
            string += bcolors.ENDC

            string += "\nDefinitions:\n"
            for definition, lines in self.definitions[function].items():
                string += bcolors.YELLOW + "  " + str(definition) + "\n" + bcolors.ENDC
                if isinstance(lines, list):
                    for item in lines:
                        string += ("    " + str(item) + "\n")
                elif isinstance(lines, dict):
                    for key, value in lines.items():
                        if key == "Def":
                            string += bcolors.RED
                        elif key == "Var":
                            string += bcolors.CYAN
                        string += ("    " + str(key) + ":" + str(value) + "\n")
                        string += bcolors.ENDC
                else:
                    string += ("    " + str(lines) + "\n")
                string += bcolors.ENDC

            string += "\nVariables:\n"
            for variable, lines in self.variables[function].items():
                string += bcolors.YELLOW + "  " + str(variable) + "\n" + bcolors.ENDC
                if isinstance(lines, list):
                    for item in lines:
                        string += ("    " + str(item) + "\n")
                elif isinstance(lines, dict):
                    for key, value in lines.items():
                        if key == "Def":
                            string += bcolors.RED
                        elif key == "Var":
                            string += bcolors.CYAN
                        string += ("    " + str(key) + ":" + str(value) + "\n")
                        string += bcolors.ENDC
                else:
                    string += ("    " + str(lines) + "\n")
                string += bcolors.ENDC

            string += "\nReachability:\n"
            for block, lines in self.reachability[function].items():
                string += bcolors.YELLOW + "  " + str(block) + "\n" + bcolors.ENDC
                if isinstance(lines, list):
                    for item in lines:
                        string += ("    " + str(item) + "\n")
                elif isinstance(lines, dict):
                    for key, value in lines.items():
                        if key in ["MAYGEN", "DOESGEN", "KILL"]:
                            string += bcolors.RED
                        elif key in ["Preds", "Succs"]:
                            string += bcolors.PURPLE
                        elif key in ["Min", "Mout", "Uin", "Uout"]:
                            string += bcolors.CYAN
                        string += ("    " + str(key) + ":" + str(value) + "\n")
                        string += bcolors.ENDC
                else:
                    string += ("    " + lines + "\n")
                string += bcolors.ENDC

        return string


    def add_dominance_edges(self, dom_str):
        #store dominance edges in data structure
        function_iter = iter(self.cfg.keys())
        for line in dom_str.splitlines():
            if not line.startswith("("):
                function = next(function_iter)
                continue
            edge = list(map(int, re.findall("\d+", line)))
            self.cfg[function][edge[0]]["Dom"] = edge[1]

    def identify_loops(self):
        #find and store back edges
        for function in self.functions:
            for block, lines in self.cfg[function].items():
                if "Succs" not in lines:
                    continue
                for succ in lines["Succs"]:
                    prev = block
                    dom = self.cfg[function][prev]["Dom"]
                    dominated = False
                    while dom != prev:
                        if dom == succ:
                            dominated = True
                            break
                        prev = dom
                        dom = self.cfg[function][prev]["Dom"]
                    if dominated and succ > block:
                        self.back_edges[function][block] = succ

        #find and store loops in CFG
        for function in self.functions:
            for n, d in self.back_edges[function].items():
                loop = [n, d]
                stack = [n]
                while len(stack) != 0:
                    m = stack.pop()
                    if "Preds" not in self.cfg[function][m]:
                        continue
                    for pred in self.cfg[function][m]["Preds"]:
                        if pred not in loop:
                            loop.append(pred)
                            stack.append(pred)
                loop.sort(reverse=True)
                self.loops[function].append({"Blocks": loop})
            self.loops[function].sort(key=lambda loop: len(loop["Blocks"]))

    def expand_line(self, function, statement):
        def repl(matchobj):
            return self.cfg[function][int(matchobj[1])][int(matchobj[2])]
        statement = re.sub("\(.*?\)", "", statement)
        prev = statement
        statement = re.sub("\[B(\d+)\.(\d+)\]", repl, prev)
        while statement != prev:
            statement = re.sub("\(.*?\)", "", statement)
            prev = statement
            statement = re.sub("\[B(\d+)\.(\d+)\]", repl, prev)
        self.function = None
        return statement

    def initialize_sets(self):
        #calculate MAYGEN, DOESGEN for each basic block
        for function in self.functions:
            for block, lines in self.cfg[function].items():
                self.reachability[function][block] = {
                    'DOESGEN': [],
                    'MAYGEN': [],
                    'KILL': []
                }
                reach_block = self.reachability[function][block]
                cfg_block = self.cfg[function][block]
                reach_block['Preds'] = cfg_block['Preds'] if 'Preds' in cfg_block else []
                reach_block['Succs'] = cfg_block['Succs'] if 'Succs' in cfg_block else []

                stmt_lines = list(filter(lambda line: isinstance(line, int), lines.keys()))
                #for each statement in block, check if assignment occurs
                for key in stmt_lines:
                    statement = lines[key]
                    stmt = None
                    var = None
                    klee_assume = False
                    array = False
                    index = None
                    indices = None
                    if "klee_assume" in statement:
                        klee_assume = True
                        definition = re.search("\((.*?)\)", lines[max(stmt_lines)])
                        stmt = self.expand_line(function, definition[1])
                        stmt = stmt.replace(" ", "")
                        for comparison in self.COMPARE_OPS + ["=="]:
                            if comparison in stmt:
                                var = stmt.partition(comparison)[0]
                                break
                    else:
                        if any(comparison in self.COMPARE_OPS + ["=="] for comparison in statement):
                            continue
                        for assignment in self.ASSIGNMENT_OPS:
                            if assignment in statement:
                                #expand all block references
                                stmt = self.expand_line(function, statement)
                                stmt = stmt.replace(" ", "")
                                var = stmt.partition(assignment)[0]
                                break

                    if stmt == None or var == None: continue

                    #check if array
                    array_match = re.match("(.*?)\[(.*?)\]", var)
                    if array_match != None:
                        array = True
                        var = array_match[1]
                        index = array_match[2]
                        if bool(re.match("\d+", index)):
                            indices = [int(index)]

                    reach_block['DOESGEN'].append(self.count[function])
                    reach_block['MAYGEN'].append(self.count[function])

                    #check if this block kills any definitions
                    keys = list(self.definitions[function].keys())
                    keys.reverse()

                    for key in keys:
                        if self.definitions[function][key]['Var'] == var:
                            #killing definitions in the same block needs to be handled differently
                            if key in reach_block['MAYGEN']:
                                reach_block['DOESGEN'].remove(key)
                                reach_block['MAYGEN'].remove(key)
                            else:
                                reach_block['KILL'].append(key)
                            break

                    #update variables object
                    self.variables[function][self.count[function]] = {
                        'Var': var,
                        "Array": array,
                        "Index": index,
                        "Indices": indices
                    }

                    #update definitions object
                    self.definitions[function][self.count[function]] = {
                        'Def': stmt,
                        'Var': var,
                        "KleeAssume": klee_assume,
                        "Array": array,
                        "Index": index
                    }
                    self.count[function] += 1

    def calculate_reachability(self, function, block):
        reach_block = self.reachability[function][block]

        if "Preds" in reach_block:
            MoutPred = []
            UoutPred = []
            for pred in reach_block["Preds"]:
                for mout in self.reachability[function][pred]["Mout"]:
                    if mout not in MoutPred: MoutPred.append(mout)
                UoutPred.append(self.reachability[function][pred]["Uout"])

            #Min = union MoutPred
            Min = MoutPred
            reach_block["Min"] = Min

            #Uin = intersection UoutPred
            Uin = list(set.intersection(*map(set, UoutPred))) if len(UoutPred) > 0 else []
            reach_block["Uin"] = Uin

            #Mout = (Min - KILL) union MAYGEN
            for kill in reach_block['KILL']:
                if kill in Min: Min.remove(kill)
            reach_block["Mout"] = reach_block["MAYGEN"].copy() + Min

            #Uout = Uin union DOESGEN
            reach_block["Uout"] = reach_block["DOESGEN"].copy()
            for uin in Uin:
                if uin not in reach_block["Uout"]: reach_block["Uout"].append(uin)
        else:
            reach_block["Mout"] = reach_block["MAYGEN"].copy()
            reach_block["Uout"] = reach_block["DOESGEN"].copy()

    def calculate_loops(self):
        #inner loops: calculate Min, Mout, Uin, Uout
        for function in self.functions:
            for loop in self.loops[function]:
                header = self.reachability[function][loop["Blocks"][0]]
                header["Mout"] = header["MAYGEN"]
                header["Uout"] = header["DOESGEN"]

                for block in loop["Blocks"][1:]:
                    self.calculate_reachability(function, block)

    def determine_loop_indices(self):
        for function in self.functions:
            for loop in self.loops[function]:
                update = self.reachability[function][loop["Blocks"][-1]]
                definition = self.definitions[function][update['MAYGEN'][0]]

                for assignment in self.ASSIGNMENT_OPS:
                    if assignment in definition['Def']:
                        var, _, val = definition['Def'].partition(assignment)
                        loop["Var"] = var
                        if assignment == "+=":
                            loop["Step"] = int(val)
                        elif assignment == "-=":
                            loop["Step"] = -int(val)
                        elif assignment == "++":
                            loop["Step"] = 1
                        elif assignment == "--":
                            loop["Step"] = -1
                        break

                condition = self.cfg[function][loop["Blocks"][0]]
                for key, statement in condition.items():
                    if not isinstance(key, int): continue
                    for comparison in self.COMPARE_OPS:
                        if comparison in statement:
                            stmt = self.expand_line(function, statement)
                            bound = int(stmt.partition(comparison)[2])
                            if comparison == "<=":
                                loop["End"] = bound + 1
                            elif comparison == "<":
                                loop["End"] = bound
                            elif comparison == ">=":
                                loop["End"] = bound - 1
                            elif comparison == ">":
                                loop["End"] = bound
                            break
                        if "End" in loop: break

                init = self.reachability[function][loop["Blocks"][0] + 1]
                for maygen in init['MAYGEN']:
                    definition = self.definitions[function][maygen]
                    if loop['Var'] in definition["Def"]:
                        loop["Start"] = int(definition["Def"].partition("=")[2])

                loop["Range"] = range(loop["Start"], loop["End"], loop["Step"])

    # header is the only way in or out of the loop
    def replace_loops(self):
        for function in self.functions:
            block_counter = max(list(filter(lambda block: isinstance(block, int), self.reachability[function].keys()))) + 1
            for loop in self.loops[function]:
                header = loop["Blocks"][0]
                header_block = self.reachability[function][header]
                exit = loop["Blocks"][-1]
                exit_block = self.reachability[function][exit]

                loop["Summary"] = block_counter
                self.reachability[function][block_counter] = {}
                loop_block = self.reachability[function][block_counter]
                loop_block["DOESGEN"] = exit_block["Uout"]
                loop_block["MAYGEN"] = exit_block["Mout"]

                for variable in loop_block["DOESGEN"]:
                    loop_var = self.variables[function][variable]
                    if loop_var["Array"] == True:
                        if loop_var["Index"] == loop["Var"]:
                            loop_var["Indices"] = list(loop["Range"])
                        elif isinstance(loop_var["Index"], int):
                            loop_var["Indices"] = [int(loop_var["Index"])]

                loop_block["Preds"] = header_block["Preds"]
                loop_block["Succs"] = header_block["Succs"]
                killed_defs = []
                gen_defs = []
                for block in loop["Blocks"]:
                    if block in loop_block["Preds"]:
                        loop_block["Preds"].remove(block)
                    if block in loop_block["Succs"]:
                        loop_block["Succs"].remove(block)

                    killed_defs += self.reachability[function][block]["KILL"]
                    gen_defs += self.reachability[function][block]["MAYGEN"]

                loop_block["KILL"] = []
                for definition in killed_defs:
                    if definition not in gen_defs:
                        loop_block["KILL"].append(definition)

                #update Succs and Preds to remove loop
                for block, lines in self.reachability[function].items():
                    for key, value in lines.items():
                        if key in ["Succs", "Preds"] and header in value:
                            value.remove(header)
                            value.append(block_counter)
                block_counter += 1

    def calculate_flat(self):
        for function in self.functions:
            entry = list(self.reachability[function].keys())[0]
            q = queue.Queue(len(self.reachability[function].keys()))
            q.put(entry)
            seen = set()
            while not q.empty():
                block = q.get()
                if "Preds" in self.reachability[function][block]:
                    ready = True
                    for pred in self.reachability[function][block]["Preds"]:
                        if pred not in seen:
                            q.put(block)
                            ready = False
                            break
                    if not ready:
                        continue
                self.calculate_reachability(function, block)
                seen.add(block)
                for succs in self.reachability[function][block]["Succs"]:
                    if succs not in seen:
                        q.put(succs)

    def reachability_analysis(self):
        self.initialize_sets()
        self.calculate_loops()
        self.determine_loop_indices()
        self.replace_loops()
        self.calculate_flat()

if __name__ == "__main__":
    #validate command line input
    if len(sys.argv) < 2:
        print("Command line arguments are required")
        exit()
    else:
        for arg in sys.argv[1:]:
            if not arg.endswith(".c") and not arg.endswith(".cpp"):
                print(arg + " is not a c or cpp file")
                exit()
            if not os.path.exists(arg):
                print(arg + " is not a valid file")
                exit()

    #generate control flow graph
    cfg_command = "clang -c -Xclang -analyze -Xclang -analyzer-checker=debug.DumpCFG "
    output = subprocess.check_output((cfg_command + sys.argv[1]).split(), stderr=subprocess.STDOUT)
    cfg_str = output.decode('UTF-8')

    #list variable and function names
    name_command = "clang -c -Xclang -analyze -Xclang -ast-list "
    output = subprocess.check_output((name_command + sys.argv[1]).split(), stderr=subprocess.STDOUT)
    name_str = output.decode('UTF-8')

    #initialize CFG
    cfg = Analyzer(cfg_str, name_str)

    #generate dominance tree
    dom_command = "clang -c -Xclang -analyze -Xclang -analyzer-checker=debug.DumpDominators "
    output = subprocess.check_output((dom_command + sys.argv[1]).split(), stderr=subprocess.STDOUT)
    dom_str = output.decode('UTF-8')

    #calculate loops
    cfg.add_dominance_edges(dom_str)
    cfg.identify_loops()

    #perform reachability analysis
    cfg.reachability_analysis()

    #debug print CFG
    print(cfg)
