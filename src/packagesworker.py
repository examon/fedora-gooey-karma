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
from yum.misc import getCacheDir

class PackagesWorker(QtCore.QThread):

    load_available_packages_start = QtCore.Signal(object)
    load_installed_packages_start = QtCore.Signal(object)
    load_available_packages_done = QtCore.Signal(object)
    load_installed_packages_done = QtCore.Signal(object)
    set_installed_packages = QtCore.Signal(object)

    def __init__(self, queue, bodhi_workers_queue, bodhi_workers_count, parent=None):
        super(PackagesWorker, self).__init__(parent)

        self.queue = queue
        self.bodhi_workers_queue = bodhi_workers_queue
        self.bodhi_workers_count = bodhi_workers_count

        self.yb = yum.YumBase()
        cachedir = getCacheDir()
        self.yb.repos.setCacheDir(cachedir)

        # RPM Transactions
        self.rpmTS = rpm.TransactionSet()

    def set_release(self, release):
        self.releasever = release

    def run(self):
        while True:
            releasever, max_days = self.queue.get()

            # Start loading packages
            self.load_installed_packages_start.emit(self)
            self.load_installed(releasever, max_days)
            # Wait for all packages to be loaded from bodhi
            self.bodhi_workers_queue.join()
            self.load_installed_packages_done.emit(releasever)

            self.queue.task_done()

    def load_installed(self, releasever, max_days):
        # Load from yum rpmdb all installed packages
        self.installed_packages = self.yb.rpmdb.returnPackages()
        # Send it to all bodhi_workers
        for i in range(self.bodhi_workers_count):
            self.bodhi_workers_queue.put(['set_installed_packages', ['bodhi_worker' + str(i), self.installed_packages]])

        # Wait for them to finish
        self.bodhi_workers_queue.join()

        # Send installed packages to GUI
        self.set_installed_packages.emit(self.installed_packages)

        # Prepare days
        now = datetime.datetime.now()
        installed_max_days = datetime.timedelta(max_days)

        # See packages for choosen release
        for pkg in self.installed_packages:
            # Get Fedora release shortcut (e.g. fc18)
            rel = pkg.release.split('.')[-1]
            # We want just packages newer than XY days
            installed = datetime.datetime.fromtimestamp(pkg.installtime)
            installed_timedelta = now - installed
            if installed_timedelta < installed_max_days:
                if rel.startswith('fc') and releasever in rel:
                    if True or pkg.ui_from_repo == '@updates-testing':
                        self.bodhi_workers_queue.put(['package_update', pkg])

# vim: set expandtab ts=4 sts=4 sw=4 :
