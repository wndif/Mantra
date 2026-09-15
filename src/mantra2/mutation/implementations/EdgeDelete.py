from ..core import MantraOperator

import pyverilog.vparser.ast as vast
import random
from random import randint

from ..utils import Collector


class EdgeDelete(MantraOperator):
    def __init__(self, ast, old_nodeid=None, new_node=None):
        super().__init__(ast, old_nodeid, new_node)

    def mutate(self):
        self.recursive_mutate(self.ast)
        return self.ast

    def recursive_mutate(self, ast_node):
        flag = False
        if isinstance(ast_node, vast.Always):
            for child in ast_node.children():
                if child.nodeid == self.old_nodeid:
                    flag = True
                    assert (isinstance(child, vast.SensList))
                    # NOTE(Mantra2): upstream read `child.list`; PyVerilog 1.2.1
                    # names this attribute `slist`, so the operator always
                    # raised AttributeError before this fix.
                    new_sens_list = list(child.slist)
                    element_to_remove = random.choice(new_sens_list)
                    new_sens_list.remove(element_to_remove)
                    ast_node.sens_list = vast.SensList(new_sens_list)
                    return ast_node

        if flag:
            return ast_node
        for child in ast_node.children():
            if child is not None:
                self.recursive_mutate(child)
        return ast_node

