#!/usr/bin/env python3
import sys
import re
import keyword
import builtins
import glob

class ShellToPythonTranspiler:
    def __init__(self, shell_script_path):
        self.shell_script_path = shell_script_path
        self.indent_level = 0
        self.used_libraries = set()

    def handle_assignment(self, line):
        match = re.match(r'(\w+)=(.*)', line)
        if match:
            var_name = match.group(1)
            value = match.group(2).strip()
            
            # If the variable name is a Python keyword or built-in function, capitalize it
            if var_name in keyword.kwlist or var_name in sorted(dir(builtins)):
                var_name = var_name.upper()

            # If the value starts with a digit, treat it as a number
            if value[0].isdigit() or (value[0] == '-' and value[1].isdigit()):
                # Handle expressions like "1$row"
                if re.match(r'(\d+)\$(\w+)', value):
                    digit, var = re.match(r'(\d+)\$(\w+)', value).groups()
                    digit = repr(digit)
                    value = f"{digit} + str({var})"
                # Handle regular numbers
                else:
                    value = int(value)
            # Handle strings
            else:
                if (value.startswith('"') and value.endswith('"')) or \
                (value.startswith("'") and value.endswith("'")):
                    value = value[1:-1]
                # If a '$' is present in the value, it's a variable reference
                if '$' in value:
                    value = re.sub(r'\$([\w]+)', r'{\1}', value)
                    value = f"f'{value}'"
                # If the value is enclosed in quotes, remove them
                else:
                    value = repr(value)
            return ' ' * self.indent_level * 4 + f"{var_name} = {value}"


    def handle_file_tests(self, line):
        match = re.match(r'(if|elif) test (-[rwxfdse]) (.+)', line)
        match_ne = re.match(r'(if|elif) test (.+)\s!=\s(.+)', line)
        if match:
            python_keyword = 'elif' if match.group(1) == 'elif' else 'if'
            operation = match.group(2)
            filename = match.group(3)

            if operation == '-r':  # readable
                self.used_libraries.add('os')
                return f'{python_keyword} os.access({repr(filename)}, os.R_OK):'
            elif operation == '-w':  # writable
                self.used_libraries.add('os')
                return f'{python_keyword} os.access({repr(filename)}, os.W_OK):'
            elif operation == '-x':  # 
                self.used_libraries.add('os')
                return f'{python_keyword} os.access({repr(filename)}, os.X_OK):'
            elif operation == '-f':  # is a file
                self.used_libraries.add('os')
                return f'{python_keyword} os.path.isfile({repr(filename)}):'
            elif operation == '-d':  # is a directory
                self.used_libraries.add('os')
                return f'{python_keyword} os.path.isdir({repr(filename)}):'
            elif operation == '-s':  # size is greater than 0
                self.used_libraries.add('os')
                return f'{python_keyword} os.path.getsize({repr(filename)}) > 0:'
            elif operation == '-e':  # file exists
                self.used_libraries.add('os')
                return f'{python_keyword} os.path.exists({repr(filename)}):'
            else:
                raise ValueError(f'Unrecognized file test operation: {operation}')
        elif match_ne: # if '!=' condition is matched
            python_keyword = 'elif' if match_ne.group(1) == 'elif' else 'if'
            first_arg = match_ne.group(2)
            second_arg = match_ne.group(3)
            return f"{python_keyword} {first_arg} != {second_arg}:"

    def remove_dollar_sign(self, var):
        if var is not None and '$' in var:
            return var.replace('$', '')
        else:
            return var


    def transpile_line(self, line):
        # Handle comments
        if line.strip().startswith("#!/bin"):
            return ''
        line = line.strip()

        if line.strip().startswith("#"):
            return ' ' * self.indent_level * 4 + line.strip()
        
        # Check for inline comments (comments after a command)
        if '#' in line:
            cmd, comment = line.split('#', 1)
            return self.transpile_line(cmd) + ' #' + comment.strip()

        if line.strip().startswith("echo *"):
            self.used_libraries.add('glob')
            return 'print(" ".join(glob.glob("*")))'


        # Handle comments
        if line.startswith("#"):
            return ' ' * self.indent_level * 4 + line

        # Handle variable assignments
        match = re.match(r'(\w+)=(.*)', line)
        if match:
            return self.handle_assignment(line)

        # Handle 'do' and 'done' keywords in loops
        if line in ['do', 'done']:
            return ''

        # Handle 'then', and 'fi' keywords in if statements
        if line in ['then']:
            return ''

        if line in ['fi']:
            self.indent_level -= 1
            return ''        
        
        match = re.match(r'if test (\S+)\s!=\s(\S+)', line)
        if match:
            self.indent_level += 1
            var1 = self.remove_dollar_sign(match.group(1))
            var2 = self.remove_dollar_sign(match.group(2))
            # Check if var2 is a digit
            if match.group(1).startswith('$'):
                return f"if {var1} != {var2}:"
            else:
                return f"if {repr(var1)} != {repr(var2)}:"

        file_test_line = self.handle_file_tests(line)
        if file_test_line is not None:
            self.indent_level += 1
            return file_test_line


        # Handle echo commands
        if line.startswith("echo"):
            rest_of_line = line[4:].strip() 

            # Check if the line has no variable references
            if "$" not in rest_of_line:
                if (rest_of_line.startswith("'") and rest_of_line.endswith("'")) or \
                (rest_of_line.startswith('"') and rest_of_line.endswith('"')):
                    rest_of_line = rest_of_line[1:-1]
                    return ' ' * self.indent_level * 4 + f"print(f'{rest_of_line}')"
                else:
                    words = rest_of_line.split()
                    parsed_words = []
                    for word in words:
                        parsed_words.append(word)
                    return ' ' * self.indent_level * 4 + f"print(f\'{' '.join(parsed_words)}\')"


            # Handle variable references in line with variable references
            else:
                if (rest_of_line.startswith("'") and rest_of_line.endswith("'")) or \
                (rest_of_line.startswith('"') and rest_of_line.endswith('"')):
                    rest_of_line = rest_of_line[1:-1]
                words = rest_of_line.split()
                parsed_words = []
                for word in words:
                    if word.startswith('$'):  # Handle variable references
                        if word[1:].isdigit():  # Check if it's a positional argument
                            self.used_libraries.add('sys')
                            parsed_words.append(f'{{sys.argv[{word[1:]}]}}')
                        else:
                            parsed_words.append(f'{{{word[1:]}}}')  
                    else:
                        parsed_words.append(word)
                return ' ' * self.indent_level * 4 + f"print(f\'{' '.join(parsed_words)}\')"


        # Handle for loops
        match = re.match(r'for (\w+) in (.*)', line)
        if match:
            self.indent_level += 1
            pattern = match.group(2).strip()
            if '*' in pattern or '?' in pattern or '[' in pattern or ']' in pattern:  # If it's a glob pattern
                self.used_libraries.add('glob')
                pattern = "sorted(glob.glob('{}'))".format(pattern)
            else:
                pattern = pattern.split()
            return f"for {match.group(1)} in {pattern}:" 

        # Handle while loops
        match = re.match(r'while (.*)', line)
        if match:
            self.indent_level += 1
            condition = match.group(1)
            condition = condition.replace('test', ' ').strip()
            
            # check if the value in the condition is a string and if so, add quotes around it
            condition_parts = condition.split(' ')
            for i, part in enumerate(condition_parts):
                if not re.match("==|>=|<=|!=", part) and not part.startswith('$'):  
                    condition_parts[i] = f"'{part}'"
                elif part.startswith('$'): 
                    condition_parts[i] = part[1:]

            return f"while {' '.join(condition_parts)}:"

        
        # Handle 'if' conditions
        match = re.match(r'if test (\S+)\s=\s(\S+)', line)
        if match:
            self.indent_level += 1
            var1 = self.remove_dollar_sign(match.group(1))
            var2 = self.remove_dollar_sign(match.group(2))
            # Check if var2 is a digit
            if match.group(1).startswith('$'):
                return f"if {var1} == {var2}:"
            else:
                return f"if {repr(var1)} == {repr(var2)}:"



        # Handle 'elif' conditions
        match = re.match(r'elif test (\S+)\s=\s(\S+)', line)
        if match:
            var1 = self.remove_dollar_sign(match.group(1))
            var2 = self.remove_dollar_sign(match.group(2))
            # Check if var2 is a digit
            if match.group(1).startswith('$'):
                return f"elif {var1} == {var2}:"
            else:
                return f"elif {repr(var1)} == {repr(var2)}:"

        match = re.match(r'elif test (\S+)\s!=\s(\S+)', line)
        if match:
            var1 = self.remove_dollar_sign(match.group(1))
            var2 = self.remove_dollar_sign(match.group(2))
            # Check if var2 is a digit
            if match.group(1).startswith('$'):
                return f"elif {var1} != {var2}:"
            else:
                return f"elif {repr(var1)} != {repr(var2)}:"


        elif line.strip() == 'else':
            return  "else:"

        elif line.strip() == 'fi':
            self.indent_level -= 1
            return ''

        # Handle read commands
        if line.startswith("read"):
            var_name = line.split()[1]
            return ' ' * self.indent_level * 4 + f"{var_name} = input()"

        # Handle cd commands
        if line.startswith("cd"):
            dir_path = line.split()[1]
            self.used_libraries.add('os')
            return ' ' * self.indent_level * 4 + f"os.chdir({repr(dir_path)})"

        # Handle exit commands
        if line.startswith("exit"):
            self.used_libraries.add('sys')
            return ' ' * self.indent_level * 4 + "sys.exit(0)"
        
        
        # Handle globbing
        if '*' in line or '?' in line or '[' in line or ']' in line:
            glob_pattern = line.split('=')[1]
            if '=' in line:
                self.used_libraries.add('glob')
                return ' ' * self.indent_level * 4 + f"glob.glob({repr(glob_pattern)})"
            else:
                self.used_libraries.add('glob')
                return ' ' * self.indent_level * 4 + " ".join(sorted(glob.glob(glob_pattern)))


        # Handle generic commands 
        match = re.match(r'(\w+)( .*)?', line)
        if match:
            if match.group(2) is None:
                self.used_libraries.add('subprocess')
                return ' ' * self.indent_level * 4 + f"subprocess.run({repr(match.group(1))})"
            else:
                command = repr(match.group(1))
                args = match.group(2).split()
                args = [arg.replace('$', '') if '$' in arg else repr(arg) for arg in args]
                all_parts = [command] + args
                self.used_libraries.add('subprocess')
                return ' ' * self.indent_level * 4 + f"subprocess.run([{', '.join(all_parts)}])"


    def transpile(self):
        transpiled_lines = []
        with open(self.shell_script_path, 'r') as file:
            for line in file:
                transpiled_line = self.transpile_line(line)
                if transpiled_line is not None:
                    transpiled_lines.append(transpiled_line)
        
        print("#!/usr/bin/python3 -u")
        for library in self.used_libraries:
            print(f"import {library}")
        
        for line in transpiled_lines:
            print(line)

                


def main():
    transpiler = ShellToPythonTranspiler(sys.argv[1])
    transpiler.transpile()

if __name__ == "__main__":
    main()
