#!/bin/bash

set -x

rpmdev-setuptree ~
cp fedora-gooey-karma.spec ~/rpmbuild/SPECS/

pushd ~/rpmbuild/SOURCES
git clone git://github.com/blaskovic/fedora-gooey-karma.git fedora-gooey-karma
#cp -r ~/Repo/fedora-gooey-karma .
tar cvzf fedora-gooey-karma.tar.gz fedora-gooey-karma
popd

rpmbuild -ba ~/rpmbuild/SPECS/fedora-gooey-karma.spec

set +x
