"""Handle program wide resources (files, images, etc...)"""
import os
from glob import glob
from pkg_resources import ResourceManager
from appdirs import user_data_dir

resource_manager = ResourceManager()

user_path = user_data_dir('mlox', 'mlox')
if not os.path.isdir(user_path):
    os.makedirs(user_path)

base_file = os.path.join(user_path, "mlox_base.txt")
user_files = glob(os.path.join(user_path, "**", "mlox*.txt"), recursive=True)
user_files.remove(base_file)

# For the updater
UPDATE_BASE = "mlox-data.7z"
update_file = os.path.join(user_path, UPDATE_BASE)
UPDATE_URL = 'https://svn.code.sf.net/p/mlox/code/trunk/downloads/' + UPDATE_BASE
