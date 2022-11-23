import sys, inspect, subprocess
import os
from optparse import OptionParser
import copy
import random
import time 
from datetime import datetime
import math
# genprog: Class Rep: you need to write your own class 
# the next line can be removed after installation
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pyverilog.vparser.parser import parse, NodeNumbering
from pyverilog.ast_code_generator.codegen import ASTCodeGenerator
from pyverilog.vparser.plyparser import ParseError
import pyverilog.vparser.ast as vast

import fitness

AST_CLASSES = []

for name, obj in inspect.getmembers(vast):
    if inspect.isclass(obj):
        AST_CLASSES.append(obj)

# print(AST_CLASSES)
# f = open("ast_classes.txt", "w+")
# for item in AST_CLASSES:
#     f.write(str(item) + "\n")
# f.close()

REPLACE_TARGETS = {} # dict from class to list of classes that are okay to substituite for the original class
for i in range(len(AST_CLASSES)):
    REPLACE_TARGETS[AST_CLASSES[i]] = []
    REPLACE_TARGETS[AST_CLASSES[i]].append(AST_CLASSES[i]) # can always replace with a node of the same type
    for j in range(len(AST_CLASSES)):
        # get the immediate parent classes of both classes, and if the parent if not Node, the two classes can be swapped
        if i != j and inspect.getmro(AST_CLASSES[i])[1] == inspect.getmro(AST_CLASSES[j])[1] and inspect.getmro(AST_CLASSES[j])[1] != vast.Node:
            REPLACE_TARGETS[AST_CLASSES[i]].append(AST_CLASSES[j])
       
# for key in REPLACE_TARGETS:
#     tmp = map(lambda x: x.__name__, REPLACE_TARGETS[key]) 
#     print("Class %s can be replaced by the following: %s" % (key.__name__, list(tmp)))
#     print()

"""
Valid targets for the delete and insert operators.
"""
DELETE_TARGETS = ["IfStatement", "NonblockingSubstitution", "BlockingSubstitution", "ForStatement", "Always", "Case", "CaseStatement", "DelayStatement", "Localparam", "Assign", "Block"]
INSERT_TARGETS = ["IfStatement", "NonblockingSubstitution", "BlockingSubstitution", "ForStatement", "Always", "Case", "CaseStatement", "DelayStatement", "Localparam", "Assign"]

TEMPLATE_MUTATIONS = { "increment_by_one": ("Identifier", "Plus"), "decrement_by_one": ("Identifier", "Minus"), 
                        "negate_equality": ("Eq", "NotEq"), "negate_inequality": ("NotEq", "Eq"), "negate_ulnot": ("Ulnot", "Ulnot"),
                        "sens_to_negedge": ("Sens", "Sens"), "sens_to_posedge": ("Sens", "Sens"), "sens_to_level": ("Sens", "Sens"), "sens_to_all": ("Sens", "Sens"),
                        "blocking_to_nonblocking": ("BlockingSubstitution", "NonblockingSubstitution"), "nonblocking_to_blocking": ("NonblockingSubstitution", "BlockingSubstitution")}
                        # "sll_to_sla": ("Sll", "Sla"), "sla_to_sll": ("Sla", "Sll"), 
                        # "srl_to_sra": ("Srl", "Sra"), "sra_to_srl": ("Sra", "Srl")}
                        # TODO: stmt to stmt in a block?
                        # TODO: empty if then somewhere? with like a random identifier for cond?
                        # TODO: use only registers for inc and dec by one?

WRITE_TO_FILE = True

GENOME_FITNESS_CACHE = {}

FITNESS_EVAL_TIMES = []

SEED = "None"
SRC_FILE = None
TEST_BENCH = None
PROJ_DIR = None
EVAL_SCRIPT = None
ORIG_FILE = ""
ORACLE = None
GENS = 5
POPSIZE = 200
RESTARTS = 1
FAULT_LOC = True
CONTROL_FLOW = True
LIMIT_TRANSITIVE_DEPENDENCY_SET = False
# TODO: Update defaults!
DEPENDENCY_SET_MAX = 5
REPLACEMENT_RATE = 1/3
DELETION_RATE = 1/3
INSERTION_RATE = 1/3
MUTATION_RATE = 1/2
CROSSOVER_RATE = 1/2
FITNESS_MODE = "outputwires"

