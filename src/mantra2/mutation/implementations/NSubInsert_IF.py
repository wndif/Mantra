import copy

from ..core import MantraOperator

import pyverilog.vparser.ast as vast
import random
from random import randint

from ..utils import Collector


class NSubInsert_IF(MantraOperator):
    def __init__(self, ast, old_nodeid=None, new_node=None):
        super().__init__(ast, old_nodeid, new_node)

    def mutate(self):
        self.recursive_mutate(self.ast)
        return self.ast

    def recursive_mutate(self, ast_node):
        flag = False
        if isinstance(ast_node, vast.IfStatement) and ast_node.nodeid == self.old_nodeid:
            flag = True
            original_stmts = []
            statement_selected = random.choice(['true_statement', 'false_statement'])
            child = eval('ast_node.' + statement_selected)
            if isinstance(child, vast.Block):
                original_stmts = original_stmts + list(child.statements)
            else:
                original_stmts.append(child)

            cut = Collector(self.ast)
            new_stmt = random.choice(cut.NonblockingSubstitution_set)
            original_stmts.append(new_stmt)
            if statement_selected == 'true_statement':
                ast_node.true_statement = vast.Block(statements=original_stmts)
            else:
                ast_node.false_statement = vast.Block(statements=original_stmts)


        if flag:
            return ast_node

        for child in ast_node.children():
            if child is not None:
                self.recursive_mutate(child)
        return ast_node

