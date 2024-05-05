

if __name__ == '__main__':

  import uvicorn

  uvicorn.run(
    "src.main:app", 
    port=6601, 
    reload=False, 
    access_log=False,
  )


