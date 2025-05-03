#!/bin/bash

# This script runs on Frappe Cloud after the app is installed
# It creates a symlink from lms to education to handle the naming inconsistency

# Create a symlink if needed
if [ -d "/home/frappe/frappe-bench/apps/lms" ] && [ ! -d "/home/frappe/frappe-bench/apps/education" ]; then
    echo "Creating symlink from education to lms"
    ln -s /home/frappe/frappe-bench/apps/lms /home/frappe/frappe-bench/apps/education
fi

# If both directories exist, merge them
if [ -d "/home/frappe/frappe-bench/apps/lms" ] && [ -d "/home/frappe/frappe-bench/apps/education" ]; then
    echo "Both directories exist, merging..."
    cp -r /home/frappe/frappe-bench/apps/education/* /home/frappe/frappe-bench/apps/lms/
    rm -rf /home/frappe/frappe-bench/apps/education
    ln -s /home/frappe/frappe-bench/apps/lms /home/frappe/frappe-bench/apps/education
fi

echo "Deployment hook completed successfully" 