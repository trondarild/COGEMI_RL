#!/bin/sh

# Absolute path to your project root (adjust if needed)
PROJECT_ROOT="/Users/trond/code/COGEMI_RL"
VENV_PYTHON="$PROJECT_ROOT/.venv/bin/python"

# Check that an argument was provided
if [ -z "$1" ]; then
  echo "Usage: sh pytest_file.sh \"test_file.py\""
  exit 1
fi

TEST_FILE="$PROJECT_ROOT/tests/$1"

"$VENV_PYTHON" -m pytest -q "$TEST_FILE"
