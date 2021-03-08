#!/bin/bash

set -e

LATEST_HASH=$(git log --pretty=format:'%h' -n 1)

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
echo "Current version: $BASE_STRING"
echo "Latest commit hash: $LATEST_HASH"
V_PATCH=$((V_PATCH + 1))
SUGGESTED_VERSION="$V_MAJOR.$V_MINOR.$V_PATCH"
echo -n "Enter a version number [$SUGGESTED_VERSION]: "
read INPUT_STRING
if [ "$INPUT_STRING" = "" ]; then
    INPUT_STRING=$SUGGESTED_VERSION
fi
echo "Will set new version to be $INPUT_STRING"

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
echo "Pushing new version to the origin ..."
git push && git push --tags
