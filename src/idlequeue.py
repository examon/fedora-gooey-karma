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

import Queue

# Queue for main thread
idle_loop = Queue.Queue()

def main_thread_call(func, *args, **kwargs):
    def idle():
        func(*args, **kwargs)
        return False
    idle_loop.put(idle)

# vim: set expandtab ts=4 sts=4 sw=4 :
