from ..core import MantraOperator

import pyverilog.vparser.ast as vast
import random
from random import randint


class ExprDelete(MantraOperator):
    def __init__(self, ast, old_nodeid=None, new_node=None):
        super().__init__(ast, old_nodeid, new_node)
        self.bin_operator = ['Power', 'Times', 'Divide', 'Mod', 'Plus', 'Minus', 'Sll', 'Srl', 'Sla', 'Sra', 'LessThan',
                             'GreaterThan', 'LessEq', 'GreaterEq', 'Eq', 'NotEq', 'Eql', 'NotEql', 'And', 'Xor', 'Xnor',
                             'Or', 'Land', 'Lor']

        self.unary_operator = ['Uxnor', 'Uxor', 'Unor', 'Uor', 'Unand', 'Unot', 'Ulnot', 'Uminus', 'Uplus']

    def mutate(self):
        self.recursive_mutate(self.ast)
        return self.ast

    def recursive_mutate(self, ast_node):
        if ast_node.nodeid == self.old_nodeid:
            new_node = ast_node.right
            if new_node is not None:
                self.replace_with_node(self.ast, ast_node.nodeid, new_node)
        for child in ast_node.children():
            if child is not None:
                self.recursive_mutate(child)
        return ast_node

