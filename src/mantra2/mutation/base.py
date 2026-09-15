"""AST rewriting primitives shared by all mutation operators.

Only the four primitives actually exercised by the bundled mutation schemas are
retained: ``replace_with_node``, ``delete_node``,
``insert_stmt_node`` and ``get_node_from_ast``.  The population-based
delete/insert/replace operators and the fault-localisation bookkeeping that came
along with the inherited code are never reached by Mantra2 and were dropped.
"""

from __future__ import annotations

import copy
import inspect

import pyverilog.vparser.ast as vast

AST_CLASSES = [
    obj for _name, obj in inspect.getmembers(vast) if inspect.isclass(obj)
]

"""Node classes that may be removed without breaking the AST."""
DELETE_TARGETS = [
    "IfStatement",
    "NonblockingSubstitution",
    "BlockingSubstitution",
    "ForStatement",
    "Always",
    "Case",
    "CaseStatement",
    "DelayStatement",
    "Localparam",
    "Assign",
    "Block",
    "Reg",
    "Wire",
]

"""Node classes that may be inserted into a ``begin ... end`` block."""
INSERT_TARGETS = [
    "IfStatement",
    "NonblockingSubstitution",
    "BlockingSubstitution",
    "ForStatement",
    "Always",
    "Case",
    "CaseStatement",
    "DelayStatement",
    "Localparam",
    "Assign",
]


class MutationOp:
    """Base class providing AST surgery helpers to mutation operators."""

    def __init__(self, ast, old_nodeid=None, new_node=None):
        self.ast = ast
        self.old_nodeid = old_nodeid
        self.new_node = new_node

    def replace_with_node(self, ast, old_nodeid, new_node):
        """Replace the node identified by ``old_nodeid`` with ``new_node``."""
        attr = vars(ast)
        for key in attr:
            if attr[key].__class__ in AST_CLASSES:
                if attr[key].nodeid == old_nodeid:
                    attr[key] = copy.deepcopy(new_node)
                    return
            elif attr[key].__class__ in [list]:
                for i in range(len(attr[key])):
                    tmp = attr[key][i]
                    if tmp.__class__ in AST_CLASSES and tmp.nodeid == old_nodeid:
                        attr[key][i] = copy.deepcopy(new_node)
                        return
            elif attr[key].__class__ in [tuple]:
                tmp_attr_key = list(attr[key])
                for i in range(len(tmp_attr_key)):
                    tmp = tmp_attr_key[i]
                    if tmp.__class__ in AST_CLASSES and tmp.nodeid == old_nodeid:
                        tmp_attr_key[i] = copy.deepcopy(new_node)
                        break
                attr[key] = tuple(tmp_attr_key)

        for c in ast.children():
            if c:
                self.replace_with_node(c, old_nodeid, new_node)

    def delete_node(self, ast, nodeid):
        """Drop the node identified by ``nodeid`` when its class is deletable."""
        attr = vars(ast)
        for key in attr:
            if attr[key].__class__ in AST_CLASSES:
                if (
                    attr[key].nodeid == nodeid
                    and attr[key].__class__.__name__ in DELETE_TARGETS
                ):
                    attr[key] = None
            elif attr[key].__class__ in [list, tuple]:
                for i in range(len(attr[key])):
                    tmp = attr[key][i]
                    if (
                        tmp.__class__ in AST_CLASSES
                        and tmp.nodeid == nodeid
                        and tmp.__class__.__name__ in DELETE_TARGETS
                    ):
                        attr[key][i] = None

        for c in ast.children():
            if c:
                self.delete_node(c, nodeid)

    def insert_stmt_node(self, ast, node, after_id):
        """Insert ``node`` into a ``Block``, immediately after ``after_id``."""
        if ast.__class__.__name__ == "Block":
            if after_id == ast.nodeid:
                ast.statements.insert(0, copy.deepcopy(node))
                return
            insert_point = -1
            for i in range(len(ast.statements)):
                stmt = ast.statements[i]
                if stmt and stmt.nodeid == after_id:
                    insert_point = i + 1
                    break
            if insert_point != -1:
                ast.statements.insert(insert_point, copy.deepcopy(node))
                return

        for c in ast.children():
            if c:
                self.insert_stmt_node(c, node, after_id)

    def get_node_from_ast(self, ast, nodeid):
        """Store the node identified by ``nodeid`` in ``self.tmp_node``."""
        if ast.nodeid == nodeid:
            self.tmp_node = ast

        for c in ast.children():
            if c:
                self.get_node_from_ast(c, nodeid)
