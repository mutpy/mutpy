from mutpy.termcolor import colored
from mutpy import codegen

class TextMutationView:
    
    def initialize(self, cfg):
        self.level_print('Start mutation process:')
        self.level_print('target: {}'.format(cfg.target), 2)
        self.level_print('tests: {}'.format(', '.join(cfg.test)), 2)
    
    def start(self):
        self.level_print('Start mutants generation and execution:')
        
    def end(self, score, killed_mutants, all_mutants, incompetent_mutatnts):
         self.level_print('Mutation score: {}'.format(colored('{:.1f}%'.format(score), 'blue', attrs=['bold'])))
         self.level_print('all: {}'.format(all_mutants), 2)
         self.level_print('killed: {}'.format(killed_mutants), 2)
         self.level_print('incompetent: {}'.format(incompetent_mutatnts), 2)
    
    def passed(self, tests):
        self.level_print('All tests passed:')
        
        for test, t in tests:
            self.level_print('{} {}'.format(test.__name__, time(t)), 2)
    
    def failed(self, result):
        self.level_print(colored('Tests failed:', 'red', attrs=['bold']))
        
        for error in result.errors:
                self.level_print('error in {} - {} '.format(error[0], error[1].split("\n")[-2]), 2)
                
        for fail in result.failures:
                self.level_print('fail in {} - {})'.format(fail[0], fail[1].split("\n")[-2]), 2)
        
    def mutation(self, op, lineno, mutant):
        self.level_print('{:<3} line {:<3}: '.format(op.name(), lineno), ended=False, level=2)
        mutant_src = codegen.to_source(mutant)
        
    def print_code(self, mutatnt):
        src_lines = mutant_src.split("\n")
        src_lines[lineno] = colored(src_lines[lineno], 'red')
        snippet = src_lines[max(0, lineno - 5):min(len(src_lines), lineno+5)]
        print("\n\n----------------------------\n"+"\n".join(snippet)+"\n----------------------------\n")
    
    def killed(self, t):
        self.level_print(time(t) + ' ' + colored('killed', 'green') , continuation=True)
    
    def survived(self, t):
        self.level_print(time(t) + ' ' + colored('survieved', 'red'), continuation=True)
    
    def timeout(self):
        self.level_print(time() + ' ' + colored('timeout', 'yellow'), continuation=True)
    
    def error(self):
        self.level_print(time() + ' ' + colored('incompetent', 'cyan'),  continuation=True)
    
    def level_print(self, msg, level=1, ended=True, continuation=False):
        end = "\n" if ended else ""
        
        if continuation:
            print(msg, end=end)
        else:
            if level == 1:
                prefix = colored('[*]', 'blue')
            elif level == 2:
                prefix = colored('   -', 'cyan')
            
            print('{} {}'.format(prefix, msg), end=end)
    
def time(t=None):
    if t is None:
        return '[    -    ]'
    else:
        return '[{:.5f} s]'.format(t)