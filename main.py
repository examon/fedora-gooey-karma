#!/usr/bin/python -tt
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
#    Author: Tomas Meszaros <exo@tty.sk>


from PySide import QtCore
from PySide import QtGui
from fedora.client import AuthError
from fedora.client import ServerError
from fedora.client.bodhi import BodhiClient
from mainwindow_gui import Ui_MainWindow
from yum import YumBase
from yum import misc

import sys
import packages
import dependences


class MainWindow(QtGui.QMainWindow):

    def __init__(self, parent=None):
        super(MainWindow, self).__init__(parent)
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.__show_karma_widget_comment()

        self.ui.actionQuit.triggered.connect(QtCore.QCoreApplication.instance().quit)
        self.ui.pkgList.currentItemChanged.connect(self._show_package_detail)
        self.ui.searchEdit.textChanged.connect(self.__search_pkg)
        self.ui.installedBtn.clicked.connect(self._show_installed)
        self.ui.availableBtn.clicked.connect(self._show_available)
        self.ui.sendBtn.clicked.connect(self.__show_karma_widget_auth)
        self.ui.okBtn.clicked.connect(self.__send_comment)
        self.ui.cancelBtn.clicked.connect(self.__show_karma_widget_comment)

        self.pkg_worker = PackagesWorker()
        self.pkg_worker.start()
        self.pkg_worker.load_packages_done.connect(self.__save_available_pkg_list)
        self.pkg_worker.load_packages_start.connect(self.__available_pkg_list_loading_info)

        self.dep_worker = DependencesWorker()
        self.dep_worker.load_dependences_done.connect(self.__save_dep_tree)
        self.dep_worker.load_dependences_start.connect(self.__dep_tree_loading_info)

    def __available_pkg_list_loading_info(self):
        message = "Please wait... Loading all available packages..."
        self.ui.statusBar.showMessage(message)
        self.ui.searchEdit.setEnabled(False)

    def __dep_tree_loading_info(self, pkg_name):
        message = "Loading Related packages: %s" % pkg_name
        self.ui.statusBar.showMessage(message)

    def __setup_yum(self):
        self.yb = YumBase()
        cachedir = misc.getCacheDir()
        self.yb.repos.setCacheDir(cachedir)

        # get installed packages from the @updates-testing
        installed_packages = self.yb.rpmdb.returnPackages()
        for pkg in installed_packages:
            if pkg.ui_from_repo == '@updates-testing':
                if pkg.nvr in self.pkg.testing_builds.keys():
                    for build in self.pkg.builds:
                        if pkg.nvr == build['nvr']:
                            build['installed'] = True

    def __save_dep_tree(self, dep_list):
        self.ui.statusBar.clearMessage()
        # save dep tree
        # show it in related packages tree widget
        for item in self.pkg.builds:
            if item['name'] == dep_list['pkg_name']:
                item['dep_tree'] = dep_list['dep_tree']
                self._show_related_packages(item['nvr'], cached=False)
                message = "Loading Related packages: %s DONE" % item['name']
                self.ui.statusBar.showMessage(message)
                break

    def __search_pkg(self):
        # used for searchEdit searching
        phrase = str(self.ui.searchEdit.text())
        self.ui.pkgList.clear()
        if not phrase:
            for build in self.pkg.builds:
                if self.ui.installedBtn.isChecked():
                    if 'installed' in build:
                        self.ui.pkgList.addItem(build['nvr'])
                elif self.ui.availableBtn.isChecked():
                    self.ui.pkgList.addItem(build['nvr'])
            return
        for build in self.pkg.builds:
            if build['nvr'].startswith(phrase):
                if self.ui.installedBtn.isChecked():
                    if 'installed' in build:
                        self.ui.pkgList.addItem(build['nvr'])
                elif self.ui.availableBtn.isChecked():
                    self.ui.pkgList.addItem(build['nvr'])
            elif phrase in build:
                if self.ui.installedBtn.isChecked():
                    if 'installed' in build:
                        self.ui.pkgList.addItem(build['nvr'])
                elif self.ui.availableBtn.isChecked():
                    self.ui.pkgList.addItem(build['nvr'])

    def __save_available_pkg_list(self, pkg_object):
        self.pkg = pkg_object
        self.__setup_yum()
        self.ui.availableBtn.setChecked(True)
        self._show_available()
        self.ui.statusBar.clearMessage()
        message = "All available packages has been loaded."
        self.ui.statusBar.showMessage(message)
        self.ui.searchEdit.setEnabled(True)

    def __decode_dict(self, dictionary, decoding='utf-8', data_type=str):
        for key in dictionary.keys():
            if isinstance(dictionary[key], data_type):
                dictionary[key] = dictionary[key].decode(decoding)

    def __show_karma_widget_auth(self):
        self.ui.usernameEdit.show()
        self.ui.usernameEdit.setFocus()
        self.ui.passwordEdit.show()
        self.ui.okBtn.show()
        self.ui.cancelBtn.show()
        self.ui.commentEdit.hide()
        self.ui.karmaBox.hide()
        self.ui.sendBtn.hide()
        message = "Please enter FAS username and passowrd."
        self.ui.statusBar.showMessage(message)

    def __show_karma_widget_comment(self):
        self.ui.usernameEdit.hide()
        self.ui.passwordEdit.hide()
        self.ui.okBtn.hide()
        self.ui.cancelBtn.hide()
        self.ui.commentEdit.show()
        self.ui.karmaBox.show()
        self.ui.sendBtn.show()
        self.ui.statusBar.clearMessage()

    def __send_comment(self):
        comment = self.ui.commentEdit.text()
        karma = self.ui.karmaBox.currentText()
        update = None
        pkg_title = None

        if comment:
            pkg_title = self.__activated_pkgList_item_text()
            if pkg_title is not None:
                for key in self.pkg.testing_builds.keys():
                    if key == pkg_title:
                        update = self.pkg.testing_builds[pkg_title]

        if update is None:
            message = "Comment not submitted: Could not get update from testing builds"
            self.ui.statusBar.showMessage(message)
            return
        if not self.ui.usernameEdit.text():
            message = "Please enter FAS username."
            self.ui.statusBar.showMessage(message)
            return
        if not self.ui.passwordEdit.text():
            message = "Please enter FAS password."
            self.ui.statusBar.showMessage(message)
            return

        bc = BodhiClient()
        bc.username = self.ui.usernameEdit.text()
        bc.password = self.ui.passwordEdit.text()

        message = "Processing... Wait please..."
        self.ui.statusBar.showMessage(message)

        for retry in range(3):
            try:
                result = bc.comment(update["title"], comment, karma=karma)
                message = "Comment submitted successfully."
                self.ui.statusBar.showMessage(message)
                # save comment and end
                self.pkg.testing_builds[pkg_title] = result['update']
                return
            except AuthError:
                message = "Invalid username or password. Please try again."
                self.ui.statusBar.showMessage(message)
            except ServerError, e:
                message = "Server error %s" % str(e)
                self.ui.statusBar.showMessage(message)

    def _show_installed(self):
        self.ui.availableBtn.setChecked(False)
        if self.ui.installedBtn.isChecked():
            try:
                self.ui.pkgList.clear()
                for build in self.pkg.builds:
                    if 'installed' in build:
                        self.ui.pkgList.addItem(build['nvr'])
                self.__search_pkg()
            except Exception, err:
                print "Packages are not ready yet. Please wait!"
                print err
        elif not self.ui.installedBtn.isChecked():
            self.ui.pkgList.clear()

    def _show_available(self):
        self.ui.installedBtn.setChecked(False)
        if self.ui.availableBtn.isChecked():
            try:
                self.ui.pkgList.clear()
                for build in self.pkg.builds:
                    self.ui.pkgList.addItem(build['nvr'])
                self.__search_pkg()
            except Exception, err:
                print "Packages are not ready yet. Please wait!"
                print err
        elif not self.ui.availableBtn.isChecked():
            self.ui.pkgList.clear()

    def _show_package_detail(self, pkg_item):
        if pkg_item is None:
            return
        data = self.pkg.testing_builds[pkg_item.text()]
        text_browser_string = ""

        ## title
        self.ui.pkgNameLabel.setText(data['builds'][0]['nvr'])

        ## yum info
        yum_values = {}
        yum_format_string = (
            "\n        Yum Info\n"
            "        ========\n\n"
            "           Name: %(name)s\n"
            "           Arch: %(arch)s\n"
            "        Version: %(version)s\n"
            "        Release: %(release)s\n"
            "           Size: %(size)s\n"
            "           Repo: %(repo)s\n"
            "      From repo: %(from_repo)s\n"
            "        Summary: %(summary)s\n"
            "            URL: %(url)s\n"
            "        License: %(license)s\n\n"
            "    Description:\n"
            "    ------------\n\n"
            "%(description)s\n\n"
        )

        yum_pkg_list = []
        for item in self.pkg.builds:
            if pkg_item.text() == item['nvr']:
                yum_pkg_list = self.yb.pkgSack.searchNames([item['name']])
        yum_pkg = None
        # pick one package which fits the best
        if len(yum_pkg_list) == 1:
            yum_pkg = yum_pkg_list[0]
        elif len(yum_pkg_list) > 1:
            for yum_pkg_item in yum_pkg_list:
                if yum_pkg_item.nvr == pkg_item.text():
                    yum_pkg = yum_pkg_item
            if yum_pkg is None:
                yum_pkg = yum_pkg_list[0]
        if yum_pkg is not None:
            # if we got yum package
            # fetch info from yum_pkg
            yum_values['name'] = yum_pkg.name
            yum_values['arch'] = yum_pkg.arch
            yum_values['version'] = yum_pkg.version
            yum_values['release'] = yum_pkg.release
            yum_values['size'] = yum_pkg.packagesize
            yum_values['repo'] = yum_pkg.repo
            yum_values['from_repo'] = yum_pkg.ui_from_repo
            yum_values['summary'] = yum_pkg.summary
            yum_values['url'] = yum_pkg.url
            yum_values['license'] = yum_pkg.license
            yum_values['description'] = yum_pkg.description
            # decode all strings found in yum_values to utf-8
            self.__decode_dict(yum_values)
            # map fetched yum info on the yum_format_string
            # add to the final browser string
            text_browser_string += yum_format_string % yum_values

        ## bodhi info
        bodhi_values = {}
        bodhi_format_string = (
            "\n      Bodhi Info\n"
            "      ==========\n\n"
            "         Status: %(status)s\n"
            "        Release: %(release)s\n"
            "      Update ID: %(updateid)s\n"
            "         Builds: %(builds)s"
            "      Requested: %(request)s\n"
            "         Pushed: %(pushed)s\n"
            " Date Submitted: %(date_submitted)s\n"
            "  Date Released: %(date_released)s\n"
            "      Submitted: %(submitter)s\n"
            "          Karma: %(karma)s\n"
            "   Stable Karma: %(stable_karma)s\n"
            " Unstable Karma: %(unstable_karma)s\n\n"
            "        Details:\n"
            "        --------\n\n"
            "%(notes)s\n"
        )

        bodhi_values['status'] = data['status']
        bodhi_values['release'] = data['release']['long_name']
        bodhi_values['updateid'] = data['updateid']
        builds_list = self.pkg.get_builds(data)
        if len(builds_list):
            build_num = 0
            builds_string = ""
            for build_item in builds_list:
                if not build_num:
                    # first build name
                    builds_string += "%s\n" % build_item
                else:
                    # second and next builds
                    builds_string += "%s%s\n" % (17 * " ", build_item)
                build_num += 1
            bodhi_values['builds'] = builds_string
        else:
            bodhi_values['builds'] = "None"
        bodhi_values['request'] = data['request']
        bodhi_values['pushed'] = "True" if data['date_pushed'] else "False"
        bodhi_values['date_submitted'] = data['date_submitted']
        bodhi_values['date_released'] = data['date_pushed']
        bodhi_values['submitter'] = data['submitter']
        bodhi_values['karma'] = data['karma']
        bodhi_values['stable_karma'] = data['stable_karma']
        bodhi_values['unstable_karma'] = data['unstable_karma']
        bodhi_values['notes'] = data['notes']
        # decode all strings found in bodhi_values to utf-8
        self.__decode_dict(bodhi_values)
        # map fetched bodhi info on the bodhi_format_string
        # add to the final browser string
        text_browser_string += bodhi_format_string % bodhi_values
        # set final browser string text
        self.ui.textBrowser.setText(text_browser_string)

        ## bugs
        self.ui.treeWidget_bugs.clear()
        bugs = self.pkg.get_bugs(data)
        if bugs:
            for i in bugs.iterkeys():
                bug = QtGui.QTreeWidgetItem()
                bug.setText(0, str(i))
                bug.setText(1, str(bugs[i]))
                self.ui.treeWidget_bugs.insertTopLevelItem(0, bug)

        ## test cases
        self.ui.treeWidget_test_cases.clear()
        test_cases_list = self.pkg.get_test_cases(data)
        if len(test_cases_list):
            for test_case_item in reversed(test_cases_list):
                tc = QtGui.QTreeWidgetItem()
                tc.setText(0, str(test_case_item))
                self.ui.treeWidget_test_cases.insertTopLevelItem(0, tc)

        ## feedback
        self.ui.treeWidget_feedback.clear()
        comments = self.pkg.get_comments(data)
        if comments:
            for i in comments:
                comment = QtGui.QTreeWidgetItem()
                comment.setText(0, str(i[2]))
                comment.setText(1, i[1])
                comment.setText(2, i[0])
                self.ui.treeWidget_feedback.insertTopLevelItem(0, comment)

        ## related packages
        self.ui.treeWidget_related_packages.clear()
        start_dep_worker = True
        for item in self.pkg.builds:
            if item['nvr'] == pkg_item.text() and 'dep_tree' in item:
                # pkg_item.text() already has dep tree dont start dep_worker
                start_dep_worker = False
        if not start_dep_worker:
            # dep tree already loaded, just show related packages without
            # starting next dep_worker
            self._show_related_packages(pkg_item.text())
        if start_dep_worker:
            # start new dep_worker and save dep tree
            for item in self.pkg.builds:
                if item['nvr'] == pkg_item.text():
                    # if dep_worker is running, dont start another
                    if self.dep_worker.isRunning():
                        break
                    self.dep_worker.set_package_name(item['name'])
                    self.dep_worker.start()

    def __activated_pkgList_item_text(self):
        index = 0
        # check current activated item in pkgList
        for i in range(self.ui.pkgList.count()):
            item = self.ui.pkgList.item(index)
            if item.isSelected():
                return item.text()
            index += 1

    def _show_related_packages(self, pkg_name, cached=True):
        if not cached:
            # return when different package is activated
            if not self.__activated_pkgList_item_text() == pkg_name:
                return
        # show related packages
        # TODO: make proper tree in treeWidget
        for item in self.pkg.builds:
            if item['nvr'] == pkg_name:
                for package in reversed(item['dep_tree']):
                    pkg = QtGui.QTreeWidgetItem()
                    pkg.setText(0, str(package))
                    self.ui.treeWidget_related_packages.insertTopLevelItem(0, pkg)


class DependencesWorker(QtCore.QThread):
    load_dependences_done = QtCore.Signal(object)
    load_dependences_start = QtCore.Signal(object)

    def __init__(self, parent=None):
        super(DependencesWorker, self).__init__(parent)

    def set_package_name(self, pkg_name):
        self.__pkg_name = pkg_name

    def run(self):
        self.load_dependences_start.emit(str(self.__pkg_name))
        __dep = dependences.Dependences(str(self.__pkg_name))
        __dep_tree = __dep.get_dep_tree()
        self.load_dependences_done.emit({'pkg_name' : self.__pkg_name,
                                         'dep_tree' : __dep_tree})


class PackagesWorker(QtCore.QThread):
    load_packages_done = QtCore.Signal(object)
    load_packages_start = QtCore.Signal(object)

    def __init__(self, parent=None):
        super(PackagesWorker, self).__init__(parent)

    def run(self):
        self.load_packages_start.emit(self)
        __packages = packages.Packages()
        __packages.load_available()
        self.load_packages_done.emit(__packages)


if __name__ == "__main__":
    app = QtGui.QApplication(sys.argv)
    win = MainWindow()
    win.show()
    sys.exit(app.exec_())

# vim: set expandtab ts=4 sts=4 sw=4 :