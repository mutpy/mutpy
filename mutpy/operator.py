import ast
import copy

class NodeIncrementalTransformer(ast.NodeTransformer):
    
    def incremental_visit(self, node):
        self.global_mutation = 0
        self.mutation_flag = False
        
        while True:
            self.current_visit = 0
            new_node = self.visit(copy.deepcopy(node))
            self.global_mutation += 1
            if self.mutation_flag == False:
                break
            else:
                self.mutation_flag = False
            yield new_node
        
    def visit(self, node):
        method = 'visit_' + node.__class__.__name__
        visitor = getattr(self, method, None)
        
        if visitor is None:
            visitor = self.generic_visit
        else:
            if self.current_visit != self.global_mutation:
                visitor = self.generic_visit
            else:
                self.mutation_flag = True
            self.current_visit += 1
                
        return visitor(node)

class ArithmeticOperatorReplacement(NodeIncrementalTransformer):
    def visit_Add(self, node):
        print('+ -> -')
        return ast.Sub()