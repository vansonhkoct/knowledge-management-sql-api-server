

if __name__ == '__main__':

  import uvicorn

  uvicorn.run(
    "src.main:app", 
    port=17891, 
    reload=True, 
    access_log=False,
  )


