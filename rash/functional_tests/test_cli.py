import os
import sys
import subprocess
import unittest
import tempfile
import shutil
import textwrap
import json

from ..utils.py3compat import getcwd
from ..config import ConfigStore
from ..tests.utils import BaseTestCase

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


class FunctionalTestMixIn(object):

    def setUp(self):
        self.home_dir = tempfile.mkdtemp(prefix='rash-test-')
        self.config_dir = os.path.join(self.home_dir, '.config')
        self.conf_base_path = os.path.join(self.config_dir, 'rash')
        self.__orig_cwd = getcwd()
        os.chdir(self.home_dir)

        self.environ = os.environ.copy()
        self.environ['HOME'] = self.home_dir
        self.conf = ConfigStore(self.conf_base_path)

    def tearDown(self):
        os.chdir(self.__orig_cwd)
        shutil.rmtree(self.home_dir)

    def popen(self, *args, **kwds):
        if 'env' in kwds:
            raise RuntimeError('Do not use env!')
        kwds['env'] = self.environ
        return subprocess.Popen(*args, **kwds)


class TestIsolation(FunctionalTestMixIn, BaseTestCase):

    """
    Make sure that test environment is isolated from the real one.
    """

    def test_config_isolation(self):
        proc = self.popen(
            [os.path.abspath(sys.executable)],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE)
        (stdout, stderr) = proc.communicate(textwrap.dedent("""
        from rash.config import ConfigStore
        conf = ConfigStore()
        print(repr(conf.base_path))
        """).encode())
        base_path = eval(stdout)
        self.assertEqual(base_path, self.conf_base_path)
        self.assertFalse(stderr)
        self.assertNotEqual(base_path, ConfigStore().base_path)


class ShellTestMixIn(FunctionalTestMixIn):

    shell = 'sh'
    source_command = '.'

    def run_shell(self, script):
        proc = self.popen(
            [self.shell],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE)
        return proc.communicate(script)

    def test_init(self):
        script = textwrap.dedent("""
        {0} $({1} init --shell {2})
        test -n "$_RASH_SESSION_ID" && echo "_RASH_SESSION_ID is defined"
        """).format(
            self.source_command, BASE_COMMAND, self.shell).encode()
        (stdout, stderr) = self.run_shell(script)
        self.assertFalse(stderr)
        self.assertIn('_RASH_SESSION_ID is defined', stdout.decode())

        assert os.path.isdir(self.conf.record_path)

        records = []
        for (root, _, files) in os.walk(self.conf.record_path):
            records.extend(os.path.join(root, f) for f in files)
        assert len(records) == 2

        from ..record import get_environ
        subenv = get_environ(['HOST'])
        for path in records:
            with open(path) as f:
                data = json.load(f)

            if 'init' in path:
                assert 'start' in data
                assert 'stop' not in data
                self.assertEqual(data['environ']['HOST'], subenv['HOST'])
            elif 'exit' in path:
                assert 'start' not in data
                assert 'stop' in data
                assert not data['environ']
            else:
                raise AssertionError(
                    "Not init or exit type record: {0}".format(path))


class TestZsh(ShellTestMixIn, BaseTestCase):
    shell = 'zsh'
