#!/bin/bash
# Use this script to run tests in jenkins or docker
export DB_USERNAME="root"

python3 manage.py test --keepdb