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
#    Inspired by: http://code.activestate.com/recipes/578299-pyqt-pyside-
#                 thread-safe-global-queue-main-loop-int/

from PySide.QtGui import *
from PySide.QtCore import *

from idlequeue import idle_loop


class ThreadDispatcher(QThread):
    def __init__(self, parent):
        QThread.__init__(self)
        self.parent = parent

    def run(self):
        while True:
            callback = idle_loop.get()
            if callback is None:
                break
            QApplication.postEvent(self.parent, _Event(callback))

    def stop(self):
        idle_loop.put(None)
        self.wait()

class _Event(QEvent):
    EVENT_TYPE = QEvent.Type(QEvent.registerEventType())

    def __init__(self, callback):
        QEvent.__init__(self, _Event.EVENT_TYPE)
        self.callback = callback

# vim: set expandtab ts=4 sts=4 sw=4 :
