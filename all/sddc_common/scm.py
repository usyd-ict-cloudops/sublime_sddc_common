from __future__ import absolute_import
import os
from collections import namedtuple
from operator import attrgetter

from git import Repo as _repo
from git.exc import GitCommandError,  InvalidGitRepositoryError

forbidden_branches = ['HEAD',]

STASH_TEMPLATE = 'Legit: stashing before {0}.'

git = os.environ.get("GIT_PYTHON_GIT_EXECUTABLE", 'git')

Branch = namedtuple('Branch', ['name', 'is_published','is_local'])

gname = attrgetter('name')
del_remote = lambda n:n.split('/',1)[-1]


class SCMFailure(Exception):
    """docstring for SCMFailure"""
    def __init__(self, msg, log=None):
        super(SCMFailure, self).__init__("{0}\n{1}".format(msg,log) if log else msg)

class MergeFailure(SCMFailure):
    """Merge Failure has occurred"""

class RemoteFailure(SCMFailure):
    """Error with remote repo"""

class FetchFailure(RemoteFailure):
    """Could not fetch from remote"""

class PushFailure(RemoteFailure):
    """Push Failure has occurred"""

class CloneFailure(RemoteFailure):
    """Clone Failure has occurred"""


def handle_abort(aborted, type=None):
    print('{0} {1}'.format('Error:', aborted.message))
    print(str(aborted.log))
    if type == 'merge':
        print('Unfortunately, there was a merge conflict.'
              ' It has to be merged manually.')
    elif type == 'unpublish':
        print('It seems that the remote branch has been already deleted.')

abort_handler = handle_abort

class Aborted(object):

    def __init__(self):
        self.message = None
        self.log = None


def abort(message, log=None, type=None):

    a = Aborted()
    a.message = message
    a.log = log

    abort_handler(a, type=type)


def get_git_config():
    try:
        if repo:
            cfg = repo.config_reader()
        else:
            cfg = git.GitConfigParser([os.path.normpath(os.path.expanduser("~/.gitconfig"))], read_only=True)
        try:
            name = cfg.get_value('user','name')
        except:
            name = None
        try:
            email = cfg.get_value('user','email')
        except:
            email = None
        return name, email
    except:
        return None


def set_git_config(name,email):
    cfg = git.GitConfigParser([os.path.normpath(os.path.expanduser("~/.gitconfig"))], read_only=False)
    cfg.set_value('user','name',name)
    cfg.set_value('user','email',email)


def repo_check(repo, require_remote=False):
    if repo is None:
        raise TypeError('Not a git repository.')

    # TODO: no remote fail
    if not repo.remotes and require_remote:
        raise ValueError('No git remotes configured. Please add one.')

    # TODO: You're in a merge state.
    return repo


def get_current_branch_name(repo):
    """Returns current branch name"""

    repo_check(repo)

    return repo.head.ref.name


def clone_from(repourl, targetdir):
    try:
        return _repo.clone_from(repourl, targetdir)
    except (GitCommandError,) as e:
        raise CloneFailure('Cloning {0} failed'.format(repourl),e)


def Repo(path):
    """Returns the current Repo, based on path."""

    try:
        return _repo(path, search_parent_directories=True)
    except InvalidGitRepositoryError:
        pass


# def get_remote(repo):

#     repo_check(repo, require_remote=True)

#     reader = repo.config_reader()

#     # If there is no remote option in legit section, return default
#     if not reader.has_option('legit', 'remote'):
#         return repo.remotes[0]

#     remote_name = reader.get('legit', 'remote')
#     if not remote_name in [r.name for r in repo.remotes]:
#         raise ValueError('Remote "{0}" does not exist! Please update your git '
#                          'configuration.'.format(remote_name))

#     return repo.remote(remote_name)


def branch_name(repo):
    """Gets current branch name"""

    repo_check(repo)

    return repo.head.ref.name


def branches(repo, local=True, remote=True, excl=forbidden_branches):
    """Returns a list of local and remote branches."""

    repo_check(repo)

    r = [n for n in map(del_remote,map(gname,repo.remote().refs)) if n not in excl] if remote and repo.remotes else []

    l = [n for n in map(gname,repo.heads) if n not in excl] if local else []

    return [Branch(n, is_published=n in r, is_local=n in l) for n in sorted(set(r+l))]


def branch_names(repo, local=True, remote=True, excl=forbidden_branches):
    """Returns a list of local and remote branch names."""

    return [b.name for b in branches(repo, local=local, remote=remote, excl=excl)]


