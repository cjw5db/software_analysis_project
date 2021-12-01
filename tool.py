import sys
import subprocess
import re
import os

#argv is an arrar of command line inputs
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
cfg = output.decode('UTF-8')

#setup data structure
functions = {}
function = ""
block = ""
for line in cfg.splitlines():
    line = line.strip() #removes whitespace on either end of line
    if len(line) == 0:
        continue
    if bool(re.match("\[", line)):
        block = re.search("\d+", line)[0]
        functions[function][block] = {}
    elif bool(re.match("\d+", line)):
        elements = line.split(":", maxsplit=1)
        functions[function][block][elements[0]] = elements[1].strip()
    elif bool(re.match("T", line)):
        elements = line.split(":", maxsplit=1)
        functions[function][block]["T"] = elements[1].strip()
    elif bool(re.match("Preds", line)):
        elements = line.split(":", maxsplit=1)
        functions[function][block]["Preds"] = re.findall("\d+", elements[1]);
    elif bool(re.match("Succs", line)):
        elements = line.split(":", maxsplit=1)
        functions[function][block]["Succs"] = re.findall("\d+", elements[1]);
    else:
        function = line
        functions[function] = {}

#generate dominance tree
dom_command = "clang -c -Xclang -analyze -Xclang -analyzer-checker=debug.DumpDominators "
output = subprocess.check_output((dom_command + sys.argv[1]).split(), stderr=subprocess.STDOUT)
dom = output.decode('UTF-8')

#store dominance edges in data structure
funcs_iter = iter(functions.keys())
for line in dom.splitlines():
    if not line.startswith("("):
        func = next(funcs_iter)
        continue
    edge = re.findall("\d+", line)
    functions[func][edge[0]]["Dom"] = edge[1]

#find and store back edges
for function, blocks in functions.items():
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

#find and store loops in CFG
for function, blocks in functions.items():
    blocks["Loops"] = []
    for n, d in blocks["Backs"].items():
        loop = [n, d]
        stack = [n]
        while len(stack) != 0:
            print(stack)
            m = stack.pop()
            if "Preds" not in blocks[m]:
                continue
            for pred in blocks[m]["Preds"]:
                if pred not in loop:
                    loop.append(pred)
                    stack.append(pred)
            print(stack)
        blocks["Loops"].append(loop)

#print data structure
for function, blocks in functions.items():
    print(function)
    for block, lines in blocks.items():
        print("\t" + block)
        if isinstance(lines, list):
            for item in lines:
                print("\t\t", end = "")
                print(*item, sep = ", ")
        else:
            for type, data in lines.items():
                print("\t\t" + type + ":" + str(data))

