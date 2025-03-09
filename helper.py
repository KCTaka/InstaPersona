import os
import re

def get_file_dir_with_ext(dir, ext):
    files = os.listdir(dir)
    files_with_ext = [file for file in files if file.endswith(ext)]
    files_with_ext.sort(key=lambda x: int(re.findall(r'\d+', x)[0]))
    return [os.path.join(dir, file) for file in files_with_ext]

def get_file_dir_from_dir(dir):
    files = os.listdir(dir)
    dirs = [file for file in files if os.path.isdir(os.path.join(dir, file))]
    dirs.sort()
    return [os.path.join(dir, dir_) for dir_ in dirs]

def transcoder(text):
    return text.encode('latin1').decode('utf-8')


