import os.path as osp
from .workflow import scm, switch_to
from sublime_plugin import WindowCommand


class GitSwitchCommand(scm.RepoHelper, WindowCommand):

    def run(self, branch=None):
        repo = self.repo
        if not repo:
            return

        repo_path = repo.working_dir

        branches = sorted(scm.branches(repo),key=lambda b:(1-b.is_local,b.is_published,b.name))

        if branch and any(b.name==branch for b in branches if b.name!=repo.head.ref.name):
            switch_to(repo, branch)
        elif branch is None:
            items = scm.get_branch_items(branches,repo.head.ref.name)
            func = partial(self.on_select,repo_path=repo_path)
            self.window.show_quick_panel(items, func, sublime.MONOSPACE_FONT)

    def on_select(self, idx, repo_path=None):
        if not repo_path:
            return

        repo = scm.Repo(repo_path)
        if not repo:
            return

        branches = sorted(scm.branches(repo),key=lambda b:(1-b.is_local,b.is_published,b.name))

        if 0 <= idx < len(branches):
            branch = branches[idx]
            if branch.name != repo.head.ref.name:
                switch_to(repo, branch.name)
