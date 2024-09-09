import unittest
from cpu import CPU
from superoptimizer import Superoptimizer, optimal_from_code, optimal_from_state
import assembler

def test_equivalence(program1, program2, input_range, max_mem, output_size=None):
    cpu = CPU(max_mem)
    for input_value in input_range:
        start_state = [input_value] + [0] * (max_mem - 1)
        output1 = cpu.execute(program1, start_state)
        output2 = cpu.execute(program2, start_state)
        
        if output_size:
            output1 = output1[:output_size]
            output2 = output2[:output_size]
        
        if output1 != output2:
            return False
    return True

class TestSuperoptimizer(unittest.TestCase):
    def test_arbitrary_start_state(self):
        cpu = CPU(4)
        program = assembler.parse("LOAD 3\nSWAP 0, 1\nINC 2")
        start_state = [1, 2, 3, 4]
        result = cpu.execute(program, start_state)
        self.assertEqual(result, [2, 3, 4, 4])

    def test_output_size(self):
        opt = Superoptimizer()
        target_state = [3, 0, 0, 0]
        result = opt.search(3, 4, 3, target_state, start_state=[0, 0, 0, 0], output_size=1)
        self.assertIsNotNone(result)
        self.assertTrue(len(result) <= 2)  # The optimal program should be at most 3 instructions long

    def test_program_equivalence(self):
        program1 = assembler.parse("LOAD 1\nINC 0\nINC 0")
        program2 = assembler.parse("LOAD 3")
        are_equivalent = test_equivalence(program1, program2, range(1, 10), 3, output_size=1)
        self.assertTrue(are_equivalent)

    def test_optimal_from_code(self):
        assembly = """
        LOAD 3
        SWAP 0, 1
        LOAD 3
        SWAP 0, 2
        """
        result = optimal_from_code(assembly, 3, 3, 5, start_state=[1, 2, 3], output_size=2)
        self.assertIsNotNone(result, "No optimal program found")
        cpu = CPU(3)
        final_state = cpu.execute(result, [1, 2, 3])
        self.assertEqual(final_state[:2], [3, 3], f"Expected [3, 3], but got {final_state[:2]}")
        self.assertTrue(len(result) <= 3, f"Expected program length <= 3, but got {len(result)}")

    def test_optimal_from_state(self):
        target_state = [3, 3, 0]
        result = optimal_from_state(target_state, 3, 5, start_state=[1, 2, 3], output_size=2)
        self.assertIsNotNone(result)
        cpu = CPU(3)
        final_state = cpu.execute(result, [1, 2, 3])
        self.assertEqual(final_state[:2], [3, 3])

if __name__ == '__main__':
    unittest.main()