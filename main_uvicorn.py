import os
from dotenv import load_dotenv
load_dotenv()

PORT = os.getenv("PORT")


if __name__ == '__main__':

  import uvicorn

  uvicorn.run(
    "src.main:app", 
    host="0.0.0.0",
    port=int(PORT) if PORT is not None and PORT != "" else 17891, 
    reload=True, 
    access_log=False,
  )


