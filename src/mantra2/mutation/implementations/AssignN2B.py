import copy
import pyverilog.vparser.ast as vast
from ..core import MantraOperator

class AssignN2B(MantraOperator):
    """
    AssignN2B: 灏嗛潪闃诲璧嬪€?(<=) 杞崲涓洪樆濉炶祴鍊?(=)
    """
    def __init__(self, ast, old_nodeid=None, new_node=None):
        super().__init__(ast, old_nodeid, new_node)

    def mutate(self):
        self.recursive_mutate(self.ast)
        return self.ast

    def recursive_mutate(self, ast_node):
        if ast_node is None: return None

        if ast_node.nodeid == self.old_nodeid:
            if isinstance(ast_node, vast.NonblockingSubstitution):
                new_stmt = vast.BlockingSubstitution(
                    left=copy.deepcopy(ast_node.left),
                    right=copy.deepcopy(ast_node.right),
                    ldelay=copy.deepcopy(ast_node.ldelay),
                    rdelay=copy.deepcopy(ast_node.rdelay)
                )
                self.replace_with_node(self.ast, self.old_nodeid, new_stmt)
            return ast_node

        for child in ast_node.children():
            if child is not None:
                self.recursive_mutate(child)
        return ast_node
