import os
from dotenv import load_dotenv
load_dotenv()

PORT = os.getenv("PORT_PROD")


if __name__ == '__main__':

  import uvicorn

  uvicorn.run(
    "src.main:app", 
    port=int(PORT) if PORT is not None and PORT != "" else 6601, 
    reload=False, 
    access_log=False,
  )


