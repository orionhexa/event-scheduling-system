from werkzeug.serving import run_simple
from src.server.event_service import wsgi_app

if __name__ == '__main__':
    # Run the WSGI application on localhost:8000
    print("Starting Event Scheduling SOAP Service on http://127.0.0.1:8000/soap?wsdl")
    run_simple('127.0.0.1', 8000, wsgi_app, use_debugger=True)