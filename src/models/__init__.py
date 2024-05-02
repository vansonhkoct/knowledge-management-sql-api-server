from tortoise import Tortoise


import sys
import os

parent_dir = os.path.dirname(os.path.realpath(__file__))
sys.path.append(parent_dir + "/../")

Tortoise.init_models(models_paths=[
  "schemas.master",
  "aerich.models",
], app_label="models")

