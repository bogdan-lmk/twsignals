# Entry point for gunicorn
from app.main import app as application

# Make app available for gunicorn
app = application

if __name__ == "__main__":
    import uvicorn
    import os
    
    port = int(os.getenv("PORT", "8000"))
    uvicorn.run(app, host="0.0.0.0", port=port)