def get_branch(repo, branch=None, local=True, remote=True, excl=forbidden_branches):
    """Returns a list of local and remote branches."""

    branch = branch_name(repo) if branch is None else branch

    return {b.name:b for b in branches(repo, local=local, remote=remote, excl=excl)}.get(branch)


def get_branch_state(b):
    return 'tracked' if b.is_published and b.is_local else 'local' if b.is_local else 'remote'


def get_branch_items(branches,branch=None):
    """Get quick panel items from a list of branches"""
    return [[['  ','* '][branch==b.name]+b.name,'  '+get_branch_state(b)] for b in branches]


class RepoHelper(object):

    @property
    def repo(self):
        """discover the repo for a sublime command"""

        if hasattr(self, 'view'):
            window = self.view.window()
            view = self.view
        elif hasattr(self, 'window'):
            window = self.window
            view = self.window.active_view()
        else:
            return

        folders = []

        view_repo = view.settings().get('git_repo')
        if view_repo:
            folders.append(view_repo)

        cur_file = view.file_name()
        if cur_file:
            folders.append(os.path.dirname(cur_file))
        
        folders.extend(window.folders())

        for folder in folders:
            if os.path.exists(folder):
                repo = Repo(folder)
                if repo:
                    return repo


# def get_branches(repo, local=True, remote_branches=True):
#     """Returns a list of local and remote branches."""

#     repo_check(repo)

#     # print local
#     branches = []

#     if remote_branches:

#         # Remote refs.
#         try:
#             for b in repo.remote('origin').refs:
#                 name = b.name.split('/',1)[-1]

#                 if name not in forbidden_branches:
#                     branches.append(Branch(name, is_published=True))
#         except (IndexError, AssertionError):
#             pass

#     if local:

#         # Local refs.
#         for b in [h.name for h in repo.heads]:

#             if b not in [br.name for br in branches] or not remote_branches:
#                 if b not in forbidden_branches:
#                     branches.append(Branch(b, is_published=False))

#     return sorted(branches, key=attrgetter('name'))


# def get_branch_names(repo, local=True, remote_branches=True):

#     repo_check(repo)

#     branches = get_branches(repo, local=local, remote_branches=remote_branches)

#     return [b.name for b in branches]


def stash_it(repo, sync=False):

    repo_check(repo)

    msg = 'syncing branch' if sync else 'switching branches'

    return repo.git.stash('save', '--include-untracked', STASH_TEMPLATE.format(msg))


def unstash_index(repo, sync=False, branch=None):
    """Returns an unstash index if one is available."""

    repo_check(repo)

    stash_list = repo.git.stash('list')

    branch = branch_name(repo) if branch is None else branch

    intent = 'syncing branch' if sync else 'switching branches'

    legit_msg = STASH_TEMPLATE.format(intent)

    # stash_name_re = "^stash@{([0-9]+)}: On "+branch+": Legit: stashing before "+intent+"\.$"

    for stash in stash_list.splitlines():

        stash_id, on_branch, msg = stash.split(': ',2)

        # stash_match = re.match(stash_name_re, stash)

        if on_branch[3:]==branch and msg==legit_msg:
            return stash_id[7:-1]
            # return stash_match.groups()[0]


def unstash_it(repo, sync=False, branch=None):
    """Unstashes changes from current branch for branch sync."""

    repo_check(repo)

    stash_index = unstash_index(repo, sync=sync, branch=branch)

    if stash_index is not None:
        return repo.git.stash('pop', 'stash@{{{0}}}'.format(stash_index))


def fetch(repo):

    repo_check(repo)

    return repo.git.fetch('origin')


def is_upstream_ahead(repo,branch=None):

    repo_check(repo, require_remote=True)

    branch = branch_name(repo) if branch is None else branch

    return any(repo.iter_commits(branch+'..'+branch+'@{u}'))


def merged(repo, branch, on_src=False):
    '''Checks to see if a branch is merged'''

    repo_check(repo)

    src, dst = ('HEAD^{}',branch+'^{}') if on_src else (branch+'^{}','HEAD^{}')

    return (repo.merge_base(src,dst) or [None])[0] == repo.rev_parse(src)


