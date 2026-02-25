import uvicorn
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

if __name__ == "__main__":
    from src.sync.env_config import env_config
    uvicorn.run(
        "src.sync.api_server:app",
        host=env_config.get_api_server_host(),
        port=env_config.get_api_server_port(),
        reload=True
    )

