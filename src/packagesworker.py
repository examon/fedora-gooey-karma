#!/usr/bin/python2 -tt
# -*- coding:  utf-8 -*-

#    Fedora Gooey Karma prototype
#    based on the https://github.com/mkrizek/fedora-gooey-karma
#
#    Copyright (C) 2013 Tomas Meszaros
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

from PySide import QtCore

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

    def __init__(self, parent=None):
        super(PackagesWorker, self).__init__(parent)

    def set_release(self, release):
        """Sets given argument as a releasever.

        Method stores given Fedora release number to the public class attribute releasever.

        Args:
            release: A string containing Fedora release version number.
        """
        self.releasever = release

    def run(self):
        """Calls load_installed and load_available, when done, emits corresponding signals.
        """
        self.load_installed_packages_start.emit(self)
        __packages_installed = Packages()
        __packages_installed.load_installed(self.releasever)
        self.load_installed_packages_done.emit((self.releasever, __packages_installed))
        print "installed done"

        self.load_available_packages_start.emit(self)
        __packages_available = Packages()
        __packages_available.load_available(self.releasever)
        self.load_available_packages_done.emit((self.releasever, __packages_available))
        print "available done"

# vim: set expandtab ts=4 sts=4 sw=4 :
