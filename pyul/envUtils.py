import os
import virtualenv
import pkg_resources
import pip

PIP_INSTALL_ARGS = ['install',
                    '--index-url',
                    'http://pypi.mapmyfitness.com/mmf/stable/+simple/']

PIP_UNINSTALL_ARGS = ['uninstall',
                      '--yes']

def get_venv_home():
    return os.environ.get('VENV_HOME') or os.path.join(os.path.expanduser('~'),'.virtualenvs')

def make_venv_home():
    venv_home = get_venv_home()
    os.makedirs(venv_home)
    
def get_env_home(name):
    return os.path.join(get_venv_home(), name)

def get_env_name(path):
    venv_home = get_venv_home()
    if not path.startswith(venv_home):
        return None
    name = os.path.basename(path)
    exists(name, True)
    return name
    
def get_paths(name):
    _, lib_dir, inc_dir, bin_dir = virtualenv.path_locations(name)
    
    venv_home = get_venv_home()
    home_dir = get_env_home(name)
    lib_dir = os.path.join(venv_home, lib_dir)
    pkg_dir = os.path.join(lib_dir, 'site-packages')
    inc_dir = os.path.join(venv_home, inc_dir)
    bin_dir = os.path.join(venv_home, bin_dir)        
    
    return home_dir, lib_dir, pkg_dir, inc_dir, bin_dir

def exists( name, raise_error=False):
    home_dir = get_env_home(name)
    if not os.path.exists(home_dir):
        if raise_error:
            raise Exception('Unable to find virtualenv {0}'.format(home_dir))
        return False
    return True

def get_envs():
    venvs = list()
    venv_home = get_venv_home()
    for directory in os.listdir(venv_home):
        if os.path.exists(os.path.join(venv_home, directory, 'bin', 'activate')):
            venvs.append(os.path.join(venv_home, directory))
    return venvs
    

def get_distribution(req):
    dist = None
    try:
        dist = pkg_resources.get_distribution(str(req))
    except:
        dist = pkg_resources.working_set.by_key.get(req.key)
    return dist

def has_conflict(req):
    dist = get_distribution(req)
    if dist is not None:
        if dist not in req:
            return True
    return False

def do_pip_cmd(args):
    value = pip.main(initial_args=args)
    #reset this to an empty list so we don't get duplicate log spam
    #from consecutive pip install runs - cuz pip is dumb and keeps adding duplicate consumers
    pip.logger.consumers = [] 
    return value

def get_dependencies(req):
    requirements = list()
    dist = get_distribution(req)
    if dist is not None:
        requirements = dist.requires(req.extras)[::-1]    
    return requirements
        
def recursive_install(req, recursive=False):  
    if get_distribution(req) is None:
        print "pip install {0} ...".format(str(req)),
        args = PIP_INSTALL_ARGS + [str(req)]
        exit_code = do_pip_cmd(args)
        if exit_code == 0:
            print 'Success!'
        elif exit_code == 1:
            print "Failed to install"
        elif exit_code == 2:
            print "Has Conflicts"
        else:
            raise Exception('Unhandled Exit Code {0}'.format(exit_code))
    if has_conflict(req):
        dist = get_distribution(req)
        print "Requirement {0} conflicts with currently installed {1}".format(req, dist)
    if recursive :
        for sub_req in get_dependencies(req):
            recursive_install(sub_req, recursive)
        
def do_install(requirements):
    for req in requirements:
        recursive_install(req)
    #We enable sub reqs the second time around so all top level requirements get installed first
    for req in requirements:
        recursive_install(req, True)
    
def parse_requirements(requirements):
    return list(pkg_resources.parse_requirements(requirements))
        
def parse_requirements_file(requirements_file):
    with open(requirements_file, 'r') as file_handle:
        return parse_requirements(file_handle.read())
    
def requires(package=None):
    do_install(parse_requirements(package))
    
def suppress_pip_output():
    print "Suppressing pip install output!"
    def log_override(self, *args, **kwargs):
        pass
    pip.logger.log = log_override   
    
        
if __name__ == '__main__':
    requirements_file = '/Users/kyle.rockman/Projects/panama/build/pip-freeze-prod.txt'
    suppress_pip_output()
    do_install_from_file(requirements_file)

