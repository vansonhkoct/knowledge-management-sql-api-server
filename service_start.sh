#!/bin/bash

# Change to the directory where server_4.py is located
cd ./

# Start server_6.py using pm2
pm2 start -f main_uvicorn.py --interpreter=venv/bin/python3 --name knowledge-management-sql-api-server-test

# Print status
pm2 status


