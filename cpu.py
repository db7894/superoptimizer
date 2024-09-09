class CPU:
    def __init__(self, max_mem_cells):
        self.max_mem_cells = max_mem_cells
        self.state = [0] * max_mem_cells
        self.ops = {'LOAD': self.load, 'SWAP': self.swap, 'XOR': self.xor, 'INC': self.inc}

    def execute(self, program, start_state=None, debug=False):
        if start_state:
            state = start_state[:self.max_mem_cells] + [0] * (self.max_mem_cells - len(start_state))
        else:
            state = [0] * self.max_mem_cells

        if debug:
            print(f"Initial state: {state}")
        for instruction in program:
            op = instruction[0]
            args = list(instruction[1:])
            args.insert(0, state)
            state = op(*args)
            if debug:
                print(f"After {op.__name__}{args[1:]}: {state}")
        return state

    def load(self, state, val, mem=0):
        state[mem] = val
        return state
    
    def swap(self, state, mem1, mem2):
        state[mem1], state[mem2] = state[mem2], state[mem1]
        return state
    
    def xor(self, state, mem1, mem2):
        state[mem1] = state[mem1] ^ state[mem2]
        return state
    
    def inc(self, state, mem):
        state[mem] += 1
        return state