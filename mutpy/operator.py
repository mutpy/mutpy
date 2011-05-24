import ast
import copy
import re

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
                if new_node:
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
        pattern = re.compile(attr_like + "_\w+")
        return [getattr(ob, attr) for attr in dir(ob) if attr == attr_like or pattern.match(attr)]
    
    def name(self):
        return ''.join([c for c in self.__class__.__name__ if str.isupper(c)])

    def find_visitors(self, node):
        method_prefix = 'visit_' + node.__class__.__name__
        visitors = MutationOperator.getattr_like(self, method_prefix)
        return visitors

        

class ArithmeticOperatorReplacement(MutationOperator):
    
    def visit_Add(self, node):
        return ast.Sub()
    
    def visit_Sub(self, node):
        return ast.Add()
    
    def visit_Mult_to_Div(self, node):
        return ast.Div()
    
    def visit_Mult_to_FloorDiv(self, node):
        return ast.FloorDiv()
    
    def visit_Div_to_Mult(self, node):
        return ast.Mult()
    
    def visit_Div_to_FloorDiv(self, node):
        return ast.FloorDiv()
    
    def visit_FloorDiv_to_Div(self, node):
        return ast.Div()
    
    def visit_FloorDiv_to_Mult(self, node):
        return ast.Mult()
    
    def visit_Mod(self, node):
        return ast.Mult()
    

class BinaryOperatorReplacement(MutationOperator):
    
    def visit_BitAnd(self, node):
        return ast.BitOr()
    
    def visit_BitOr(self, node):
        return ast.BitAnd()
    
    def visit_BitXor(self, node):
        return ast.BitAnd()
    
    def visit_LShift(self, node):
        return ast.RShift()
    
    def visit_RShift(self, node):
        return ast.LShift()
    

class LogicaOperatorReplacement(MutationOperator):
    
    def visit_And(self, node):
        return ast.Or()
    
    def visit_Or(self, node):
        return ast.And()

class ConditionalOperatorReplacement(MutationOperator):
    
    def visit_Lt(self, node):
        return ast.Gt()
    
    def visit_Lt_to_LtE(self, node):
        return ast.LtE()
        
    def visit_Gt(self, node):
        return ast.Lt()
    
    def visit_Gt_to_GtE(self, node):
        return ast.GtE()
    
    def visit_LtE(self, node):
        return ast.GtE()
    
    def visit_LtE_to_Lt(self, node):
        return ast.Lt()
    
    def visit_GtE(self, node):
        return ast.LtE()
    
    def visit_GtE_to_Gt(self, node):
        return ast.Gt()
    
    def visit_Eq(self, node):
        return ast.NotEq()

    def visit_NotEq(self, node):
        return ast.Eq()


class UnaryOperatorReplacement(MutationOperator):
    
    def visit_USub(self, node):
        return ast.UAdd()
    
    def visit_UAdd(self, node):
        return ast.USub()
    
        
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
    
    def visit_Expr(self, node):
        return ast.Pass()
 
       
class ConditionNegation(MutationOperator):
    
    def negate_test(self, node):
        not_node = ast.UnaryOp(op=ast.Not(), operand=node.test)
        node.test = not_node
        return node
    
    def visit_While(self, node):
        return self.negate_test(node)
    
    def visit_If(self, node):
        return self.negate_test(node)

    
class SliceIndexReplace(MutationOperator):
    
    def visit_Slice(self, node):
        node.lower, node.upper, node.step = node.upper, node.step, node.lower
        return node
    
class MembershipTestReplacement(MutationOperator):
    
    def visit_In(self, node):
        return ast.NotIn()
    
    def visit_NotIn(self, node):
        return ast.In()
    
class ExceptionHandleDeletion(MutationOperator):
    
    def visit_ExceptHandler(self, node):
        return None


class ZeroIterationLoop(MutationOperator):
    
    def zero_iteration(self, node):
        node.body = [ast.Break()]
        return node
    
    def visit_For(self, node):
        return self.zero_iteration(node)
    
    def visit_While(self, node):
        return self.zero_iteration(node)

class OneIterationLoop(MutationOperator):
    
    def one_iteration(self, node):
        node.body.append(ast.Break())
        return node
    
    def visit_For(self, node):
        return self.one_iteration(node)
    
    def visit_While(self, node):
        return self.one_iteration(node)
    
    
class ReverseIterationLoop(MutationOperator):
    
    def visit_For(self, node):
        old_iter = node.iter
        node.iter = ast.Call(func=ast.Name(id='reversed'), args=[old_iter], keywords=[], starargs=None, kwargs=None)
        return node
