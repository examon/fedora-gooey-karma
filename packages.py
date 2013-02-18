#!/usr/bin/python -tt
# -*- coding: utf-8 -*-

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
#    Author: Tomas Meszaros <exo@tty.sk>


from fedora.client.bodhi import BodhiClient


class Packages(object):

    __BODHI_URL = 'https://admin.fedoraproject.org/updates/'

    def __init__(self):
        self.bc = BodhiClient(self.__BODHI_URL, debug=None)

    def get_builds(self, data):
        builds = []
        for build in data['builds']:
            builds.append(build['nvr'])
        return builds

    def get_bugs(self, data):
        bugs = {}
        if len(data['bugs']):
            for bug in data['bugs']:
                bugs[bug['bz_id']] = bug['title']
        return bugs

    def get_comments(self, data):
        comments = []
        if len(data['comments']):
            for comment in data['comments']:
                anonymous = ""
                if comment['anonymous']:
                    anonymous = " (unauthenticated)"
                comments.append([comment['text'], comment['author'] + anonymous, comment['karma']])
        return comments

    def get_test_cases(self, data):
        if data['nagged'] is not None:
            if 'test_cases' in data['nagged']:
                test_cases = data['nagged']['test_cases']
                for i in range(len(test_cases)):
                    test_cases[i] = test_cases[i].replace("QA:Testcase ", "")
                return test_cases
        # when package does not have test cases
        return []

    def load_available(self):
        SET_LIMIT = 1000
        RELEASE = "F18"

        testing_updates = self.bc.query(release=RELEASE, status="testing", limit=SET_LIMIT)["updates"]
        testing_updates = [x for x in testing_updates if not x["request"]]
        testing_updates.extend(self.bc.query(release=RELEASE, status="pending", request="testing", limit=SET_LIMIT)["updates"])

        self.builds = []
        self.testing_builds = {}

        for update in testing_updates:
            for build in update['builds']:
                self.testing_builds[build['nvr']] = update
                self.builds.append({'nvr': build['nvr'], 'name': build['package']['name']})

# vim: set expandtab ts=4 sts=4 sw=4 :