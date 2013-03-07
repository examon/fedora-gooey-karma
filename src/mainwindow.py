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


import sys
import webbrowser
import yum
import multiprocessing
from fedora.client import AuthError
from fedora.client import ServerError
from fedora.client.bodhi import BodhiClient
from mainwindow_gui import Ui_MainWindow
from yum.misc import getCacheDir
from yum import Errors
from PySide import QtCore
from PySide import QtGui


class MainWindow(QtGui.QMainWindow):

    __BUGZILLA_REDHAT_URL = "http://bugzilla.redhat.com/show_bug.cgi?id="
    __FEDORAPEOPLE_TESTCASE_URL = "https://fedoraproject.org/wiki/QA:Testcase_"

    def __init__(self, parent=None):
        super(MainWindow, self).__init__(parent)
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        self.yb = yum.YumBase()
        cachedir = getCacheDir()
        self.yb.repos.setCacheDir(cachedir)

        self.pkg_available = {}
        self.pkg_installed = {}

        self.__show_karma_widget_comment()
        self.__hide_karma_name_filter()

        self.ui.actionQuit.triggered.connect(QtCore.QCoreApplication.instance().quit)
        self.ui.pkgList.currentItemChanged.connect(self.__show_package_detail)
        self.ui.searchEdit.textChanged.connect(self.__search_pkg)
        self.ui.karmaUsernameEdit.textChanged.connect(self.__filter_already_submitted)
        self.ui.installedBtn.clicked.connect(self.__show_installed)
        self.ui.availableBtn.clicked.connect(self.__show_available)
        self.ui.sendBtn.clicked.connect(self.__show_karma_widget_auth)
        self.ui.okBtn.clicked.connect(self.__send_comment)
        self.ui.cancelBtn.clicked.connect(self.__show_karma_widget_comment)
        self.ui.loadPackagesBtn.clicked.connect(self.__start_pkg_worker)
        self.ui.releaseComboBox.currentIndexChanged.connect(self.__refresh_package_list)
        self.ui.treeWidget_bugs.itemClicked.connect(self.__show_bug_in_browser)
        self.ui.treeWidget_test_cases.itemClicked.connect(self.__show_testcase_in_browser)
        self.ui.karmaCheckBox.stateChanged.connect(self.__filter_already_submitted)

        self.pkg_worker = PackagesWorker()
        self.pkg_worker.load_available_packages_done.connect(self.__save_available_pkg_list)
        self.pkg_worker.load_available_packages_start.connect(self.__available_pkg_list_loading_info)
        self.pkg_worker.load_installed_packages_done.connect(self.__save_installed_pkg_list)
        self.pkg_worker.load_installed_packages_start.connect(self.__installed_pkg_list_loading_info)

    def __start_pkg_worker(self):
        if self.pkg_worker.isRunning():
            # don't start another pkg_worker while another has been already
            return
        releasever = self.ui.releaseComboBox.currentText().split()[-1]
        self.pkg_worker.set_release(releasever)
        self.pkg_worker.start()

    def __available_pkg_list_loading_info(self):
        release = self.ui.releaseComboBox.currentText()
        message = "Please wait... Loading all available packages. [%s]" % release
        self.ui.statusBar.showMessage(message)

    def __installed_pkg_list_loading_info(self):
        release = self.ui.releaseComboBox.currentText()
        message = "Please wait... Loading all installed packages. [%s]" % release
        self.ui.statusBar.showMessage(message)

    def __show_bug_in_browser(self):
        bug_id = self.ui.treeWidget_bugs.currentItem().text(0)
        webbrowser.open_new_tab("%s%s" % (self.__BUGZILLA_REDHAT_URL, bug_id))

    def __show_testcase_in_browser(self):
        testcase_name = self.ui.treeWidget_test_cases.currentItem().text(0).replace(' ', '_')
        webbrowser.open_new_tab("%s%s" % (self.__FEDORAPEOPLE_TESTCASE_URL, testcase_name))

    def __refresh_package_list(self):
        if self.ui.installedBtn.isChecked():
            self.__show_installed()
        elif self.ui.availableBtn.isChecked():
            self.__show_available()
        elif not self.ui.installedBtn.isChecked() and not self.ui.availableBtn.isChecked():
            self.ui.installedBtn.setChecked(True)
            self.__show_installed()

    def __search_pkg(self):
        # used for searchEdit searching
        if not self.ui.installedBtn.isChecked() and not self.ui.availableBtn.isChecked():
            return
        if self.__get_current_set() is None:
            return

        phrase = str(self.ui.searchEdit.text())
        if not phrase:
            if self.ui.karmaCheckBox.isChecked() and self.ui.karmaUsernameEdit.text() and self.ui.installedBtn.isChecked():
                self.__filter_already_submitted()
            else:
                self.__populate_pkgList()
            return

        self.ui.pkgList.clear()
        for build in self.__get_current_set().builds:
            if build['nvr'].startswith(phrase):
                if self.ui.installedBtn.isChecked():
                    if 'installed' in build:
                        self.ui.pkgList.addItem(build['nvr'])
                elif self.ui.availableBtn.isChecked():
                    self.ui.pkgList.addItem(build['nvr'])

    def __get_current_set(self):
        """ Returns installed or available pkg object.
        Depends which one is used at the moment.
        """
        releasever = self.ui.releaseComboBox.currentText().split()[-1]
        if self.ui.availableBtn.isChecked():
            try:
                return self.pkg_available[releasever]
            except AttributeError, e:
                print "pkg_available is not ready: %s" % e
        elif self.ui.installedBtn.isChecked():
            try:
                return self.pkg_installed[releasever]
            except AttributeError, e:
                print "pkg_installed is not ready: %s" % e
        else:
            raise ValueError("Could not return pkg_available or pkg_installed.")

    def __save_available_pkg_list(self, pkg_object):
        print "save available"
        self.pkg_available[pkg_object[0]] = pkg_object[1]
        releasever = self.ui.releaseComboBox.currentText().split()[-1]
        if releasever == pkg_object[0]:
            self.ui.availableBtn.setChecked(True)
            self.__show_available()
        self.ui.statusBar.clearMessage()
        message = "All available packages has been loaded. [Fedora %s]" % pkg_object[0]
        self.ui.statusBar.showMessage(message)
        self.ui.searchEdit.setEnabled(True)

    def __save_installed_pkg_list(self, pkg_object):
        print "save installed"
        self.pkg_installed[pkg_object[0]] = pkg_object[1]
        releasever = self.ui.releaseComboBox.currentText().split()[-1]
        if releasever == pkg_object[0]:
            self.ui.installedBtn.setChecked(True)
            self.__show_installed()
        self.ui.statusBar.clearMessage()
        message = "All installed packages has been loaded. [Fedora %s]" % pkg_object[0]
        self.ui.statusBar.showMessage(message)
        self.ui.searchEdit.setEnabled(True)

    def __decode_dict(self, dictionary, decoding='utf-8', data_type=str):
        for key in dictionary:
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
                for key in self.__get_current_set().testing_builds:
                    if key == pkg_title:
                        update = self.__get_current_set().testing_builds[pkg_title]

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
                self.__get_current_set().testing_builds[pkg_title] = result['update']
                return
            except AuthError:
                message = "Invalid username or password. Please try again."
                self.ui.statusBar.showMessage(message)
            except ServerError, e:
                message = "Server error %s" % str(e)
                self.ui.statusBar.showMessage(message)

    def __show_karma_name_filter(self):
        self.ui.karmaCheckBox.show()
        self.ui.karmaUsernameEdit.show()

    def __hide_karma_name_filter(self):
        self.ui.karmaCheckBox.hide()
        self.ui.karmaUsernameEdit.hide()

    def __filter_already_submitted(self):
        """ Add only those installed packages to the pkgList for which user did not
        submitted karma. (uses username from the karmaUsernameEdit)
        """
        if not self.ui.karmaCheckBox.isChecked() or not self.ui.karmaUsernameEdit.text():
            self.__populate_pkgList()
            return
        self.ui.pkgList.clear()

        for build in self.__get_current_set().builds:
            data = self.__get_current_set().testing_builds[build['nvr']]
            comments = self.__get_current_set().get_comments(data)
            already_submitted = False
            for comment in comments:
                if comment[1] == self.ui.karmaUsernameEdit.text():
                    already_submitted = True
                    break
            if not already_submitted:
                self.ui.pkgList.addItem(build['nvr'])

    def __populate_pkgList(self):
        self.ui.pkgList.clear()
        for build in self.__get_current_set().builds:
            if self.ui.installedBtn.isChecked() and 'installed' in build:
                self.ui.pkgList.addItem(build['nvr'])
            elif self.ui.availableBtn.isChecked():
                self.ui.pkgList.addItem(build['nvr'])

    def __show_installed(self):
        if self.ui.installedBtn.isChecked():
            self.__show_karma_name_filter()
        else:
            self.__hide_karma_name_filter()
        self.ui.availableBtn.setChecked(False)
        if self.ui.installedBtn.isChecked():
            try:
                self.__populate_pkgList()
                self.__search_pkg()
            except Exception, err:
                print "Packages are not ready yet. Please wait!"
                print err
        elif not self.ui.installedBtn.isChecked():
            self.ui.pkgList.clear()

    def __show_available(self):
        self.__hide_karma_name_filter()
        self.ui.installedBtn.setChecked(False)
        if self.ui.availableBtn.isChecked():
            try:
                self.__populate_pkgList()
                self.__search_pkg()
            except Exception, err:
                print "Packages are not ready yet. Please wait!"
                print err
        elif not self.ui.availableBtn.isChecked():
            self.ui.pkgList.clear()

    def __show_package_detail(self, pkg_item):
        """Shows package detail in the MainWindow.

        Updates all info in every widget when user click on the item in the pkgList.

        Args:
            pkg_item: A currently selected pkgList item widget.

        Returns:
            Returns when pkg_item is None.
        """
        if pkg_item is None:
            return
        data = self.__get_current_set().testing_builds[pkg_item.text()]
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
        yum_pkg_deplist = None
        for item in self.__get_current_set().builds:
            if pkg_item.text() == item['nvr']:
                yum_pkg_list = yum_pkg_deplist = self.yb.pkgSack.searchNames([item['name']])
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

            ## related packages
            self.ui.treeWidget_related_packages.clear()
            deplist = []

            try:
                deplist = self.yb.findDeps(yum_pkg_deplist)
            except Errors.NoMoreMirrorsRepoError, e:
                print "_show_package_detail() error: %s" % e

            for key in deplist:
                for packages in deplist[key]:
                    pkg_name = deplist[key][packages][0]
                    pkg = QtGui.QTreeWidgetItem()
                    pkg.setText(0, str(pkg_name))
                    self.ui.treeWidget_related_packages.insertTopLevelItem(0, pkg)

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
        builds_list = self.__get_current_set().get_builds(data)
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
        bugs = self.__get_current_set().get_bugs(data)
        if bugs:
            for key in bugs:
                bug = QtGui.QTreeWidgetItem()
                bug.setText(0, str(key))
                bug.setText(1, str(bugs[key]))
                self.ui.treeWidget_bugs.insertTopLevelItem(0, bug)

        ## test cases
        self.ui.treeWidget_test_cases.clear()
        test_cases_list = self.__get_current_set().get_test_cases(data)
        if len(test_cases_list):
            for test_case_item in reversed(test_cases_list):
                tc = QtGui.QTreeWidgetItem()
                tc.setText(0, str(test_case_item))
                self.ui.treeWidget_test_cases.insertTopLevelItem(0, tc)

        ## feedback
        self.ui.treeWidget_feedback.clear()
        comments = self.__get_current_set().get_comments(data)
        if comments:
            for i in comments:
                comment = QtGui.QTreeWidgetItem()
                comment.setText(0, str(i[2]))
                comment.setText(1, i[1])
                comment.setText(2, i[0])
                self.ui.treeWidget_feedback.insertTopLevelItem(0, comment)

    def __activated_pkgList_item_text(self):
        """Finds currently activated item in the pkgList.

        Returns:
            item.text(), currently activated item text.
        """
        index = 0
        # check current activated item in pkgList
        for i in range(self.ui.pkgList.count()):
            item = self.ui.pkgList.item(index)
            if item.isSelected():
                return item.text()
            index += 1


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

        self.yb = yum.YumBase()
        cachedir = getCacheDir()
        self.yb.repos.setCacheDir(cachedir)

        self.builds = []
        self.testing_builds = {}

    def get_builds(self, data):
        """Fetches builds from the data.

        Retrieves builds list from the packages data.

        Args:
            data: A doctionary containing Bodhi client query output for each package (see: testing_builds).

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
            data: A doctionary containing Bodhi client query output for each package (see: testing_builds).

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
            data: A doctionary containing Bodhi client query output for each package (see: testing_builds).

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
                comments.append([comment['text'], comment['author'] + anonymous, comment['karma']])
        return comments

    def get_test_cases(self, data):
        """Gets package test cases from the data

        Retrieves all test cases from the package data.

        Args:
            data: A doctionary containing Bodhi client query output for each package (see: testing_builds).

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
        testing_updates = self.bc.query(release=releasever, status='testing', limit=pkg_limit)['updates']
        testing_updates = [x for x in testing_updates if not x['request']]
        testing_updates.extend(self.bc.query(release=releasever, status='pending', request='testing', limit=pkg_limit)['updates'])

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
        query_1 = multiprocessing.Process(target=self.__bodhi_query_pkg, args=(child_conn_1, q1, releasever))
        parent_conn_2, child_conn_2 = multiprocessing.Pipe()
        query_2 = multiprocessing.Process(target=self.__bodhi_query_pkg, args=(child_conn_2, q2, releasever))
        parent_conn_3, child_conn_3 = multiprocessing.Pipe()
        query_3 = multiprocessing.Process(target=self.__bodhi_query_pkg, args=(child_conn_3, q3, releasever))
        parent_conn_4, child_conn_4 = multiprocessing.Pipe()
        query_4 = multiprocessing.Process(target=self.__bodhi_query_pkg, args=(child_conn_4, q4, releasever))

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


def main():
    app = QtGui.QApplication(sys.argv)
    win = MainWindow()
    win.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()

# vim: set expandtab ts=4 sts=4 sw=4 :