TIME_NOW = datetime.today().strftime('%Y-%m-%d-%H:%M:%S')

config_file = open("repair.conf", "r")
configs = config_file.readlines()
for c in configs:
    if c != "\n" and not c.startswith("#"):
        c = c.strip().split("=")
        param, val = c[0].lower(), c[1]
        if param == "seed":
            SEED = val
            print("Using SEED = %s" % SEED)
        elif param == "src_file":
            SRC_FILE = val
            print("Using SRC_FILE = %s" % SRC_FILE)
        elif param == "test_bench":
            TEST_BENCH = val
            print("Using TEST_BENCH = %s" % TEST_BENCH)
        elif param == "eval_script":
            EVAL_SCRIPT = val
            print("Using EVAL_SCRIPT = %s" % EVAL_SCRIPT)
        elif param == "orig_file":
            ORIG_FILE = val
            print("Using ORIG_FILE = %s" % ORIG_FILE)
        elif param == "proj_dir":
            PROJ_DIR = val
            print("Using PROJ_DIR = %s" % PROJ_DIR)
        elif param == "fitness_mode":
            FITNESS_MODE = val
            print("Using FITNESS_MODE = %s" % FITNESS_MODE)
        elif param == "oracle":
            ORACLE = val
            print("Using ORACLE = %s" % ORACLE)
        elif param == "gens":
            GENS = int(val)
            print("Using GENS = %d" % GENS)
        elif param == "popsize":
            POPSIZE = int(val)
            print("Using POPSIZE = %d" % POPSIZE)
        elif param == "mutation_rate":
            MUTATION_RATE = float(val)
            print("Using MUTATION_RATE = %f" % MUTATION_RATE)
        elif param == "crossover_rate":
            CROSSOVER_RATE = float(val)
            print("Using CROSSOVER_RATE = %f" % CROSSOVER_RATE)
        elif param == "deletion_rate":
            DELETION_RATE = float(val)
            print("Using DELETION_RATE = %f" % DELETION_RATE)
        elif param == "insertion_rate":
            INSERTION_RATE = float(val)
            print("Using INSERTION_RATE = %f" % INSERTION_RATE)
        elif param == "replacement_rate":
            REPLACEMENT_RATE = float(val)
            print("Using REPLACEMENT_RATE = %f" % REPLACEMENT_RATE)
        elif param == "restarts":
            RESTARTS = int(val)
            print("Using RESTARTS = %d" % RESTARTS)
        elif param == "fault_loc":          
            if val.lower() == "true": FAULT_LOC = True
            if val.lower() == "false": FAULT_LOC = False
            print("Using FAULT_LOC = %s" % FAULT_LOC) 
        elif param == "control_flow":          
            if val.lower() == "true": CONTROL_FLOW = True
            if val.lower() == "false": CONTROL_FLOW = False
            print("Using CONTROL_FLOW = %s" % CONTROL_FLOW) 
        elif param == "limit_transitive_dependency_set":          
            if val.lower() == "true": LIMIT_TRANSITIVE_DEPENDENCY_SET = True
            if val.lower() == "false": LIMIT_TRANSITIVE_DEPENDENCY_SET = False
            print("Using LIMIT_TRANSITIVE_DEPENDENCY_SET = %s" % LIMIT_TRANSITIVE_DEPENDENCY_SET) 
        elif param == "dependency_set_max":
            DEPENDENCY_SET_MAX = int(val)
            print("Using DEPENDENCY_SET_MAX = %d" % DEPENDENCY_SET_MAX)
        else:
            print("ERROR: Invalid parameter: %s" % param)
            exit(1)
config_file.close()

