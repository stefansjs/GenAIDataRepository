#!/bin/bash

set -ex

THIS_DIR="$(cd $(dirname ${BASH_SOURCE[0]}) && pwd)"
REPO_DIR=$(cd "$THIS_DIR/../repo" && pwd)

python -m http.server --directory "$REPO_DIR" $@
