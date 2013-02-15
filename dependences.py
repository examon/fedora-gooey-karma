#!/usr/bin/python -tt

# This code contains portion of pkg-provs-tree-view.py written by Seth Vidal,
# available at http://skvidal.fedorapeople.org/misc/pkg-provs-tree-view.py

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
import yum


class Dependences(object):

    def __init__(self, pname):
        if not pname:
            return

        self.dep_tree = []

        self.yb = yum.YumBase()
        self.yb.doConfigSetup(debuglevel=0, errorlevel=1)
        cachedir = yum.misc.getCacheDir()
        if cachedir is None:
            self.yb.logger.error("Error: Could not make cachedir, exiting")
            sys.exit(50)
        self.yb.repos.setCacheDir(cachedir)
        self.yb.conf.cache = 0

        try:
            self.yb.doRepoSetup()
        except yum.Errors.RepoError, e:
            self.yb.logger.error("Could not setup repo: %s" % (e))
            sys.exit(50)

        all_pkgs = self.yb.pkgSack.returnNewestByNameArch()

        done = False
        exact, match, unmatch = yum.packages.parsePackages(all_pkgs, [pname], casematch=0)
        pkgs = exact + match
        if done:
            print ''
        for pkg in sorted(pkgs):
            if done:
                print ''
            done = True
            self.__tree_dep(pkg)

    def __print_prov(self, prov, level):
        indent = ''
        if level:
            indent = ' - ' * (level - 1)
        out_str = "%s%s" % (indent, str(prov))
        self.dep_tree.append(out_str)

    __all_provs = {}
    def __pkg2prov(self, pkg):
        arch = pkg.arch
        if arch == 'i686':
            arch = 'i386'
        prov = "%s.%s" % (pkg.name, arch)
        return prov

    def __maybe_add_pkg(self, loc_provs, pkgs, pkg):
        prov = self.__pkg2prov(pkg)
        if prov in loc_provs:
            return
        if prov in self.__all_provs:
            pkgs[pkg] = None
            return
        pkgs[pkg] = True
        self.__all_provs[prov] = True
        return

    __prov2pkgs_dict = {}
    def __prov2pkgs(self, prov):
        if str(prov) in self.__prov2pkgs_dict:
            return self.__prov2pkgs_dict[str(prov)]

        requirers = []
        try:
            requirers = self.yb.pkgSack.getRequires(prov[0],prov[1], prov[2])
        except yum.Errors.YumBaseError:
            print >>sys.stderr, "No package provides %s" % str(prov)
            return []

        self.__prov2pkgs_dict[str(prov)] = requirers
        return requirers

    def __pkg_eq(self, pkg, oth):
        upkg = "%s-%s:%s-%s" % (pkg.name, pkg.epoch, pkg.version, pkg.release)
        uoth = "%s-%s:%s-%s" % (oth.name, oth.epoch, oth.version, oth.release)
        return upkg == uoth

    def __tree_dep(self, pkg, level=0):
        self.__print_prov(pkg, level)
        rpkgs = {}
        loc_provs = {}
        filetupes = []
        for n in pkg.filelist + pkg.dirlist + pkg.ghostlist:
            filetupes.append((n, None, (None,None, None)))
        for rptup in pkg.returnPrco('provides') + filetupes:
            (rpn, rpf, (rp,rpv,rpr)) = rptup
            if not rpn.startswith('rpmlib'):
                for npkg in sorted(self.__prov2pkgs(rptup), reverse=True):
                    self.__maybe_add_pkg(loc_provs, rpkgs, npkg)
        for rpkg in sorted(rpkgs):
            if self.__pkg_eq(pkg, rpkg):
                continue
            if rpkgs[rpkg] is None:
                self.__print_prov(rpkg, level + 1)
                continue
            self.__tree_dep(rpkg, level + 1)

    def get_dep_tree(self):
        return self.dep_tree
