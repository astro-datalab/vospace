#!/usr/bin/env python2.7

"""A FUSE based filesystem view of VOSpace."""

import time
import myvos as vos
import sys
import urllib
from myfuse import Operations, FuseOSError
from threading import Lock
from errno import EIO, ENOENT, EPERM, EAGAIN, EFAULT
import os
from os import O_RDONLY, O_WRONLY, O_RDWR, O_APPEND
from CadcCache import Cache, CacheCondition, CacheRetry, CacheAborted, \
    IOProxy, FlushNodeQueue, CacheError
from logExceptions import logExceptions
import logging

logger = logging.getLogger('myvofs')
logger.setLevel(logging.ERROR)
if sys.version_info[1] > 6:
    logger.addHandler(logging.NullHandler())


def flag2mode(flags):
    md = {O_RDONLY: 'r', O_WRONLY: 'w', O_RDWR: 'w+'}
    m = md[flags & (O_RDONLY | O_WRONLY | O_RDWR)]

    # If the write bit was set, check to see if the append bit was also set.
    if flags | O_APPEND:
        m = m.replace('w', 'a', 1)

    return m


class MyIOProxy(IOProxy):
    def __init__(self, vofs, path):
        super(MyIOProxy, self).__init__()
        self.vofs = vofs
        # This is the vofile object last used
        self.lastVOFile = None
        self.size = None
        self.md5 = None
        self.path = path
        self.condition = CacheCondition(None)

    def __str__(self):
        return "Path:{0}  Size:{1}  MD5:{2}  condition:{3}".format(self.path,
                                                                   self.size,
                                                                   self.md5,
                                                                   self.condition)
        
    #@logExceptions()
    def writeToBacking(self):
        """
        Write a file in the cache to the remote file.
        """
        logger.debug("***** CALLING HERE *****")
        logger.debug("PUSHING contents of %s to VOSpace location %s " %
                (self.cacheFile.cacheDataFile, self.cacheFile.path))

        (size, mtime) = self.cacheFile.getFileInfo()

        logger.debug("opening a new vo file for {0}".format(self.cacheFile.path))
        dest_uri = self.vofs.getNode(self.cacheFile.path).uri
        md5 = hashlib.md5()
        BUFSIZE = Cache.IO_BLOCK_SIZE
        vo_file_handle = self.vofs.client.open(dest_uri, mode=os.O_WRONLY, size=size)
        cache_file_handle = open(self.cacheFile.cacheDataFile, 'r')
        try:
            while True:
                buf = cache_file_handle.read(BUFSIZE)
                if len(buf) == 0:
                    break
                if self.cacheFile.writeAborted:
                    raise CacheAborted("Write to VOSpace aborted.")
                vo_file_handle.write(buf)
                md5.update(buf)
        except Exception as e:
            logger.debug("{0}".format(e))
            raise e
        finally:
            vo_file_handle.close()
            cache_file_handle.close()

        vo_md5 = self.vofs.getNode(dest_uri, force=True).props.get('MD5','d41d8cd98f00b204e9800998ecf8427e')
        if md5.hexdigest() != vo_md5:
            raise OSError(EIO,
                          "md5 sums of source ({0}) and destination ){1}) don't match".format(
                              self.cacheFile.cacheDataFile, dest_uri))

        return vo_md5

    @logExceptions()
    def readFromBacking(self, size=None, offset=0,
            blockSize=Cache.IO_BLOCK_SIZE):
        """
        Read from VOSpace into cache
        """

        # Read a range
        if size is not None or offset != 0:
            if size is None:
                endStr = ""
            else:
                endStr = str(offset + size - 1)
            byte_range = "bytes=%s-%s" % (str(offset), endStr)
        else:
            byte_range = None
        logger.debug("reading range: %s" % (str(byte_range)))

        if self.lastVOFile is None:
            logger.debug("Opening a new vo file on %s",
                    self.cacheFile.path)
            self.lastVOFile = self.vofs.client.open(self.cacheFile.path,
                    mode=os.O_RDONLY, view="data", size=size, range=byte_range,
                    possible_partial_read=True)
        else:
            logger.debug("Opening a existing vo file on %s",
                    self.lastVOFile.URLs[self.lastVOFile.urlIndex])
            self.lastVOFile.open(
                    self.lastVOFile.URLs[self.lastVOFile.urlIndex],
                    bytes=byte_range, possible_partial_read=True)
        try:
