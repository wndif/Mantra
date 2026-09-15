import copy

from ..core import MantraOperator

import pyverilog.vparser.ast as vast
import random
from random import randint

from ..utils import Collector


class NSubInsert_Case(MantraOperator):
    def __init__(self, ast, old_nodeid=None, new_node=None):
        super().__init__(ast, old_nodeid, new_node)

    def mutate(self):
        self.recursive_mutate(self.ast)
        return self.ast

    def recursive_mutate(self, ast_node):
        flag = False
        if isinstance(ast_node, vast.Case) and ast_node.nodeid == self.old_nodeid:
            flag = True
            original_stmts = []
            child = ast_node.statement
            if isinstance(child, vast.Block):
                original_stmts.append(*ast_node.statement.statements)
            else:
                original_stmts.append(ast_node.statement)

            cut = Collector(self.ast)
            new_stmt = random.choice(cut.NonblockingSubstitution_set)
            original_stmts.append(new_stmt)
            ast_node.statement = vast.Block(statements=original_stmts)

        if flag:
            return ast_node

        for child in ast_node.children():
            if child is not None:
                self.recursive_mutate(child)
        return ast_node

