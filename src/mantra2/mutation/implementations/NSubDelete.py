import copy

from ..core import MantraOperator

import pyverilog.vparser.ast as vast
import random
from random import randint


class NSubDelete(MantraOperator):
    def __init__(self, ast, old_nodeid=None, new_node=None):
        super().__init__(ast, old_nodeid, new_node)

    def mutate(self):
        self.recursive_mutate(self.ast)
        return self.ast

    def recursive_mutate(self, ast_node):
        if ast_node.nodeid == self.old_nodeid:
            assert (isinstance(ast_node, vast.NonblockingSubstitution))
            new_node = vast.Block([])
            if new_node is not None:
                self.replace_with_node(self.ast, self.old_nodeid, new_node)
            return ast_node

        for child in ast_node.children():
            if child is not None:
                self.recursive_mutate(child)
        return ast_node

