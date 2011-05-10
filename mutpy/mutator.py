from mutpy import operator


class Mutator:
    
    def __init__(self, target_ast, cfg):
        self.target_ast = target_ast
        self.cfg = cfg
        
    def mutate(self):
        operators = [operator.ArithmeticOperatorReplacement(), operator.ConstantReplacement(),
                     operator.StatementDeletion(), operator.ConditionNegation(), operator.SliceIndexReplace()]
        for op in operators:
            for mutant, lineno in op.incremental_visit(self.target_ast):
                yield op, lineno, mutant
