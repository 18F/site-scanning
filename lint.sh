#! /usr/bin/env bash

set -o errexit
set -o nounset
set -o pipefail

printf "Security linting with bandit...\n"
bandit -r . 

printf "\n Type checking with pyright...\n"
pyright

printf "\n Checking code quality with flake8...\n"
flake8 . --benchmark

printf "\n Checking that code is formatted with black...\n"
black . --check