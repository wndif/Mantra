import random

import pyverilog.vparser.ast as vast


class Collector:
    COLLECTION_NAME = [
        "Assign",
        "NonblockingSubstitution",
        "BlockingSubstitution",
        'Identifier',
        'Operator'
    ]

    def __init__(self, ast_node):
        pass
        for node in Collector.COLLECTION_NAME:
            setattr(self, f'{node}_set', [])

        self.collect(ast_node)

        # for node in Collector.COLLECTION_NAME:
        #     obj = getattr(self, f'{node}_set')
        #     setattr(self, f'random_{node}', lambda: random.choice(obj))

    def collect(self, ast_node: vast.Node):
        for child in ast_node.children():
            self.generic_visit(child)
            self.collect(child)

    def generic_visit(self, ast_node: vast.Node):
        for node_name in Collector.COLLECTION_NAME:
            if isinstance(ast_node, eval('vast.' + node_name)):
                obj = getattr(self, f'{node_name}_set')
                obj.append(ast_node)
