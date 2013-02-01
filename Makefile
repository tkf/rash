# E.g., RASH_TOX_OPTS=-e py27
RASH_TOX_OPTS ?=

.PHONY: test clean

test:
	tox $(RASH_TOX_OPTS)

sdist:
	rm MANIFEST
	tox $(RASH_TOX_OPTS) --sdistonly

clean:
	rm -rf *.egg-info .tox MANIFEST
