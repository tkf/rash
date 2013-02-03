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

    def get_record_data(self, record_type):
        top = os.path.join(self.conf.record_path, record_type)
        for (root, _, files) in os.walk(top):
            for f in files:
                path = os.path.join(root, f)
                with open(path) as f:
                    data = json.load(f)
                yield dict(path=path, data=data)

    def get_all_record_data(self):
        return dict(
            init=list(self.get_record_data('init')),
            exit=list(self.get_record_data('exit')),
            command=list(self.get_record_data('command')),
        )

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
        records = self.get_all_record_data()
        self.assertEqual(len(records['init']), 1)
        self.assertEqual(len(records['exit']), 1)
        self.assertEqual(len(records['command']), 0)

        from ..record import get_environ
        subenv = get_environ(['HOST'])

        data = records['init'][0]['data']
        assert 'start' in data
        assert 'stop' not in data
        self.assertEqual(data['environ']['HOST'], subenv['HOST'])
        init_id = data['session_id']

        data = records['exit'][0]['data']
        assert 'start' not in data
        assert 'stop' in data
        assert not data['environ']
        exit_id = data['session_id']

        self.assertEqual(init_id, exit_id)

    def test_postexec(self):
        script = textwrap.dedent("""
        {0} $({1} init --shell {2})
        {3}
        """).format(
            self.source_command, BASE_COMMAND, self.shell,
            self.test_postexec_script).encode()
        (stdout, stderr) = self.run_shell(script)

        # stderr may have some errors in it
        if stderr:
            print("Got STDERR from {0} (but it's OK to ignore it)"
                  .format(self.shell))
            print(stderr)

        records = self.get_all_record_data()
        self.assertEqual(len(records['init']), 1)
        self.assertEqual(len(records['exit']), 1)
        self.assertEqual(len(records['command']), 1)

        init_data = records['init'][0]['data']
        command_data = records['command'][0]['data']
        assert command_data['session_id'] == init_data['session_id']
        assert command_data['environ']['PATH']
        assert isinstance(command_data['stop'], int)
        if self.shell.endswith('zsh'):
            assert isinstance(command_data['start'], int)
        else:
            assert 'start' not in command_data

    test_postexec_script = None
    """Set this to a shell script for :meth:`test_postexc`."""


class TestZsh(ShellTestMixIn, BaseTestCase):
    shell = 'zsh'
    test_postexec_script = textwrap.dedent("""\
    rash-precmd
    """)

    def test_hook_installation(self):
        script = textwrap.dedent("""
        {0} $({1} init --shell {2})
        echo $precmd_functions
        echo $preexec_functions
        """).format(
            self.source_command, BASE_COMMAND, self.shell).encode()
        (stdout, stderr) = self.run_shell(script)
        self.assertIn('rash-precmd', stdout.decode())
        self.assertIn('rash-preexec', stdout.decode())


class TestBash(ShellTestMixIn, BaseTestCase):
    shell = 'bash'
    test_postexec_script = textwrap.dedent("""\
    rash-precmd
    rash-precmd
    """)

    def test_hook_installation(self):
        script = textwrap.dedent("""
        {0} $({1} init --shell {2})
        echo $PROMPT_COMMAND
        """).format(
            self.source_command, BASE_COMMAND, self.shell).encode()
        (stdout, stderr) = self.run_shell(script)
        self.assertIn('rash-precmd', stdout.decode())
