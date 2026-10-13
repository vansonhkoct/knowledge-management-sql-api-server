
import bcrypt
import uuid

def makeObjectID():
  object_id = uuid.uuid4().hex[:24]
  print(object_id)
  return object_id

def makeUuid():
  return uuid.uuid4()


def hashPassword(password: str):
    # Generate a salt and hash the password
    salt = bcrypt.gensalt()
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed_password.decode('utf-8')


def checkPassword(hashed_password: str, password: str):
    check = bcrypt.checkpw(
      password=password.encode('utf-8'),
      hashed_password=hashed_password.encode('utf-8'),
    )
    return check
