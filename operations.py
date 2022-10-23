import os, yaml, requests, tempfile, shutil
from struct import pack

def loadConfig(path):
    configFile = open(path, 'r')
    yamlData = yaml.load(configFile, yaml.Loader)
    configFile.close()

    return yamlData

config = loadConfig('/etc/sappy/sappy.conf')

def build(package):
    sync(False)
    
    pkgBranch = package.split('/')[0]
    pkgName = package.split('/')[1]

    branchPkgs = readIndex(pkgBranch)
    if not pkgName in branchPkgs:
        print("Package '" + pkgName + "' is not present in branch '" + pkgBranch + "' !")
        exit(1)

    infoFile = open('INFO', 'wb')
    req = requests.get('http://' + config['host'] + '/' + config['release'] + '/' + pkgBranch + '/' + pkgName)
    infoFile.write(req.content)
    infoFile.close()
    pkgInfo = readPkgInfo()
    os.remove('INFO')
    if 'makedeps' in pkgInfo:
        for d in pkgInfo['makedeps'].split():
            os.system('ROOT=' + os.path.abspath(config['workdir']) + ' squirrel get ' + d + ' --no-index')

    real_root = os.open("/", os.O_PATH)
    # Mount the filesystems
    os.system('mount --bind /dev ' + config['workdir'] + '/dev')
    os.system('mount --rbind /sys ' + config['workdir'] + '/sys')
    os.system('mount -t proc proc ' + config['workdir'] + '/proc')
    os.system('mount -t tmpfs tmpfs ' + config['workdir'] + '/run')
    os.system('mount --make-slave ' + config['workdir'] + '/dev')
    os.system('mount --make-rslave ' + config['workdir'] + '/sys')

    os.chroot(config['workdir'])
    os.chdir('/')
    with tempfile.TemporaryDirectory() as tmpdirname:
        os.chdir(tmpdirname)
        infoFile = open('INFO', 'wb')
        req = requests.get('http://' + config['host'] + '/' + config['release'] + '/' + pkgBranch + '/' + pkgName)
        infoFile.write(req.content)
        infoFile.close()
        req.close()
        for source in pkgInfo['source'].split():
            print('Downloading package source...')
            with requests.get(source.strip(), stream=True) as r:
                r.raise_for_status()
                with open(source.strip().split('/')[-1], 'wb') as f:
                    for chunk in r.iter_content(chunk_size=8192): 
                        # If you have chunk encoded response uncomment if
                        # and set chunk_size parameter to None.
                        #if chunk: 
                        f.write(chunk)
        
        os.makedirs('work')
        os.makedirs('root')
        os.environ['PKG'] = os.path.abspath('./root')
        os.environ['MAKEFLAGS'] = "-j1"
        os.chdir('work')
        os.system('XZ_OPTS=9 tar -xf ../' + pkgInfo['source'].split()[-1].split('/')[-1])

        if len(os.listdir('.')) == 1:
            os.chdir(os.listdir('.')[0])

        out = os.system(pkgInfo['build'])
        if out != 0:
            print('ERROR:')
        print(os.listdir(os.environ['PKG']))
        print("Successfully built package '" + pkgInfo['name'] + "'.")
        print('Generating package binary...')
        os.chdir(os.environ['PKG'])
        # Create the binary archive with the tree
        os.system('find . > .TREE')
        os.chdir('..')
        os.system('tar -cJpf ' + pkgInfo['name'] + '-' + pkgInfo['version'] + '.tar.xz root')
        shutil.copy(pkgInfo['name'] + '-' + pkgInfo['version'] + '.tar.xz', '/')
        os.chdir(real_root)
        os.chroot('.')
        print('Successfully generated the package binary.')
        print('Unomounting filesystems.')
        os.system('umount -R ' + config['workdir'] + '/*')

def readPkgInfo():
    pkg_file = open('INFO', 'r')

    record_build = False
    opened_brackets = 0
    info = {}
    bracket_name = ""
    for line in pkg_file.readlines():
        if line.startswith("#") or line == "" or line == "\n":
            continue
        if "(" not in line or line.split(': ')[0] == "description":
            if not record_build:
                info[line.split(": ")[0].strip()] = line.split(": ")[1].strip()
            else:
                if line.replace('\n','').strip() != ")" or (")" in line and opened_brackets > 1):
                    info[bracket_name] += line
        else:
            record_build = True
            opened_brackets += 1
            if opened_brackets > 1:
                info[bracket_name] += line
            else:
                bracket_name = line.split("(")[0].strip()
            if not bracket_name in info:
                info[bracket_name] = ""  

        if ")" in line:
            opened_brackets -= 1
    return info

def readIndex(branch):
    packages = {}

    try:
        index = open('/etc/sappy/store/' + config['release'] + '/' + branch + '/INDEX', 'r')
    except FileNotFoundError:
        print("Index of branch '" + branch + "' not found ! Have you correctly specified the branch name ?")
        exit(1)

    for line in index.readlines():
        packages[line.split()[0].strip()] = line.split()[1].strip()

    return packages

def setup():
    os.chdir(config['workdir'])
    dirsToCreate = ['etc', 'var', 'usr', 'usr/lib', 'usr/bin', 'usr/sbin', 'lib64']
    linksToDo = {'bin': 'usr/bin', 'lib': 'usr/lib', 'sbin': 'usr/sbin'}

    for dir in dirsToCreate:
        os.makedirs(dir)
    for link in linksToDo:
        os.symlink(linksToDo[link], link)

    chrootPackages = [
        'binutils',
        'gcc',
        'm4',
        'bash',
        'coreutils',
        'diffutils',
        'file',
        'findutils',
        'gawk',
        'grep',
        'gzip',
        'make',
        'patch',
        'sed',
        'tar',
        'xz',
        'gettext',
        'bison',
        'perl',
        'python3',
        'texinfo',
        'util-linux'
    ]

    for package in chrootPackages:
        os.system('ROOT=' + config['workdir'] + ' squirrel get ' + package + ' --no-index')

    print('Successful setup.')
    
def sync(verbose=True):
    os.chdir('/etc/sappy/store')

    os.makedirs(config['release'], exist_ok=True)
    os.chdir(config['release'])

    for branch in config['branches']:
        if verbose:
            print("Syncing '" + branch + "' branch...")
        os.makedirs(branch, exist_ok=True)
        os.chdir(branch)
        # Get INDEX of branch
        index = open('INDEX', 'wb')
        req = requests.get('http://' + config['host'] + '/' + config['release'] + '/' + branch + '/INDEX')
        index.write(req.content)
        req.close()
        index.close()

    if verbose:
        print()
        print('All branches have been successfully synced !')