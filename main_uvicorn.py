import os
import argparse
from dotenv import load_dotenv

load_dotenv(
  verbose=True,
  override=True,
)

if __name__ == '__main__':
  import uvicorn

  # Parse command line arguments
  parser = argparse.ArgumentParser(description='Run the FastAPI application with uvicorn')
  parser.add_argument('--port', type=int, help='Port to run the server on (overrides environment variable)')
  parser.add_argument('--reload', action='store_true', default=True, help='Enable auto-reload (default: True)')
  parser.add_argument('--no-reload', dest='reload', action='store_false', help='Disable auto-reload')
  parser.add_argument('--prod', action='store_true', help='Production mode (sets port from PORT_PROD, reload=False)')

  args = parser.parse_args()

  # Determine port
  if args.prod:
    port = int(os.getenv("PORT_PROD", 6601))
    reload = False
    access_log = False
  else:
    # Use command line port, env PORT, or default 17891
    port = args.port or (int(os.getenv("PORT")) if os.getenv("PORT") else 17891)
    reload = args.reload
    access_log = False

  uvicorn.run(
    "src.main:app",
    host="0.0.0.0",
    port=port,
    reload=reload,
    access_log=access_log,
  )