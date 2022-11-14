PREFIX := /usr/local

clean:
	rm -rf dist

install:
	cd ../rh-gitleaks && make install
	mkdir -p $(DESTDIR)$(PREFIX)/bin
	install ./bin/rh-pre-commit $(DESTDIR)$(PREFIX)/bin/rh-pre-commit
	install ./bin/rh-multi-pre-commit $(DESTDIR)$(PREFIX)/bin/rh-multi-pre-commit
