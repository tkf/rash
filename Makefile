.PHONY: test clean

test:
	tox

clean:
	rm -rf *.egg-info .tox MANIFEST
