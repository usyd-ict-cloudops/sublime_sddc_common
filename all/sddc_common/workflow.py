
import os
import os.path as osp
import re
from . import scm

class WorkflowError(Exception):
    """Base Workflow Error"""

class ProjectMissing(WorkflowError):
    """The Project Folder is missing"""

class NotInProject(WorkflowError):
    """The Folder is not in the project tree"""

class BadURLMap(WorkflowError):
    """The Project Folder is missing"""

class BadURLProvider(WorkflowError):
    """The authority for the repo url is incorrect"""

class BadURLMapType(TypeError,WorkflowError):
    """The Project Folder is missing"""
    fmt = "rewrite_map should be one of None, 'bitbucket', 'github', or dict not {0.__class__.__name__}"
    def __init__(self, rewrite_map):
        super(BadURLMap, self).__init__(self.fmt.format(rewrite_map))

class BadBranch(WorkflowError):
    """Some thing is wrong with this branch"""
    fmt = 'Some thing is wrong with branch {0}'
    def __init__(self, branch):
        super(BadBranch, self).__init__(self.fmt.format(branch))

class NotAllowed(BadBranch):
    """The branch is not allowed in this context"""
    fmt = 'The {0} branch is not allowed in this context'

class MasterNotAllowed(NotAllowed):
    """The branch is not allowed in this context"""
    fmt = '{0}'

class SameBranch(BadBranch):
    """The target and current branches are the same"""
    fmt = 'The {0} branch is the current branch'

class BranchMissing(BadBranch):
    """The branch you are referring to does not exist."""
    fmt = 'The {0} branch does not exist'

class DirtyBranch(BadBranch):
    """The branch is dirty"""
    fmt = "The {0} branch has uncommitted changes"


bitbucket_path_to_slug_map = {
    '^applications/(?P<name>\w+)/data$': 'hiera-applications-{0[name]}',
    '^applications/(?P<prefix>\w+)/modules/(?P<name>\w+)$': 'puppet-{0[name]}',
    '^applications/(?P<name>\w+)/wiki/data$': 'hiera-applications-{0[name]}/wiki',
    '^applications/(?P<prefix>\w+)/wiki/modules/(?P<name>\w+)$': 'puppet-{0[name]}/wiki',
    '^tenants/(?P<name>\w+)/data$': 'hiera-tenants-{0[name]}',
    '^tenants/(?P<prefix>\w+)/modules/(?P<name>\w+)$': 'puppet-{0[name]}',
    '^tenants/(?P<name>\w+)/wiki/data$': 'hiera-tenants-{0[name]}/wiki',
    '^tenants/(?P<prefix>\w+)/wiki/modules/(?P<name>\w+)$': 'puppet-{0[name]}/wiki',
    '^global/data/(?P<name>\w+)$': 'hiera-{0[name]}',
    '^global/modules/(?P<name>\w+)$': 'puppet-{0[name]}',
    '^global/wiki/data/(?P<name>\w+)$': 'hiera-{0[name]}/wiki',
    '^global/wiki/modules/(?P<name>\w+)$': 'puppet-{0[name]}/wiki'
}

github_path_to_slug_map = {
    '^applications/(?P<name>\w+)/data$': 'hiera-applications-{0[name]}',
    '^applications/(?P<prefix>\w+)/modules/(?P<name>\w+)$': 'puppet-{0[name]}',
    '^applications/(?P<name>\w+)/wiki/data$': 'hiera-applications-{0[name]}.wiki',
    '^applications/(?P<prefix>\w+)/wiki/modules/(?P<name>\w+)$': 'puppet-{0[name]}.wiki',
    '^tenants/(?P<name>\w+)/data$': 'hiera-tenants-{0[name]}',
    '^tenants/(?P<prefix>\w+)/modules/(?P<name>\w+)$': 'puppet-{0[name]}',
    '^tenants/(?P<name>\w+)/wiki/data$': 'hiera-tenants-{0[name]}.wiki',
    '^tenants/(?P<prefix>\w+)/wiki/modules/(?P<name>\w+)$': 'puppet-{0[name]}.wiki',
    '^global/data/(?P<name>\w+)$': 'hiera-{0[name]}',
    '^global/modules/(?P<name>\w+)$': 'puppet-{0[name]}',
    '^global/wiki/data/(?P<name>\w+)$': 'hiera-{0[name]}.wiki',
    '^global/wiki/modules/(?P<name>\w+)$': 'puppet-{0[name]}.wiki'
}

default_path_to_slug_map = bitbucket_path_to_slug_map

default_url_fmt = 'git@{provider}:{account}/{name}'


def get_config():
    return scm.get_git_config()


def set_config(name, email):
    scm.set_git_config(name, email)


def switch_to(repo, branch):
    # switch_to(repo,'develop')
    if repo.is_dirty():
        scm.stash_it(repo)
    scm.checkout_branch(repo, branch)
    if scm.unstash_index(repo):
        scm.unstash_it(repo)


def path_to_repo_name(path, project_root=None, rewrite_map=None):
    if not isinstance(rewrite_map, dict):
        if rewrite_map is None:
            rewrite_map = default_path_to_slug_map
        elif rewrite_map == 'bitbucket':
            rewrite_map = bitbucket_path_to_slug_map
        elif rewrite_map == 'github':
            rewrite_map = github_path_to_slug_map
        else:
            raise BadURLMapType(rewrite_map)

    # Assume path is relative to the project_root unless it is provided
    if project_root is not None:
        path = osp.relpath(path,project_root)

    try:
        mapkey = max((k for k in rewrite_map if re.match(k,path)),key=len)
    except ValueError:
        raise BadURLMap("Cannot map path {0} to repo name".format(path))

    try:
        return rewrite_map[mapkey].format(re.match(mapkey,path).groupdict())
    except (IndexError,AttributeError) as e:
        raise BadURLMap("regex '{0}' does not map to format string '{1}' for path {2}: {3}".format(mapkey,rewrite_map[mapkey],path,e))


