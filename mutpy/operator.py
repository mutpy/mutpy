import ast
import copy

def notmutate(sth):
    return sth


class MutationResign(Exception): pass


class MutationOperator(ast.NodeTransformer):
    
    def mutate(self, node, to_mutate):
        self.muteted_node_number = 0
        self.visit_method_number = 0
        self.mutation_flag = False
        
        while True:
            self.visited_node_number = 0
            node_copy = copy.deepcopy(node)
            new_node = self.visit(node_copy)
            
            if not self.visit_method_number:
                self.muteted_node_number += 1
                
            if not self.mutation_flag:
                break
            
            self.mutation_flag = False
            
            yield new_node, self.mutate_lineno
        


    def visit(self, node):
        if hasattr(node, 'lineno'):
            self.curr_line = node.lineno
            
        if self.mutation_flag:
            return node
        
        try:
            for decorator in node.decorator_list:
                if decorator.id == notmutate.__name__:
                    return node
        except AttributeError:
            pass
            
        visitors = self.find_visitors(node)
        
        if not visitors:
            new_node = self.generic_visit(node)
        else:
            if self.visited_node_number < self.muteted_node_number:
                self.visited_node_number += 1
                new_node = self.generic_visit(node)
            else:
                new_node = self.visit_with_visitors(node, visitors)
                    
        return new_node
    
    def visit_with_visitors(self, node, visitors):
        while self.visit_method_number < len(visitors):
            visitor = visitors[self.visit_method_number]
            try:
                new_node = visitor(node)
                self.mutate_lineno = node.lineno if hasattr(node, 'lineno') else self.curr_line
                self.mutation_flag = True
                ast.copy_location(new_node, node)
                if visitor is visitors[-1]:
                    self.visit_method_number = 0
                    self.visited_node_number += 1
                else:
                    self.visit_method_number += 1
                    
                break
            except MutationResign:
                self.visit_method_number += 1
                self.muteted_node_number += 1
        else:
            self.visit_method_number = 0
            self.visited_node_number += 1
            new_node = self.generic_visit(node)
        
        return new_node
        
    @staticmethod
    def getattr_like(ob, attr_like):
        return [getattr(ob, attr) for attr in dir(ob) if attr.startswith(attr_like)]
    
    def name(self):
        return ''.join([c for c in self.__class__.__name__ if str.isupper(c)])

    def find_visitors(self, node):
        method_prefix = 'visit_' + node.__class__.__name__
        visitors = MutationOperator.getattr_like(self, method_prefix)
        return visitors

        

class ArithmeticOperatorReplacement(MutationOperator):
    
    def visit_Add(self, node):
        return ast.Sub()
    
        
class ConstantReplacement(MutationOperator):
    
    def visit_Num(self, node):
        return ast.Num(n=node.n + 1)
    
    def visit_Str(self, node):
        return ast.Str(s='mutpy')
    
    def visit_Str_empty(self, node):
        if not node.s:
            raise MutationResign()
        
        return ast.Str(s='')

class StatementDeletion(MutationOperator):
    
    def visit_Assign(self, node):
        return ast.Pass()
    
    def visit_Return(self, node):
        return ast.Pass()
 
       
class ConditionNegation(MutationOperator):
    
    def visit_While(self, node):
        not_node = ast.UnaryOp(op=ast.Not(), operand=node.test)
        node.test = not_node
        return node

    
class SliceIndexReplace(MutationOperator):
    
    def visit_Slice(self, node):
        node.lower, node.upper, node.step = node.upper, node.step, node.lower
        return node
