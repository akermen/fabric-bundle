"""
    Fabric script for offline Git bundle deployment.
    adapted from: https://github.com/xeyownt/git-subundle

    Akermen https://EksiKalori.com
    27.09.2020
"""
from __future__ import print_function
import os
import sys
from fabric.api import hide
from fabric.api import settings
from cuisine import file_exists
from cuisine import dir_exists
from cuisine import file_upload
from cuisine import mode_local
from cuisine import mode_remote
from cuisine import dir_ensure
from cuisine import cd as cuisine_cd
from cuisine import run as cuisine_run

def _remove_prefix(text, prefix):
    if text.startswith(prefix):
        return text[len(prefix):]
    return text


def _git_unbundle_helper(bundle_file, repository_dir, module_dir=None, force=False, branch=None, remote='bundle'):
    """
    Helper method for Git unbundling.
    """

    if not file_exists(bundle_file):
        print("    [e] could not find (%s)!" % bundle_file)
        sys.exit(1)

    print("    [-] bundle '%s'" % os.path.basename(bundle_file))

    if not repository_dir:
        print("    [e] missing repository directory")
        sys.exit(1)

    print("    [-] repository '%s'" % repository_dir)

    if module_dir:
        print("    [-] module directory'%s'" % module_dir)

    if module_dir:
        module = os.path.basename(module_dir)

        if file_exists(os.path.join(module_dir, '.git')) or dir_exists(os.path.join(module_dir, '.git')):
            with cuisine_cd(module_dir):
                found = False
                with settings(warn_only=True):  # keeps running if command returns error
                    with hide('warnings'):
                        ret = cuisine_run('git remote | grep -q "^%s$"' % remote)
                        print("    [!] 'ERROR:root:' or similar messages are acceptable at this point")
                        found = not ret.failed

                if not found:
                    ret = cuisine_run('git remote add %s "%s"' % (remote, bundle_file))
                else:
                    # Bundle remote found. Make sure URL points to our BUNDLE_FILE
                    print('git remote -v | egrep -q "^%s[[:space:]]+%s"' % (remote, bundle_file))
                    ret = cuisine_run('git remote -v | egrep -q "^%s[[:space:]]+%s"' % (remote, bundle_file))
                    if ret.failed:
                        if force:
                            # force mode, we overwrite existing remote
                            cuisine_run('git remote set-url %s "%s"' % (remote, bundle_file))
                        else:
                            print("    [e] exists but has the wrong URL '%s'" % remote)
                            sys.exit(1)

                # NOTE: '--quiet' is added to prevent false-positive error codes
                ret = cuisine_run('git -c fetch.prune=false fetch --quiet %s' % remote)
                if ret.failed:
                    print("    [e] failed to fetch")
                    sys.exit(1)

                ret = cuisine_run('git bundle unbundle "%s"' % bundle_file)
                if ret.failed:
                    print("    [e] failed to unbundle")
                    sys.exit(1)

        else:
            # NOTE: '--quiet' is added to prevent false-positive error codes
            ret = cuisine_run('git -C "%s" submodule --quiet init "%s"' % (repository_dir, module))
            if ret.failed:
                print("    [e] failed to initialize submodule")
                sys.exit(1)

            ret = cuisine_run('git -C "%s" config submodule."%s".url %s' % (repository_dir, module, bundle_file))
            if ret.failed:
                print("    [e] failed to configure submodule")
                sys.exit(1)

            # NOTE: '--quiet' is added to prevent false-positive error codes
            ret = cuisine_run('git -C "%s" submodule --quiet update "%s"' % (repository_dir, module))
            if ret.failed:
                print("    [e] failed to update submodule")
                sys.exit(1)

            if not dir_exists(module_dir):
                print("    [e] does not exist '%s'" % module_dir)
                sys.exit(1)

            with cuisine_cd(module_dir):
                ret = cuisine_run('git remote rename origin %s' % remote)
                if ret.failed:
                    print("    [e] failed to rename remote")
                    sys.exit(1)

                ret = cuisine_run('git bundle unbundle "%s"' % bundle_file)
                if ret.failed:
                    print("    [e] failed to ubundle")
                    sys.exit(1)

    else:
        if dir_exists(repository_dir):

            with cuisine_cd(repository_dir):
                found = False
                with settings(warn_only=True):  # keeps running if command returns error
                    with hide('warnings'):
                        ret = cuisine_run('git remote | grep -q "^%s$"' % remote)
                        print("    [!] 'ERROR:root:' or similar messages are acceptable at this point")
                        found = not ret.failed

                if not found:
                    # Remote bundle not found. Create one.
                    ret = cuisine_run('git remote add %s %s' % (remote, bundle_file))
                    if ret.failed:
                        print("    [e] failed to add remote")
                        sys.exit(1)

                else:
                    # Remote bundle found. Make sure URL points to our BUNDLE_FILE
                    print ('git remote -v | egrep -q "^%s[[:space:]]+%s"' % (remote, bundle_file))
                    ret = cuisine_run('git remote -v | egrep -q "^%s[[:space:]]+%s"' % (remote, bundle_file))
                    if ret.failed:
                        print("    [e] failed to check remote")
                        sys.exit(1)

                    if force:
                        # force mode, we overwrite existing remote
                        ret = cuisine_run('git remote set-url %s "%s"' % (remote, bundle_file))
                        if ret.failed:
                            print("    [e] failed set remote url")
                            sys.exit(1)
                    else:
                        print("    [e] exists but has the wrong URL '%s'" % remote)
                        sys.exit(1)

                # NOTE: '--quiet' is added to prevent false-positive error codes
                ret = cuisine_run('git -c fetch.prune=false fetch --quiet --recurse-submodules=no %s' % remote)
                if ret.failed:
                    print("    [e] failed to fetch")
                    sys.exit(1)

                ret = cuisine_run('git bundle unbundle "%s"' % bundle_file)
                if ret.failed:
                    print("    [e] failed to unbundle")
                    sys.exit(1)

        else:
            # NOTE: branch is only for main repository, not used for submodules
            if not branch:
                branch = cuisine_run("git bundle list-heads %s | head -n 1| cut -d' ' -f2" % bundle_file)
                if not branch:
                    branch = "HEAD"
            branch = _remove_prefix(branch, 'refs/heads/')

            print("    [-] branch '%s'" % branch)
            # NOTE: '--quiet' is added to prevent false-positive error codes
            ret = cuisine_run('git clone --quiet -b %s "%s" -o %s %s' % (
                branch, bundle_file, remote, repository_dir))
            if ret.failed:
                print("    [e] failed to clone")
                sys.exit(1)


