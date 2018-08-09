
.PHONY: public push

publish: push
	python setup.py sdist upload

push:
	dev/push.sh