#            vos.logger.debug("HERE*")
            vos.logger.debug("reading from %s" % (
                    str(self.lastVOFile.URLs[self.lastVOFile.urlIndex])))
            while True:
                try:
                    buff = self.lastVOFile.read(blockSize)
                except IOError as e:
                    # existing URLs do not work anymore. Try another
                    # transfer, forcing a full negotiation. This
                    # handles the case that we tried a short cut URL
                    # and it failed, so now we can try the full URL
                    # list. If it still fails let the error propagate
                    # to client
                    logger.debug("Error while reading: {0}".format(io_error))
                    # MJG: Should view = "data" instead of "defaultview"
                    self.lastVOFile = self.vofs.client.open(
                            self.cacheFile.path, mode=os.O_RDONLY, view="defaultview",
                            size=size, range=byte_range, full_negotiation=True, possible_partial_read=True)
                    buff = self.lastVOFile.read(blockSize)

                if not self.cacheFile.gotHeader:
                    info = self.lastVOFile.getFileInfo()
                    self.cacheFile.setHeader(info[0], info[1])

                if buff is None:
                    logger.debug("buffer for {0} is None".format(self.cacheFile.path))
                else:
                    logger.debug("Writing: {0} bytes at {1} to cache for {2}".format(len(buff), offset, self.cacheFile.path))
                if not buff:
                    break
                try:
#                    vos.logger.debug("HERE*")
                    self.writeToCache(buff, offset)
                except CacheAborted:
                    # The transfer was aborted.
                    break
                offset += len(buff)
        except Exception as e:
            self.exception = e
            raise
        finally:
            self.lastVOFile.close()

        logger.debug("Wrote: %d bytes to cache for %s" % (offset,
                self.cacheFile.path))

    def getMD5(self):
        if self.md5 is None:
            node = self.vofs.getNode(self.path)
            self.setSize(int(node.props.get('length')))
            self.setMD5(node.props.get('MD5'))

        return self.md5

    def getSize(self):
        if self.size is None:
            node = self.vofs.getNode(self.path)
            self.setSize(int(node.props.get('length')))
            self.setMD5(node.props.get('MD5'))

        return self.size

    def set_md5(self, md5):
        """
        set the value of the MD5 sum returned for this location.

        @rtype : str
        @param md5: str representation of the MD5 sum of a file.
        """
        self.md5 = md5

    def setSize(self, size):
        self.size = size


class HandleWrapper(object):
    """
    Wrapper for cache file handlers. Each wrapper represents an open request.
    Multiple wrappers of the same file share the same cache file handler.
    """

    # A list of all file handles
    handleList = {}
    myLock = Lock()

    def __init__(self, cacheFileHandle, readOnly=False):
        self.cacheFileHandle = cacheFileHandle
        self.readOnly = readOnly
        with HandleWrapper.myLock:
            HandleWrapper.handleList[id(self)] = self

    def getId(self):
        return id(self)

    @staticmethod
    def findHandle(id):
        with HandleWrapper.myLock:
            theHandle = HandleWrapper.handleList[id]
        return theHandle

    @logExceptions()
    def release(self):
        with HandleWrapper.myLock:
            del HandleWrapper.handleList[id(self)]


class VOFS(Operations):
    cacheTimeout = 30.0
    """
    The VOFS filesystem opperations class.  Requires the vos (VOSpace)
    python package.

    To use this you will also need a VOSpace account from the CADC.
    """
    ### VOSpace doesn't support these so I've disabled these operations.
    chown = None
    link = None
    mknode = None
    symlink = None
    getxattr = None
    listxattr = None
    removexattr = None
    setxattr = None
    chmod = None
    
    def __init__(self, root, cache_dir, options, conn=None,
                 cache_limit=1024, cache_nodes=False,
                 cache_max_flush_threads=10, secure_get=False):
        """Initialize the VOFS.

        cache_limit is in MB.
        The style here is to use dictionaries to contain information
        about the Node.  The full VOSpace path is used as the Key for
        most of these dictionaries."""

        self.cache_nodes = cache_nodes

        # Standard attribtutes of the Node
        # Where in the file system this Node is currently located
        self.loading_dir = {}

        # Command line options.
        # This seems to just be opt.readonly so set this explicitly
        self.opt = options