def path_to_repo_url(path, account, project_root=None, rewrite_map=None, provider=None, url_fmt=None):

    fmt = default_url_fmt if url_fmt is None else url_fmt

    if provider is None:
        if rewrite_map in ('bitbucket',None):
            provider = 'bitbucket.org'
        elif rewrite_map == 'github':
            provider = 'github.com'
        elif url_fmt is not None:
            pass
        else:
            raise BadURLProvider("Provider cannot be null")

    name = path_to_repo_name(path, project_root, rewrite_map)

    return fmt.format(provider=provider, account=account, name=name)


def work_on(path, branch=None, account=None, project_root=None, rewrite_map=None, provider=None, url_fmt=None, off_branch=None):
    """Switch or Sprout or Clone"""

    if project_root is None:
        project_root = os.getcwd()

    if not osp.exists(project_root):
        raise ProjectMissing("Project folder does not exist: {0}".format(project_root))

    if osp.isabs(path):
        if not path.startswith(project_root):
            raise NotInProject("Path {0} not in project folder {1}".format(path,project_root))
    else:
        path = osp.join(project_root, path)

    repo = scm.Repo(path) if osp.exists(path) else None

    if repo is None:
        repourl = path_to_repo_url(path, account, project_root, rewrite_map, provider, url_fmt)
        repo = scm.clone_from(repourl, path)

    # if repo.working_tree_dir == path:
    #     pass

    if branch is not None and branch != scm.branch_name(repo):
        branches = {b.name:b for b in scm.branches(repo)}
        if branch not in branches:
            if scm.branch_on_remote(repo, branch):
                scm.fetch(repo)
                # Track
                scm.track_branch(repo, branch)
            else:
                # Sprout
                scm.sprout_branch(repo, branch, off_branch)
        else:
            if not branches[branch].is_local:
                scm.track_branch(repo, branch)

        switch_to(repo, branch)

    return repo


def sync_for(repo, branch=None):
    """Stashes unstaged changes, Fetches remote data, Performs smart
    pull+merge, Pushes local commits up, and Unstashes changes.

    Defaults to current branch.
    """

    original_branch = scm.branch_name(repo)

    is_external = False
    allow_push = True
    
    if branch:
        is_external = branch != original_branch
    else:
        # Sync current branch.
        branch = original_branch

    is_remote = scm.branch_on_remote(repo, branch)

    is_local = branch in scm.branch_names(repo)

    if is_local or is_remote:

        if is_external:
            switch_to(repo, branch)

        if repo.is_dirty():
            scm.stash_it(repo, sync=True)

        if is_remote:
            try:
                scm.smart_pull(repo)
            except scm.GitCommandError:
                allow_push = False
        else:
            scm.fetch(repo)

        if allow_push and is_local:
            scm.push(repo, branch)

        if scm.unstash_index(repo, sync=True):
            scm.unstash_it(repo, sync=True)

        if is_external:
            switch_to(repo, original_branch)

    else:
        raise BranchMissing('The {0} branch does not exist')


def deploy_for(repo, message, *files, all_files=True, untracked_files=True, branch=None, switch_back=True):
    """Switch, Sync, Add, Commit, Push"""

    original_branch = scm.branch_name(repo)

    if branch is None:
        branch = original_branch
    elif branch != original_branch:
        if branch not in scm.branch_names(repo):
            return BranchMissing(branch)
        switch_to(repo, branch)

    scm.smart_pull(repo)

    if scm.commit(repo, message, *files, all_files=all_files, untracked_files=untracked_files):
        scm.push(repo, branch)

    if switch_back and branch != original_branch:
        switch_to(repo, original_branch)


def undo(repo, branch=None):
    '''Should never be used.'''
    if branch is not None:
        if scm.branch_name(repo)!=branch:
            switch_to(repo, branch)
    scm.undo(repo)


def version_for(repo, path, versions_ago=1, branch=None):
    '''Get a prior version of a file'''
    pass


def finalize_for(repo, branch, force=False):
    '''Delete local and remote branches.'''
    if branch == 'master':
        raise MasterNotAllowed("You cannot destroy the master branch.")
    if scm.branch_name(repo)==branch:
        switch_to(repo, 'master')
    unstash_index = scm.unstash_index(repo, branch=branch)
    if unstash_index and not force:
        raise DirtyBranch(branch)
    scm.destroy_branch(repo, branch)


def promote_for(repo, branch, finalize=False, force=False, force_finalize=False, overwrite=True):
    """Promote a lower level branch to the current branch"""
    if repo.is_dirty():
        raise DirtyBranch(branch)
    scm.smart_pull(repo)
    if not scm.merged(repo, branch):
        scm.smart_merge(repo, branch, allow_rebase=False,force_theirs=overwrite if force else None)
    if finalize:
        finalize_for(repo, branch, force_finalize)
    scm.push(repo)


def promote_to(repo, branch, finalize=False, force=False, force_finalize=False, overwrite=True):
    """Promote the current branch to a higher level branch"""
    src_branch = scm.branch_name(repo)
    if src_branch==branch:
        raise SameBranch(branch)
    if repo.is_dirty() and finalize and not force_finalize:
        raise DirtyBranch(branch)
    switch_to(repo, branch)
    promote_for(repo, src_branch, finalize=finalize, force=force, force_finalize=force_finalize, overwrite=overwrite)
