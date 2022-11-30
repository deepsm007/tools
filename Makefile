.PHONY: format
format:
	for makefile in $$(ls */Makefile); do \
		cd $$(dirname $$makefile) && make $@ && cd $(shell pwd); \
	done

.PHONY: clean
clean:
	for makefile in $$(ls */Makefile); do \
		cd $$(dirname $$makefile) && make $@ && cd $(shell pwd); \
	done

.PHONY: setup
setup:
	for makefile in $$(ls */Makefile); do \
		cd $$(dirname $$makefile) && make $@ && cd $(shell pwd); \
	done

.PHONY: test
test:
	for makefile in $$(ls */Makefile); do \
		cd $$(dirname $$makefile) && make $@ && cd $(shell pwd); \
	done
