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

import webbrowser

class WebBrowser:

    # URL constants
    __BUGZILLA_REDHAT_URL = "http://bugzilla.redhat.com/show_bug.cgi?id="
    __PACKAGE_INFO_URL = "https://apps.fedoraproject.org/packages/"
    __FEDORAPEOPLE_TESTCASE_URL = "https://fedoraproject.org/wiki/QA:Testcase_"
    __KOJI_PACKAGES_URL = "http://kojipkgs.fedoraproject.org//packages/"

    def __init__(self, main):
        # Grab MainWindow instance
        self.main = main

    def show_bug_in_browser(self):
        bug_id = self.main.ui.treeWidget_bugs.currentItem().text(0)
        webbrowser.open_new_tab("%s%s" % (self.__BUGZILLA_REDHAT_URL, bug_id))

    def show_relevant_pkg_in_browser(self):
        widget = self.main.ui.treeWidget_related_packages.currentItem()
        if widget.parent() is not None:
            # Do not need to open new tab when double clicked at "Desktop packages"
            # or "Other packages", so affect childs only
            webbrowser.open_new_tab("%s%s" % (self.__PACKAGE_INFO_URL, widget.text(0).strip()))

    def show_bodhi_update_in_browser(self):
        update = self.main.get_bodhi_update()
        if not update:
            return
        webbrowser.open_new_tab(update['bodhi_url'])

    def download_source_rpm(self):
        update = self.main.get_bodhi_update()
        if not update:
            return

        name = update['parsed_nvr']['name']
        version = update['parsed_nvr']['version']
        release = update['parsed_nvr']['release']

        # Set-up url
        url = self.__KOJI_PACKAGES_URL + "%s/%s/%s/src/%s.src.rpm" % (name, version, release, update['itemlist_name'])
        # Maybe it would be nice to show Save dialog and save directly to hdd
        webbrowser.open_new_tab(url)

    def show_testcase_in_browser(self):
        testcase_name = self.main.ui.treeWidget_test_cases.currentItem().text(0).replace(' ', '_')
        webbrowser.open_new_tab("%s%s" % (self.__FEDORAPEOPLE_TESTCASE_URL, testcase_name))

# vim: set expandtab ts=4 sts=4 sw=4 :
