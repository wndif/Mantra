import copy

from ..core import MantraOperator

import pyverilog.vparser.ast as vast
import random
from random import randint

from ..utils import Collector


class NSubMove(MantraOperator):
    def __init__(self, ast, old_nodeid=None, new_node=None):
        super().__init__(ast, old_nodeid, new_node)

    def mutate(self):
        self.recursive_mutate(self.ast)
        return self.ast

    def recursive_mutate(self, ast_node):
        flag = False
        if isinstance(ast_node, vast.IfStatement) and ast_node.nodeid == self.old_nodeid:
            flag = True
            true_statement = copy.deepcopy(ast_node.true_statement)
            false_statement = copy.deepcopy(ast_node.false_statement)
            # print(vars(true_statement))
            # print(vars(false_statement))
            direction = random.randint(0,1)
            if false_statement is None: # 鍋囧畾true_statement涓€瀹氶潪绌?
                direction = 1

            if direction == 1:
                if isinstance(true_statement, vast.Block):
                    statements = true_statement.statements
                    if len(statements) <= 0:
                        raise Exception(" Can not select a statement from empty Block")
                    elem = random.choice(statements)
                    new_true_statement = (list(true_statement.statements))
                    new_true_statement.remove(elem)
                    ast_node.true_statement = vast.Block(new_true_statement)
                    if isinstance(false_statement, vast.Block):
                        new_false_statement = vast.Block([*false_statement.statements, elem])
                    else:
                        if false_statement is not None:
                            new_false_statement = vast.Block([false_statement, elem])
                        else:
                            new_false_statement = vast.Block([elem])
                    ast_node.false_statement = new_false_statement
                else:
                    new_true_statement = []
                    ast_node.true_statement = vast.Block(new_true_statement)
                    if isinstance(false_statement, vast.Block):
                        new_false_statement = vast.Block([*false_statement.statements, true_statement])
                    else:
                        if false_statement is not None:
                            new_false_statement = vast.Block([false_statement, true_statement])
                        else:
                            new_false_statement = vast.Block([true_statement])
                    ast_node.false_statement = new_false_statement
            else:
                if isinstance(false_statement, vast.Block):
                    statements = false_statement.statements
                    if len(statements) <= 0:
                        raise Exception(" Can not select a statement from empty Block")
                    elem = random.choice(statements)
                    new_false_statement = (list(false_statement.statements))
                    new_false_statement.remove(elem)
                    ast_node.false_statement = vast.Block(new_false_statement)
                    if isinstance(true_statement, vast.Block):
                        new_true_statement = vast.Block([*true_statement.statements, elem])
                    else:
                        if true_statement is not None:
                            new_true_statement = vast.Block([true_statement, elem])
                        else:
                            new_true_statement = vast.Block([elem])
                    ast_node.true_statement = new_true_statement
                else:
                    new_false_statement = []
                    ast_node.false_statement = vast.Block(new_false_statement)
                    if isinstance(true_statement, vast.Block):
                        new_true_statement = vast.Block([*true_statement.statements, false_statement])
                    else:
                        if true_statement is not None:
                            new_true_statement = vast.Block([true_statement, false_statement])
                        else:
                            new_true_statement = vast.Block([false_statement])
                    ast_node.true_statement = new_true_statement
            return ast_node

        if flag:
            return ast_node

        for child in ast_node.children():
            if child is not None:
                self.recursive_mutate(child)
        return ast_node


