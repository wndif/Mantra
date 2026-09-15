from ..core import MantraOperator

import pyverilog.vparser.ast as vast
import random
from random import randint


class PointerUpdate(MantraOperator):
    def __init__(self, ast, old_nodeid=None, new_node=None):
        super().__init__(ast, old_nodeid, new_node)
        self.pattern = ['pointer', 'IntConst']

        self.new_node = vast.IntConst(randint(1, 32))

    def mutate(self):
        self.recursive_mutate(self.ast)
        return self.ast

    def recursive_mutate(self, ast_node):
        if ast_node.nodeid == self.old_nodeid:
            self.replace_with_node(self.ast, ast_node.nodeid, self.new_node)
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

