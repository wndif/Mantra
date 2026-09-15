import copy

from ..core import MantraOperator

import pyverilog.vparser.ast as vast
import random
from random import randint


class PartselectInsert(MantraOperator):
    def __init__(self, ast, old_nodeid=None, new_node=None):
        super().__init__(ast, old_nodeid, new_node)

    def mutate(self):
        self.recursive_mutate(self.ast)
        return self.ast

    def recursive_mutate(self, ast_node):
        if ast_node.nodeid == self.old_nodeid:
            assert (isinstance(ast_node, vast.Identifier))
            # new_right = ast_node.right.
            # var = ast_node.right
            new_var = copy.deepcopy(ast_node)
            rand_a = randint(1, 32)
            rand_b = randint(1, 32)
            rand_1 = min(rand_a, rand_b)
            rand_2 = max(rand_a, rand_b)
            new_ptr1 = vast.IntConst(rand_1)
            new_ptr2 = vast.IntConst(rand_2)

            new_partselect = vast.Partselect(new_var, new_ptr1, new_ptr2)
            self.replace_with_node(self.ast, ast_node.nodeid, new_partselect)
            return ast_node
        for child in ast_node.children():
            if child is not None:
                self.recursive_mutate(child)
        return ast_node

    # def recursive_mutate(self, ast_node):
    #     if ast_node == self.old_nodeid:
    #         for child in ast_node.children():
    #             if child.__class__.__name__ == "IntConst":
    #                 self.mutationop.replace_with_node(self.ast, child.nodeid, self.new_node)
    #     for child in ast_node.children():
    #         if child is not None:
    #             self.recursive_mutate(child)
    #     return ast_node

