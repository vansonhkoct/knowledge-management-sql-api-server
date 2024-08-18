#!/bin/bash

# Stop server_4.py using pm2
pm2 stop knowledge-management-sql-api-server-test

# Remove from pm2 process list
pm2 delete knowledge-management-sql-api-server-test

# Print status
pm2 status


