from flask import Flask, request, Response, jsonify
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
import xml.etree.ElementTree as ET
from datetime import date, time
import re
import os
import json

from .models import db
from .database_service import EventService as DatabaseEventService

app = Flask(__name__)
CORS(app)  # Enable CORS for cross-origin requests

# Database configuration
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{os.path.join(basedir, "..", "..", "event_scheduling.db")}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize database
db.init_app(app)

# Create tables
with app.app_context():
    db.create_all()

def validate_importance(value):
    """Validate importance field."""
    if value not in ['low', 'medium', 'high']:
        raise ValueError(f"Invalid importance value: {value}")
    return value

def validate_recurrence(value):
    """Validate recurrence field."""
    if value not in ['none', 'daily', 'weekly', 'monthly', 'annually']:
        raise ValueError(f"Invalid recurrence value: {value}")
    return value

def parse_soap_request(xml_data):
    """Parse SOAP request XML and extract event data."""
    try:
        root = ET.fromstring(xml_data)
        
        # Find the Body element
        body = root.find('.//{http://schemas.xmlsoap.org/soap/envelope/}Body')
        if body is None:
            raise ValueError("SOAP Body not found")
        
        # Find the operation
        operation = None
        event_data = None
        event_id = None
        
        for child in body:
            if child.tag.endswith('AddEvent'):
                operation = 'AddEvent'
                event_data = parse_event_from_xml(child)
            elif child.tag.endswith('GetEvent'):
                operation = 'GetEvent'
                event_id = child.find('.//{http://eventscheduling.com/schemas}eventId')
                if event_id is not None:
                    event_id = event_id.text
            elif child.tag.endswith('GetAllEvents'):
                operation = 'GetAllEvents'
            elif child.tag.endswith('UpdateEvent'):
                operation = 'UpdateEvent'
                event_data = parse_event_from_xml(child)
            elif child.tag.endswith('DeleteEvent'):
                operation = 'DeleteEvent'
                event_id = child.find('.//{http://eventscheduling.com/schemas}eventId')
                if event_id is not None:
                    event_id = event_id.text
        
        return operation, event_data, event_id
    except ET.ParseError as e:
        raise ValueError(f"Invalid XML: {e}")

def parse_event_from_xml(element):
    """Parse event data from XML element."""
    event = {}
    
    # Find event element
    event_elem = element.find('.//{http://eventscheduling.com/schemas}eventData') or element.find('.//{http://eventscheduling.com/schemas}event')
    if event_elem is None:
        event_elem = element
    
    # Parse event fields
    namespace = 'http://eventscheduling.com/schemas'
    for field in ['id', 'title', 'agenda', 'date', 'time', 'importance', 'location', 'coordinator', 'recurrence']:
        elem = event_elem.find(f'.//{{{namespace}}}{field}')
        if elem is not None:
            event[field] = elem.text
    
    # Parse participants
    participants_elem = event_elem.find(f'.//{{{namespace}}}participants')
    if participants_elem is not None:
        participants = []
        for participant in participants_elem.findall(f'.//{{{namespace}}}participant'):
            if participant.text:
                participants.append(participant.text)
        event['participants'] = participants
    
    return event

