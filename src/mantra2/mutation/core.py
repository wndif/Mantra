"""Base class for mutation operators.

The ``MantraOperator`` this class is derived from carried twenty additional
mutation methods (DMO/DMS/CGA/TMD/SRA/...).  They are unreachable from Mantra2,
so only the constructor contract and the ``mutate`` hook remain.
"""

from __future__ import annotations

from .base import MutationOp


class MantraOperator(MutationOp):
    """Contract implemented by every mutation schema.

    Subclasses receive the parsed AST and the id of the node selected by the
    mutation-point pattern, and return the mutated AST from ``mutate``.
    """

    def __init__(self, ast, old_nodeid=None, new_node=None):
        super().__init__(ast, old_nodeid, new_node)

    def mutate(self):
        raise NotImplementedError
