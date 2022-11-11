import os, yaml, requests, tempfile, shutil, sys, urllib, urllib.request
from struct import pack

def loadConfig(path):
    configFile = open(path, 'r')
    yamlData = yaml.load(configFile, yaml.Loader)
    configFile.close()

    return yamlData

def loadSquirrelConfig(path):
    branches = {}
    conf = open(path, 'r')
    for line in conf:
        branches[line.split()[0].strip()] = line.split()[1].strip()

    return branches

config = loadConfig('/etc/sappy/sappy.conf')
squirrelConf = loadSquirrelConfig('/etc/squirrel/branches')

def build(package):
    sync(False)
    
    pkgBranch = package.split('/')[0]
    pkgName = package.split('/')[1]

    branchPkgs = readIndex(pkgBranch)
    if not pkgName in branchPkgs:
        print("Package '" + pkgName + "' is not present in branch '" + pkgBranch + "' !")
        exit(1)

    infoFile = open('INFO', 'wb')
    req = urllib.request.urlopen(squirrelConf[pkgBranch] + '/' + pkgName)
    infoData = req.read()
    infoFile.write(infoData)
    infoFile.close()
    pkgInfo = readPkgInfo()
    os.remove('INFO')
    if 'makedeps' in pkgInfo:
        for d in pkgInfo['makedeps'].split():
            real_root = os.open("/", os.O_PATH)
            os.system('ROOT=' + os.path.abspath(config['workdir']) + ' squirrel get ' + d + ' --chroot=' + os.path.abspath(config['workdir']) + ' -y')
            os.chdir(real_root)
            os.chroot(".")
            # Back to old root
            os.close(real_root)
            os.chdir(config['workdir'])

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
    os.system('export PATH=/usr/bin:/usr/sbin')
    with tempfile.TemporaryDirectory() as tmpdirname:
        os.chdir(tmpdirname)
        infoFile = open('INFO', 'wb')
        infoFile.write(infoData)
        infoFile.close()
        req.close()
        for source in pkgInfo['source'].split():
            if source == "N/A":
                continue
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
        print(os.listdir('.'))
        os.environ['PKG'] = os.path.abspath('./root')
        os.environ['MAKEFLAGS'] = "-j1"
        os.chdir('work')
        print(os.listdir('..'))
        if pkgInfo['source'].split()[-1] != 'N/A':
            cmd = 'tar -xf ../' + pkgInfo['source'].split()[-1].split('/')[-1]
            out = os.system(cmd)
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

        if ")" == line.strip():
            record_build = False
            continue

        if "(" not in line or line.split(': ')[0] == "description":
            if not record_build:
                info[line.split(": ")[0].strip()] = line.split(": ")[1].strip()
            else:
                info[bracket_name] += line
        else:
            if record_build:
                info[bracket_name] += line
            else:
                bracket_name = line.split("(")[0].strip()
            record_build = True
            if not bracket_name in info:
                info[bracket_name] = ""

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
    dirsToCreate = ['etc', 'dev', 'proc', 'sys', 'var', 'run', 'usr', 'tmp', 'usr/lib', 'usr/bin', 'usr/sbin', 'etc/squirrel', 'usr/lib/python3.10/site-packages/certifi/']
    linksToDo = {'bin': 'usr/bin', 'lib': 'usr/lib', 'sbin': 'usr/sbin', 'lib64': 'usr/lib', 'usr/lib64': 'lib', 'etc/mtab': '/proc/self/mounts'}
    for dir in dirsToCreate:
        os.makedirs(dir)
    for link in linksToDo:
        os.symlink(linksToDo[link], link)

    shutil.copy(sys.path[0] + '/assets/group', 'etc/group')
    shutil.copy(sys.path[0] + '/assets/passwd', 'etc/passwd')
    shutil.copy('/etc/squirrel/branches', 'etc/squirrel/branches')
    shutil.copy('/usr/lib/python3.10/site-packages/certifi/cacert.pem', 'usr/lib/python3.10/site-packages/certifi/cacert.pem')

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
        'systemd',
        'util-linux',
        'linux-api-headers',
        'gcc-lib-c++',
        'zstd',
        'pkg-config',
        'libtool'
    ]

    fp = open('INDEX', 'w')
    fp.close()

    installedPkgs = []
    for package in chrootPackages:
        real_root = os.open("/", os.O_PATH)
        os.system('ROOT=' + config['workdir'] + ' squirrel get ' + package + ' --chroot=' + config['workdir'] + ' -y')
        installedPkgs.append(package)
        os.chdir(real_root)
        os.chroot(".")
        # Back to old root
        os.close(real_root)
        os.chdir(config['workdir'])
    shutil.copy('/etc/hosts', config['workdir'] + '/etc/')
    shutil.copy('/etc/resolv.conf', config['workdir'] + '/etc/')
    shutil.copy('/etc/ssl/certs/ca-certificates.crt', config['workdir'] + '/etc/ssl/certs/')

    print('Successful setup.')

def sync(verbose=True):
    os.makedirs('/etc/sappy/store/' + config['release'], exist_ok=True)
    os.chdir('/etc/sappy/store')

    for branch in config['branches']:
        os.chdir('/etc/sappy/store/' + config['release'])
        if verbose:
            print("Syncing '" + branch + "' branch...")
        os.makedirs(branch, exist_ok=True)
        os.chdir(branch)
        # Get INDEX of branch
        index = open('INDEX', 'wb')
        req = urllib.request.urlopen(squirrelConf[branch] + '/INDEX')
        index.write(req.read())
        req.close()
        index.close()

    if verbose:
        print()
        print('All branches have been successfully synced !')