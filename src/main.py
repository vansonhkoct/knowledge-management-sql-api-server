import traceback

try:
  from apiapp.APIApplication import app
  
except Exception as e:
  stacktrace1 = traceback.format_exc()
  e1 = e
  pass



try:
  from src.apiapp.APIApplication import app
  
except Exception as e:
  stacktrace2 = traceback.format_exc()
  e2 = e
  print(stacktrace1, e1)
  print(stacktrace2, e2)
  pass
  



