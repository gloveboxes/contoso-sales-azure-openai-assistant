from chainlit.utils import mount_chainlit
from fastapi import FastAPI

app = FastAPI()


mount_chainlit(app=app, target="app.py", path="/sales")
