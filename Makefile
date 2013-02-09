# E.g., RASH_TOX_OPTS=-e py27
RASH_TOX_OPTS ?=

.PHONY: test tox-sdist clean cog upload

## Testing
test:
	tox $(RASH_TOX_OPTS)

tox-sdist:
	rm -f MANIFEST
	tox $(RASH_TOX_OPTS) --sdistonly

clean:
	rm -rf *.egg-info .tox MANIFEST

## Update files using cog.py
cog: rash/__init__.py
rash/__init__.py: README.rst
	cd rash && cog.py -r __init__.py

## Upload to PyPI
upload: cog
	python setup.py register sdist upload
