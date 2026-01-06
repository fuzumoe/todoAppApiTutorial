import os
import tempfile

os.environ.setdefault("LOG_FILE", os.path.join(tempfile.gettempdir(), "test_app.log"))
