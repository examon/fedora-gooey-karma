# Tomas Meszaros <exo@tty.sk>

VERSION = 1.0
NAME = fedora-gooey-karma

ifndef PREFIX
PREFIX = /usr
endif

SOURCES = src/*.py $(NAME)
DISTFILES = AUTHORS COPYING README Makefile fedora-gooey-karma.py src

all:
	@echo Use \'make PREFIX=/usr/local install\' to install
	@echo or \'make dist\' to create distribution tar.gz archive

install:
	install -d $(PREFIX)/bin
	install -d $(PREFIX)/share/$(NAME)
	install src/$(NAME) $(PREFIX)/bin
	install -m 644 src/*.py $(PREFIX)/share/$(NAME)

dist:
	test ! -e $(NAME)-$(VERSION)
	mkdir $(NAME)-$(VERSION)
	cp -a -p $(DISTFILES) $(NAME)-$(VERSION)
	tar --gzip -cvf $(NAME)-$(VERSION).tar.gz $(NAME)-$(VERSION)
	rm -rf $(NAME)-$(VERSION)

clean:
	rm -f *.tar.gz
	rm -f src/*.pyc
