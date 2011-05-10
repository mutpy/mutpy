import ast
import copy


class NodeIncrementalTransformer(ast.NodeTransformer):
    
    def incremental_visit(self, node):
        self.global_mutation = 0
        self.mutation_flag = False
        ast.fix_missing_locations(node)
        while True:
            self.current_visit = 0
            node_copy = copy.deepcopy(node)
            new_node = self.visit(node_copy)
            self.global_mutation += 1
            if self.mutation_flag == False:
                break
            else:
                self.mutation_flag = False
            yield new_node, self.mutate_lineno
        
    def visit(self, node):
        if hasattr(node, 'lineno'):
            self.curr_line = node.lineno
            
        if self.mutation_flag:
            return node
            
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
        
    @staticmethod
    def getattr_like(ob, attr):
        for a in dir(ob):
            if a.startswith(attr):
                yield getattr(ob, attr)


class Operator(NodeIncrementalTransformer):
    
    def name(self):
        return ''.join([c for c in self.__class__.__name__ if str.isupper(c)])
        
    def mutate(self, node):
        self.mutate_lineno = node.lineno if hasattr(node, 'lineno') else self.curr_line
        return node


class ArithmeticOperatorReplacement(Operator):
    
    def visit_Add(self, node):
        return self.mutate(ast.copy_location(ast.Sub(), node))
        
class ConstantReplacement(Operator):
    
    def visit_Num(self, node):
        return self.mutate(ast.copy_location(ast.Num(n=node.n + 1), node))
        
    def visit_Str(self, node):
        if node.s:
            new_s = ''
        else:
            new_s = 'mutpy'
        
        return self.mutate(ast.copy_location(ast.Str(s=new_s), node))

class StatementDeletion(Operator):
    
    def delete_statement(self, node):
        return self.mutate(ast.copy_location(ast.Pass(), node))
        
    def visit_Assign(self, node):
        return self.delete_statement(node)
    
    def visit_Return(self, node):
        return self.delete_statement(node)
        
class ConditionNegation(Operator):
    
    def visit_While(self, node):
        not_node = ast.UnaryOp(op=ast.Not(), operand=node.test)
        ast.copy_location(not_node, node)
        node.test = not_node
        return self.mutate(node)
    
class SliceIndexReplace(Operator):
    
    def visit_Slice(self, node):
        node.lower, node.upper, node.step = node.upper, node.step, node.lower
        return self.mutate(node)
