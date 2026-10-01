"""
GastroWise AI Microservice - Legacy Entrypoint Wrapper
This wrapper imports the enterprise modular application from `main.py`
to preserve 100% backward compatibility for all start scripts and commands.
"""

from main import app

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=5000, reload=True)
