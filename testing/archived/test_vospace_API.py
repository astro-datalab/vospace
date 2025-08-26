#!/usr/bin/env python

# COVERAGE
# _ls (works)
# _ln (works)
# _mkdir (works)
# _rmdir (works)
# _get
# _put
# _cp (works)
# _mv (works)
# _rm
# _stat

# NOT COVERED
# _load
# _saveAs
# _tag
# _access

from dl import authClient as ac, queryClient as qc, storeClient as sc
from datetime import datetime
import getpass
import argparse
import tempfile
import os
import shutil
import hashlib
import time

DRY_RUN=False

def vo_print(uri, response, function, expresp='OK'):
    if response and isinstance(response, (tuple, list)):
        response = [ r for r in response if r != 'OK' ]
        if not response:
            vo_print(uri, 'OK', function, expresp=expresp)
        elif len(response) == 1:
            vo_print(uri, response[0], function, expresp=expresp)
        else:
            vo_print(uri, "\n\t".join(response), function, expresp=expresp)
    elif response == expresp or (isinstance(expresp, dict) and response.startswith(expresp.get("start", "OK"))
            and response.endswith(expresp.get("end", "OK"))):
        if response == 'OK': print ("OK %s %s" % (function, uri))
        else: print ("OK ERROR %s %s\n\t%s" % (function, uri, response))
    else:
        print ("FAIL %s %s\n\t%s" % (function, uri, repr(response)))


def vo_put(*args, **kwds):
    if DRY_RUN:
        return

    wdata = ""
    for uri in args:
        with tempfile.NamedTemporaryFile() as tmpf:
            wdata = datetime.now().isoformat()
            tmpf.write(wdata.encode('utf-8'))
            tmpf.flush()
            vo_print(" -> ".join((os.path.basename(tmpf.name), uri)),
                     sc.put(tmpf.name, uri, debug=global_debug), "PUT", **kwds)
    return wdata


def vo_put_multi_random(no_of_files, *args, **kwds):
    if DRY_RUN:
        return

    wdata = []
    for i in range(0, no_of_files):
        for uri in args:
            with tempfile.NamedTemporaryFile() as tmpf:
                content = os.urandom(1024) #1KB
                tmpf.write(content) 
                tmpf.flush()
                file_uri = uri % i
                vo_print(file_uri, sc.put(tmpf.name, file_uri, debug=global_debug), "PUT", **kwds)
                wdata.append((tmpf.name,
                              hashlib.md5(content).hexdigest(),
                              file_uri))
    return wdata


def vo_put_multi(*args, **kwds):
    if DRY_RUN:
        return

    nfiles = kwds.pop('nfiles', 5)
    for uri in args:
        tmpd = tempfile.mkdtemp()
        for i in range(nfiles):
            (tmph, tmpn) = tempfile.mkstemp(dir=tmpd)
            os.write(tmph, datetime.now().isoformat().encode('utf-8'))
            os.close(tmph)
        vo_print(" -> ".join((os.path.basename(tmpd), uri)), sc.put(tmpd, uri, debug=global_debug), "PUT", **kwds)
        shutil.rmtree(tmpd)


def vo_get(*args, **kwds):
    if DRY_RUN:
        return

    expdata = kwds.pop('expdata', None)
    expresp = kwds.get('expresp', None)
    for uri in args:
        with tempfile.NamedTemporaryFile() as tmpf:
            vo_print(" -> ".join((uri, os.path.basename(tmpf.name))), sc.get(uri, tmpf.name, debug=global_debug), "GET", **kwds)
            if not expresp or expresp == 'OK':
                tmpf.seek(0)
                tread = tmpf.read().decode('utf-8')
                if tread != expdata: print("\tUNEXPECTED DATA: " + tread)


def vo_get_multi_and_cmp(put_files_info, **kwds):
    if DRY_RUN:
        return

    for local_file, hash, uri in put_files_info:
        with tempfile.NamedTemporaryFile() as tmpf:
            vo_print(uri, sc.get(uri, tmpf.name, debug=global_debug), "GET", **kwds)
            tread = tmpf.read()
            if hash == hashlib.md5(tread).hexdigest():
                print("\tDownloaded file:[%s] same as uploaded file [OK]" % uri)
            else:
                print("\tDownloaded file:[%s] differs from uploaded file [FAIL]" % uri)


