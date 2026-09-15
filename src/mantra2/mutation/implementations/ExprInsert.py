import copy

from ..core import MantraOperator

import pyverilog.vparser.ast as vast
import random
from random import randint

from ..utils import Collector


class ExprInsert(MantraOperator):
    def __init__(self, ast, old_nodeid=None, new_node=None):
        super().__init__(ast, old_nodeid, new_node)
        self.bin_operators = ['Power', 'Times', 'Divide', 'Mod', 'Plus', 'Minus', 'Sll', 'Srl', 'Sla', 'Sra', 'LessThan',
                             'GreaterThan', 'LessEq', 'GreaterEq', 'Eq', 'NotEq', 'Eql', 'NotEql', 'And', 'Xor', 'Xnor',
                             'Or', 'Land', 'Lor']

        self.unary_operators = ['Uxnor', 'Uxor', 'Unor', 'Uor', 'Unand', 'Unot', 'Ulnot', 'Uminus', 'Uplus']

    def mutate(self):
        self.recursive_mutate(self.ast)
        return self.ast

    def recursive_mutate(self, ast_node):
        if ast_node.nodeid == self.old_nodeid:
            cut = Collector(self.ast)
            new_right_node = random.choice(cut.Operator_set)
            new_right_node = copy.deepcopy(new_right_node)
            random_operator = random.choice(self.bin_operators)
            new_node = eval('vast.'+random_operator)(ast_node, new_right_node)

            if new_node is not None:
                self.replace_with_node(self.ast, ast_node.nodeid, new_node)
        for child in ast_node.children():
            if child is not None:
                self.recursive_mutate(child)
        return ast_node

