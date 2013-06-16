#!/usr/bin/python2 -tt
# -*- coding:  utf-8 -*-

#    Fedora Gooey Karma prototype
#    based on the https://github.com/mkrizek/fedora-gooey-karma
#
#    Copyright (C) 2013 
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
#    Author: Branislav Blaskovic <branislav@blaskovic.sk>
#    Author: Tomas Meszaros <exo@tty.sk>

import yum
import rpm
import datetime
from PySide import QtCore
from fedora.client import BodhiClient
from yum.misc import getCacheDir

from packages import Packages

class PackagesWorker(QtCore.QThread):
    """Worker class used for new thread.

    Attributes:
        releasever: A string storing Fedora release version number.
        load_available_packages_start: A signal, emitted when load_available is called.
        load_available_packages_done: A signal, emitted when load_available returns.
        load_installed_packages_start: A signal, emitted when load_installed is called.
        load_installed_packages_done: A signal, emitted when load_installed returns.
    """

    load_available_packages_start = QtCore.Signal(object)
    load_installed_packages_start = QtCore.Signal(object)
    load_available_packages_done = QtCore.Signal(object)
    load_installed_packages_done = QtCore.Signal(object)

    set_installed_packages = QtCore.Signal(object)

    def __init__(self, queue, bodhi_workers_queue, parent=None):
        super(PackagesWorker, self).__init__(parent)
        
        self.queue = queue
        self.bodhi_workers_queue = bodhi_workers_queue

        self.yb = yum.YumBase()
        cachedir = getCacheDir()
        self.yb.repos.setCacheDir(cachedir)

        # RPM Transactions
        self.rpmTS = rpm.TransactionSet()

    def set_release(self, release):
        """Sets given argument as a releasever.

        Method stores given Fedora release number to the public class attribute releasever.

        Args:
            release: A string containing Fedora release version number.
        """
        self.releasever = release

    def run(self):
        while True:
            releasever = self.queue.get()
            
            print "Starting Packages worker for F" + str(releasever)
            """Calls load_installed and load_available, when done, emits corresponding signals.
            """
            self.load_installed_packages_start.emit(self)
            self.load_installed(releasever)
            self.bodhi_workers_queue.join()
            self.load_installed_packages_done.emit(releasever)

            self.queue.task_done()

    def load_installed(self, releasever):
        """Loads installed packages related to the releasever.

        Loads all locally installed packages related to the Fedora release version.
        Processes only those installed packages which are from @updates-testing repo.

        Stores all loaded data in the testing_builds & builds.

        Args:
            releasever: Fedora release version number (e.g. 18).
        """
        
        # Load from yum rpmdb all installed packages
        installed_packages = self.yb.rpmdb.returnPackages()

        # Send installed packages to GUI
        self.set_installed_packages.emit(installed_packages)

        installed_packages_count = len(installed_packages)
        installed_updates_testing = []
        
        # Prepare days
        # TODO: grab it from GUI, not constant
        now = datetime.datetime.now()
        max_days = 10
        installed_max_days = datetime.timedelta(max_days)

        # See packages for choosen release
        for pkg in installed_packages:
            # Get Fedora release shortcut (e.g. fc18)
            rel = pkg.release.split('.')[-1]
            # We want just packages newer than XY days
            installed = datetime.datetime.fromtimestamp(pkg.installtime)
            installed_timedelta = now - installed
            if installed_timedelta < installed_max_days:
                if rel.startswith('fc') and releasever in rel:
                    if pkg.ui_from_repo == '@updates-testing':
                        self.bodhi_workers_queue.put(pkg)

# vim: set expandtab ts=4 sts=4 sw=4 :
