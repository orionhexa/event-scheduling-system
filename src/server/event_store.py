import uuid

# Simple in-memory storage dictionary
# Key: Event ID (str), Value: Event data (dict or object)
EVENT_STORE = {}

class EventStore:
    """Manages in-memory storage for events."""
    
    @staticmethod
    def add_event(event_data):
        """Creates a new event and assigns a unique ID."""
        # Ensure the event_data is a mutable dictionary for modification
        event_dict = dict(event_data)
        
        # Generate a unique ID (as a string)
        new_id = str(uuid.uuid4())
        event_dict['id'] = new_id
        
        # Store the event
        EVENT_STORE[new_id] = event_dict
        return new_id

    @staticmethod
    def get_event(event_id):
        """Retrieves an event by ID."""
        return EVENT_STORE.get(event_id)

    @staticmethod
    def get_all_events():
        """Retrieves all events."""
        return list(EVENT_STORE.values())

    @staticmethod
    def update_event(event_data):
        """Updates an existing event's details."""
        event_id = event_data.get('id')
        if event_id in EVENT_STORE:
            # Update all fields
            EVENT_STORE[event_id].update(event_data)
            return True
        return False

    @staticmethod
    def delete_event(event_id):
        """Deletes an event by ID."""
        if event_id in EVENT_STORE:
            del EVENT_STORE[event_id]
            return True
        return False