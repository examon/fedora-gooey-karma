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

from PySide import QtCore
from fedora.client import BodhiClient

class BodhiWorker(QtCore.QThread):

    bodhi_query_done = QtCore.Signal(object)

    def __init__(self, queue, parent=None):
        super(BodhiWorker, self).__init__(parent)
        self.queue = queue

        bodhi_url = 'https://admin.fedoraproject.org/updates/'
        self.bc = BodhiClient(bodhi_url, useragent="Fedora Gooey Karma", debug=None)

    def run(self):
        while True:
            package = self.queue.get()

            # Get info about this build
            bodhi_update = self.__bodhi_query_pkg(package)
            if bodhi_update:
                # If we get info from bodhi, prepare some info
                # and send it to GUI
                bodhi_update['bugs_by_id'] = self.__get_bugs_by_id(bodhi_update)
                bodhi_update['bodhi_url'] = self.__get_url(bodhi_update)
                bodhi_update['test_cases'] = self.__get_testcases(bodhi_update)
                bodhi_update['formatted_comments'] = self.__get_comments(bodhi_update)
                self.bodhi_query_done.emit(bodhi_update)

            self.queue.task_done()

    def __bodhi_query_pkg(self, package):
        # Search by name
        rel = package.release.split('.')[-1].replace('fc','F')
        pkg_update = self.bc.query(release=rel, package=package.name)['updates']

        if pkg_update:
            for update in pkg_update:
                for build in update['builds']:
                    # Does this build match with our current build?
                    if build['nvr'] == package.nvr:
                        update['itemlist_name'] = package.nvr
                        return update

        return None

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
        """Fetches user comments from the data.

        Loads all user freedback info, e.g. comments, karma, username.

        Args:
            data: A dictionary containing Bodhi client query output for each package (see: testing_builds).

        Returns:
            comments: A list of lists where earch sublist represents feedback for one package.

                      comments = [ ["Feedback string", "author nickname", int(karma)], ... ]
        """
        comments = []
        if len(data['comments']):
            for comment in data['comments']:
                anonymous = ""
                if comment['anonymous']:
                    anonymous = " (unauthenticated)"
                comments.append([comment['text'], comment['author'] + anonymous,
                                comment['karma']])
        return comments

# vim: set expandtab ts=4 sts=4 sw=4 :
