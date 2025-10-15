#!/bin/sh
# Simple health check - just check if any python process exists
pgrep python > /dev/null 2>&1 || exit 1
