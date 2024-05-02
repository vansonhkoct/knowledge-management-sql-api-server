## Prerequisites

```
python3 -m venv ./venv
pip install -r requirements
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