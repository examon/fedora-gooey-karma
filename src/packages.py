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

import yum
import rpm
from fedora.client.bodhi import BodhiClient
from yum.misc import getCacheDir

class Packages(object):
    """This class makes information retrieval from the Bodhi query data easier.

    Attributes:
        builds: A list of dictionaries, where each dict contains basic info about one package.

                builds[index]['nvr'] - full package name (including version, etc.)
                builds[index]['name'] - package name without version
                builds[index]['installed'] - True when package is installed

        testing_builds: A dictionary containing Bodhi client query output for earch package
    """

    def __init__(self):
        bodhi_url = 'https://admin.fedoraproject.org/updates/'
        self.bc = BodhiClient(bodhi_url, debug=None)
        
        # Yum Base
        self.yb = yum.YumBase()
        cachedir = getCacheDir()
        self.yb.repos.setCacheDir(cachedir)

        # RPM Transactions
        self.rpmTS = rpm.TransactionSet()

        self.builds = []
        self.testing_builds = {}

    def get_package_info(self, name):
        packages = self.rpmTS.dbMatch('name', name)
        out = []
        for package in packages:
            out.append(package)

        return out

    def get_builds(self, data):
        """Fetches builds from the data.

        Retrieves builds list from the packages data.

        Args:
            data: A dictionary containing Bodhi client query output for each package (see: testing_builds).

        Returns:
            builds: A list of all builds fetched from the data.
        """
        builds = []
        for build in data['builds']:
            builds.append(build['nvr'])
        return builds

    def get_bugs(self, data):
        """Fetches bugs from the data.

        Searches for all bugs in package data.

        Args:
            data: A dictionary containing Bodhi client query output for each package (see: testing_builds).

        Returns:
            bugs: A list of all builds fetched from the data.

                  bugs = { bug_id: "Bug commentary", .... }
        """
        bugs = {}
        if len(data['bugs']):
            for bug in data['bugs']:
                bugs[bug['bz_id']] = bug['title']
        return bugs

    def get_comments(self, data):
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

    def get_test_cases(self, data):
        """Gets package test cases from the data

        Retrieves all test cases from the package data.

        Args:
            data: A dictionary containing Bodhi client query output for each package (see: testing_builds).

        Returns:
            test_cases: A list containing all test cases related to data.

            When data does not contains any test cases, returns empty list.
        """
        if data['nagged'] is not None:
            if 'test_cases' in data['nagged']:
                test_cases = data['nagged']['test_cases']
                for i in range(len(test_cases)):
                    test_cases[i] = test_cases[i].replace("QA:Testcase ", "")
                return test_cases
        # when package does not have test cases
        return []

    def load_available(self, releasever):
        """Loads available packages from the bodhi related to the passed release version.

        Should load only pending & testing packages.
        Bodhi url: https://admin.fedoraproject.org/updates

        Stores all loaded data in the testing_builds & builds.

        Args:
            releasever: Fedora release version number (e.g. 18).
        """
        pkg_limit = 1000
        releasever = "%s%s" % ("F", releasever)
        # This takes way too long...
        testing_updates = self.bc.query(release=releasever, status='testing',
                                        limit=pkg_limit)['updates']
        testing_updates = [x for x in testing_updates if not x['request']]
        testing_updates.extend(self.bc.query(release=releasever, status='pending',
                               request='testing', limit=pkg_limit)['updates'])
        for update in testing_updates:
            for build in update['builds']:
                self.testing_builds[build['nvr']] = update
                self.builds.append({'nvr': build['nvr'],
                                    'name': build['package']['name']})

    def __bodhi_query_pkg(self, conn, installed_updates_testing, releasever):
        release_short = "%s%s" % ("F", releasever)
        for package in installed_updates_testing:
            pkg_update = self.bc.query(release=release_short, package=package)['updates']
            if pkg_update:
                for update in pkg_update:
                    for build in update['builds']:
                        if not build['nvr'] in self.testing_builds:
                            self.testing_builds[build['nvr']] = update
                            self.builds.append({'nvr': build['nvr'],
                                                'name': build['package']['name'],
                                                'installed': True})
        conn.send([self.builds, self.testing_builds])


    def load_installed(self, releasever):
        """Loads installed packages related to the releasever.

        Loads all locally installed packages related to the Fedora release version.
        Processes only those installed packages which are from @updates-testing repo.

        Stores all loaded data in the testing_builds & builds.

        Args:
            releasever: Fedora release version number (e.g. 18).
        """
        installed_packages = self.yb.rpmdb.returnPackages()
        installed_updates_testing = []
        for pkg in installed_packages:
            # get Fedora release shortcut (e.g. fc18)
            rel = pkg.release.split('.')[-1]
            if rel.startswith('fc') and releasever in rel:
                if pkg.ui_from_repo == '@updates-testing':
                    installed_updates_testing.append(pkg.nvr)

        # split installed_updates_testing to four chunks
        # each Process will process one quarter
        quarter = len(installed_updates_testing) / 4
        q1 = installed_updates_testing[0:quarter]
        q2 = installed_updates_testing[quarter:(2 * quarter)]
        q3 = installed_updates_testing[(2 * quarter):(3 * quarter)]
        q4 = installed_updates_testing[(3 * quarter):len(installed_updates_testing)]

        # using 4x Process to speed it up
        parent_conn_1, child_conn_1 = multiprocessing.Pipe()
        query_1 = multiprocessing.Process(target=self.__bodhi_query_pkg,
                                          args=(child_conn_1, q1, releasever))
        parent_conn_2, child_conn_2 = multiprocessing.Pipe()
        query_2 = multiprocessing.Process(target=self.__bodhi_query_pkg,
                                          args=(child_conn_2, q2, releasever))
        parent_conn_3, child_conn_3 = multiprocessing.Pipe()
        query_3 = multiprocessing.Process(target=self.__bodhi_query_pkg,
                                          args=(child_conn_3, q3, releasever))
        parent_conn_4, child_conn_4 = multiprocessing.Pipe()
        query_4 = multiprocessing.Process(target=self.__bodhi_query_pkg,
                                          args=(child_conn_4, q4, releasever))

        query_1.start()
        query_2.start()
        query_3.start()
        query_4.start()
        query_1.join()
        query_2.join()
        query_3.join()
        query_4.join()

        builds_1, testing_builds_1 = parent_conn_1.recv()
        for i in builds_1:
            self.builds.append(i)
        builds_2, testing_builds_2 = parent_conn_2.recv()
        for i in builds_2:
            self.builds.append(i)
        builds_3, testing_builds_3 = parent_conn_3.recv()
        for i in builds_3:
            self.builds.append(i)
        builds_4, testing_builds_4 = parent_conn_4.recv()
        for i in builds_4:
            self.builds.append(i)

        self.testing_builds.update(testing_builds_1)
        self.testing_builds.update(testing_builds_2)
        self.testing_builds.update(testing_builds_3)
        self.testing_builds.update(testing_builds_4)

# vim: set expandtab ts=4 sts=4 sw=4 :
