
import sublime
import os
import subprocess
import threading
from functools import partial
from sublime_plugin import WindowCommand

class StatusWatcher(object):

	TIME = 50  # 50 ms delay
	OPTS = '-\\|/'

	def __init__(self, thread, msg):
		self.counter = 0
		# self.direction = 1
		self.msg = msg
		self.thread = thread

	def progress(self):
		if not self.thread.is_alive():
			sublime.status_message('')
			return

		status = '[{0}] {1}'.format(self.OPTS[self.counter],self.msg)
		self.counter = (self.counter+1)%len(self.OPTS)
		sublime.status_message(status)
		sublime.set_timeout(self.progress, self.TIME)

	def start(self):
		self.thread.start()
		sublime.set_timeout(self.progress, 0)


class CMDHelper(object):

	verbose = False

	def startupinfo(self):
		startupinfo = None
		if hasattr(subprocess, 'STARTUPINFO'):
			startupinfo = subprocess.STARTUPINFO()
			startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
			startupinfo.wShowWindow = subprocess.SW_HIDE
		return startupinfo

	def cmd_async(self, command, cwd=None, **callbacks):

		def async_inner(cmd, cwd, encoding='utf-8', verbose=False, on_data=None, on_complete=None, on_error=None, on_exception=None):
			try:
				if verbose:
					print('async-cmd: %s', cmd)

				if cwd:
					os.chdir(cwd)

				buf = None if callable(on_data) else []

				proc = subprocess.Popen(cmd,
										stdout=subprocess.PIPE,
										stderr=subprocess.STDOUT,
										startupinfo=self.startupinfo(),
										env=os.environ.copy())

				for line in iter(proc.stdout.readline, b''):
					if verbose:
						print('async-out: %s', line.strip())
					line = line.decode(encoding)
					if callable(on_data):
						sublime.set_timeout(partial(on_data, line), 0)
					else:
						buf.append(line)

				proc.wait()
				if verbose:
					print('async-exit: %s', proc.returncode)
				if proc.returncode == 0:
					if callable(on_complete):
						sublime.set_timeout(partial(on_complete, proc.returncode, buf), 0)
				else:
					if callable(on_error):
						sublime.set_timeout(partial(on_error, proc.returncode, buf), 0)

			except (OSError, UnicodeDecodeError) as e:
				if verbose:
					print('async-exception: %s' % e)
				if callable(on_exception):
					sublime.set_timeout(partial(on_exception, e), 0)


		thread = threading.Thread(target=partial(async_inner, command, cwd, **callbacks))
		return thread

	def cmd_async_with_status(self, cmd, cwd=None, msg='', **callbacks):
		thread = self.cmd_async(cmd, cwd=cwd, **callbacks)
		runner = StatusWatcher(thread, msg)
		runner.start()


class AsyncCmd(CMDHelper):

	status_fmt = ''

	def run_command(self, cmd , cwd=None, data_on_complete=True, state=None):
		self.cmd_async_with_status(
			cmd,
			cwd,
			msg=self.status_fmt.format(cmd,cwd,state),
			on_data=None if data_on_complete else partial(self.on_data, state=state),
			on_complete=partial(self.on_complete, state=state),
			on_error=partial(self.on_error, state=state),
			on_exception=partial(self.on_exception, state=state)
		)

	def handle(self,event,state,*items):
		pass

	def on_data(self,line,state):
		self.handle('data', state, line)

	def on_complete(self,returncode,buf,state):
		self.handle('complete', state, returncode, buf)

	def on_error(self,returncode,buf,state):
		self.handle('error', state, returncode, buf)

	def on_exception(self,e,state):
		self.handle('exception', state, e)


def update_state(state, buf=''):
	s = state['stage']
	o = state['cmds'][s].get('out','_')
	if o!='_':
		state['out'][o] = buf
	state['out']['_'] = buf
	state['stage']+=1


class AsyncMacroCmd(AsyncCmd):

	def on_complete(self, returncode, buf, state):
		if state:
			update_state(state, buf)
			self.window.run_command(state['macro'],args={"state":state})


class AsyncMacro(object):

	@classmethod
	def make_state(cls, macro, cmds, env=None):
		return {
			"stage": 0,
			"out": {'_':''},
			"macro": macro,
			"env": env if isinstance(env,dict) else {},
			"cmds": cmds if isinstance(cmds,list) else [cmds] if isinstance(cmds,dict) else []
		}

	def run_macro(self, state):
		if state['stage'] < len(state['cmds']):
			print('Running Macro')
			print(state)
			cmd = state['cmds'][state['stage']]
			args = state['env'].copy()
			args.update(cmd['args'])
			if cmd.get('is_sync'):
				self.window.run_command(cmd['command'],args=args)
				update_state(state)
				self.window.run_command(state['macro'],args={"state":state})
			else:
				args['state'] = state
				self.window.run_command(cmd['command'],args=args)


class AsyncExecCommand(AsyncMacroCmd,WindowCommand):

	status_fmt = '[{1}]$ {0}'

	def run(self,cmd,**args):
		self.run_command(cmd,**args)


class AsyncMacroCommand(AsyncMacro,WindowCommand):

	def run(self,cmds=None,env=None,macro='async_macro',state=None):
		state = state if isinstance(state,dict) else self.make_state(macro, cmds, env)
		self.run_macro(state)


class SimpleArgsPrinterCommand(WindowCommand):

	def run(self, **args):
		print(args)
		


class TestAsyncMacroCommand(WindowCommand):

	def run(self,**args):
		print('running test')
		self.window.run_command('async_macro',args={"cmds":[
			{"command":"async_exec","args":{'cmd':['ls','/']}},
			{"command":"simple_args_printer","args":{'cmd':'abcd'},'is_sync':True}
		]})
