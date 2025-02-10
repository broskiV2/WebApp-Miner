from app import app
from asgiref.wsgi import WsgiToAsgi

asgi_app = WsgiToAsgi(app)

if __name__ == "__main__":
    app.run() 