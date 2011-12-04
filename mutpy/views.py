import time
import yaml

from mutpy import codegen, termcolor


class ViewNotifier:
    PREFIX = 'notify_'

    def __init__(self, views):
        self.views = views

    def add_view(self, views):
        self.views.append(views)

    def del_view(self, views):
        self.views.remove(views)

    def notify_all_views(self, notify, *args):
        for views in self.views:
            if hasattr(views, notify):
                attr = getattr(views, notify)
                attr(*args)

    def __getattr__(self, name):
        if name.startswith(ViewNotifier.PREFIX):
            notify = name[len(ViewNotifier.PREFIX):]
            return lambda * args: self.notify_all_views(notify, *args)
        else:
            raise AttributeError(name)


class QuietTextView:

    def __init__(self, colored_output=False):
        self.colored_output = colored_output

    def end(self, score, time_reg):
        self.level_print('Mutation score {}: {}'.format(self.time_format(time_reg.main_task),
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
        if self.colored_output:
            return termcolor.colored(text, color, on_color, attrs)
        else:
            return text

    @staticmethod
    def time_format(time=None):
        if time is None:
            return '[    -    ]'
        else:
            return '[{:.5f} s]'.format(time)


class TextView(QuietTextView):

    def __init__(self, colored_output=False, show_mutants=False):
        super().__init__(colored_output)
        self.show_mutants = show_mutants

    def initialize(self, targets, tests):
        self.level_print('Start mutation process:')
        self.level_print('targets: {}'.format(', '.join(targets)), 2)
        self.level_print('tests: {}'.format(', '.join(tests)), 2)

    def start(self):
        self.level_print('Start mutants generation and execution:')

    def end(self, score, time_reg):
        super().end(score, time_reg)
        self.level_print('all: {}'.format(score.all_mutants), 2)

        if score.all_mutants:
            self.level_print('killed: {} ({:.1f}%)'.format(score.killed_mutants,
                                                       100 * score.killed_mutants / score.all_mutants), 2)
            self.level_print('survived: {} ({:.1f}%)'.format(score.survived_mutants,
                                                       100 * score.survived_mutants / score.all_mutants), 2)
            self.level_print('incompetent: {} ({:.1f}%)'.format(score.incompetent_mutants,
                                                            100 * score.incompetent_mutants / score.all_mutants), 2)
            self.level_print('timeout: {} ({:.1f}%)'.format(score.timeout_mutants,
                                                        100 * score.timeout_mutants / score.all_mutants), 2)

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

    def mutation(self, number, op, filename, lineno, mutant):
        self.level_print('[#{:>4}] {:<3} {}:{:<3}: '.format(number, op.name(), filename, lineno), ended=False, level=2)
        if self.show_mutants:
            self.print_code(mutant, lineno)

    def cant_load(self, name):
        self.level_print(self.decorate('Bad path: ', 'red', attrs=['bold']) + name)

    def print_code(self, mutant, lineno):
        mutant_src = codegen.to_source(mutant)
        mutant_src = codegen.add_line_numbers(mutant_src)
        src_lines = mutant_src.split("\n")
        lineno = min(lineno, len(src_lines))
        src_lines[lineno - 1] = self.decorate('~' + src_lines[lineno - 1][1:], 'yellow')
        snippet = src_lines[max(0, lineno - 5):min(len(src_lines), lineno + 5)]
        print("\n{}\n".format('-'*80) + "\n".join(snippet) + "\n{}".format('-'*80))

    def killed(self, time, killer):
        self.level_print(self.time_format(time) + ' ' + self.decorate('killed', 'green') + ' by ' + str(killer),
                         continuation=True)

    def survived(self, time):
        self.level_print(self.time_format(time) + ' ' + self.decorate('survived', 'red'), continuation=True)

    def timeout(self):
        self.level_print(self.time_format() + ' ' + self.decorate('timeout', 'yellow'), continuation=True)

    def error(self):
        self.level_print(self.time_format() + ' ' + self.decorate('incompetent', 'cyan'), continuation=True)


class YAMLRaportView:

    def __init__(self, file_name):
        self.file_name = file_name
        self.mutation_info = []
        self.stream = open(self.file_name, 'w')

    def initialize(self, target, tests):
        init = {'target': target, 'tests': tests}
        self.dump(init)

    def end_mutation(self, status, time, killer=None):
        self.current_mutation['status'] = status
        self.current_mutation['time'] = time
        self.current_mutation['killer'] = killer
        self.mutation_info.append(self.current_mutation)

    def mutation(self, number, op, file, lineno, mutant):
        self.current_mutation = {'number': number,
                                 'filename': file,
                                 'operator': op.__name__,
                                 'line': lineno}

    def killed(self, time, killer):
        self.end_mutation('killed', time, str(killer))

    def survived(self, time):
        self.end_mutation('survived', time)

    def error(self):
        self.end_mutation('incompetent', None)

    def timeout(self):
        self.end_mutation('timeout', None)

    def end(self, score, time_reg):
        self.dump({'mutations': self.mutation_info, 
                   'time_stats': ttime_reg.stats()})

    def dump(self, to_dump):
        yaml.dump(to_dump, self.stream, default_flow_style=False)

    def __del__(self):
        self.stream.close()