def vo_get_multi(*args, **kwds):
    if DRY_RUN:
        return

    for uri in args:
        tmpd = tempfile.mkdtemp()
        vo_print(" -> ".join((uri, os.path.basename(tmpd))), sc.get(uri, tmpd, debug=global_debug), "GET", **kwds)
        shutil.rmtree(tmpd)


def vo_mv(*args, **kwds):
    if DRY_RUN:
        return

    for uris in args:
        vo_print(" -> ".join(uris), sc.mv(uris[0], uris[1]), "MOVE", **kwds)


def vo_cp(*args, **kwds):
    if DRY_RUN:
        return

    for uris in args:
        vo_print(" -> ".join(uris), sc.cp(uris[0], uris[1]), "COPY", **kwds)


def vo_rm(*args, **kwds):
    if DRY_RUN:
        return

    for uri in args:
        vo_print(uri, sc.rm(uri, verbose=True), "RM", **kwds)


def vo_mkdir(*args, **kwds):
    if DRY_RUN:
        return

    for uri in args:
        vo_print(uri, sc.mkdir(uri), "MKDIR", **kwds)


def vo_rmdir(*args, **kwds):
    if DRY_RUN:
        return

    for uri in args:
        vo_print(uri, sc.rmdir(uri), "RMDIR", **kwds)


def vo_list(*args):
    if DRY_RUN:
        return

    for uri in args:
        print("LIST [%s]" % uri)
        print("\t" + "\n\t".join(sc.ls(uri, format="long").splitlines()))


def vo_link(*args, **kwds):
    if DRY_RUN:
        return

    for uris in args:
        vo_print(" -> ".join(uris), sc.ln(uris[0], uris[1]), "LN", **kwds)


host = os.uname()[1]
defstoragemanager = "http://localhost:7003"
defauth = "https://datalab.noao.edu/auth"
level = 1
defuser = os.environ['USER']
seed_node = "2b45951a-c237-4d11-a017-3154d24e5969"

parser = argparse.ArgumentParser(description='Test the storage client.')
parser.add_argument('-u', '--username', default=defauth, help="VOSpace username")
parser.add_argument('-s', '--seed', default=seed_node, help="Node container name in which to perform the test")
parser.add_argument('-a', '--auth_svc', default=defauth, help="VOSpace auth svc[%(default)s]")
parser.add_argument('-t', '--token', default=None, help="Token")
parser.add_argument('-sm', '--storagemgr', default=defstoragemanager, help="VOSpace storemanager [%(default)s]")
parser.add_argument('-l', '--level', default=level, choices=[0, 1, 2, 3, 4, 5, 6], type=int, help="Test level [%(default)s]")
parser.add_argument('-d', '--debug', default=False, action="store_true", help="Debug")
args = parser.parse_args()

if args.auth_svc:
    ac.set_svc_url(args.auth_svc)
else:
    ac.set_svc_url(defauth)

if args.storagemgr:
    sc.set_svc_url(args.storagemgr)
else:
    sc.set_svc_url(defstoragemanager)

if args.token:
    token = args.token
else:
    token = None

while not token:
    token = ac.login(args.username, getpass.getpass('Enter {} password (+ENTER): '.format(args.username)))

global_debug = args.debug
remote_debug = not global_debug

while global_debug != remote_debug:
    remote_debug = True if sc.sc_client.getFromURL(sc.get_svc_url(), '/debug', None).content.decode().lower() == 'true'\
        else False

if args.seed:
    seed_node = args.seed

LIST_LARGE_ARCH_CONTAINER = False
LIST_ARCH_CONTAINER = False
COPY_DIR_FROM_ARCHIVE = False
MOVE_ARCHIVE_COPY = False
CREATE_LINKS_FROM_ARCHIVE_NODES = False
UPLOAD_DOWNLOAD_MV_RANDOM_FILES = False

