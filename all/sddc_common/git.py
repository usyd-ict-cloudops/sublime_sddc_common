
from sublime_plugin import WindowCommand
from .async import AsyncMacroCmd, AsyncMacro


class AsyncGitCloneCommand(AsyncMacroCmd,WindowCommand):

	status_fmt = 'Cloning {0[2]} into {0[3]}'

	def run(self, repourl, target_dir, **kwargs):
		self.run_command(['git','clone',repourl,target_dir], **kwargs)


class AsyncGitCommand(AsyncMacroCmd,WindowCommand):

	status_fmt = '[{1}] {0[2]} into {0[3]}'

	def run(self, cmd, repo, **kwargs):
		self.run_command(['git']+cmd, repo, **kwargs)


class AsyncGitAddCommitPush(AsyncMacro,WindowCommand):
	def run(self, msg, repo, all_files=True, include_untracked=True, state=None):
		if state is None:
			if msg is None:
				return
			if repo is None:
				return
			cmds = []
			flags = '-m'
			if all_files:
				if include_untracked:
					cmds.append({"command":"async_git","args":{'cmd':['add','.']}})
				else:
					flags = '-am'
			else:
				fn = self.window.active_view().file_name()
				if not fn:
					return
				cmds.append({"command":"async_git","args":{'cmd':['add',fn]}})
			cmds.append({"command":"async_git","args":{'cmd':['commit',flags,msg]}})
			cmds.append({"command":"async_git","args":{'cmd':['push','-c','push.default=upstream','origin']}})
			state = self.make_state('async_git_add_commit_push', cmds , {"repo":repo})
		self.run_macro(state)


class AsyncGitSwitch(AsyncMacro,WindowCommand):
	def run(self, branch=None, repo=None, include_untracked=False, state=None):
		if state is None:
			if branch is None:
				return
			if repo is None:
				return
			cmds = []
			if include_untracked:
				cmds.append({"command":"async_git","args":{'cmd':['add','.']}})
			else:
				flags = '-am'
			else:
				fn = self.window.active_view().file_name()
				if not fn:
					return
				cmds.append({"command":"async_git","args":{'cmd':['add',fn]}})
			cmds.append({"command":"async_git","args":{'cmd':['commit',flags,msg]}})
			cmds.append({"command":"async_git","args":{'cmd':['push','-c','push.default=upstream','origin']}})
			state = self.make_state('async_git_add_commit_push', cmds , {"repo":repo})
		self.run_macro(state)
