from app.main import api_app

# Explicit top-level ASGI export for Vercel Python runtime detection.
app = api_app
