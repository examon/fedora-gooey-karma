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

import os
import pickle

class PackagesHolder:

    def __init__(self):
        self.__db = []

    # Override some methods to be able to work with it as with list
    def __getitem__(self, key):
        # This method allows to use foo[x]
        if key < len(self.__db) and key >= 0:
            return self.__db[key]
        else:
            raise KeyError("PackageHolder: out of range")

    def __iter__(self):
        # This method allows to use iteration, like foo in bar
        class iterator(object):
            def __init__(self, obj):
                self.obj = obj
                self.index = -1

            def __iter__(self):
                 return self

            def next(self):
                if self.index < len(self.obj)-1:
                    self.index += 1
                    return self.obj[self.index]
                else:
                    raise StopIteration

        return iterator(self.__db)

    # Common methods
    def add_package(self, package):
        package = package.strip()
        if package == '':
            return False

        if package not in self.__db:
            self.__db.append(package)
            return True

        return False

    def remove_package(self, package):
        package = package.strip()
        try:
            self.__db.remove(package)
            return True
        except:
            pass

        return False


class Config:

    def __init__(self):
        self.__config_file = None
        try:  
            self.__config_file = os.environ["HOME"] + "/.fedora-gooey-karma"
        except KeyError: 
            print "Please set the environment variable HOME"


        self.ignored_packages = PackagesHolder()
        self.favorited_packages = PackagesHolder()
        self.__fas_name = ''
        self.__fas_password = ''

    # Getters, setters, deleters
    def get_fas_name(self): return self.__fas_name
    def get_fas_password(self): return self.__fas_password
    def set_fas_name(self, name): self.__fas_name = name
    def set_fas_password(self, password): self.__fas_password = password

    # Set properties
    fas_name = property(get_fas_name, set_fas_name)
    fas_password = property(get_fas_password, set_fas_password)

    def load_config(self):
        # Loads config from home dir
        obj = None
        try:
            f = open(self.__config_file, 'rb')
            obj = pickle.load(f)
            f.close()
        except:
            print "Cannot open config file " + self.__config_file


        # If we have object from pickle file, assign it
        if obj:
            for attr in ['favorited_packages', 'ignored_packages', '__fas_name', '__fas_password']:
                setattr(self, attr, getattr(obj, attr, None))


    def save_config(self):
        # Saves config to home dir
        try:
            f = open(self.__config_file, 'wb')
            pickle.dump(self, f)
            f.close()
        except:
            print "Cannot open config file " + self.__config_file


# vim: set expandtab ts=4 sts=4 sw=4 :