# MJG        self.readonly = readonly

        # What is the 'root' of the VOSpace? (eg vos:MyVOSpace)
        self.root = root

        # VOSpace is a bit slow so we do some caching.
        self.cache = Cache(cache_dir, cache_limit, False, VOFS.cacheTimeout, \
                               maxFlushThreads=cache_max_flush_threads)

        # All communication with the VOSpace goes through this client
        # connection.
        try:
            # MJG: We're not using the CADC short cut or secure get
            self.client = vos.Client(rootNode=root, conn=conn)
#             self.client = vos.Client(rootNode=root, conn=conn, cadc_short_cut=True, secure_get=secure_get)
        except Exception as e:
            e = FuseOSError(getattr(e, 'errno', EIO))
            e.filename = root
            e.strerror = getattr(e, 'strerror', 'failed while making mount')
            raise e

        # Create a condition variable to get rid of those nasty sleeps
        self.condition = CacheCondition(lock=None, timeout=VOFS.cacheTimeout)
        
    def __call__(self, op, *args):
        logger.debug('-> {0} {1}'.format(op, repr(args)))
        ret = None
        try:
            if not hasattr(self, op):
                raise FuseOSError(EFAULT)
            ret = getattr(self, op)(*args)
            return ret
        except Exception as all_exceptions:
            errno = EAGAIN
            ret = str(all_exceptions)
            if getattr(all_exceptions, 'errno', None) is not None:
                errno = all_exceptions.errno
            exception = FuseOSError(errno)
            raise exception
        finally:
            logger.debug('<- {0} {1}'.format(op, repr(ret)))

    #@logExceptions()
    def access(self, path, mode):
        """Check if path is accessible.

        Only checks read access, mode is currently ignored"""
        logger.debug("Checking if -->{0}<-- is accessible".format(path))
        try:
            self.getNode(path)
        except:
            return -1
        return 0

    #@logExceptions()
    def no_chmod(self, path, mode):
        """
        Set the read/write groups on the VOSpace node based on chmod style
        modes.

        This function is a bit funny as the VOSpace spec sets the name
        of the read and write groups instead of having mode setting as
        a separate action.  A chmod that adds group permission thus
        becomes a chgrp action.

        Here I use the logic that the new group will be inherited from
        the container group information.
        """
        logger.debug("Changing mode for %s to %d" % (path, mode))

        node = self.getNode(path)
        parent = self.getNode(os.path.dirname(path))

        if node.groupread == "NONE":
            node.groupread = parent.groupread
        if node.groupwrite == "NONE":
            node.groupwrite = parent.groupwrite
        # The 'node' object returned by getNode has a chmod method
        # that we now call to set the mod, since we set the group(s)
        # above.  NOTE: If the parrent doesn't have group then NONE is
        # passed up and the groupwrite and groupread will be set tovos:
        # the string NONE.
        if node.chmod(mode):
            # Now set the time of change/modification on the path...
            # TODO: This has to be broken. Attributes may come from Cache if
            # the file is modified. Even if they don't come from the cache,
            # the getAttr method calls getNode with force=True, which returns
            # a different Node object than "node". The st_ctime value will be
            # updated on the newly replaced node in self.node[path] but
            # not in node, then node is pushed to vospace without the st_time
            # change, and then it is pulled back, overwriting the change that
            # was made in self.node[path]. Plus modifying the mtime of the file
            # is not conventional Unix behaviour. The mtime of the parent
            # directory would be changed.
            self.getattr(path)['st_ctime'] = time.time()
            ## if node.chmod returns false then no changes were made.
            self.client.update(node)
            self.getNode(path, force=True)
            # MJG: Any changes only currently come into effect when the
            # next mount happens

    #@logExceptions()
    def create(self, path, flags, fi=None):
        """Create a node. Currently ignores the ownership mode
        @param path: the container/dataNode in VOSpace to be created
        @param flags: Read/Write settings (eg. 600)
        """

        logger.debug("Creating a node: %s with flags %s" %
                (path, str(flags)))

        # Create is handle by the client.
        # This should fail if the basepath doesn't exist
        try:
            self.client.open(path, os.O_CREAT).close() # *** MJG
            node = self.getNode(path)
            parent = self.getNode(os.path.dirname(path))

            # Force inheritance of group settings.
            node.groupread = parent.groupread
            node.groupwrite = parent.groupwrite
            if node.chmod(flags):
                # chmod returns True if the mode changed but doesn't do update.
                self.client.update(node)
                node = self.getNode(path, force=True)

        except Exception as e:
            logger.error(str(e))
            logger.error("Error trying to create Node {0}".format(path))
            f = FuseOSError(getattr(e, 'errno', EIO))
            f.strerror = getattr(e, 'strerror', 'failed to create {0}'.format(path))
            raise f

        ## now we can just open the file in the usual way and return the handle
        return self.open(path, os.O_WRONLY)

    def destroy(self, path):
        """Called on filesystem destruction. Path is always /

           Call the flushNodeQueue join() method which will block
           until any running and/or queued jobs are finished"""
    
        if self.cache.flushNodeQueue is None:
            raise CacheError("flushNodeQueue has not been initialized")
        self.cache.flushNodeQueue.join()
        self.cache.flushNodeQueue = None

    #@logExceptions()
    def fsync(self, path, data_sync, file_id):
