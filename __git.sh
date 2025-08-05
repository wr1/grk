#!/bin/bash

# Simple script to commit recent changes with a summary message
# Assumes changes from {'files':[...]} are already applied (unfolded) to the filesystem
# Usage: ./__git.sh [commit_message_prefix]

PREFIX="${1:-Applied LLM changes}"

# Stage all changes (adds, mods, deletes)
git add -A

# Get summary from git status
SUMMARY=$(git status --porcelain | awk '
  BEGIN { added=0; mod=0; del=0 }
  /^A / { added++ }
  /^M / { mod++ }
  /^D / { del++ }
  END { 
    if (added > 0) print "Added " added " files";
    if (mod > 0) print "Modified " mod " files";
    if (del > 0) print "Deleted " del " files";
  }'
)

# Commit if there are changes
git diff --cached --quiet || git commit -m "$PREFIX\n$SUMMARY"

