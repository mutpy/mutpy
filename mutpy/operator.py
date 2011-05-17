import ast
import copy


class MutationOperator(ast.NodeTransformer):
    
    def mutate(self, node, to_mutate):
        self.global_mutation = 0
        self.visitor_number = 0
        self.mutation_flag = False
        while True:
            self.current_visit = 0
            node_copy = copy.deepcopy(node)
            new_node = self.visit(node_copy)
            if self.visitor_number == 0:
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
        visitors = MutationOperator.getattr_like(self, method)
        if not visitors:
            visitor = self.generic_visit
        else:
            if self.current_visit < self.global_mutation:
                visitor = self.generic_visit
                self.current_visit += 1
            else:
                self.mutate_lineno = node.lineno if hasattr(node, 'lineno') else self.curr_line
                self.mutation_flag = True
                visitor = visitors[self.visitor_number]
                if visitor is visitors[-1]:
                    self.visitor_number = 0
                    self.current_visit += 1
                else:
                    self.visitor_number += 1
                
        return visitor(node)
        
    @staticmethod
    def getattr_like(ob, attr_like):
        return [getattr(ob, attr) for attr in dir(ob) if attr.startswith(attr_like)]
    
    def name(self):
        return ''.join([c for c in self.__class__.__name__ if str.isupper(c)])
        

class ArithmeticOperatorReplacement(MutationOperator):
    
    def visit_Add(self, node):
        return ast.copy_location(ast.Sub(), node)

        
class ConstantReplacement(MutationOperator):
    
    def visit_Num(self, node):
        return ast.copy_location(ast.Num(n=node.n + 1), node)
        
    def visit_Str(self, node):
        return ast.copy_location(ast.Str(s='mutpy'), node)
    
    def visit_Str_empty(self, node):
        return ast.copy_location(ast.Str(s=''), node)

class StatementDeletion(MutationOperator):
    
    def delete_statement(self, node):
        return ast.copy_location(ast.Pass(), node)
        
    def visit_Assign(self, node):
        return self.delete_statement(node)
    
    def visit_Return(self, node):
        return self.delete_statement(node)
 
       
class ConditionNegation(MutationOperator):
    
    def visit_While(self, node):
        not_node = ast.UnaryOp(op=ast.Not(), operand=node.test)
        ast.copy_location(not_node, node)
        node.test = not_node
        return node

    
class SliceIndexReplace(MutationOperator):
    
    def visit_Slice(self, node):
        node.lower, node.upper, node.step = node.upper, node.step, node.lower
        return node
