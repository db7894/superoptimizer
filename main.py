import unittest
import sys

if __name__ == "__main__":
    test_suite = sys.argv[1] if len(sys.argv) > 1 else "all"

    if test_suite == "all" or test_suite == "superoptimizer":
        print("Running Superoptimizer tests:")
        from test.test_superoptimizer import TestSuperoptimizer
        suite = unittest.TestLoader().loadTestsFromTestCase(TestSuperoptimizer)
        unittest.TextTestRunner(verbosity=2).run(suite)
        print("\n")

    if test_suite == "all" or test_suite == "pruning":
        print("Running Pruning Strategy tests:")
        from test.test_pruning_strategies import TestPruningStrategies
        suite = unittest.TestLoader().loadTestsFromTestCase(TestPruningStrategies)
        unittest.TextTestRunner(verbosity=2).run(suite)
        print("\n")

    if test_suite not in ["all", "superoptimizer", "pruning"]:
        print(f"Unknown test suite: {test_suite}")
        print("Usage: python main.py [all|superoptimizer|pruning]")