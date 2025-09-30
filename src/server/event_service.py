from spyne.application import Application
from spyne.server.wsgi import WsgiApplication
from spyne.decorator import srpc
from spyne.model.complex import ComplexModel, Array
from spyne.model.primitive import Unicode, Integer, Boolean, String, Date, Time
from spyne.server.wsgi import WsgiApplication
from spyne.service import ServiceBase
from spyne.protocol.soap import Soap11
from spyne.protocol.http import HttpRpc
from spyne.server.wsgi import WsgiApplication
from datetime import date, time

from .event_store import EventStore

# Define the Enumerations and Complex Types to mirror event.xsd
ImportanceType = String.customize(
    min_length=1, max_length=10, 
    pattern='(low|medium|high)'
)
RecurrenceType = String.customize(
    min_length=4, max_length=8, 
    pattern='(none|daily|weekly|monthly|annually)'
)

class ParticipantType(ComplexModel):
    """Corresponds to the <participants> structure."""
    __namespace__ = 'http://eventscheduling.com/schemas'
    participant = Array(Unicode) # Represents multiple <participant> strings

class EventType(ComplexModel):
    """Corresponds to the main <event> structure."""
    __namespace__ = 'http://eventscheduling.com/schemas'
    
    # NOTE: The id will be auto-assigned in AddEvent, but required for Update/Delete
    id = Unicode
    title = Unicode
    agenda = Unicode
    date = Date  # Spyne's Date maps to xsd:date
    time = Time  # Spyne's Time maps to xsd:time
    importance = ImportanceType
    location = Unicode
    coordinator = Unicode
    participants = ParticipantType.customize(min_occurs=0) # Optional participants
    recurrence = RecurrenceType
    

class EventService(ServiceBase):
    """Implementation of the Event Scheduling SOAP Service."""
    
    __target_namespace__ = 'http://eventscheduling.com/wsdl'
    __in_header__ = __out_header__ = None

    @srpc(EventType, _returns=Unicode)
    def AddEvent(eventData):
        """
        Adds a new event to the store.
        @param eventData: EventType object containing event details.
        @returns: The unique ID (string) of the newly created event.
        """
        # Convert Spyne ComplexModel to a simple dictionary for the store
        event_dict = eventData.to_dict()
        
        # The EventStore handles ID assignment
        event_id = EventStore.add_event(event_dict)
        return event_id

    @srpc(Unicode, _returns=EventType.customize(min_occurs=0))
    def GetEvent(eventId):
        """
        Retrieves a specific event by ID.
        @param eventId: The ID (string) of the event to retrieve.
        @returns: EventType object or None if not found.
        """
        event_data = EventStore.get_event(eventId)
        if event_data:
            # Convert simple dictionary back to Spyne ComplexModel
            return EventType(**event_data)
        # Returning None will result in an empty response body or a SOAP fault if configured
        return None

    # NOTE: Spyne does not easily allow defining a custom complex type for the response,
    # so we will return an Array of EventType objects, which is common in SOAP service implementations.
    @srpc(_returns=Array(EventType))
    def GetAllEvents():
        """
        Retrieves all events in the store.
        @returns: An array of EventType objects.
        """
        all_events = EventStore.get_all_events()
        # Convert all event dictionaries to EventType objects
        return [EventType(**e) for e in all_events]

    @srpc(EventType, _returns=Boolean)
    def UpdateEvent(eventData):
        """
        Updates an existing event.
        @param eventData: EventType object with the ID and new details.
        @returns: True if update was successful, False otherwise.
        """
        event_dict = eventData.to_dict()
        return EventStore.update_event(event_dict)

    @srpc(Unicode, _returns=Boolean)
    def DeleteEvent(eventId):
        """
        Deletes an event by ID.
        @param eventId: The ID (string) of the event to delete.
        @returns: True if deletion was successful, False otherwise.
        """
        return EventStore.delete_event(eventId)


# Create the Spyne Application
application = Application([EventService],
                          tns='http://eventscheduling.com/wsdl', 
                          in_protocol=Soap11(validator='lxml'), # Use lxml for validation
                          out_protocol=Soap11()
                          )

# Wrap the Spyne Application with a WSGI interface (e.g., for Flask/Werkzeug)
wsgi_app = WsgiApplication(application)