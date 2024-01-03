import sys, inspect, subprocess
import copy
import random
from pyverilog.vparser.parser import parse, NodeNumbering
from pyverilog.ast_code_generator.codegen import ASTCodeGenerator
import pyverilog.vparser.ast as vast

AST_CLASSES = []

for name, obj in inspect.getmembers(vast):
    if inspect.isclass(obj):
        AST_CLASSES.append(obj)
REPLACE_TARGETS = {} # dict from class to list of classes that are okay to substituite for the original class
for i in range(len(AST_CLASSES)):
    REPLACE_TARGETS[AST_CLASSES[i]] = []
    REPLACE_TARGETS[AST_CLASSES[i]].append(AST_CLASSES[i]) # can always replace with a node of the same type
    for j in range(len(AST_CLASSES)):
        # get the immediate parent classes of both classes, and if the parent if not Node, the two classes can be swapped
        if i != j and inspect.getmro(AST_CLASSES[i])[1] == inspect.getmro(AST_CLASSES[j])[1] and inspect.getmro(AST_CLASSES[j])[1] != vast.Node:
            REPLACE_TARGETS[AST_CLASSES[i]].append(AST_CLASSES[j])
       
# for key in REPLACE_TARGETS:
#     tmp = map(lambda x: x.__name__, REPLACE_TARGETS[key]) 
#     print("Class %s can be replaced by the following: %s" % (key.__name__, list(tmp)))
#     print()

"""
Valid targets for the delete and insert operators.
"""
DELETE_TARGETS = ["IfStatement", "NonblockingSubstitution", "BlockingSubstitution", "ForStatement", "Always", "Case", "CaseStatement", "DelayStatement", "Localparam", "Assign", "Block", "Reg", "Wire"]
INSERT_TARGETS = ["IfStatement", "NonblockingSubstitution", "BlockingSubstitution", "ForStatement", "Always", "Case", "CaseStatement", "DelayStatement", "Localparam", "Assign"]

