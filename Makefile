# E.g., RASH_TOX_OPTS=-e py27
RASH_TOX_OPTS ?=

.PHONY: test tox-sdist clean

test:
	tox $(RASH_TOX_OPTS)

tox-sdist:
	rm -f MANIFEST
	tox $(RASH_TOX_OPTS) --sdistonly

clean:
	rm -rf *.egg-info .tox MANIFEST
