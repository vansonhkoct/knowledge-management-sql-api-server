
from bson import ObjectId

def makeObjectID():
  object_id = str(ObjectId())
  print(object_id)  
  return object_id
