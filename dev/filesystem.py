# Copyright (c) 2016-2017, Matteo Cafasso
# All rights reserved.

# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:

# 1. Redistributions of source code must retain the above copyright notice,
# this list of conditions and the following disclaimer.

# 2. Redistributions in binary form must reproduce the above copyright notice,
# this list of conditions and the following disclaimer in the documentation
# and/or other materials provided with the distribution.

# 3. Neither the name of the copyright holder nor the names of its contributors
# may be used to endorse or promote products derived from this software without
# specific prior written permission.

# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO,
# THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR
# PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS
# BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY,
# OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT
# OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY,
# WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE
# OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE,
# EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.


"""GuestFS wrapper to facilitate File System analysis."""

import os
import re
import stat
import logging

from tempfile import NamedTemporaryFile

from guestfs import GuestFS


class FileSystem:
    """Convenience wrapper over GuestFS instance.

    Simplifies some common routines.

    Automatically translates paths according to the contained File System.

    """
    def __init__(self, disk_path):
        self._root = None
        self._handler = GuestFS()

        self.disk_path = disk_path

    def __enter__(self):
        self.mount()

        return self

    def __exit__(self, *_):
        self.umount()

    def __getattr__(self, attr):
        return getattr(self._handler, attr)

    @property
    def osname(self):
        """Returns the Operating System name."""
        return self._handler.inspect_get_type(self._root)

    @property
    def fsroot(self):
        """Returns the file system root."""
        if self.osname == 'windows':
            return '{}:\\'.format(
                self._handler.inspect_get_drive_mappings(self._root)[0][0])
        else:
            return self._handler.inspect_get_mountpoints(self._root)[0][0]

    def mount(self, readonly=True):
        """Mounts the given disk.
        It must be called before any other method.

        """
        self._handler.add_drive_opts(self.disk_path, readonly=True)
        self._handler.launch()

        for mountpoint, device in self._inspect_disk():
            if readonly:
                self._handler.mount_ro(device, mountpoint)
            else:
                self._handler.mount(device, mountpoint)

        if self._handler.inspect_get_type(self._root) == 'windows':
            self.path = self._windows_path
        else:
            self.path = posix_path

    def _inspect_disk(self):
        """Inspects the disk and returns the mountpoints mapping
        as a list which order is the supposed one for correct mounting.

        """
        roots = self._handler.inspect_os()

        if roots:
            self._root = roots[0]
            return sorted(self._handler.inspect_get_mountpoints(self._root),
                          key=lambda m: len(m[0]))
        else:
            raise RuntimeError("No OS found on the given disk image.")

    def umount(self):
        """Unmounts the disk.

        After this method is called no further action is allowed.

        """
        self._handler.close()

    def download(self, source, destination):
        """Downloads the file on the disk at source into destination."""
        self._handler.download(posix_path(source), destination)

    def ls(self, path):
        """Lists the content at the given path."""
        return self._handler.ls(posix_path(path))

    def nodes(self, path):
        """Iterates over the files and directories contained within the disk
        starting from the given path.

        Yields the path of the nodes.

        """
        path = posix_path(path)

        yield from (self.path(path, e) for e in self._handler.find(path))

    def checksum(self, path, hashtype='sha1'):
        """Returns the checksum of the given path."""
        return self._handler.checksum(hashtype, posix_path(path))

    def checksums(self, path, hashtype='sha1'):
        """Iterates over the files hashes contained within the disk
        starting from the given path.

        The hashtype keyword allows to choose the file hashing algorithm.

        Yields the following values:

            "C:\\Windows\\System32\\NTUSER.DAT", "hash" for windows
            "/home/user/text.txt", "hash" for other FS

        """
        with NamedTemporaryFile(buffering=0) as tempfile:
            self._handler.checksums_out(hashtype, posix_path(path),
                                        tempfile.name)

            yield from ((self.path(f[1].lstrip('.')), f[0])
                        for f in (l.decode('utf8').strip().split(None, 1)
                                  for l in tempfile))

    def stat(self, path):
        """Retrieves the status of the node at the given path.

        Returns a dictionary.

        """
        return self._handler.stat(posix_path(path))

    def file(self, path):
        """Analogous to Unix file command.
        Returns the type of node at the given path.

        """
        return self._handler.file(posix_path(path))

    def exists(self, path):
        """Returns whether the path exists."""
        return self._handler.exists(posix_path(path))

    def path(self, *segments):
        """Normalizes the path returned by guestfs in the File System format."""
        raise NotImplementedError("FileSystem needs to be mounted first")

    def _windows_path(self, *segments):
        drive = self._handler.inspect_get_drive_mappings(self._root)[0][0]

        return "%s:%s" % (drive, os.path.join(*segments).replace('/', '\\'))


def hash_filesystem(filesystem, hashtype='sha1'):
    """Utility function for running the files iterator at once.

    Returns a dictionary.

        {'/path/on/filesystem': 'file_hash'}

    """
    try:
        return dict(filesystem.checksums('/'))
    except RuntimeError:
        results = {}

        logging.warning("Error hashing disk %s contents, iterating over files.",
                        filesystem.disk_path)

        for path in filesystem.nodes('/'):
            try:
                regular = stat.S_ISREG(filesystem.stat(path)['mode'])
            except RuntimeError:
                continue  # unaccessible node

            if regular:
                try:
                    results[path] = filesystem.checksum(path, hashtype=hashtype)
                except RuntimeError:
                    logging.debug("Unable to hash %s.", path)

        return results


def posix_path(*segments):
    return re.sub('^[a-zA-Z]:', '', os.path.join(*segments)).replace('\\', '/')
