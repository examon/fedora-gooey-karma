# Tomas Meszaros <exo@tty.sk>


name = fedora-gooey-karma
prefix = /usr/local
bindir = $(prefix)/bin

SOURCES = src/*.py $(NAME)
DISTFILES = AUTHORS COPYING README Makefile fedora-gooey-karma.py src

install:
	install -D -p -m 755 src/$(name) $(DESTDIR)$(bindir)/$(name)
	install -D -p -m 755 src/mainwindow.py $(DESTDIR)$(prefix)/share/$(name)
	install -D -p -m 755 src/mainwindow_gui.py $(DESTDIR)$(prefix)/share/$(name)