level_action = {0: (False, False, False, False, False, False),
                1: (False, True, False, False, False, True),
                2: (False, True, False, False, True, True),
                3: (False, True, True, False, False, True),
                4: (False, True, True, False, True, True),
                5: (True, False, False, False, True, True),
                6: (True, False, True, True, True, True)}


if args.level:
    LIST_LARGE_ARCH_CONTAINER, LIST_ARCH_CONTAINER, COPY_DIR_FROM_ARCHIVE, MOVE_ARCHIVE_COPY,\
    CREATE_LINKS_FROM_ARCHIVE_NODES, UPLOAD_DOWNLOAD_MV_RANDOM_FILES = level_action[args.level]


if LIST_LARGE_ARCH_CONTAINER:
    arch_container = ("vos://datalab.noao!vospace/ls_dr8/calib/wise/modelsky", 36481)
else:
    arch_container = ("vos://datalab.noao!vospace/ls_dr8/south/tractor/275",110)


t0 = time.time()
# base folder where we conduct our tests
#vo_list(token)
#vo_list("")
# clean up b4 we start
parent_working_container = "./%s" % seed_node
print ("-> Remove/clean seed parent container [%s] if exists" % parent_working_container)
vo_rmdir(parent_working_container, expresp="A Node does not exist with the requested URI.")


# creating the directories we are going to work on
print ("-> START: Create working containers")
tpartial0 = time.time()
vo_mkdir(seed_node, "%s/Z/" % seed_node,
         "%s/Z/Y" % seed_node,
         "%s/Z/W" % seed_node,
         "%s/R" % seed_node)
tpartial = time.time()
print("---> END: Make directories [%s]/Z/[Y,W] [%s]/R in [%.2f]s" % (seed_node, seed_node, tpartial - tpartial0))

# List archive container/directory
if LIST_ARCH_CONTAINER or LIST_LARGE_ARCH_CONTAINER:
    print("-> START: List archive container [%s]" % arch_container[0])
    tpartial0 = time.time()
    #vo_list(arch_container[0])
    #print("\t" + "\n\t".join(sc.ls(uri, format="long").splitlines()))
    arch_dir_list = sc.ls(arch_container[0], format="long").splitlines()
    # choose one file from the list to test link
    arch_file_link_to_list = arch_dir_list[10]
    tpartial = time.time()
    arch_dir_list_size = len(arch_dir_list)
    if arch_dir_list_size == arch_container[1]:
      print("OK LIST [%s] with [%d] files" % arch_container)
    else:
      print("FAIL LIST [%s], number of files don't match" % arch_container[0])
    print("---> END: List dirs [%s] n [%.2f]s" % (arch_container[0],  tpartial - tpartial0))

# COPY a directory we know we have data on, internally, within the VOSpace
if COPY_DIR_FROM_ARCHIVE:
    container_to_copy_from = arch_container[0]
    container_to_copy_to = "vos://%s/Z/Y" % seed_node
    print("-> START: Copy archive container from [%s] to [%s]" % (container_to_copy_from, container_to_copy_to))
    tpartial0 = time.time()
    vo_cp((container_to_copy_from, container_to_copy_to))

    ## LIST directories
    list_copy_dir = "vos://%s/Z/Y/275" % seed_node
    no_of_files_copied = len(sc.ls(list_copy_dir).split(','))

    tpartial = time.time()
    print("---> END: Copy container from [%s] to [%s] in [%.2f]s [%d] files copied" % (container_to_copy_from, container_to_copy_to, 
                                                                                       tpartial-tpartial0, no_of_files_copied))

