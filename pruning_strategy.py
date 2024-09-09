from abc import ABC, abstractmethod
from z3 import *

class PruningStrategy(ABC):
    @abstractmethod
    def is_valid_program(self, program, max_mem, max_val):
        pass

class BasicPruningStrategy(PruningStrategy):
    def is_valid_program(self, program, max_mem, max_val):
        # no consecutive LOAD operations
        for i in range(len(program) - 1):
            if program[i][0].__name__ == 'load' and program[i+1][0].__name__ == 'load':
                return False

        # no XOR with itself (always results in 0)
        for instruction in program:
            if instruction[0].__name__ == 'xor' and instruction[1] == instruction[2]:
                return False

        # no SWAP with itself (no op)
        for instruction in program:
            if instruction[0].__name__ == 'swap' and instruction[1] == instruction[2]:
                return False

        # no ops on unused memory locations
        used_memory = set([0])  # first memory location is always used
        for instruction in program:
            if instruction[0].__name__ == 'load':
                used_memory.add(0)
            elif instruction[0].__name__ in ['swap', 'xor']:
                used_memory.update([instruction[1], instruction[2]])
            elif instruction[0].__name__ == 'inc':
                used_memory.add(instruction[1])

        if len(used_memory) < len(set(range(max(used_memory) + 1))):
            return False

        return True

class SMTPruningStrategy(PruningStrategy):
    def __init__(self):
        self.solver = Solver()
        self.state_cache = {}
        self.constraints = []
        self.max_val = None

    def create_symbolic_state(self, max_mem):
        if max_mem not in self.state_cache:
            self.state_cache[max_mem] = [BitVec(f"mem_{i}", 32) for i in range(max_mem)]
        return self.state_cache[max_mem]

    def instruction_to_smt(self, instruction, state):
        op, *args = instruction
        if op.__name__ == 'load':
            value, address = args if len(args) == 2 else (args[0], 0)
            return [If(i == address, value, state[i]) for i in range(len(state))]
        elif op.__name__ == 'swap':
            return [If(i == args[0], state[args[1]],
                       If(i == args[1], state[args[0]], state[i])) for i in range(len(state))]
        elif op.__name__ == 'xor':
            return [If(i == args[0], state[args[0]] ^ state[args[1]], state[i]) for i in range(len(state))]
        elif op.__name__ == 'inc':
            return [If(i == args[0], state[args[0]] + 1, state[i]) for i in range(len(state))]

    def is_valid_program(self, program, max_mem, max_val):
        if self.max_val != max_val:
            self.max_val = max_val
            self.solver.reset()

        state = [BitVec(f"mem_{i}", 32) for i in range(max_mem)]
        self.solver.add([And(s >= 0, s <= max_val) for s in state])

        for op, *args in program:
            if op.__name__ == 'load':
                value, address = args if len(args) == 2 else (args[0], 0)
                self.solver.push()
                self.solver.add(state[address] == value)
                if self.solver.check() == unsat:
                    self.solver.pop()
                    return False
                self.solver.pop()
                state[address] = BitVecVal(value, 32)
            elif op.__name__ == 'swap':
                state[args[0]], state[args[1]] = state[args[1]], state[args[0]]
            elif op.__name__ == 'xor':
                new_val = state[args[0]] ^ state[args[1]]
                self.solver.push()
                self.solver.add(new_val >= 0, new_val <= max_val)
                if self.solver.check() == unsat:
                    self.solver.pop()
                    return False
                self.solver.pop()
                state[args[0]] = new_val
            elif op.__name__ == 'inc':
                new_val = (state[args[0]] + 1) % (max_val + 1)
                state[args[0]] = new_val

        return True

class HeuristicPruningStrategy(PruningStrategy):
    def __init__(self):
        self.max_val = None
        self.max_mem = None

    def is_valid_program(self, program, max_mem, max_val):
        if self.max_val != max_val or self.max_mem != max_mem:
            self.max_val = max_val
            self.max_mem = max_mem

        state = [0] * max_mem
        last_op = None
        last_args = None
        used_memory = set()
        operation_count = {op: 0 for op in ['load', 'swap', 'xor', 'inc']}

        for op, *args in program:
            operation_count[op.__name__] += 1

            # no consecutive identical operations (except INC)
            if op.__name__ == last_op and op.__name__ != 'inc' and args == last_args:
                return False

            # no XOR with itself (always results in 0)
            if op.__name__ == 'xor' and args[0] == args[1]:
                return False

            if op.__name__ == 'swap' and args[0] == args[1]:
                return False

            # limit # of each operation type
            if operation_count[op.__name__] > max_mem:
                return False

            # all memory locations should be used
            if op.__name__ in ['swap', 'xor', 'inc']:
                used_memory.update(args)
            elif op.__name__ == 'load':
                used_memory.add(args[1] if len(args) > 1 else 0)

            if op.__name__ == 'load':
                value, address = args if len(args) == 2 else (args[0], 0)
                if value > max_val:
                    return False
                state[address] = value
            elif op.__name__ == 'swap':
                state[args[0]], state[args[1]] = state[args[1]], state[args[0]]
            elif op.__name__ == 'xor':
                state[args[0]] ^= state[args[1]]
            elif op.__name__ == 'inc':
                state[args[0]] = (state[args[0]] + 1) % (max_val + 1)

            last_op = op.__name__
            last_args = args

        # all memory locations are used
        if len(used_memory) < max_mem:
            return False

        return True