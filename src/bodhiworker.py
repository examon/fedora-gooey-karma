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

import re
import subprocess
from PySide import QtCore
from fedora.client import BodhiClient

class BodhiWorker(QtCore.QThread):

    bodhi_query_done = QtCore.Signal(object)

    def __init__(self, worker_name, queue, parent=None):
        super(BodhiWorker, self).__init__(parent)
        self.queue = queue

        self.worker_name = worker_name

        bodhi_url = 'https://admin.fedoraproject.org/updates/'
        self.bc = BodhiClient(bodhi_url, useragent="Fedora Gooey Karma", debug=None)
        self.installed_packages = []

    def run(self):
        while True:
            action, data = self.queue.get()

            if action == 'package_update':
                package = data
                # Get info about this build
                variant, bodhi_update = self.__bodhi_query_pkg(package)
                if bodhi_update:
                    # If we get info from bodhi, prepare some info
                    # and send it to GUI
                    bodhi_update['bugs_by_id'] = self.__get_bugs_by_id(bodhi_update)
                    bodhi_update['bodhi_url'] = self.__get_url(bodhi_update)
                    bodhi_update['test_cases'] = self.__get_testcases(bodhi_update)
                    bodhi_update['formatted_comments'] = self.__get_comments(bodhi_update)
                    bodhi_update['relevant_packages'] = self.__get_relevant_packages(package.name)
                    bodhi_update['parsed_nvr'] = self.__parse_nvr(bodhi_update['itemlist_name'])
                    self.bodhi_query_done.emit([variant, bodhi_update])
                else:
                    # If there is no info from Bodhi, send info to main thread to adjust progress bar
                    self.bodhi_query_done.emit(['progress_only', None])


            elif action == 'set_installed_packages':
                # Is this item for this worker?
                # data[0] worker_name, data[1] installed_packages
                if self.worker_name != data[0]:
                    self.queue.put([action, data])

                self.installed_packages = data[1]
            else:
                print "Bodhi worker: Unknown action"

            self.queue.task_done()

    def __parse_nvr(self, nvr):
        splitted = nvr.split('-')

        # We need at least 3 items
        if len(splitted) < 3:
            return

        # Get items from array
        name = '-'.join(splitted[0:(len(splitted)-2)])
        version = splitted[-2]
        release = splitted[-1]

        return {'name':name, 'version':version, 'release':release}

    def __get_relevant_packages(self, package):
        pkgs = {}
        pkgs['desktop'] = {}
        pkgs['others'] = {}

        # TODO: Should be rewritten to pure python code
        try:
            p = subprocess.Popen('repoquery -q --qf "%{name}" --whatrequires ' + str(package),
                                 shell=True,
                                 stdout=subprocess.PIPE,
                                 stderr=subprocess.STDOUT)

            for line in p.stdout.readlines():
                name = line.lstrip().rstrip()
                for installed_pkg in self.installed_packages:
                    if installed_pkg.name == name:
                        # Which category is it?
                        category = 'others'
                        ## Search for desktop file
                        for filename in installed_pkg.filelist:
                            if re.search('^/usr/share/applications/(.*).desktop$', filename):
                                category = 'desktop'
                                break

                        pkgs[category][name] = installed_pkg
        except IOError, e:
            print "BodhiWorker.__get_relevant_packages: %s" % str(e)


        return pkgs

    def __bodhi_query_pkg(self, package):
        # Search by name
        rel = package.release.split('.')[-1].replace('fc','F')
        pkg_update = self.bc.query(release=rel, package=package.name, status='testing')['updates']

        if pkg_update:
            for update in pkg_update:
                for build in update['builds']:
                    # Does this build match with our current build?
                    if build['nvr'] == package.nvr:
                        update['itemlist_name'] = package.nvr
                        update['yum_package'] = package
                        update['variant'] = 'installed'
                        return ['installed', update]
                    # If not, there could be newer version
                    elif build.package.name == package.name:
                        update['itemlist_name'] = build['nvr']
                        update['yum_package'] = build.package
                        update['variant'] = 'available'
                        return ['available', update]

        return [None, None]

    def __get_bugs_by_id(self, data):
        # Prepare bugs for easier use
        bugs = {}
        if len(data['bugs']):
            for bug in data['bugs']:
                bugs[bug['bz_id']] = bug['title']

        return bugs

    def __get_url(self, data):
        return 'https://admin.fedoraproject.org/updates/' + str(data['updateid'])

    def __get_testcases(self, data):
        if data['nagged'] is not None:
            if 'test_cases' in data['nagged']:
                test_cases = data['nagged']['test_cases']
                for i in range(len(test_cases)):
                    test_cases[i] = test_cases[i].replace("QA:Testcase ", "")
                return test_cases
        # when package does not have test cases
        return []

    def __get_comments(self, data):
        # Get comments and rewrite it to better formatted dict
        comments = []
        i = 1
        if len(data['comments']):
            for comment in data['comments']:
                anonymous = ""
                if comment['anonymous']:
                    anonymous = " (unauthenticated)"
                comments.append({'ord':i,
                                 'text':comment['text'],
                                 'author':comment['author'] + anonymous,
                                 'karma':comment['karma']})
                i = i + 1

        return comments

# vim: set expandtab ts=4 sts=4 sw=4 :