def git_bundle(repository_dir, bundle_file=None):
    """
    creates Git bundles including submodules.

    @param repository_dir: Repository directory path
    @param bundle_file: Git bundle file path

    set 'mode_local() or mode_remote() before calling this method.

    usage from command line:
        fab mode_local git_bundle:<repository-path>,<bundle-file>
    """

    print("[-] creating Git repository bundle")

    if not dir_exists(repository_dir):
        print("    [e] could not find (%s)!" % repository_dir)
        sys.exit(1)

    bundle_file = bundle_file if bundle_file else os.path.basename(repository_dir)
    bundle_dir = os.path.dirname(bundle_file)

    bundle_extension = os.path.splitext(bundle_file)[1][1:].strip()
    if bundle_extension and bundle_extension.lower() == 'bundle':
        bundle_base = os.path.basename(os.path.splitext(bundle_file)[0].strip())
    else:
        bundle_base = os.path.basename(bundle_file)

    bundles = []

    # NOTE: 'sort' puts (for not all cases) base repository first in the list
    script = 'find %s -iname "*.git" -print0 | xargs -0 -n 1 echo | sort -n' % (
        repository_dir)
    items = cuisine_run(script).split('\n')
    for item in items:
        root = os.path.dirname(item)
        print("    [-] repository: %s" % os.path.basename(root))

        file_base = os.path.relpath(root, repository_dir)
        file_base = '' if file_base == '.' else file_base
        file_base = "%s%s%s" % (bundle_base, ('_%s' % file_base) if file_base != '' else '', '.bundle')
        file_path = os.path.join(bundle_dir, file_base)
        print("    [-] bundle: %s" % os.path.relpath(file_path, bundle_dir))

        with cuisine_cd(root):
            ret = cuisine_run('git bundle create "%s" --all' % file_path)
            if ret.failed:
                print("    [e] could not create bundle!")
                sys.exit(1)
            bundles.append(file_base)

    print("    [-] completed")

    return bundles


