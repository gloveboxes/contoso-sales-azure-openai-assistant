import os

from chainlit.utils import mount_chainlit
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

env = os.getenv("ENV", "development")

# Set the target path based on the environment
if env == "development":
    target = "src/app.py"
elif env == "production":
    target = "app.py"
else:
    raise ValueError(f"Unknown environment: {env}")

app = FastAPI()


mount_chainlit(app=app, target=target, path="/sales")
