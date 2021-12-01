import sys
import subprocess
import re
import os

class CFG:
    def __init__(self, cfg_str):
        self.cfg = {}
        function = ""
        block = ""
        for line in cfg_str.splitlines():
            line = line.strip() #removes whitespace on either end of line
            if len(line) == 0:
                continue
            if bool(re.match("\[", line)):
                block = re.search("\d+", line)[0]
                self.cfg[function][block] = {}
            elif bool(re.match("\d+", line)):
                elements = line.split(":", maxsplit=1)
                self.cfg[function][block][elements[0]] = elements[1].strip()
            elif bool(re.match("T", line)):
                elements = line.split(":", maxsplit=1)
                self.cfg[function][block]["T"] = elements[1].strip()
            elif bool(re.match("Preds", line)):
                elements = line.split(":", maxsplit=1)
                self.cfg[function][block]["Preds"] = re.findall("\d+", elements[1]);
            elif bool(re.match("Succs", line)):
                elements = line.split(":", maxsplit=1)
                self.cfg[function][block]["Succs"] = re.findall("\d+", elements[1]);
            else:
                function = line
                self.cfg[function] = {}

    def add_dominance_edges(self, dom_str):
        #store dominance edges in data structure
        function_iter = iter(self.cfg.keys())
        for line in dom_str.splitlines():
            if not line.startswith("("):
                function = next(function_iter)
                continue
            edge = re.findall("\d+", line)
            self.cfg[function][edge[0]]["Dom"] = edge[1]

    def calculate_back_edges(self):
        #find and store back edges
        for function, blocks in self.cfg.items():
            blocks["Backs"] = {}
            for block, lines in blocks.items():
                if "Succs" in lines:
                    for succ in lines["Succs"]:
                        prev = block
                        dom = blocks[prev]["Dom"]
                        dominated = False
                        while dom != prev:
                            if dom == succ:
                                dominated = True
                            prev = dom
                            dom = blocks[prev]["Dom"]
                        if dominated and succ > block:
                            blocks["Backs"][block] = succ

    def calculate_loops(self):
        #find and store loops in CFG
        for function, blocks in self.cfg.items():
            blocks["Loops"] = []
            for n, d in blocks["Backs"].items():
                loop = [n, d]
                stack = [n]
                while len(stack) != 0:
                    m = stack.pop()
                    if "Preds" not in blocks[m]:
                        continue
                    for pred in blocks[m]["Preds"]:
                        if pred not in loop:
                            loop.append(pred)
                            stack.append(pred)
                blocks["Loops"].append(loop)

    def __str__(self):
        #print data structure
        string = ""
        for function, blocks in self.cfg.items():
            string += (function + "\n")
            for block, lines in blocks.items():
                string += ("\t" + block + "\n")
                if isinstance(lines, list):
                    for item in lines:
                        string += ("\t\t" + ", ".join(item) + "\n")
                elif isinstance(lines, dict):
                    for key, value in lines.items():
                        string += ("\t\t" + key + ":" + str(value) + "\n")
                else:
                    string += ("\t\t" + lines + "\n")
        return string

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

    cfg = CFG(cfg_str)

    #generate dominance tree
    dom_command = "clang -c -Xclang -analyze -Xclang -analyzer-checker=debug.DumpDominators "
    output = subprocess.check_output((dom_command + sys.argv[1]).split(), stderr=subprocess.STDOUT)
    dom_str = output.decode('UTF-8')

    cfg.add_dominance_edges(dom_str)
    cfg.calculate_back_edges()
    cfg.calculate_loops()

    print(cfg)