def create_soap_response(operation, data=None, success=None, error=None):
    """Create SOAP response XML."""
    envelope = ET.Element('{http://schemas.xmlsoap.org/soap/envelope/}Envelope')
    envelope.set('xmlns:soap', 'http://schemas.xmlsoap.org/soap/envelope/')
    envelope.set('xmlns:tns', 'http://eventscheduling.com/wsdl')
    envelope.set('xmlns:sch', 'http://eventscheduling.com/schemas')
    
    body = ET.SubElement(envelope, '{http://schemas.xmlsoap.org/soap/envelope/}Body')
    
    if error:
        fault = ET.SubElement(body, '{http://schemas.xmlsoap.org/soap/envelope/}Fault')
        fault_code = ET.SubElement(fault, 'faultcode')
        fault_code.text = 'Server'
        fault_string = ET.SubElement(fault, 'faultstring')
        fault_string.text = str(error)
    else:
        response_elem = ET.SubElement(body, f'{{http://eventscheduling.com/wsdl}}{operation}Response')
        
        if operation == 'AddEvent' and data:
            result = ET.SubElement(response_elem, '{http://eventscheduling.com/wsdl}return')
            result.text = data
        elif operation == 'GetEvent' and data:
            create_event_xml(response_elem, data)
        elif operation == 'GetAllEvents' and data:
            for event in data:
                create_event_xml(response_elem, event)
        elif operation in ['UpdateEvent', 'DeleteEvent']:
            result = ET.SubElement(response_elem, '{http://eventscheduling.com/wsdl}return')
            result.text = 'true' if success else 'false'
    
    return ET.tostring(envelope, encoding='unicode')

def create_event_xml(parent, event_data):
    """Create event XML element."""
    event_elem = ET.SubElement(parent, '{http://eventscheduling.com/schemas}event')
    
    namespace = 'http://eventscheduling.com/schemas'
    for field in ['id', 'title', 'agenda', 'date', 'time', 'importance', 'location', 'coordinator', 'recurrence']:
        if field in event_data and event_data[field] is not None:
            field_elem = ET.SubElement(event_elem, f'{{{namespace}}}{field}')
            field_elem.text = str(event_data[field])
    
    if 'participants' in event_data and event_data['participants']:
        participants_elem = ET.SubElement(event_elem, f'{{{namespace}}}participants')
        for participant in event_data['participants']:
            participant_elem = ET.SubElement(participants_elem, f'{{{namespace}}}participant')
            participant_elem.text = participant

class EventService:
    """Implementation of the Event Scheduling SOAP Service."""
    
    @staticmethod
    def add_event(event_data):
        """Add a new event to the store."""
        try:
            # Validate fields
            if 'importance' in event_data:
                event_data['importance'] = validate_importance(event_data['importance'])
            if 'recurrence' in event_data:
                event_data['recurrence'] = validate_recurrence(event_data['recurrence'])
            
            with app.app_context():
                event_id = DatabaseEventService.add_event(event_data)
                return event_id
        except Exception as e:
            raise ValueError(f"Failed to add event: {e}")

    @staticmethod
    def get_event(event_id):
        """Retrieve a specific event by ID."""
        with app.app_context():
            return DatabaseEventService.get_event(event_id)

    @staticmethod
    def get_all_events():
        """Retrieve all events."""
        with app.app_context():
            return DatabaseEventService.get_all_events()

    @staticmethod
    def update_event(event_data):
        """Update an existing event."""
        try:
            # Validate fields
            if 'importance' in event_data:
                event_data['importance'] = validate_importance(event_data['importance'])
            if 'recurrence' in event_data:
                event_data['recurrence'] = validate_recurrence(event_data['recurrence'])
            
            with app.app_context():
                return DatabaseEventService.update_event(event_data)
        except Exception as e:
            raise ValueError(f"Failed to update event: {e}")

    @staticmethod
    def delete_event(event_id):
        """Delete an event by ID."""
        with app.app_context():
            return DatabaseEventService.delete_event(event_id)

