import os
import sys
import unittest

def additional_tests():
    setup_file = sys.modules['__main__'].__file__
    setup_dir = os.path.abspath(os.path.dirname(setup_file))
    print("\n***Looking for tests in %s\n" % setup_dir)
    return unittest.defaultTestLoader.discover(setup_dir, top_level_dir=setup_dir)
