
.PHONY: public push

publish: push
	python setup.py sdist upload

push:
	pip freeze | grep -v -- -e > requirements.txt
	git commit -a -m'requirements update'
	git push