@app.route('/soap', methods=['POST'])
def soap_endpoint():
    """SOAP endpoint for event operations."""
    try:
        xml_data = request.get_data(as_text=True)
        operation, event_data, event_id = parse_soap_request(xml_data)
        
        if operation == 'AddEvent':
            result = EventService.add_event(event_data)
            response_xml = create_soap_response('AddEvent', data=result)
        elif operation == 'GetEvent':
            result = EventService.get_event(event_id)
            if result:
                response_xml = create_soap_response('GetEvent', data=result)
            else:
                response_xml = create_soap_response('GetEvent', error="Event not found")
        elif operation == 'GetAllEvents':
            result = EventService.get_all_events()
            response_xml = create_soap_response('GetAllEvents', data=result)
        elif operation == 'UpdateEvent':
            success = EventService.update_event(event_data)
            response_xml = create_soap_response('UpdateEvent', success=success)
        elif operation == 'DeleteEvent':
            success = EventService.delete_event(event_id)
            response_xml = create_soap_response('DeleteEvent', success=success)
        else:
            response_xml = create_soap_response('Unknown', error="Unknown operation")
        
        return Response(response_xml, content_type='text/xml')
    
    except Exception as e:
        error_response = create_soap_response('Error', error=str(e))
        return Response(error_response, content_type='text/xml', status=500)

@app.route('/soap', methods=['GET'])
def wsdl():
    """Serve WSDL file."""
    import os
    try:
        # Get the directory of the current file and go up two levels to reach the project root
        current_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(os.path.dirname(current_dir))
        wsdl_path = os.path.join(project_root, 'wsdl', 'EventService.wsdl')
        
        with open(wsdl_path, 'r') as f:
            wsdl_content = f.read()
        return Response(wsdl_content, content_type='text/xml')
    except FileNotFoundError:
        return "WSDL file not found", 404

# Additional REST API endpoints for testing and database interaction
@app.route('/api/events', methods=['GET'])
def api_get_all_events():
    """REST API endpoint to get all events as JSON."""
    try:
        events = DatabaseEventService.get_all_events()
        return jsonify({'events': events, 'status': 'success'})
    except Exception as e:
        return jsonify({'error': str(e), 'status': 'error'}), 500

@app.route('/api/events/<event_id>', methods=['GET'])
def api_get_event(event_id):
    """REST API endpoint to get a specific event as JSON."""
    try:
        event = DatabaseEventService.get_event(event_id)
        if event:
            return jsonify({'event': event, 'status': 'success'})
        else:
            return jsonify({'error': 'Event not found', 'status': 'error'}), 404
    except Exception as e:
        return jsonify({'error': str(e), 'status': 'error'}), 500

@app.route('/api/events', methods=['POST'])
def api_create_event():
    """REST API endpoint to create a new event."""
    try:
        event_data = request.get_json()
        if not event_data:
            return jsonify({'error': 'No data provided', 'status': 'error'}), 400
        
        # Validate required fields
        required_fields = ['title', 'date', 'time', 'coordinator']
        for field in required_fields:
            if field not in event_data:
                return jsonify({'error': f'Missing required field: {field}', 'status': 'error'}), 400
        
        event_id = DatabaseEventService.add_event(event_data)
        return jsonify({'event_id': event_id, 'status': 'success'}), 201
    except Exception as e:
        return jsonify({'error': str(e), 'status': 'error'}), 500

@app.route('/api/events/<event_id>', methods=['PUT'])
def api_update_event(event_id):
    """REST API endpoint to update an event."""
    try:
        event_data = request.get_json()
        if not event_data:
            return jsonify({'error': 'No data provided', 'status': 'error'}), 400
        
        event_data['id'] = event_id
        success = DatabaseEventService.update_event(event_data)
        if success:
            return jsonify({'status': 'success'})
        else:
            return jsonify({'error': 'Event not found', 'status': 'error'}), 404
    except Exception as e:
        return jsonify({'error': str(e), 'status': 'error'}), 500

@app.route('/api/events/<event_id>', methods=['DELETE'])
def api_delete_event(event_id):
    """REST API endpoint to delete an event."""
    try:
        success = DatabaseEventService.delete_event(event_id)
        if success:
            return jsonify({'status': 'success'})
        else:
            return jsonify({'error': 'Event not found', 'status': 'error'}), 404
    except Exception as e:
        return jsonify({'error': str(e), 'status': 'error'}), 500

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return jsonify({'status': 'healthy', 'database': 'connected'})

# Create WSGI app for compatibility
wsgi_app = app