if UPLOAD_DOWNLOAD_MV_RANDOM_FILES:
    # UPLOAD a local file to VOSpace
    print("-> START: Upload random files...")
    tpartial0 = time.time()
    wdata = vo_put_multi_random(args.level, "%s/R/random%%d.fits" % seed_node)
    tpartial = time.time()
    upload_dir = "vos://%s/R" % seed_node
    upload_dir_list = sc.ls(upload_dir, format='long').splitlines()

    print("---> END: Upload files in [%.2f]s [%d] files uploaded" % ((tpartial - tpartial0), len(upload_dir_list)))

    # Download Files
    print("-> START: Download uploaded directory ...")
    tpartial0 = time.time()
    vo_get_multi_and_cmp(wdata, expresp="OK")
    tpartial = time.time()
    print("---> END: Download files in [%.2f]s" % (tpartial - tpartial0))

    # MOVE directories internally
    print("-> START: Move uploaded directory ...")
    tpartial0 = time.time()
    mv_dir_from = "vos://%s/R" % seed_node
    mv_dir_to = "vos://%s/Z" % seed_node
    vo_mv((mv_dir_from, mv_dir_to))
    mv_dir = "vos://%s/Z/R" % seed_node
    mv_dir_ls = sc.ls(mv_dir, format='long').splitlines()
    dir_list = sc.ls("vos://%s/Z/R" % seed_node, format="long").splitlines()
    file_link_to_list = dir_list[-1]
    tpartial = time.time()
    print("---> END: Move directory [%s] to [%s] in [%.2f]s [%d] files moved" % (mv_dir_from, mv_dir_to, tpartial - tpartial0, len(mv_dir_ls)))

    if not CREATE_LINKS_FROM_ARCHIVE_NODES:
        # test link of directory
        link_to = 'vos://%s/L' % seed_node
        link_from = mv_dir_to + "/R"
        print("-> START: Create Link of uploaded container [%s] to [%s]" % (link_from, link_to))
        tpartial0 = time.time()
        file_link = file_link_to_list.split(" ")[-1]

        vo_link((link_from, link_to))
        #vo_list("%s/L" % seed_node)
        #vo_list("%s/L/%s" % (seed_node, file_link))

        link_file = 'vos://%s/L/%s' % (seed_node, file_link)
        res = sc.ls(link_file)
        if res == file_link:
          print("OK LIST %s" %link_file);
        else:
          print("FAIL LIST %s" %link_file);

        tpartial = time.time()
        print("---> END: Link directory [%s] to [%s] in [%.2f]s" % (link_from, link_to, tpartial - tpartial0))

if MOVE_ARCHIVE_COPY:
    # MOVE directories internally
    mv_dir_from = "%s/Z/Y" % seed_node
    mv_dir_to = "%s/Z/W" % seed_node
    print("-> START: Move archive copy from [%s] to [%s]" % (mv_dir_from, mv_dir_to))
    tpartial0 = time.time()
    vo_mv((mv_dir_from, mv_dir_to))

    mv_dir = "vos://%s/Z/W" % seed_node
    mv_dir_ls = sc.ls(mv_dir,format='long').splitlines()
    tpartial = time.time()
    print("---> END: Move directory [%s] to [%s] in [%.2f]s [%d] files moved" % (mv_dir_from, mv_dir_to, tpartial - tpartial0, len(mv_dir_ls)))


if CREATE_LINKS_FROM_ARCHIVE_NODES:
    # test link of directory
    link_to = 'vos://%s/L' % seed_node
    print("-> START: Create Link of arch container [%s] to [%s]" % (arch_container[0], link_to))
    tpartial0 = time.time()
    vo_link((arch_container[0], link_to))
    #vo_list("%s/L" % seed_node)
    file_link = arch_file_link_to_list.split(" ")[-1]
    link_file = 'vos://%s/L/%s' % (seed_node, file_link)
    res = sc.ls(link_file)
    if res == file_link:
      print("OK LIST LN %s" %link_file);
    else:
      print("FAIL LIST LN %s" %link_file);
    #vo_list('vos://%s/L/%s' % (seed_node, file_link))
    tpartial = time.time()
    print("---> END: Link directory [%s] to [%s] in [%.2f]s" % (arch_container[0], link_to, tpartial - tpartial0))


#clean up

print("-> START: Cleanup parent working container [%s]" % seed_node)
tpartial0 = time.time()
vo_rmdir(seed_node)
tpartial = time.time()
print("--> END: Remove/cleanup [%s] directory [%.2f]s" % (seed_node, tpartial - tpartial0))

t1 = time.time()
total = t1-t0
print("--> Total Execution Time [%.2f]" % total)
