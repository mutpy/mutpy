import time

from mutpy import codegen, termcolor


class ViewNotifier:   
    PREFIX = 'notify_'
    
    def __init__(self, views):
        self.views = views
                     
    def add_view(self, view):
        self.views.append(view)
    
    def del_view(self, view):
        self.views.remove(view)
        
    def notify_all_views(self, notify, *kwargs):
        for view in self.views:
            if hasattr(view, notify):
                attr = getattr(view, notify)
                attr(*kwargs)
                
    def __getattr__(self, name):
        if name.startswith(ViewNotifier.PREFIX):
            notify = name[len(ViewNotifier.PREFIX):]
            return lambda * args: self.notify_all_views(notify, *args)
        else:
            raise AttributeError(name)


class QuietTextMutationView:
    
    def __init__(self, cfg):
        self.cfg = cfg
        
    def end(self, score, time):
        self.level_print('Mutation score {}: {}'.format(self.time_format(time),
                                                         self.decorate('{:.1f}%'.format(score.count()),
                                                                       'blue', attrs=['bold'])))
    
    def level_print(self, msg, level=1, ended=True, continuation=False):
        end = "\n" if ended else ""
        
        if continuation:
            print(msg, end=end)
        else:
            if level == 1:
                prefix = self.decorate('[*]', 'blue')
            elif level == 2:
                prefix = self.decorate('   -', 'cyan')
            
            print('{} {}'.format(prefix, msg), end=end)

    def decorate(self, text, color=None, on_color=None, attrs=None):
        if self.cfg.colored_output:
            return termcolor.colored(text, color, on_color, attrs)
        else:
            return text
    
    @staticmethod        
    def time_format(time=None):
        if time is None:
            return '[    -    ]'
        else:
            return '[{:.5f} s]'.format(time)
        

class TextMutationView(QuietTextMutationView):
    
    def initialize(self):
        self.level_print('Start mutation process:')
        self.level_print('target: {}'.format(self.cfg.target), 2)
        self.level_print('tests: {}'.format(', '.join(self.cfg.test)), 2)
        
    def start(self):
        self.level_print('Start mutants generation and execution:')
        
    def end(self, score, time):
        super().end(score, time)
        self.level_print('all: {}'.format(score.all_mutants), 2)
        self.level_print('killed: {}'.format(score.killed_mutants), 2)
        self.level_print('incompetent: {}'.format(score.incompetent_mutants), 2)
        self.level_print('timeout: {}'.format(score.timeout_mutants), 2)
    
    def passed(self, tests):
        self.level_print('All tests passed:')
        
        for test, target, time in tests:
            test_name = test.__name__ + ('.' + target if target else '')
            self.level_print('{} {}'.format(test_name, self.time_format(time)), 2)
    
    def failed(self, result):
        self.level_print(self.decorate('Tests failed:', 'red', attrs=['bold']))
        
        for error in result.errors:
                self.level_print('error in {} - {} '.format(error[0], error[1].split("\n")[-2]), 2)
                
        for fail in result.failures:
                self.level_print('fail in {} - {}'.format(fail[0], fail[1].split("\n")[-2]), 2)
        
    def mutation(self, op, lineno, mutant):
        self.level_print('{:<3} line {:<3}: '.format(op.name(), lineno), ended=False, level=2)
        if self.cfg.show_mutants:
            self.print_code(mutant, lineno)
    
    def cant_load(self, name):
        self.level_print(self.decorate('Bad path: ', 'red', attrs=['bold']) + name)
        
    def print_code(self, mutant, lineno):
        mutant_src = codegen.to_source(mutant)
        mutant_src = codegen.add_line_numbers(mutant_src)
        src_lines = mutant_src.split("\n")
        
        src_lines[lineno - 1] = self.decorate(src_lines[lineno - 1], 'yellow')
        snippet = src_lines[max(0, lineno - 5):min(len(src_lines), lineno + 5)]
        print("\n{}\n".format('-'*80) + "\n".join(snippet) + "\n{}".format('-'*80))
    
    def killed(self, time):
        self.level_print(self.time_format(time) + ' ' + self.decorate('killed', 'green') , continuation=True)
    
    def survived(self, time):
        self.level_print(self.time_format(time) + ' ' + self.decorate('survived', 'red'), continuation=True)
    
    def timeout(self):
        self.level_print(self.time_format() + ' ' + self.decorate('timeout', 'yellow'), continuation=True)
    
    def error(self):
        self.level_print(self.time_format() + ' ' + self.decorate('incompetent', 'cyan'), continuation=True)
    
        
class YAMLRaportMutationView:
    
    def __init__(self, file_name):
        file = open(file_name, 'w')
        file.write('# raport genereted by MutPy - {}'.format(time.ctime()))
        file.close()
