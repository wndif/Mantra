import MutationOp
import copy
import pyverilog.vparser.ast as vast
import random
from random import randint
 
class MantraOperators(MutationOp.MutationOp):
    def __init__(self, name, symbol, function):
        self.name = name
        self.symbol = symbol
        self.function = function
        self.mutationop = MutationOp.MutationOp(None, None, None)

    ######Data Mis-Access######
    def DMO(self, ast, pointer_id, new_IntConst_node):
        if ast.node_id == pointer_id:
            for child in ast.children():
                if child.__class__.__name__ == "IntConst":
                    self.mutationop.replace_with_node(ast, child.node_id, new_IntConst_node)
        for child in ast.children():
            if child is not None:
                self.DMO(child, pointer_id, new_IntConst_node)
        return ast

    def DMS(self, ast, srl_id, new_IntConst_node):
        if ast.node_id == srl_id:
            for child in ast.children():
                if child.__class__.__name__ == "IntConst":
                    self.mutationop.replace_with_node(ast, child.node_id, new_IntConst_node)
        for child in ast.children():
            if child is not None:
                self.DMO(child, srl_id, new_IntConst_node)
        return ast
    
    def DMI(self, ast, partselect_id):
        if ast.node_id == partselect_id:
            for child in ast.children():
                if child.__class__.__name__ == "IntConst":
                    self.mutationop.replace_with_node(ast, child.node_id, vast.IntConst(int(child.value) - 1))
        for child in ast.children():
            if child is not None:
                self.DMI(child, partselect_id)
        return ast
    
    def get_dcl_width(self, ast):
        for child in ast.children():
            if child.__class__.__name__ == "Decl":
                for next_child in child.children():
                    if next_child.__class__.__name__ == "Width":
                        for next_next_child in next_child.children():
                            if next_next_child.__class__.__name__ == "IntConst":
                                return next_next_child.value
            else:
                self.get_dcl_id(child)
        pass
    
    def DIE(self, ast, partselect_id):
        if ast.node_id == partselect_id:
            for child in ast.children():
                if child.__class__.__name__ == "IntConst":
                    self.mutationop.replace_with_node(ast, child.node_id, self.get_dcl_width - vast.IntConst(int(child.value)))
        for child in ast.children():
            if child is not None:
                self.DIE(child, partselect_id)
        return ast


    ######Communication######
    def CMA(self, ast, function_id):
        if ast.node_id == function_id:
            for child in ast.children():
                if child.__class__.__name__ == "ParamArg":
                    for next_child in child.children():
                        if next_child.__class__.__name__ == "IntConst":
                            new_node_value = randint(1,100)
                            self.mutationop.replace_with_node(ast, next_child.node_id, vast.IntConst(new_node_value))
        for child in ast.children():
            if child is not None:
                self.CMP(child, function_id)
        return ast


    def CGA(self, ast, block_id):
        if ast.node_id == block_id:
            for child in ast.children():
                if child.__class__.__name__ == "NonblockingSubstitution" or child.__class__.__name__ == "BlockingSubstitution":
                    new_node = copy.deepcopy(child)
                    for new_ndoe_child in new_node.children():
                        if new_ndoe_child.__class__.__name__ == "Rvalue":
                            for next_new_node_child in new_ndoe_child.children():
                                if next_new_node_child.__class__.__name__ == "IntConst":
                                    next_new_node_child.value = randint(1,100)
                                    self.mutationop.insert_stmt_node(ast, new_node, block_id)
        for child in ast.children():
            if child is not None:
                self.CGA(child, block_id)
        return ast
    
    def CRV(self, ast, if_id):
        if ast.node_id == if_id:
            for child in ast.children():
                if child.__class__.__name__ == "Identifier" and "valid" in child.name:
                    self.mutationop.replace_with_node(ast, child.node_id, vast.IntConst(1))
        for child in ast.children():
            if child is not None:
                self.CRV(child, if_id)
        return ast
    
    def CMP(self, ast, instance_id):
        if ast.node_id == instance_id:
            for child in ast.children():
                if child.__class__.__name__ == "ParamArg":
                    for next_child in child.children():
                        if next_child.__class__.__name__ == "IntConst":
                            new_node_value = randint(1,100)
                            self.mutationop.replace_with_node(ast, next_child.node_id, vast.IntConst(new_node_value))
        for child in ast.children():
            if child is not None:
                self.CMP(child, instance_id)
        return ast

        
    def CDP(self, ast, instance_id):
        if ast.node_id == instance_id:
            for child in ast.children():
                if child.__class__.__name__ == "PortArg":
                    self.mutationop.replace_with_node(ast, child.node_id, None)
        for child in ast.children():
            if child is not None:
                self.CDP(child, instance_id)
        return ast
    ######Timing######
    def TAA(self, ast, block_id):
        if ast.node_id == block_id:
            for child in ast.children():
                if child.__class__.__name__ == "NonblockingSubstitution" or child.__class__.__name__ == "BlockingSubstitution":
                    new_node = copy.deepcopy(child)
                    for new_ndoe_child in new_node.children():
                        if new_ndoe_child.__class__.__name__ == "Rvalue":
                            for next_new_node_child in new_ndoe_child.children():
                                if next_new_node_child.__class__.__name__ == "Identifier":
                                    # next_new_node_child.value = randint(1,100)
                                    self.mutationop.insert_stmt_node(ast, new_node, block_id)
        for child in ast.children():
            if child is not None:
                self.TAA(child, block_id)
        return ast

    def TMD(self, ast, delay_id):
        if ast.node_id == delay_id:
            for child in ast.children():
                if child.__class__.__name__ == "IntConst":
                    new_node = copy.deepcopy(child)
                    new_node.value = randint(1,100)
                    self.mutationop.replace_with_node(ast, child.node_id, new_node)
        for child in ast.children():
            if child is not None:
                self.TMD(child, delay_id)
        return ast


    def TRA(self, ast, always_id):
        self.mutationop.delete_node(ast, always_id)
        return ast
    

    ######Semantic######
    def SRC(self, ast, case_id):
        self.mutationop.delete_node(ast, case_id)
        return ast
    
   
    def SRI(self, ast, if_id):
        self.mutationop.delete_node(ast, if_id)
        return ast
    
    ###SRE is same with SRI
    def SRE(self, ast, else_id):
        pass
    
    def SME_operator(self, ast, block_id, replace_node_id):
        if ast.node_id == block_id:
            for child in ast.children():
                if child.__class__.__name__ == "NonblockingSubstitution" or child.__class__.__name__ == "BlockingSubstitution":
                    for new_ndoe_child in child.children():
                        if new_ndoe_child.__class__.__name__ == "Rvalue":
                            for next_new_node_child in new_ndoe_child.children():
                                if next_new_node_child.__class__.__name__ == "Plus":
                                    replace_node =copy.deepcopy(self.mutationop.get_node_from_ast(ast, replace_node_id))
                                    # print(replace_node.__class__.__name__)
                                    self.mutationop.replace_with_node(next_new_node_child, next_new_node_child.node_id, replace_node)
        for child in ast.children():
            if child is not None:
                self.SME_operator(child, block_id, replace_node_id)
        return ast
        
    def SME_constant(self, ast, block_id):
        if ast.node_id == block_id:
            for child in ast.children():
                if child.__class__.__name__ == "NonblockingSubstitution" or child.__class__.__name__ == "BlockingSubstitution":
                    for new_ndoe_child in child.children():
                        if new_ndoe_child.__class__.__name__ == "Rvalue":
                            for next_new_node_child in new_ndoe_child.children():
                                if next_new_node_child.__class__.__name__ == "IntConst":
                                    next_new_node_child.value = randint(1,100)
        for child in ast.children():
            if child is not None:
                self.SME_constant(child, block_id)
        return ast

    def SRA(self, ast, assignment_id):
        self.mutationop.delete_node(ast, assignment_id)
        return ast

    def SRR(self, ast, reg_id):
        self.mutationop.delete_node(ast, reg_id)
        return ast

    def SRW(self, ast, wire_id):
        self.mutationop.delete_node(ast, wire_id)
        return ast
    
