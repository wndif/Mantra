import copy

from ..core import MantraOperator

import pyverilog.vparser.ast as vast
import random
from random import randint

from ..utils import Collector


class NSubInsert(MantraOperator):
    def __init__(self, ast, old_nodeid=None, new_node=None):
        super().__init__(ast, old_nodeid, new_node)

    def mutate(self):
        self.recursive_mutate(self.ast)
        return self.ast

    def recursive_mutate(self, ast_node):
        if isinstance(ast_node, vast.Block) and ast_node.nodeid == self.old_nodeid:
            try:
                cut = Collector(self.ast)
                new_stmt = random.choice(cut.NonblockingSubstitution_set)
                ast_node.statements = tuple(list(ast_node.statements) + [new_stmt])
            except IndexError:
                print(f'IndexError in NSubInsert.recursive_mutate')
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

