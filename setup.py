import os
from dotenv import load_dotenv

load_dotenv()

def get_user_input(key_name):
    key = input(f"Enter {key_name}: ")
    with open(".env", "a") as file:
        file.write(f"{key_name}={key}\n")
    
    return key


HF_READ_TOKEN=os.getenv("HF_READ_TOKEN")
HF_WRITE_TOKEN=os.getenv("HF_WRITE_TOKEN")

IG_USERNAME=os.getenv("IG_USERNAME")
IG_PASSWORD=os.getenv("IG_PASSWORD")

TARGET_NAME=os.getenv("TARGET_NAME")
MODEL_NAME = os.getenv("MODEL_NAME")


if not HF_READ_TOKEN:
    HF_READ_TOKEN = get_user_input("HF_READ_TOKEN")
if not HF_WRITE_TOKEN:
    HF_WRITE_TOKEN = get_user_input("HF_WRITE_TOKEN")
    
if not IG_USERNAME:
    IG_USERNAME = get_user_input("IG_USERNAME")
if not IG_PASSWORD:
    IG_PASSWORD = get_user_input("IG_PASSWORD")
    
if not TARGET_NAME:
    TARGET_NAME = get_user_input("TARGET_NAME")
if not MODEL_NAME:
    MODEL_NAME = get_user_input("MODEL_NAME")
    


if __name__ == '__main__':
    print("Your HF_READ_TOKEN is: ", HF_READ_TOKEN)
    print("Your HF_WRITE_TOKEN is: ", HF_WRITE_TOKEN)
    print("Your IG_USERNAME is: ", IG_USERNAME)
    print("Your IG_PASSWORD is: ", IG_PASSWORD)
    print("Your TARGET_NAME is: ", TARGET_NAME)
    print("Your MODEL_NAME is: ", MODEL_NAME)