#        if self.opt.readonly:
        if self.readonly:
            vos.logger.debug("File system is readonly, no sync allowed")
            return

        try:
            fh = HandleWrapper.file_handle(file_id)
        except KeyError:
            raise FuseOSError(EIO)

        if fh.read_only:
            raise FuseOSError(EPERM)

        fh.cache_file_handle.fsync()

    def getNode(self, path, force=False, limit=0):
        """Use the client and pull the node from VOSpace.

        Currently force=False is the default... so we never check
        VOSpace to see if the node metadata is different from what we
        have.  This doesn't keep the node metadata current but is
        faster if VOSpace is slow.
        @type limit: int or None
        @rtype : vos.Node
        @param path: the VOSpace node to get
        @param force: force retrieval (true) or provide cached version if available (false)?
        @param limit: Number of child nodes to retrieve per request, if limit  is None then get max returned by service.
        """

        ## Pull the node meta data from VOSpace.
        logger.debug("requesting node {0} from VOSpace. Force: {1}".format(path, force))
        node = self.client.getNode(path, force=force, limit=limit)

        return node
    
    #@logExceptions()
    def getattr(self, path, id=None):
        """
        Build some attributes for this file, we have to make-up some stuff
        """
        # Try to get the attributes from the cache first. This will only return
        # a result if the files has been modified and not flushed to vospace.
