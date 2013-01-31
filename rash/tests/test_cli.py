import os
import subprocess
import unittest

BASE_COMMAND = 'rash'

try:
    run_command = subprocess.check_output
except AttributeError:

    def run_command(*args, **kwds):
        assert 'stdout' not in kwds
        with open(os.devnull, 'w') as devnull:
            kwds['stdout'] = devnull
            subprocess.check_call(*args, **kwds)


def run_cli(command, *args, **kwds):
    run_command([BASE_COMMAND] + command, *args, **kwds)


class TestCLI(unittest.TestCase):

    def test_command_init_known_shell(self):
        run_cli(['init', '--shell', 'zsh'])

    def test_command_init_unknown_shell(self):
        self.assertRaises(
            subprocess.CalledProcessError,
            run_cli,
            ['init', '--shell', 'UNKNOWN_SHELL'], stderr=subprocess.PIPE)
