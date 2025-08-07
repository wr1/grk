#!/bin/bash

# Script to stage and commit specific changes from a JSON file (cfold format)
# Assumes changes are already applied (unfolded) to the filesystem
# Usage: ./__git.sh <json_file> [commit_message_prefix]

set -e

if [ $# -lt 1 ]; then
  echo "Usage: $0 <json_file> [commit_message_prefix]"
  echo "Stages and commits specific file changes from JSON with a summary message."
  exit 1
fi

JSON_FILE="$1"
PREFIX="${2:-Applied LLM changes}"

# Check if jq is installed
if ! command -v jq &> /dev/null; then
    echo "jq is required but not installed. Please install jq."
    exit 1
fi

# Check if JSON file exists
if [ ! -f "$JSON_FILE" ]; then
  echo "JSON file not found: $JSON_FILE"
  exit 1
fi

# Extract files array (assume structure with 'files' key or root array)
FILES=$(jq '.files // .' "$JSON_FILE")
LEN=$(echo "$FILES" | jq 'length')

# Lists for summary
ADDED=()
MODIFIED=()
DELETED=()

# Stage changes (assumes files are already created/updated/deleted on disk)
for i in $(seq 0 $(($LEN - 1))); do
  PATH=$(echo "$FILES" | jq -r ".[${i}].path")
  DELETE=$(echo "$FILES" | jq -r ".[${i}].delete // false")
  if [ "$DELETE" = "true" ]; then
    if git ls-files --error-unmatch "$PATH" &> /dev/null; then
      git rm "$PATH"
      DELETED+=("$PATH")
    fi
  else
    # For add/update: git add will handle both new and modified
    git add "$PATH"
    if git ls-files --error-unmatch "$PATH" &> /dev/null; then
      MODIFIED+=("$PATH")
    else
      ADDED+=("$PATH")
    fi
  fi
done

# Generate commit message
MESSAGE="$PREFIX"
if [ ${#ADDED[@]} -gt 0 ]; then
  MESSAGE="$MESSAGE\nAdded: ${ADDED[*]}"
fi
if [ ${#MODIFIED[@]} -gt 0 ]; then
  MESSAGE="$MESSAGE\nModified: ${MODIFIED[*]}"
fi
if [ ${#DELETED[@]} -gt 0 ]; then
  MESSAGE="$MESSAGE\nDeleted: ${DELETED[*]}"
fi

# Commit if there are staged changes
git diff --cached --quiet || git commit -m "$MESSAGE"
echo "Changes committed with message:"
echo -e "$MESSAGE"

