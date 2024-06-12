# Getting Started with Knowledge-Management-SQL-API-Server

## Prerequisites

```
python3 -m venv ./venv
source venv/bin/activate
pip install -r requirements.txt
```

## Local run

```
python3 main_uvicorn.py
```



## Debug

Run/Debug using VSCode (already attached `.vscode/launch.json`)


## New db

```
aerich init -t database.TORTOISE_ORM
aerich init-db
```


## Update db schema

```
aerich migrate
aerich upgrade
```


## Important notes

Due to a sophisticated bug of `Aerich` - the combination of using `Aerich` and `TortoiseORM` causes `aerich migrate` to break when adding or modifying `Many-To-Many` relationships directly using `ManyToManyField`. A better workaround would be using `ForeignKeyField` to relate to a dedicated `Many-To-Many` table. By this workaround the proxy table also supports extra field customizations and higher flexibility.
