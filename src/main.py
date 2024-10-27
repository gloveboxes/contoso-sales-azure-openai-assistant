import os

from chainlit.utils import mount_chainlit
from fastapi import FastAPI

# Map environment to target path
target = {"development": "src/app.py", "production": "app.py"}.get(os.getenv("ENV", "development"))

app = FastAPI()
mount_chainlit(app=app, target=target, path="/sales")
