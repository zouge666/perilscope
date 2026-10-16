import os

from loss_experience.api import create_app

app = create_app(os.environ.get("DATA_DIR", "data"))
