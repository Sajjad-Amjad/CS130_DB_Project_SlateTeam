import uvicorn
import os
from app.core.config import PROJECT_NAME

def main():
    """Run the application server."""
    print(f"Starting {PROJECT_NAME} API server...")
    
    # Determine host and port
    host = os.getenv("HOST", "127.0.0.1")
    port = int(os.getenv("PORT", "8000"))
    
    # Start the server
    uvicorn.run("app.main:app", host=host, port=port, reload=True)

if __name__ == "__main__":
    main()