def git_unbundle(bundle_file, repository_dir=None, branch=None, force=False, remote='bundle'):
    """
    unbundles Git bundles including submodules.

    @param bundle_file: Git bundle file path
    @param repository_dir: Target repository directory path
    @param branch: Git branch
    @param force: Ignore existing Git directory
    @param remote: Bundle remote name

    set 'mode_local() or mode_remote() before calling this method.

    usage from command line:
        fab mode_local git_unbundle:<bundle-file>,<repository-path>,branch=<branch>
    """

    print("[-] unbundling Git repository bundle")

    if not file_exists(bundle_file):
        print("    [e] could not find (%s)!" % bundle_file)
        sys.exit(1)

    bundle_extension = os.path.splitext(bundle_file)[1][1:].strip()
    if bundle_extension and bundle_extension.lower() == 'bundle':
        filename = os.path.splitext(bundle_file)[0].strip()
        bundle_base = os.path.basename(filename)
    else:
        bundle_base = os.path.basename(bundle_file)

    if repository_dir:
        repository_dir = repository_dir
    else:
        repository_dir = bundle_base

    print("    [-] unbundling to '%s'" % repository_dir)

    if not force and dir_exists(repository_dir):
        script = 'find %s -iname "*.git" -print0 | xargs -0 -n 1 echo' % repository_dir
        items = cuisine_run(script).split('\n')
        if items:
            print("    [e] directory is not empty (%s)!" % repository_dir)
            sys.exit(1)

    _git_unbundle_helper(bundle_file, repository_dir, branch=branch, force=force, remote=remote)

    bundle_file_dir = os.path.dirname(bundle_file)

    script = 'find %s -type f -iname "%s_*.bundle" -print0 | xargs -0 -n 1 echo | sort -n' % (
        bundle_file_dir, bundle_base)
    items = cuisine_run(script).split('\n')
    for bundle_file in items:
        module_dir = os.path.splitext(bundle_file)[0].strip()
        module_dir = os.path.basename(module_dir)
        module_dir = _remove_prefix(module_dir, bundle_base)
        module_dir = _remove_prefix(module_dir, '_')
        module_dir = os.path.join(repository_dir, module_dir)

        _git_unbundle_helper(bundle_file, repository_dir, module_dir, force=force, remote=remote)


def deploy_bundle(local_path, deploy_path, file_name='bunle', branch='master', remote='bundle'):
    """
    deploys Git bundle and setup repository


    usage from command line:
        fab deploy_bundle:<local-path>,<deploy-path>
    """

    mode_local()

    local_bundle_dir = os.path.join(os.path.join(local_path, 'temp'))
    local_bundle_file = os.path.join(local_bundle_dir, file_name)
    bundle_file_names = git_bundle(local_path, local_bundle_file)

    if not bundle_file_names:
        return

    mode_remote()

    remote_bundle_dir = os.path.join(deploy_path, 'temp')
    dir_ensure(remote_bundle_dir)

    main_bundle_file = None

    for bundle_file_name in bundle_file_names:
        local_bundle_file = os.path.join(local_bundle_dir, bundle_file_name)
        remote_bundle_file = os.path.join(remote_bundle_dir, bundle_file_name)

        if not main_bundle_file:
            main_bundle_file = remote_bundle_file

        file_upload(remote_bundle_file, local_bundle_file)

    git_unbundle(main_bundle_file, deploy_path, branch, force=True, remote=remote)
