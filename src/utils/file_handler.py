import os

def create_directories_if_not_exist(path):
    """
    Creates directories at the specified path if they do not already exist.
    """
    if not os.path.exists(path):
        os.makedirs(path)
        print(f"Created directory: {path}")
    else:
        print(f"Directory already exists: {path}")