#        attr = self.cache.getAttr(path)
#        return attr is not None and attr or self.getNode(path, limit=0, force=False).attr
        cacheFileAttrs = self.cache.getAttr(path)
        logger.debug("***** GETATTR %s *****" % path)
        if cacheFileAttrs is not None:
            return cacheFileAttrs

        return self.getNode(path, limit=0, force=False).attr

    
    def init(self, path):
        """Called on filesystem initialization. (Path is always /)

           Here is where we start the worker threads for the queue
           that flushes nodes."""

        self.cache.flushNodeQueue = \
            FlushNodeQueue(maxFlushThreads=self.cache.maxFlushThreads)

    #@logExceptions()
    def mkdir(self, path, mode):
        """Create a container node in the VOSpace at the correct location.

        set the mode after creation. """
        try:
            self.client.mkdir(path)
        except IOError as io_error:
            if "read-only mode" in str(io_error):
                raise FuseOSError(EPERM)
            raise FuseOSError(getattr(io_error, 'errno', EFAULT))

    #@logExceptions()
    def open(self, path, flags, *mode):
        """Open file with the desired modes

        Here we return a handle to the cached version of the file
        which is updated if older and out of synce with VOSpace.

        """

        logger.debug("Opening %s with flags %s" % (path, flag2mode(flags)))
        node = None

        # according to man for open(2), flags must contain one of O_RDWR,
        # O_WRONLY or O_RDONLY. Because O_RDONLY=0 and options other than
        # O_RDWR, O_WRONLY and O_RDONLY may be present,
        # readonly = (flags == O_RDONLY) and readonly = (flags | # O_RDONLY)
        # won't work. The only way to detect if it's a read only is to check
        # whether the other two flags are absent.
        read_only = ((flags & (os.O_RDWR | os.O_WRONLY)) == 0)

        must_exist = not ((flags & os.O_CREAT) == os.O_CREAT)
        cache_file_attrs = self.cache.getAttr(path)
        if cache_file_attrs is None and not read_only:
            # file in the cache not in the process of being modified.
            # see if this node already exists in the cache; if not get info
            # from vospace
            try:
                node = self.getNode(path)
            except IOError as e:
                if e.errno == 404:
                    # file does not exist
                    if not flags & os.O_CREAT:
                        # file doesn't exist unless created
                        raise FuseOSError(ENOENT)
                else:
                    raise FuseOSError(e.errno)

        ### check if this file is locked, if locked on vospace then don't open
        locked = False

        if node and node.props.get('islocked', False):
            logger.debug("%s is locked." % path)
            locked = True

        if not read_only and node and not locked:
            if node.type == "vos:DataNode":
                parent_node = self.getNode(os.path.dirname(path),
                        force=False, limit=1)
                if parent_node.props.get('islocked', False):
                    logger.debug("%s is locked by parent node." % path)
                    locked = True
            elif node.type == "vos:LinkNode":
                try:
                    # sometimes targetNodes aren't internal... so then not
                    # locked
                    target_node = self.getNode(node.target, force=False,
                            limit=1)
                    if target_node.props.get('islocked', False):
                        logger.debug("{0} target node is locked.".format(path))
                        locked = True
                    else:
                        target_parent_node = self.getNode(os.path.dirname(
                                node.target), force=False, limit=1)
                        if target_parent_node.props.get('islocked', False):
                            logger.debug(
                                    "{0} is locked by target parent node.".format(path))
                            locked = True
                except Exception as lock_exception:
                    logger.warn("Error while checking for lock: {0}".format(str(lock_exception)))
                    pass

        if locked and not read_only:
            # file is locked, cannot write
            e = OSError(ENOENT)
            e.filename = path
            e.strerror = "Cannot create locked file"
            logger.debug("{0}".format(e))
            raise e

        my_proxy = MyIOProxy(self, path)
        if node is not None:
            my_proxy.setSize(int(node.props.get('length')))
            my_proxy.setMD5(node.props.get('MD5'))

        logger.debug("IO Proxy initialized:{0}  in backing.".format(my_proxy))
            
        # new file in cache library or if no node information (node not in
        # vospace).
        handle = self.cache.open(path, flags & os.O_WRONLY != 0, must_exist,
                my_proxy, self.cache_nodes)

        logger.debug("Creating file:{0}  in backing.".format(path))

        if flags & os.O_TRUNC != 0:
            handle.truncate(0)
        if node is not None:
            handle.setHeader(my_proxy.getSize(), my_proxy.get_md5())
        return HandleWrapper(handle, read_only).get_id()

    #@logExceptions()
    def read(self, path, size=0, offset=0, file_id=None):
        """
        Read the required bytes from the file and return a buffer containing
        the bytes.
        """

        ## Read from the requested filehandle, which was set during 'open'
        if file_id is None:
            raise FuseOSError(EIO)

        logger.debug("reading range: %s %d %d %d" %
                (path, size, offset, file_id))

        try:
            fh = HandleWrapper.find_handle(file_id)
        except KeyError:
            raise FuseOSError(EIO)

        return fh.cache_file_handle.read(size, offset)

    #@logExceptions()
    def readlink(self, path):
        """
        Return a string representing the path to which the symbolic link
        points.

        path: filesystem location that is a link

        returns the file that path is a link to.

        Currently doesn't provide correct capabilty for VOSpace FS.
        """
        return self.getNode(path).name+"?link="+urllib.quote_plus(self.getNode(path).target)

    #@logExceptions()
    def readdir(self, path, id):
        """Send a list of entries in this directory"""
        logger.debug("Getting directory list for {0}".format(path))
        ## reading from VOSpace can be slow, we'll do this in a thread
        import thread
        with self.condition:
            if not self.loading_dir.get(path, False):
                self.loading_dir[path] = True
                thread.start_new_thread(self.load_dir, (path, ))

            while self.loading_dir.get(path, False):
                logger.debug("Waiting ... ")
                self.condition.wait()
        return ['.', '..'] + [e.name.encode('utf-8') for e in self.getNode(
                path, force=False, limit=None).getNodeList()]

    #@logExceptions()
    def load_dir(self, path):
        """Load the dirlist from VOSpace.
        This should always be run in a thread."""
        try:
            logger.debug("Starting getNodeList thread")
            self.getNode(path, force=True,
                    limit=None).getNodeList()
            logger.debug("Got listing for {0}".format(path))
        finally:
            self.loading_dir[path] = False
            with self.condition:
                self.condition.notify_all()
        return

    def flush(self, path, file_id):

        logger.debug("flushing {0}".format(file_id))
        fh = HandleWrapper.file_handle(file_id)

        try:
            fh.cache_file_handle.flush()
        except CacheRetry as ce:
            logger.critical(str(ce))
            logger.critical("Push to VOSpace reached FUSE timeout, continuing VOSpace push in background.")
            pass
        return 0
    
    #@logExceptions()
    def release(self, path, id):
        """Close the file

        @param path: vospace path to close reference to
        @param file_id: file_handle_id to close reference to
        """
        logger.debug("releasing file %d " % file_id)
        fh = HandleWrapper.file_handle(file_id)
        fh.cache_file_handle.release()
        if fh.cache_file_handle.fileModified:
            # This makes the node disappear from the nodeCache.
            with self.client.nodeCache.volatile(path):
                pass
        return fh.release()

    #@logExceptions()
    def rename(self, src, dest):
        """Rename a data node into a new container"""
        logger.debug("Original %s -> %s" % (src, dest))
        #if not self.client.isfile(src):
        #   return -1
        #if not self.client.isdir(os.path.dirname(dest)):
        #    return -1
        try:
            logger.debug("Moving %s to %s" % (src, dest))
            result = self.client.move(src, dest)
            logger.debug(str(result))
            if result:
                self.cache.renameFile(src, dest)
                return 0
            return -1
        except Exception, e:
            vos.logger.error("%s" % str(e))
            import re
            if re.search('NodeLocked', str(e)) is not None:
                raise FuseOSError(EPERM)
            return -1

    #@logExceptions()
    def rmdir(self, path):
        node = self.getNode(path)
        if node and node.props.get('islocked', False):
            logger.debug("%s is locked." % path)
            raise FuseOSError(EPERM)
        self.client.delete(path)

    #@logExceptions()
    def statfs(self, path):
        node = self.getNode(path)
        block_size = 512
        n_bytes = 2 ** 33
        free = 2 ** 33

        if 'quota' in node.props:
            bytes = int(node.props.get('quota', 2 ** 33))
            used = int(node.props.get('length', 2 ** 33))
            free = bytes - used
        sfs = {'f_bsize': block_size, 'f_frsize': block_size, 'f_blocks': int(n_bytes / block_size),
               'f_bfree': int(free / block_size), 'f_bavail': int(free / block_size),
               'f_files': len(node.getNodeList()), 'f_ffree': 2 * 10, 'f_favail': 2 * 10, 'f_flags': 0,
               'f_namemax': 256}
        return sfs

    #@logExceptions()
    def truncate(self, path, length, file_id=None):
        """Perform a file truncation to length bytes"""
        logger.debug("Attempting to truncate {0}({1}) to length {2}".format(path, file_id, length))

        if file_id is None:
            # Ensure the file exists.
            if length == 0:
                fh = self.open(path, os.O_RDWR | os.O_TRUNC)
                self.release(path, fh)
                return

            fh = self.open(path, os.O_RDWR)
            try:
                self.truncate(path, length, fh)
            finally:
                self.release(path, fh)
        else:
            fh = HandleWrapper.find_handle(file_id)
            if fh.read_only:
                logger.debug("file was not opened for writing")
                raise FuseOSError(EPERM)
            fh.cache_file_handle.truncate(length)
        return

    #@logExceptions()
    def unlink(self, path):
        node = self.getNode(path, force=False, limit=1)
        if node and node.props.get('islocked', False):
            logger.debug("%s is locked." % path)
            raise FuseOSError(EPERM)
        self.cache.unlinkFile(path)
        if node:
            self.client.delete(path)

    @logExceptions()
    def write(self, path, data, size, offset, file_id=None):
        import ctypes

#        if self.opt.readonly:
        if self.readonly:
            logger.debug("File system is readonly.. so writing 0 bytes\n")
            return 0

        try:
            fh = HandleWrapper.find_handle(file_id)
        except KeyError:
            raise FuseOSError(EIO)

        if fh.read_only:
            logger.debug("file was not opened for writing")
            raise FuseOSError(EPERM)

        logger.debug("%s -> %s" % (path, fh))
        logger.debug("%d --> %d" % (offset, offset + size))
        return fh.cache_file_handle.write(data, size, offset)
