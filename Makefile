# Branislav Blaskovic <branislav@blaskovic.sk>
# Tomas Meszaros <exo@tty.sk>


name = fedora-gooey-karma
prefix = /usr/local
bindir = $(prefix)/bin

all:

install:
	mkdir -p $(DESTDIR)$(prefix)/share/$(name)
	install -D -p -m 755 src/$(name) $(DESTDIR)$(bindir)/$(name)
	install -D -p -m 755 src/*.py $(DESTDIR)$(prefix)/share/$(name)/

uninstall:
	rm -rf $(DESTDIR)$(prefix)/share/$(name)
	rm -f $(DESTDIR)$(bindir)/$(name)

clean:
	rm src/*.pyc
