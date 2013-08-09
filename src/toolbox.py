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

from PySide import QtGui

class Toolbox:
    def __init__(self, main):
        # Grab MainWindow instance
        self.main = main

    def __toolbox_current_tab(self):
        # What is the currently selected toolbox?
        if self.main.ui.toolBoxWhatToTest.currentIndex() == self.main.ui.toolBoxWhatToTest.count() -1:
            return 'ignored'
        else:
            return 'favorite'

    def negative_karma_clicked(self, item, column):
        # Get package name even if comment selected
        if item.parent() is not None:
            item = item.parent()

        # Set package name as search text
        self.main.ui.searchEdit.setText(str(item.text(0)))

    def currently_running_clicked(self, item, column):
        # Get package name even if comment selected
        if item.parent() is not None:
            item = item.parent()

        # Set package name as search text
        self.main.ui.searchEdit.setText(str(item.text(0)))

    def favorite_item_clicked(self, item, column):
        # Get package name
        # Do this only when package is selected (not the header text)
        if item.parent() is not None:
            self.main.ui.searchEdit.setText(str(item.text(0)))

    def move_toolbox_buttons(self, index):
        ## Copy widget with pkg list tools to current index one
        if self.__toolbox_current_tab() == 'ignored':
            self.main.ui.toolBoxIgnoredLayout.addWidget(self.main.ui.tool_add_remove_pkg)
        else:
            self.main.ui.toolBoxFavoriteLayout.addWidget(self.main.ui.tool_add_remove_pkg)

    def config_add_package(self):
        # Add package from lineedit to config according to selected toolbox
        if self.__toolbox_current_tab() == 'ignored':
            self.main.config.ignored_packages.add_package(self.main.ui.tool_pkg_name.text())
        else:
            self.main.config.favorited_packages.add_package(self.main.ui.tool_pkg_name.text())
        self.update_favorite_ignored_pkg_lists()
        self.main.ui.tool_pkg_name.clear()
        self.main.config.save_config()

    def config_remove_package(self):
        # Removes selected package
        if self.__toolbox_current_tab() == 'ignored':
            try:
                self.main.config.ignored_packages.remove_package(self.main.ui.tool_pkg_list_ignored.currentItem().text(0))
            except:
                pass
        else:
            try:
                self.main.config.favorited_packages.remove_package(self.main.ui.tool_pkg_list_favorite.currentItem().text(0))
            except:
                pass
        self.main.config.save_config()
        self.update_favorite_ignored_pkg_lists()

    def update_favorite_ignored_pkg_lists(self):
        self.main.ui.tool_pkg_list_ignored.clear()
        self.main.ui.tool_pkg_list_favorite.clear()

        # Prepare list of package names
        pkg_names = []
        for key in self.main.installed_updates.keys():
            pkg_names.append(self.main.installed_updates[key].parsed_nvr['name'])

        # Top level items
        def create_top_level_item(text, widget):
            item = QtGui.QTreeWidgetItem()
            item.setText(0, text)
            widget.insertTopLevelItem(0, item)
            item.setExpanded(True)
            return item

        # Top level items
        ## Set names
        fav_not_available = create_top_level_item('Bodhi update not available', self.main.ui.tool_pkg_list_favorite)
        fav_available = create_top_level_item('Bodhi update available', self.main.ui.tool_pkg_list_favorite)

        # Favorite packages
        for pkg in self.main.config.favorited_packages:
            item = QtGui.QTreeWidgetItem()
            item.setText(0, pkg)
            # If this package name is in available packages
            if pkg in pkg_names:
                fav_available.addChild(item)
            else:
                fav_not_available.addChild(item)

        # Ignored packages
        for pkg in self.main.config.ignored_packages:
            item = QtGui.QTreeWidgetItem()
            item.setText(0, pkg)
            self.main.ui.tool_pkg_list_ignored.insertTopLevelItem(0, item)

# vim: set expandtab ts=4 sts=4 sw=4 :
