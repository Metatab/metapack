pip freeze | grep -v -- -e | grep -v 'meta='  > requirements.txt
git commit -a -m'requirements update'
version=$(mp info -v | awk '{print $2}')
git tag -a v$version -m'v$version'
git push
git push origin v$version