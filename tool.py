import sys
import subprocess
import re

#generate control flow graph
command = "clang -c -Xclang -analyze -Xclang -analyzer-checker=debug.DumpCFG "
output = subprocess.check_output((command + sys.argv[1]).split(), stderr=subprocess.STDOUT)
cfg = output.decode('UTF-8')


#setup data structure
functions = {}
function = ""
block = ""
for line in cfg.splitlines():
    line = line.strip()
    if len(line) == 0:
        continue
    if bool(re.match("\[", line)):
        block = re.search("B\d+", line)[0]
        functions[function][block] = {}
    elif bool(re.match("\d+", line)):
        elements = line.split(":", maxsplit=1)
        functions[function][block][elements[0]] = elements[1].strip()
    elif bool(re.match("T", line)):
        elements = line.split(":", maxsplit=1)
        functions[function][block]["T"] = elements[1].strip()
    elif bool(re.match("Preds", line)):
        functions[function][block]["Preds"] = re.findall("B\d", line);
    elif bool(re.match("Succs", line)):
        functions[function][block]["Succs"] = re.findall("B\d", line);
    else:
        function = line
        functions[function] = {}


#print data structure
for function in functions:
    print(function)
    for block in functions[function]:
        print("\t" + block)
        for statement in functions[function][block]:
            print("\t\t" + statement + ":" + str(functions[function][block][statement]))

