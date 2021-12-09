import sys
import subprocess
import re
import os

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
    def __init__(self, cfg_str, name_str):
        self.functions = []
        self.cfg = {}
        self.back_edges = {}
        self.loops = {}
        self.definitions = {}
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
                self.definitions[function] = { 'Count': 0 }
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

            string += "\n    Back Edges:\n" + bcolors.GREEN
            for key, value in self.back_edges[function].items():
                string += "    " + str(key) + ":" + str(value) + "\n"
            string += bcolors.ENDC

            string += "\n    Loops:\n" + bcolors.GREEN
            for loop in self.loops[function]:
                string += "    " + str(loop) + "\n"
            string += bcolors.ENDC

            string += "\n    Definitions:\n" + bcolors.GREEN
            for key, value in self.definitions[function].items():
                string += "    " + str(key) + ":" + str(value) + "\n"
            string += bcolors.ENDC

            string += "\n    Reachability:\n" + bcolors.GREEN
            for key, value in self.reachability[function].items():
                string += "    " + str(key) + ":" + str(value) + "\n"
            string += bcolors.ENDC

        string += "\n    Vars:\n"
        string += "    " + str(self.names)

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

    ASSIGNMENT_OPS = ["+=", "-=", "=", "++", "--"]

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

                #for each statement in block, check if assignment occurs
                for key in list(filter(lambda line: isinstance(line, int), lines.keys())):
                    statement = lines[key]
                    if "==" in statement: continue
                    for assignment in self.ASSIGNMENT_OPS:
                        if assignment in statement:
                            #expand all block references
                            stmt = self.expand_line(function, statement)
                            var = stmt.partition(assignment)[0]

                            definition_count = self.definitions[function]["Count"]
                            reach_block['DOESGEN'].append(var)
                            reach_block['MAYGEN'].append(definition_count)

                            #check if this block kills any definitions
                            keys = list(self.definitions[function].keys())
                            keys.remove('Count')
                            keys.reverse()
                            for key in keys:
                                if self.definitions[function][key]['Var'] == var:
                                    #killing definitions in the same block needs to be handled differently
                                    if key in reach_block['MAYGEN']:
                                        reach_block['DOESGEN'].remove(var)
                                        reach_block['MAYGEN'].remove(key)
                                    else:
                                        reach_block['KILL'].append(key)
                                    break

                            #update definitions object
                            self.definitions[function][definition_count] = { 'Def': stmt, 'Var': var }
                            self.definitions[function]["Count"] = definition_count + 1
                            break

    def calculate_loops(self):
        #inner loops: calculate Min, Mout, Uin, Uout
        for function in self.functions:
            for loop in self.loops[function]:
                header = self.reachability[function][loop["Blocks"][0]]
                header["Mout"] = header["MAYGEN"]
                header["Uout"] = header["DOESGEN"]

                for block in loop["Blocks"][1:]:
                    cfg_block = self.cfg[function][block]
                    reach_block = self.reachability[function][block]
                    MoutPred = []
                    UoutPred = []
                    for pred in cfg_block["Preds"]:
                        MoutPred += self.reachability[function][pred]["Mout"]
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
                    reach_block["Mout"] = reach_block["MAYGEN"] + Min

                    #Uout = Uin union DOESGEN
                    reach_block["Uout"] = reach_block["DOESGEN"] + Uin

    def determine_loop_indices(self):
        for function in self.functions:
            for loop in self.loops[function]:
                init = self.reachability[function][loop["Blocks"][0] + 1]
                cond = self.reachability[function][loop["Blocks"][0]]
                update = self.reachability[function][loop["Blocks"][-1]]
                definition = self.definitions[function][update['MAYGEN'][0]]
                begin = 0
                end = 0
                step = 0
                for assignment in self.ASSIGNMENT_OPS:
                    if assignment in definition['Def']:
                        var, _, val = definition['Def'].partition(assignment)
                        if assignment == "+=":
                            step = int(val)
                        elif assignment == "-=":
                            step = -int(val)
                        elif assignment == "++":
                            step = 1
                        elif assignemnt == "--":
                            step = -1
                        break

    def calculate_reachability(self):
        self.initialize_sets()
        self.calculate_loops()
        self.determine_loop_indices()

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
    cfg.calculate_reachability()

    #debug print CFG
    print(cfg)
