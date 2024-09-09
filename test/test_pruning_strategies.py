import unittest
from pruning_strategy import BasicPruningStrategy, SMTPruningStrategy, HeuristicPruningStrategy
from cpu import CPU
import time
import signal
from superoptimizer import Superoptimizer

class TimeoutException(Exception):
    pass

def timeout_handler(signum, frame):
    raise TimeoutException("Function call timed out")

def verify_solution(cpu, program, start_state, target_state):
    result_state = cpu.execute(program, start_state.copy())
    return result_state == target_state

class TestPruningStrategies(unittest.TestCase):
    def setUp(self):
        self.basic_strategy = BasicPruningStrategy()
        self.smt_strategy = SMTPruningStrategy()

    def test_basic_pruning_consecutive_loads(self):
        program = [(CPU.load, 1), (CPU.load, 2)]
        self.assertFalse(self.basic_strategy.is_valid_program(program, 3, 5))

    def test_basic_pruning_xor_with_itself(self):
        program = [(CPU.xor, 0, 0)]
        self.assertFalse(self.basic_strategy.is_valid_program(program, 3, 5))

    def test_basic_pruning_swap_with_itself(self):
        program = [(CPU.swap, 1, 1)]
        self.assertFalse(self.basic_strategy.is_valid_program(program, 3, 5))

    def test_basic_pruning_unused_memory(self):
        program = [(CPU.load, 1), (CPU.swap, 0, 2)]
        self.assertFalse(self.basic_strategy.is_valid_program(program, 3, 5))

    def test_smt_pruning(self):
        program = [(CPU.load, 1), (CPU.inc, 0), (CPU.inc, 0)]
        self.assertTrue(self.smt_strategy.is_valid_program(program, 3, 5))
        
        invalid_program = [(CPU.load, 6)]
        self.assertFalse(self.smt_strategy.is_valid_program(invalid_program, 3, 5))

    def test_pruning_performance(self):
        target_state = [2, 1, 0]
        start_state = [0, 1, 2]
        max_length = 3
        max_mem = 3
        max_val = 5
        timeout = 10

        results = {}
        cpu = CPU(max_mem)
        
        for pruning_strategy, name in [
            (None, "No pruning"),
            (BasicPruningStrategy(), "Basic pruning"),
            # (SMTPruningStrategy(), "SMT pruning"),
            (HeuristicPruningStrategy(), "Heuristic pruning")
        ]:
            signal.signal(signal.SIGALRM, timeout_handler)
            signal.alarm(timeout)
            
            try:
                start_time = time.time()
                opt = Superoptimizer(pruning_strategy)
                result = opt.search(max_length, max_mem, max_val, target_state, start_state)
                end_time = time.time()
                
                results[name] = {
                    "time": end_time - start_time,
                    "result": result
                }
                
                if result is None:
                    print(f"{name}: No solution found in {results[name]['time']:.2f}s")
                else:
                    print(f"{name}: Solution found in {results[name]['time']:.2f}s")
                    print(f"Solution: {result}")
                    if verify_solution(cpu, result, start_state, target_state):
                        print("Solution verified correct")
                    else:
                        print("WARNING: Solution is incorrect!")
                
            except TimeoutException:
                print(f"{name}: Timed out after {timeout} seconds")
                results[name] = {"time": timeout, "result": None}
            finally:
                signal.alarm(0)

        valid_results = [r["result"] for r in results.values() if r["result"] is not None]
        if valid_results:
            if all(r == valid_results[0] for r in valid_results):
                print("All strategies that found a solution produced the same result.")
            else:
                print("Warning: Pruning strategies produced different results:")
                for name, result in results.items():
                    if result["result"] is not None:
                        print(f"{name}: {result['result']}")
        else:
            print("Warning: No strategy found a solution within the time limit")
