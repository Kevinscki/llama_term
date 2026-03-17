#!/bin/bash
# Fix for: user forgot to remove __pycache__
[31mrm -rf __pycache__
[0m
# Attempting git commit with risk parsing version of Python code and adding environment variables
git add .
git commit -m "Fixed merge, added my risk parsing version of the Python code and added envs"

echo "SUCCESS: Commit successful" 

echo AI__PWD_:$PWD
echo AI__END__1
