from itertools import product
from cpu import CPU
from pruning_strategy import BasicPruningStrategy, SMTPruningStrategy
import assembler

# Helper function that finds the optimal code given the assembly code.
def optimal_from_code(assembly, max_length, max_mem, max_val, start_state=None, output_size=None, debug=False):
    cpu = CPU(max_mem)
    program = assembler.parse(assembly)

    if debug:
        print(f"***Assembly***\n{assembly}\n")
        print(f"Parsed program: {program}")
    
    # Execute the program on a copy of the start state
    if start_state:
        temp_state = start_state.copy()
    else:
        temp_state = [0] * max_mem

    if debug:
        print(f"Initial temp_state: {temp_state}")
    
    target_state = cpu.execute(program, temp_state)
    
    if debug:
        print(f"***Source***{assembly}")
        print(f"***Target State***\n{target_state}\n")
        print(f"***Start State***\n{start_state}\n")
    return optimal_from_state(target_state, max_length, max_val, start_state, output_size, debug)

# Helper function that finds the optimal code given the goal state.
def optimal_from_state(target_state, max_length, max_val, start_state=None, output_size=None, debug=False):
    max_mem = len(target_state)
    if debug:
        print(f"***Target State***\n{target_state}\n") 
        if start_state:
            print(f"*** Start State***\n{start_state}\n")
    opt = Superoptimizer()
    shortest_program = opt.search(max_length, max_mem, max_val, target_state, start_state, output_size, debug)
    if shortest_program is not None:
        disassembly = assembler.output(shortest_program)
        if debug:
            print(f"***Optimal***\n{disassembly}\n{'='*20}\n")
    else:
        print("No solution found")
    return shortest_program

class Superoptimizer:
    def __init__(self, pruning_strategy=BasicPruningStrategy()):
        self.program_cache = {}
        self.pruning_strategy = pruning_strategy

    # Generates all possible programs.
    def generate_programs(self, cpu, max_length, max_mem, max_val):
        for length in range(1, max_length + 1):
            for prog in product(cpu.ops.values(), repeat=length):
                arg_sets = []
                for op in prog:
                    if op == cpu.load:
                        arg_sets.append([tuple([val]) for val in range(max_val + 1)])
                    elif op == cpu.swap or op == cpu.xor: 
                        arg_sets.append(product(range(max_mem), repeat=2))
                    elif op == cpu.inc:
                        arg_sets.append([tuple([val]) for val in range(max_mem)])
                for arg_set in product(*arg_sets):
                    program = [(op, *args) for op, args in zip(prog, arg_set)]
                    if self.pruning_strategy is None or self.pruning_strategy.is_valid_program(program, max_mem, max_val):
                        yield program

    # Tests all of the generated programs and returns the shortest.
    def search(self, max_length, max_mem, max_val, target_state, start_state=None, output_size=None, debug=False): 
        cpu = CPU(max_mem)

        initial_state = cpu.execute([], start_state)
        if output_size:
            initial_state = initial_state[:output_size]
            target = target_state[:output_size]
        else:
            target = target_state
    
        if initial_state == target:
            return []  # Empty program, as start state already matches target

        count = 0
        for program in self.generate_programs(cpu, max_length, max_mem, max_val):
            state = cpu.execute(program, start_state)

            if output_size:
                state = state[:output_size]
                target = target_state[:output_size]
            else:
                target = target_state

            if state == target:
                if debug:
                    print(f"Solution found: {program}")
                state_key = tuple(state) 
                if state_key not in self.program_cache or len(program) < len(self.program_cache[state_key]):
                    self.program_cache[state_key] = program

            if debug:
                print(f"Tried program: {program}, resulted in state: {state}")

            # Debugging.
            if debug:
                count += 1
                if count % 10000 == 0:
                    print(f"Tried {count} programs. Last program: {assembler.output(program)}, resulted in state: {state}")
                if count % 1000000 == 0: 
                    print(f"Programs searched: {count:,}")
                if count % 10000000 == 0: 
                    solution = self.program_cache.get(tuple(target), None)
                    print(f"Best solution: {solution}")

        return self.program_cache.get(tuple(target), None)
