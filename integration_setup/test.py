#!/usr/bin/env python

import unittest
import integration_setup
import os

def count_dir_nonhidden():
    return len(list(filter(lambda d: not d.startswith('.'), os.listdir('.'))))

class ShellTest(unittest.TestCase):

    def test_enqueue_and_run_commands(self):
        # Test pipe and output direction
        shell = integration_setup.Shell()
        shell.enqueue(['ls', '-1', '|', 'wc', '-l', '>', 'dirlist.txt'])
        shell.run_commands(noprompt=True)
        count = count_dir_nonhidden()
        self.assertEqual(count, int(open('dirlist.txt', 'r').read().strip()))
        os.unlink('dirlist.txt')
        # Test str->STDIN
        test_str = 'hello world'
        shell.enqueue(['tee', 'hello.txt'], stdin=test_str)
        shell.run_commands(noprompt=True)
        self.assertEqual(test_str, open('hello.txt', 'r').read())
        os.unlink('hello.txt')


class IntegrationSetupTest(unittest.TestCase):
    pass

if __name__ == '__main__':
    unittest.main()
