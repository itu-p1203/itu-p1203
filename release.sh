#!/bin/bash
#
# Bump the version, run auto-changelog, and push to Git
#
# Based on:
# - https://gist.github.com/pete-otaqui/4188238
# - https://gist.github.com/mareksuscak/1f206fbc3bb9d97dec9c

set -e

NOW="$(date +'%B %d, %Y')"
RED="\033[1;31m"
GREEN="\033[0;32m"
YELLOW="\033[1;33m"
BLUE="\033[1;34m"
PURPLE="\033[1;35m"
CYAN="\033[1;36m"
WHITE="\033[1;37m"
RESET="\033[0m"

LATEST_HASH=`git log --pretty=format:'%h' -n 1`

QUESTION_FLAG="${GREEN}?"
WARNING_FLAG="${YELLOW}!"
NOTICE_FLAG="${CYAN}❯"

PUSHING_MSG="${NOTICE_FLAG} Pushing new version to the ${WHITE}origin${RESET}..."

VERSION_FILE="itu_p1203/__init__.py"
VERSION_FILE_2="VERSION"
VERSION_FILE_3="pyproject.toml"

if ! poetry run gitchangelog > /dev/null; then
    echo "gitchangelog is not installed in poetry or not configured properly. Run 'poetry install' first."
    exit 1
fi

if [[ $(git diff --stat) != '' ]]; then
  echo "Working dir is dirty, please commit/stash all changes"
  exit 1
fi

BASE_STRING=$(grep -Eo '[0-9]+\.[0-9]+\.[0-9]+' "$VERSION_FILE")
BASE_LIST=(`echo $BASE_STRING | tr '.' ' '`)
V_MAJOR=${BASE_LIST[0]}
V_MINOR=${BASE_LIST[1]}
V_PATCH=${BASE_LIST[2]}
echo -e "${NOTICE_FLAG} Current version: ${WHITE}$BASE_STRING"
echo -e "${NOTICE_FLAG} Latest commit hash: ${WHITE}$LATEST_HASH"
V_PATCH=$((V_PATCH + 1))
SUGGESTED_VERSION="$V_MAJOR.$V_MINOR.$V_PATCH"
echo -ne "${QUESTION_FLAG} ${CYAN}Enter a version number [${WHITE}$SUGGESTED_VERSION${CYAN}]: "
read INPUT_STRING
if [ "$INPUT_STRING" = "" ]; then
    INPUT_STRING=$SUGGESTED_VERSION
fi
echo -e "${NOTICE_FLAG} Will set new version to be ${WHITE}$INPUT_STRING${RESET}"

# replace the python version
perl -pi -e "s/\Q$BASE_STRING\E/$INPUT_STRING/" "$VERSION_FILE" "$VERSION_FILE_2" "$VERSION_FILE_3"

git add "$VERSION_FILE" "$VERSION_FILE_2" "$VERSION_FILE_3"

# bump initially but to not push yet
git commit -m "Bump version to ${INPUT_STRING}."
git tag -a -m "Tag version ${INPUT_STRING}." "v$INPUT_STRING"

# generate the changelog
poetry run gitchangelog > CHANGELOG.md

# add the changelog and amend it to the previous commit and tag
git add CHANGELOG.md
git commit --amend --no-edit
git tag -a -f -m "Tag version ${INPUT_STRING}." "v$INPUT_STRING"

# push to remote
echo -e "$PUSHING_MSG"
git push && git push --tags
