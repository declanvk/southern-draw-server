#!/usr/bin/env bash
set -euo pipefail
IFS=$'\n\t'

ORIGINAL_DIR=${PWD}

# Do not move this script from the scripts directory, it requires this and the relative path to website/
SCRIPTS_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null && pwd )"

git checkout release
git merge master
git commit

./${SCRIPTS_DIR}/build_static.sh

WEBSITE_DIR="${SCRIPTS_DIR}/../website"

cp -r $WEBSITE_DIR/dist/ static/

git push heroku-dev release:master

git checkout master
