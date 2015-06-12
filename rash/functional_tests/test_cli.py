# Copyright (C) 2013-  Takafumi Arakaki

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.


import os
import sys
import subprocess
import unittest
import tempfile
import shutil
import textwrap
import json
import time

from ..utils.py3compat import PY3
from ..config import ConfigStore
from ..tests.utils import BaseTestCase, skipIf

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

    """
    MixIn class for isolating functional test environment.

    SOMEDAY: Make FunctionalTestMixIn work in non-*nix systems.
    (I think) This isolation does not work in Mac OS in Windows!
    I can workaround this by adding --config-dir global
    option to specify configuration directory from
    command line, rather than using $HOME.

    """

    def setUp(self):
        self.home_dir = tempfile.mkdtemp(prefix='rash-test-')
        self.config_dir = os.path.join(self.home_dir, '.config')
        self.conf_base_path = os.path.join(self.config_dir, 'rash')

        self.environ = os.environ.copy()
        self.environ['HOME'] = self.home_dir
        # FIXME: run the test w/o $TERM
        self.environ['TERM'] = 'xterm-256color'
        # Make sure that $XDG_CONFIG_HOME does not confuse sub processes
        if 'XDG_CONFIG_HOME' in self.environ:
            del self.environ['XDG_CONFIG_HOME']

        self.cfstore = ConfigStore(self.conf_base_path)

    def tearDown(self):
        # Kill daemon if exists
        try:
            if os.path.exists(self.cfstore.daemon_pid_path):
                with open(self.cfstore.daemon_pid_path) as f:
                    pid = f.read().strip()
                print("Daemon (PID={0}) may be left alive.  Killing it..."
                      .format(pid))
                subprocess.call(['kill', pid])
        except Exception as e:
            print("Got error while trying to kill daemon: {0}"
                  .format(e))

        try:
            shutil.rmtree(self.home_dir)
        except OSError:
            print("Failed to remove self.home_dir={0}. "
                  "Can be timing issue.  Trying again..."
                  .format(self.home_dir))
            time.sleep(0.1)
            shutil.rmtree(self.home_dir)

    def popen(self, *args, **kwds):
        if 'env' in kwds:
            raise RuntimeError('Do not use env!')
        if 'cwd' in kwds:
            raise RuntimeError('Do not use cwd!')
        kwds['env'] = self.environ
        kwds['cwd'] = self.home_dir
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
        cfstore = ConfigStore()
        print(repr(cfstore.base_path))
        """).encode())
        stderr = stderr.decode()
        stdout = stdout.decode()
        base_path = eval(stdout)
        self.assertEqual(base_path, self.conf_base_path)
        self.assertFalse(stderr)
        self.assertNotEqual(base_path, ConfigStore().base_path)


class ShellTestMixIn(FunctionalTestMixIn):

    shell = 'sh'
    eval_command = 'eval'

    def run_shell(self, script):
        proc = self.popen(
            [self.shell],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE)
        (stdout, stderr) = proc.communicate(script.encode())
        return (stdout.decode(), stderr.decode())

    def get_record_data(self, record_type):
        top = os.path.join(self.cfstore.record_path, record_type)
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

    def _get_init_script(self, no_daemon=True, daemon_options=[],
                        daemon_outfile=None):
        options = []
        if no_daemon:
            options.append('--no-daemon')
        options.extend(map('--daemon-opt={0}'.format, daemon_options))
        if daemon_outfile:
            options.extend(['--daemon-outfile', daemon_outfile])
        optstr = ' '.join(options)
        return "{0} $({1} init --shell {2} {3})".format(
            self.eval_command, BASE_COMMAND, self.shell, optstr)

    def get_script(self, script='', **kwds):
        init_script = self._get_init_script(**kwds)
        return '\n'.join([init_script, textwrap.dedent(script)])

    def test_init(self):
        script = self.get_script("""
        test -n "$_RASH_SESSION_ID" && echo "_RASH_SESSION_ID is defined"
        """)
        (stdout, stderr) = self.run_shell(script)
        self.assertFalse(stderr)
        self.assertIn('_RASH_SESSION_ID is defined', stdout)

        assert os.path.isdir(self.cfstore.record_path)
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
        script = self.get_script(self.test_postexec_script)
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

    def test_exit_code(self):
        script = self.get_script(self.test_exit_code_script)
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

        command_data = [d['data'] for d in records['command']]
        self.assertEqual(command_data[0]['exit_code'], 1)

    test_exit_code_script = None
    """Set this to a shell script for :meth:`test_exit_code`."""

    def test_pipe_status(self):
        script = self.get_script(self.test_pipe_status_script)
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

        command_data = [d['data'] for d in records['command']]
        self.assertEqual(command_data[0]['pipestatus'], [1, 0])

    test_pipe_status_script = None
    """Set this to a shell script for :meth:`test_pipe_status`."""

    def test_non_existing_directory(self):
        main_script = """
        _rash-precmd
        mkdir non_existing_directory

        _rash-precmd
        cd non_existing_directory

        _rash-precmd
        rmdir ../non_existing_directory

        _rash-precmd
        :

        _rash-precmd
        cd ..
        """
        script = self.get_script(main_script)
        (stdout, stderr) = self.run_shell(script)
        self.assertNotIn('Traceback', stderr)

    @skipIf(PY3, "watchdog does not support Python 3")
    def test_daemon(self):
        daemon_outfile = os.path.join(self.cfstore.base_path, 'daemon.out')
        script = self.get_script(
            no_daemon=False, daemon_outfile=daemon_outfile,
            daemon_options=['--keep-json', '--log-level=DEBUG'])
        (stdout, stderr) = self.run_shell(script)

        # These are useful when debugging, so let's leave them:
        print(stderr)
        print(stdout)
        print(self.cfstore.daemon_pid_path)

        # Print daemon process output for debugging
        with open(daemon_outfile) as f:
            daemon_output = f.read().strip()
            if daemon_output:
                print("Daemon process output ({0})".format(daemon_outfile))
                print(daemon_output.decode())

        # The daemon process should create a PID file containing a number
        @self.assert_poll_do(
            "Daemon did not produce PID file at: {0}"
            .format(self.cfstore.daemon_pid_path))
        def pid_file_contains_a_number():
            try:
                with open(self.cfstore.daemon_pid_path) as f:
                    return f.read().strip().isdigit()
            except IOError:
                return False

        # Read the PID file
        with open(self.cfstore.daemon_pid_path) as f:
            pid = int(f.read().strip())

        # The daemon process should be alive
        ps_pid_cmd = ['ps', '--pid', str(pid)]
        try:
            run_command(ps_pid_cmd)
        except subprocess.CalledProcessError:
            raise AssertionError(
                'At this point, daemon process should be live '
                '("ps --pid {0}" failed).'.format(pid))

        # The daemon should create a log file
        self.assert_poll(lambda: os.path.exists(self.cfstore.daemon_log_path),
                         "daemon_log_path={0!r} is not created on time"
                         .format(self.cfstore.daemon_log_path))

        # The daemon should write some debug message to the log file
        # (Note: --log-level=DEBUG is given by $RASH_INIT_DAEMON_OPTIONS)
        with open(self.cfstore.daemon_log_path) as f:
            @self.assert_poll_do("Nothing written in log file.")
            def log_file_written():
                return f.read().strip()

        # Kill command should succeeds
        run_command(['kill', '-TERM', str(pid)])

        # The daemon should be killed by the TERM signal
        @self.assert_poll_do(
            "Daemon process {0} failed to exit.".format(pid))
        def terminated():
            try:
                run_command(ps_pid_cmd)
                return False
            except subprocess.CalledProcessError:
                return True

        # The daemon should remove the PID file on exit
        self.assert_poll(
            lambda: not os.path.exists(self.cfstore.daemon_pid_path),
            "Daemon did not remove PID file at: {0}".format(
                self.cfstore.daemon_pid_path))

    @staticmethod
    def assert_poll(assertion, message, num=100, tick=0.1):
        """
        Run `assersion` every `tick` second `num` times.

        If none of `assersion` call returns true, it raise
        an assertion error with `message`.

        """
        for i in range(num):
            if assertion():
                break
            time.sleep(tick)
        else:
            raise AssertionError(message)

    @classmethod
    def assert_poll_do(cls, message, *args, **kwds):
        """
        Decorator to run :meth:`assert_poll` right after the definition.
        """
        def decorator(assertion):
            cls.assert_poll(assertion, message, *args, **kwds)
            return assertion
        return decorator


class TestZsh(ShellTestMixIn, BaseTestCase):
    shell = 'zsh'
    test_postexec_script = """
    _rash-precmd
    """
    test_exit_code_script = """
    false
    _rash-precmd
    """
    test_pipe_status_script = """
    false | true
    _rash-precmd
    """

    def test_zsh_executes_preexec(self):
        script = self.get_script('echo _RASH_EXECUTING=$_RASH_EXECUTING')
        (stdout, stderr) = self.run_shell(script)
        self.assertFalse(stderr)
        self.assertIn('_RASH_EXECUTING=t', stdout)

    def test_hook_installation(self):
        script = self.get_script("""
        echo $precmd_functions
        echo $preexec_functions
        """)
        (stdout, stderr) = self.run_shell(script)
        self.assertIn('_rash-precmd', stdout)
        self.assertIn('_rash-preexec', stdout)


class TestBash(ShellTestMixIn, BaseTestCase):
    shell = 'bash'
    test_postexec_script = """
    eval "$PROMPT_COMMAND"
    eval "$PROMPT_COMMAND"
    """
    test_exit_code_script = """
    eval "$PROMPT_COMMAND"
    false
    eval "$PROMPT_COMMAND"
    """
    test_pipe_status_script = """
    eval "$PROMPT_COMMAND"
    false | true
    eval "$PROMPT_COMMAND"
    """

    def test_hook_installation(self):
        script = self.get_script('echo $PROMPT_COMMAND')
        (stdout, stderr) = self.run_shell(script)
        self.assertIn('_rash-precmd', stdout)
