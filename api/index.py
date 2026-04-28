from app.main import web_app

# Explicit top-level ASGI export for Vercel Python runtime detection.
app = web_app
