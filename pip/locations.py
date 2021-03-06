"""Locations where we look for configs, install stuff, etc"""

import sys
import site
import os
import tempfile
import getpass
from pip.backwardcompat import get_python_lib
import pip.exceptions


def running_under_virtualenv():
    """
    Return True if we're running inside a virtualenv, False otherwise.

    """
    return hasattr(sys, 'real_prefix')


def virtualenv_no_global():
    """
    Return True if in a venv and no system site packages.
    """
    #this mirrors the logic in virtualenv.py for locating the no-global-site-packages.txt file
    site_mod_dir = os.path.dirname(os.path.abspath(site.__file__))
    no_global_file = os.path.join(site_mod_dir, 'no-global-site-packages.txt')
    if running_under_virtualenv() and os.path.isfile(no_global_file):
        return True

def _get_build_prefix():
    """ Returns a safe build_prefix """
    path = os.path.join(tempfile.gettempdir(), 'pip-build-%s' % \
        getpass.getuser())
    if sys.platform == 'win32':
        """ on windows(tested on 7) temp dirs are isolated """
        return path
    try:
        os.mkdir(path)
    except OSError:
        file_uid = None
        try:
            fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
            file_uid = os.fstat(fd).st_uid
            os.close(fd)
        except OSError:
            file_uid = None
        if file_uid != os.getuid():
            msg = "The temporary folder for building (%s) is not owned by your user!" \
                % path
            print (msg)
            print("pip will not work until the temporary folder is " + \
                 "either deleted or owned by your user account.")
            raise pip.exceptions.InstallationError(msg)
    return path

if running_under_virtualenv():
    build_prefix = os.path.join(sys.prefix, 'build')
    src_prefix = os.path.join(sys.prefix, 'src')
else:
    # Use tempfile to create a temporary folder for build
    # Note: we are NOT using mkdtemp so we can have a consistent build dir
    # Note: using realpath due to tmp dirs on OSX being symlinks
    build_prefix = os.path.realpath(_get_build_prefix())

    ## FIXME: keep src in cwd for now (it is not a temporary folder)
    try:
        src_prefix = os.path.join(os.getcwd(), 'src')
    except OSError:
        # In case the current working directory has been renamed or deleted
        sys.exit("The folder you are executing pip from can no longer be found.")

# under Mac OS X + virtualenv sys.prefix is not properly resolved
# it is something like /path/to/python/bin/..
build_prefix = os.path.abspath(build_prefix)
src_prefix = os.path.abspath(src_prefix)

# FIXME doesn't account for venv linked to global site-packages

site_packages = get_python_lib()
user_dir = os.path.expanduser('~')
if sys.platform == 'win32':
    bin_py = os.path.join(sys.prefix, 'Scripts')
    # buildout uses 'bin' on Windows too?
    if not os.path.exists(bin_py):
        bin_py = os.path.join(sys.prefix, 'bin')
    default_storage_dir = os.path.join(user_dir, 'pip')
    default_config_file = os.path.join(default_storage_dir, 'pip.ini')
    default_log_file = os.path.join(default_storage_dir, 'pip.log')
else:
    bin_py = os.path.join(sys.prefix, 'bin')
    default_storage_dir = os.path.join(user_dir, '.pip')
    default_config_file = os.path.join(default_storage_dir, 'pip.conf')
    default_log_file = os.path.join(default_storage_dir, 'pip.log')

    # Forcing to use /usr/local/bin for standard Mac OS X framework installs
    # Also log to ~/Library/Logs/ for use with the Console.app log viewer
    if sys.platform[:6] == 'darwin' and sys.prefix[:16] == '/System/Library/':
        bin_py = '/usr/local/bin'
        default_log_file = os.path.join(user_dir, 'Library/Logs/pip.log')