class MutationOp(ASTCodeGenerator):

    def __init__(self, popsize, fault_loc, control_flow):
        self.numbering = NodeNumbering()
        self.popsize = popsize
        self.fault_loc = fault_loc
        self.control_flow = control_flow
        # temporary variables used for storing data for the mutation operators
        self.fault_loc_set = set()
        self.new_vars_in_fault_loc = dict()
        self.wires_brought_in = dict()
        self.implicated_lines = set() # contains the line number implicated by FL
        # self.stoplist = set()
        self.tmp_node = None 
        self.deletable_nodes = []
        self.insertable_nodes = []
        self.replaceable_nodes = []
        self.node_class_to_replace = None
        self.nodes_by_class = []
        self.stmt_nodes = []
        self.max_node_id = -1

    """ 
    Replaces the node corresponding to old_node_id with new_node.
    """
    def replace_with_node(self, ast, old_node_id, new_node):
        attr = vars(ast)
        for key in attr: # loop through all attributes of this AST
            if attr[key].__class__ in AST_CLASSES: # for each attribute that is also an AST
                if attr[key].node_id == old_node_id:
                    attr[key] = copy.deepcopy(new_node)
                    return
            elif attr[key].__class__ in [list, tuple]: # for attributes that are lists or tuples
                for i in range(len(attr[key])): # loop through each AST in that list or tuple
                    tmp = attr[key][i]
                    if tmp.__class__ in AST_CLASSES and tmp.node_id == old_node_id:
                        attr[key][i] = copy.deepcopy(new_node)
                        return

        for c in ast.children():
            if c: self.replace_with_node(c, old_node_id, new_node)
    
    """
    Deletes the node with the node_id provided, if such a node exists.
    """
    def delete_node(self, ast, node_id):
        attr = vars(ast)
        for key in attr: # loop through all attributes of this AST
            if attr[key].__class__ in AST_CLASSES: # for each attribute that is also an AST
                if attr[key].node_id == node_id and attr[key].__class__.__name__ in DELETE_TARGETS:
                    attr[key] = None
            elif attr[key].__class__ in [list, tuple]: # for attributes that are lists or tuples
                for i in range(len(attr[key])): # loop through each AST in that list or tuple
                    tmp = attr[key][i]
                    if tmp.__class__ in AST_CLASSES and tmp.node_id == node_id and tmp.__class__.__name__ in DELETE_TARGETS:
                        attr[key][i] = None

        for c in ast.children():
            if c: self.delete_node(c, node_id)
    
    """
    Inserts node with node_id after node with after_id.
    """
    def insert_stmt_node(self, ast, node, after_id): 
        if ast.__class__.__name__ == "Block":
            if after_id == ast.node_id:
                # node.show()
                # input("...")
                ast.statements.insert(0, copy.deepcopy(node))
                return
            else:
                insert_point = -1
                for i in range(len(ast.statements)):
                    stmt = ast.statements[i]
                    if stmt and stmt.node_id == after_id:
                        insert_point = i + 1
                        break
                if insert_point != -1:
                    # print(ast.statements)
                    ast.statements.insert(insert_point, copy.deepcopy(node))
                    # print(ast.statements)
                    return

        for c in ast.children():
            if c: self.insert_stmt_node(c, node, after_id)
    
    """
    Gets the node matching the node_id provided, if one exists, by storing it in the temporary node variable.
    Used by the insert and replace operators.
    """    
    def get_node_from_ast(self, ast, node_id):
        if ast.node_id == node_id:
            self.tmp_node = ast
        
        for c in ast.children():
            if c: self.get_node_from_ast(c, node_id)

    """ 
    Gets all the line numbers for the code implicated by the FL.
    """    
    def collect_lines_for_fl(self, ast):
        if ast.node_id in self.fault_loc_set:
            self.implicated_lines.add(ast.lineno)
        
        for c in ast.children():
            if c: self.collect_lines_for_fl(c)

    """
    Gets a list of all nodes that can be deleted.
    """
    def get_deletable_nodes(self, ast):
        # with fault localization, make sure that any node being deleted is also in DELETE_TARGETS 
        if self.fault_loc and len(self.fault_loc_set) > 0:
            if ast.node_id in self.fault_loc_set and ast.__class__.__name__ in DELETE_TARGETS:
                self.deletable_nodes.append(ast.node_id)
        else:
            if ast.__class__.__name__ in DELETE_TARGETS:
                self.deletable_nodes.append(ast.node_id)

        for c in ast.children():
            if c: self.get_deletable_nodes(c) 

    """
    Gets a list of all nodes that can be inserted into to a begin ... end block.
    """
    def get_insertable_nodes(self, ast):
        # with fault localization, make sure that any node being used is also in INSERT_TARGETS (to avoid inserting, e.g., overflow+1 into a block statement)
        if self.fault_loc and len(self.fault_loc_set) > 0: 
            if ast.node_id in self.fault_loc_set and ast.__class__.__name__ in INSERT_TARGETS:
                self.insertable_nodes.append(ast.node_id)
        else:        
            if ast.__class__.__name__ in INSERT_TARGETS:
                self.insertable_nodes.append(ast.node_id)

        for c in ast.children():
            if c: self.get_insertable_nodes(c) 
    
    """
    Gets the class of the node being replaced in a replace operation. 
    This class is used to find potential sources for the replacement.
    """
    def get_node_to_replace_class(self, ast, node_id):
        if ast.node_id == node_id:
            self.node_class_to_replace = ast.__class__

        for c in ast.children():
            if c: self.get_node_to_replace_class(c, node_id)
    
    """
    Gets all nodes that compatible to be replaced with a node of the given class type. 
    These nodes are potential sources for replace operations.
    """
    def get_replaceable_nodes_by_class(self, ast, node_type):
        if ast.__class__ in REPLACE_TARGETS[node_type]:
            self.replaceable_nodes.append(ast.node_id)

        for c in ast.children():
            if c: self.get_replaceable_nodes_by_class(c, node_type)
    
    """
    Gets all nodes that are of the given class type. 
    These nodes are used for applying mutation templates.
    """
    # TODO: do this only for fault loc set?
    def get_nodes_by_class(self, ast, node_type):
        if ast.__class__.__name__ == node_type:
            self.nodes_by_class.append(ast.node_id)

        for c in ast.children():
            if c: self.get_nodes_by_class(c, node_type)

    """
    Gets all nodes that are found within a begin ... end block. 
    These nodes are potential destinations for insert operations.
    """
    def get_nodes_in_block_stmt(self, ast):
        if ast.__class__.__name__ == "Block":
            if len(ast.statements) == 0: # if empty block, return the node id for the block (so that a node can be inserted into the empty block)
                self.stmt_nodes.append(ast.node_id)
            else:
                for c in ast.statements:
                    if c: self.stmt_nodes.append(c.node_id)
        
        for c in ast.children():
            if c: self.get_nodes_in_block_stmt(c)

    """
    Control dependency analysis of the given program branch.
    """
    def analyze_program_branch(self, ast, cond_list, mismatch_set, uniq_headers):
        if ast:
            if ast.__class__.__name__ == "Identifier" and (ast.name in mismatch_set or ast.name in tuple(self.new_vars_in_fault_loc.values())):
                for cond in cond_list:
                    if cond: self.add_node_and_children_to_fault_loc(cond, mismatch_set, uniq_headers, ast)

            for c in ast.children():
                self.analyze_program_branch(c, cond_list, mismatch_set, uniq_headers)
    
    """
    The delete, insert, and replace operators to be called from outside the class.
    Note: node_id, with_id, and after_id would not be none if we are trying to regenerate AST from patch list, and would be none for a random mutation.
    """
    def delete(self, ast, patch_list, node_id=None):
        self.deletable_nodes = [] # reset deletable nodes for the next delete operation, in case previous delete returned early

        if node_id == None:
            self.get_deletable_nodes(ast) # get all nodes that can be deleted without breaking the AST / syntax
            if len(self.deletable_nodes) == 0: # if no nodes can be deleted, return without attepmting delete
                print("Delete operation not possible. Returning with no-op.")
                return patch_list, ast
            
            node_id = random.choice(self.deletable_nodes) # choose a random node_id to delete
            print("Deleting node with id %s\n" % node_id)

        self.delete_node(ast, node_id) # delete the node corresponding to node_id
        self.numbering.renumber(ast) # renumber nodes
        self.max_node_id = self.numbering.c # reset max_node_id
        self.numbering.c = -1
        self.deletable_nodes = [] # reset deletable nodes for the next delete operation

        child_patchlist = copy.deepcopy(patch_list)
        child_patchlist.append("delete(%s)" % node_id) # update patch list

        return child_patchlist, ast
    
    def insert(self, ast, patch_list, node_id=None, after_id=None):
        self.insertable_nodes = [] # reset the temporary variables, in case previous insert returned early
        self.tmp_node = None

        if node_id == None and after_id == None:
            self.get_insertable_nodes(ast) # get all nodes with a type that is suited to insertion in block statements -> src
            self.get_nodes_in_block_stmt(ast) # get all nodes within a block statement -> dest
            if len(self.insertable_nodes) == 0 or len(self.stmt_nodes) == 0: # if no insertable nodes exist, exit gracefully
                print("Insert operation not possible. Returning with no-op.")
                return patch_list, ast
            
            after_id = random.choice(self.stmt_nodes) # choose a random src and dest
            
            node_id = random.choice(self.insertable_nodes)
            print("Inserting node with id %s after node with id %s\n" % (node_id, after_id))
        self.get_node_from_ast(ast, node_id) # get the node associated with the src node id
        self.insert_stmt_node(ast, self.tmp_node, after_id) # perform the insertion
        self.numbering.renumber(ast) # renumber nodes
        self.max_node_id = self.numbering.c # reset max_node_id
        self.numbering.c = -1
        
        child_patchlist = copy.deepcopy(patch_list)
        child_patchlist.append("insert(%s,%s)" % (node_id, after_id)) # update patch list

        return child_patchlist, ast
    
    def replace(self, ast, patch_list, node_id=None, with_id=None):
        self.tmp_node = None # reset the temporary variables (in case previous replace returned sooner)
        self.replaceable_nodes = []
        self.node_class_to_replace = None

        if node_id == None:
            if self.max_node_id == -1: # if max_id is not know yet, traverse the AST to find the number of nodes -- needed to pick a random id to replace
                self.numbering.renumber(ast)
                self.max_node_id = self.numbering.c
                self.numbering.c = -1 # reset the counter for numbering
            if self.fault_loc and len(self.fault_loc_set) > 0:
                
                node_id = random.choice(tuple(self.fault_loc_set)) # get a fault loc target if fault localization is being used
            else:      
                      
                node_id = random.randint(0,self.max_node_id) # get random node id to replace
            print("Node to replace id: %s" % node_id)

        self.get_node_to_replace_class(ast, node_id) # get the class of the node associated with the random node id
        print("Node to replace class: %s" % self.node_class_to_replace)
        if self.node_class_to_replace == None: # if the node does not exist, return with no-op
            return patch_list, ast
        
        if with_id == None:       
            self.get_replaceable_nodes_by_class(ast, self.node_class_to_replace) # get all valid nodes that have a class that could be substituted for the original node's class
            if len(self.replaceable_nodes) == 0: # if no replaceable nodes exist, exit gracefully
                print("Replace operation not possible. Returning with no-op.")
                return patch_list, ast
            print("Replaceable nodes: %s" % str(self.replaceable_nodes))
            
            with_id = random.choice(self.replaceable_nodes) # get a random node id from the replaceable nodes
            print("Replacing node id %s with node id %s" % (node_id,with_id))  
        
        self.get_node_from_ast(ast, with_id) # get the node associated with with_id

        # safety guard: this could happen if crossover makes the GA think a node is actually suitable for replacement when in reality it is not....    
        if self.tmp_node.__class__ not in REPLACE_TARGETS[self.node_class_to_replace]: 
            print(self.tmp_node.__class__)
            print(REPLACE_TARGETS[self.node_class_to_replace])
            return patch_list, ast  

        self.replace_with_node(ast, node_id, self.tmp_node) # perform the replacement
        self.tmp_node = None # reset the temporary variables
        self.replaceable_nodes = []
        self.node_class_to_replace = None
        self.numbering.renumber(ast) # renumber nodes
        self.max_node_id = self.numbering.c # update max_node_id
        self.numbering.c = -1
        
        child_patchlist = copy.deepcopy(patch_list)
        child_patchlist.append("replace(%s,%s)" % (node_id, with_id)) # update patch list

        return child_patchlist, ast
    