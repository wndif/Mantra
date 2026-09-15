from ..core import MantraOperator

import pyverilog.vparser.ast as vast
import random
from random import randint


class ExprUpdate(MantraOperator):
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
            new_node = None
            if ast_node.__class__.__name__ in self.bin_operator: # binary operator
                new_operator = random.choice([x for x in self.bin_operator if x != ast_node.__class__.__name__])
                new_node = eval('vast.' + new_operator)(ast_node.left, ast_node.right)
            elif ast_node.__class__.__name__ in self.unary_operator: # unary operator
                new_operator = random.choice([x for x in self.unary_operator if x != ast_node.__class__.__name__])
                new_node = eval('vast.' + new_operator)(ast_node.right)

            else:
                # print(f'No node is matched in {self.__class__}')
                raise NotImplementedError(f'No node is matched in {self.__class__}')
            if new_node is not None:
                self.replace_with_node(self.ast, ast_node.nodeid, new_node)
        for child in ast_node.children():
            if child is not None:
                self.recursive_mutate(child)
        return ast_node