def smart_merge(repo, branch, allow_rebase=True, force_theirs=None):

    repo_check(repo)

    from_branch = branch_name(repo)

    merges = repo.git.log('--merges', '{0}..{1}'.format(branch, from_branch))

    if allow_rebase:
        verb = 'merge' if merges.count('commit') else 'rebase'
    else:
        verb = 'merge'

    try:
        if verb == 'merge' and force_theirs is not None:
            if force_theirs:
                # Overwrite our conflicting differences with theirs
                return getattr(repo.git, verb)(branch,X='theirs')
            else:
                # Discard their conflicting changes being merged in
                return getattr(repo.git, verb)(branch,X='ours')
        else:
            # Merge and abort if there are conflicts
            return getattr(repo.git, verb)(branch)
    except GitCommandError as why:
        log = getattr(repo.git, verb)('--abort')
        abort('Merge failed. Reverting.', log='{0}\n{1}'.format(why, log), type='merge')
        raise why


def smart_pull(repo):
    'git log --merges origin/master..master'

    repo_check(repo)

    branch = branch_name(repo)

    fetch(repo)

    return smart_merge(repo, '{0}/{1}'.format('origin', branch))


def commit(repo, message, *files, all_files=True, untracked_files=True):

    repo_check(repo)

    if repo.is_dirty() or repo.untracked_files:
        if all_files:
            if untracked_files:
                repo.git.add(all=True)
            else:
                repo.git.add(update=True)
        elif files:
            repo.index.add(files)
        else:
            return

    # Check that something is to be committed
    if repo.head.is_valid()
        if not repo.index.diff("HEAD"):
            return
    else:
        if not list(repo.index.iter_blobs()):
            return

    return repo.index.commit(message)

def undo(repo):

    repo_check(repo)

    repo.head.reset('HEAD^')


def is_upstream_behind(repo,branch=None):

    repo_check(repo, require_remote=True)

    branch = branch_name(repo) if branch is None else branch

    return any(repo.iter_commits(branch+'@{u}..'+branch))

def push(repo, branch=None):

    repo_check(repo, require_remote=True)

    branch = branch_name(repo) if branch is None else branch

    if branch in repo.heads:
        try:
            repo.remotes.origin.push('{0}:{0}'.format(branch,branch))
        except GitCommandError:
            raise PushFailure("")
        if not repo.heads[branch].tracking_branch():
            repo.heads[branch].set_tracking_branch(repo.remotes.origin.refs[branch])


def branch_on_remote(repo, branch):
    # Determine if a branch is in a remote repository

    repo_check(repo, require_remote=True)

    try:
        return repo.git.ls_remote('origin', branch,heads=True)
    except GitCommandError:
        raise RemoteFailure('Cannot contact remote repository',next(repo.remotes.origin.urls))


def checkout_branch(repo, branch):
    """Checks out given branch."""

    repo_check(repo)

    repo.heads[branch].checkout()


def track_branch(repo, branch):
    "Creates a new branch that tracks a remote branch"

    repo_check(repo, require_remote=True)

    remote = repo.remotes.origin.refs[branch]

    return repo.create_head(branch, remote).set_tracking_branch(remote)


def sprout_branch(repo, branch, off_branch=None):
    """Creates branch from current unless provided."""

    repo_check(repo)

    off_branch = branch_name(repo) if off_branch is None else off_branch

    return repo.create_head(branch, repo.heads[off_branch])


def destroy_branch(repo, branch):
    '''Delete a branch both locally and remotely'''

    repo_check(repo)

    head = get_branch(repo, branch)

    if head is None:
        return

    if head.name == branch_name(repo):
        return

    index = unstash_index(repo, branch=head.name)
    if index:
        repo.git.stash('drop', index)

    if head.is_published:
        repo.git.push('origin',head.name,delete=True)

    if head.is_local:
        repo.git.branch(head.name,D=True)


# def graft_branch(repo, branch):
#     """Merges branch into current branch, and deletes it."""

#     repo_check(repo)

#     log = []

#     try:
#         msg = repo.git.merge('--no-ff', branch)
#         log.append(msg)
#     except GitCommandError as why:
#         log = repo.git.merge('--abort')
#         abort('Merge failed. Reverting.', log='{0}\n{1}'.format(why, log), type='merge')


#     out = repo.git.branch('-D', branch)
#     log.append(out)
#     return '\n'.join(log)


# def unpublish_branch(repo, branch):
#     """Unpublishes given branch."""

#     repo_check(repo)

#     try:
#         return repo.git.push('origin', ':{0}'.format(branch))
#     except GitCommandError:
#         _, _, log = repo.git.fetch('origin', '--prune', with_extended_output=True)
#         abort('Unpublish failed. Fetching.', log=log, type='unpublish')


# def publish_branch(repo, branch):
#     """Publishes given branch."""

#     repo_check(repo)

#     return repo.git.push('-u', 'origin', branch)

