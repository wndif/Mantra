import MutationOp, MantraOperators
from pyverilog.vparser.parser import parse, NodeNumbering
import pyverilog.vparser.ast as vast
from pyverilog.ast_code_generator.codegen import ASTCodeGenerator
import sys, inspect, subprocess
import os, random
from optparse import OptionParser
from random import randint
 

def visit_children(ast, node_dict=None):
    if node_dict is None:
        node_dict = {}
    if ast is None:
        return node_dict
    for child in ast.children():
        if child is not None:
            # Save the child's name and id to the dictionary
            node_dict[child.node_id] = child.__class__.__name__
            visit_children(child, node_dict)
    return node_dict


def visit_children_attr(ast):
    for child in ast.children():
        if child is not None:
            # Save the child's name and id to the dictionary
            print(vars(child))
            visit_children_attr(child)

if __name__ == "__main__":
    ast, directives = parse(["test.v"])
    mutationop = MutationOp.MutationOp(None, None, None) 
    mantra_operator = MantraOperators.MantraOperators(None, None, None)
    nodeid_name_dict = visit_children(ast)


    for key,value in nodeid_name_dict.items():
        #get mutation index for DMO
        if value == "Pointer":
            pointer_id = key
        elif value == "Srl":
            srl_id = key
        elif value == "Partselect":
            partselect_id = key
        elif value == "Case":
            case_id = key
        elif value == "IfStatement":
            if_id = key
        elif value == "Assign":
            assignment_id = key
        elif value == "Reg":
            reg_id = key
        elif value == "Wire":
            wire_id = key
        elif value == "Plus":
            plus_id = key
        elif value == "Always":
            always_id = key
        elif value == "DelayStatement":
            delay_id = key

    ast.show()
    new_ast = mantra_operator.DMO(ast, pointer_id, vast.IntConst(randint(1,100)))
    codegen = ASTCodeGenerator()
    src_code = codegen.visit(ast)
    print(src_code)
    