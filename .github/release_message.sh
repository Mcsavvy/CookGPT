#!/usr/bin/env bash

# Get the tag before the current one
previous_tag=$(git tag -l | tail -n 2 | head -n 1)
# strip first 3 lines
echo "$(gitchangelog "^$previous_tag" HEAD | tail -n +3)"