TB_ID = TEST_BENCH.split("/")[-1].replace(".v","")



if SEED == "None":
    SEED = "repair_%s" % TIME_NOW

SEED_CTR = 0
def inc_seed():
    global SEED_CTR
    SEED_CTR += 1
    return SEED + str(SEED_CTR)


def main():
    start_time = time.time()

    INFO = "Verilog code parser"
    USAGE = "Usage: python example_parser.py file ..."

    def showVersion():
        print(INFO)
        print(USAGE)
        sys.exit()

    optparser = OptionParser()
    optparser.add_option("-v","--version",action="store_true",dest="showversion",
                         default=False,help="Show the version")
    optparser.add_option("-I","--include",dest="include",action="append",
                         default=[],help="Include path")
    optparser.add_option("-D",dest="define",action="append",
                         default=[],help="Macro Definition")
    (options, args) = optparser.parse_args()

    filelist = [SRC_FILE, TEST_BENCH]

    if options.showversion:
        showVersion()

    for f in filelist:
        if not os.path.exists(f): raise IOError("file not found: " + f)

    if len(filelist) == 0:
        showVersion()

    LOG = False
    CODE_FROM_PATCHLIST = False
    MINIMIZE_ONLY = False

    for i in range(1, len(sys.argv)):
        cmd = sys.argv[i]
        if "log" in cmd.lower():
            val = cmd.split("=")[1]
            if val.lower() == "true": LOG = True
            elif val.lower() == "false": LOG = False
            print("Using LOG = %s" % LOG)
        elif "code_from_patchlist" in cmd.lower():
            val = cmd.split("=")[1]
            if val.lower() == "true": CODE_FROM_PATCHLIST = True
            elif val.lower() == "false": CODE_FROM_PATCHLIST = False
            print("Using CODE_FROM_PATCHLIST = %s" % CODE_FROM_PATCHLIST)
        elif "minimize" in cmd.lower():
            val = cmd.split("=")[1]
            if val.lower() == "true": MINIMIZE_ONLY = True
            elif val.lower() == "false": MINIMIZE_ONLY = False
            print("Using MINIMIZE_ONLY = %s" % MINIMIZE_ONLY)
        else:
            print("Invalid command line argument: %s. Aborting." % cmd)

    codegen = ASTCodeGenerator()
    # parse the files (in filelist) to ASTs (PyVerilog ast)

    ast, directives = parse([SRC_FILE],
                            preprocess_include=PROJ_DIR.split(","),
                            preprocess_define=options.define)

    ast.show()
    src_code = codegen.visit(ast)
    print(src_code)

    print("\n\n")

    patch_list = ['replace(61, 70)']
    print("===========================================================================")

    intconst_nodeid_list = []

    def my_traverse(cur_node):
        if cur_node == None:
            return
        node_type = type(cur_node)
        if isinstance(cur_node, vast.IntConst):
            print(node_type)
            attr = vars(cur_node)
            intconst_nodeid_list.append(attr['node_id'])
            print(attr)
        for c in cur_node.children():
            my_traverse(c)

    my_traverse(ast)

    print(intconst_nodeid_list)

    target_node_id = intconst_nodeid_list[1]

    new_int_const = "4'b1001"

    def my_mutation(cur_node, target_node_id, new_int_const):
        if cur_node == None:
            return
   
        if isinstance(cur_node, vast.IntConst):
            attr = vars(cur_node)
            print('node_id = ', attr['node_id'], ', targetid = ', target_node_id)
            if attr['node_id'] == target_node_id:
                attr['value'] = new_int_const
                print('*********************')
                return

        for c in cur_node.children():
            my_mutation(c, target_node_id, new_int_const)
    my_mutation(ast, target_node_id, new_int_const)
    my_traverse(ast)
    src_code = codegen.visit(ast)
    print(src_code)
    numbering = NodeNumbering()
    numbering.renumber(ast)
    max_node_id = numbering.c
    print(max_node_id)



if __name__ == '__main__':
    main()
