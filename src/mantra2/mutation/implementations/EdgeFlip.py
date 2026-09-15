from ..core import MantraOperator

import pyverilog.vparser.ast as vast
import random
from random import randint
class EdgeFlip(MantraOperator):
    def __init__(self, ast, old_nodeid=None, new_node=None):
        super().__init__(ast, old_nodeid, new_node)

    def mutate(self):
        self.recursive_mutate(self.ast)
        return self.ast

    def recursive_mutate(self, ast_node):
        if ast_node.nodeid == self.old_nodeid:
            if ast_node.type == 'posedge':
                ast_node.type = 'negedge'
            else:
                ast_node.type = 'posedge'
            # And -> Or
            new_node = None
            # if isinstance(ast_node, vast.Always):
            #     ast_node.sens_list = []

            # if isinstance(ast_node, vast.Input):
            #     new_node = vast.Output(ast_node.name)
            # TODO: add more mutation operators
            # else:
            #     # print(f'No node is matched in {self.__class__}')
            #     raise NotImplementedError(f'No node is matched in {self.__class__}')
            # if new_node is not None:
            #     self.replace_with_node(self.ast, ast_node.nodeid, new_node)
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

