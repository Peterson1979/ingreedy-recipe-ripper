# wsgi.py
from app import app # Import the Flask app object from your main app.py file

# This file tells hosting platforms like Render how to run the application
# using a WSGI server (like Gunicorn, which Render often uses by default,
# or Waitress if specified). The 'app' variable is the entry point.

if __name__ == "__main__":
    # This part is generally NOT executed by the hosting platform's WSGI server,
    # but it allows running locally with Waitress via "python wsgi.py" if needed.
    # However, using "python app.py" for local dev is usually preferred.
    try:
        from waitress import serve
        print("Starting development server with Waitress (via wsgi.py)...")
        # Use 0.0.0.0 to be accessible on local network if needed
        # Use a common dev port
        serve(app, host='0.0.0.0', port=8080)
    except ImportError:
        print("Waitress not installed. Run 'pip install waitress'")
    except Exception as e:
        print(f"Error starting Waitress: {e}")