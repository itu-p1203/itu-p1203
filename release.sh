#!/usr/bin/env bash
#
# Release the project and bump version number in the process.

set -e

cd "$(dirname "$0")"

FORCE=false

usage() {
    echo "Usage: $0 [options] VERSION"
    echo
    echo "VERSION:"
    echo "  major: bump major version number"
    echo "  minor: bump minor version number"
    echo "  patch: bump patch version number"
    echo
    echo "Options:"
    echo "  -f, --force:  force release"
    echo "  -h, --help:   show this help message"
    exit 1
}

# parse args
while [ "$#" -gt 0 ]; do
    case "$1" in
    -f | --force)
        FORCE=true
        shift
        ;;
    -h | --help)
        usage
        ;;
    *)
        break
        ;;
    esac
done

# check if version is specified
if [ "$#" -ne 1 ]; then
    usage
fi

if [ "$1" != "major" ] && [ "$1" != "minor" ] && [ "$1" != "patch" ]; then
    usage
fi

# check if git is clean and force is not enabled
if ! git diff-index --quiet HEAD -- && [ "$FORCE" = false ]; then
    echo "Error: git is not clean. Please commit all changes first."
    exit 1
fi

if ! command -v uv &> /dev/null; then
    echo "Error: uv is not installed. Please install uv from https://docs.astral.sh/uv/"
    exit 1
fi

if ! command -v git-cliff &> /dev/null; then
    echo "Error: git-cliff is not installed. Please install from https://git-cliff.org/."
    exit 1
fi

# check if poetry is available for requirements export
if ! command -v poetry &> /dev/null; then
    echo "Warning: poetry is not installed. Requirements files will not be updated."
    echo "Install poetry from https://python-poetry.org/"
    SKIP_POETRY=true
else
    SKIP_POETRY=false
fi

echo "Would bump version:"
uv version --bump "$1" --dry-run

# prompt for confirmation
if [ "$FORCE" = false ]; then
    read -p "Do you want to release? [yY] " -n 1 -r
    echo
else
    REPLY="y"
fi
echo

if [[ $REPLY =~ ^[Yy]$ ]]; then
    # replace version number in pyproject.toml and uv.lock
    uv version --bump "$1"

    new_version=$(uv version --short)

    # Special handling: update version in additional files
    VERSION_FILE="itu_p1203/__init__.py"
    VERSION_FILE_2="VERSION"

    if [ -f "$VERSION_FILE" ]; then
        perl -pi -e "s/\d+\.\d+\.\d+/$new_version/" "$VERSION_FILE"
        git add "$VERSION_FILE"
    fi

    if [ -f "$VERSION_FILE_2" ]; then
        echo "$new_version" > "$VERSION_FILE_2"
        git add "$VERSION_FILE_2"
    fi

    # Special handling: export requirements using poetry
    if [ "$SKIP_POETRY" = false ]; then
        echo "Exporting requirements..."
        poetry export --without-hashes -f requirements.txt > requirements.txt
        poetry export --with dev -f requirements.txt --output requirements.dev.txt --without-hashes
        git add requirements.txt requirements.dev.txt
    fi

    # commit changes
    git add pyproject.toml uv.lock
    git commit -m "bump version to $new_version"
    git tag -a "v$new_version" -m "v$new_version"

    # generate changelog
    git-cliff > CHANGELOG.md

    git add CHANGELOG.md
    git commit --no-verify --amend --no-edit
    git tag -a -f -m "v$new_version" "v$new_version"

    # push changes
    git push origin master
    git push origin "v$new_version"
else
    echo "Aborted."
    exit 1
fi
