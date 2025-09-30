from .models import db, Event, Participant
from datetime import datetime, date, time

class EventService:
    """Database service for event operations."""
    
    @staticmethod
    def add_event(event_data):
        """Add a new event to the database."""
        try:
            # Create event from dictionary
            event = Event.from_dict(event_data)
            
            # Add event to database
            db.session.add(event)
            db.session.flush()  # Get the ID without committing
            
            # Add participants if provided
            if 'participants' in event_data and event_data['participants']:
                for participant_name in event_data['participants']:
                    if participant_name:  # Skip empty names
                        participant = Participant(name=participant_name, event_id=event.id)
                        db.session.add(participant)
            
            db.session.commit()
            return event.id
            
        except Exception as e:
            db.session.rollback()
            raise Exception(f"Failed to add event: {str(e)}")
    
    @staticmethod
    def get_event(event_id):
        """Get an event by ID."""
        try:
            event = Event.query.get(event_id)
            if event:
                return event.to_dict()
            return None
        except Exception as e:
            raise Exception(f"Failed to get event: {str(e)}")
    
    @staticmethod
    def get_all_events():
        """Get all events."""
        try:
            events = Event.query.all()
            return [event.to_dict() for event in events]
        except Exception as e:
            raise Exception(f"Failed to get events: {str(e)}")
    
    @staticmethod
    def update_event(event_data):
        """Update an existing event."""
        try:
            event_id = event_data.get('id')
            if not event_id:
                return False
            
            event = Event.query.get(event_id)
            if not event:
                return False
            
            # Update event fields
            event.update_from_dict(event_data)
            
            # Update participants if provided
            if 'participants' in event_data:
                # Remove existing participants
                Participant.query.filter_by(event_id=event_id).delete()
                
                # Add new participants
                for participant_name in event_data['participants']:
                    if participant_name:  # Skip empty names
                        participant = Participant(name=participant_name, event_id=event_id)
                        db.session.add(participant)
            
            db.session.commit()
            return True
            
        except Exception as e:
            db.session.rollback()
            raise Exception(f"Failed to update event: {str(e)}")
    
    @staticmethod
    def delete_event(event_id):
        """Delete an event by ID."""
        try:
            event = Event.query.get(event_id)
            if not event:
                return False
            
            # Delete participants (cascade should handle this, but explicit is better)
            Participant.query.filter_by(event_id=event_id).delete()
            
            # Delete event
            db.session.delete(event)
            db.session.commit()
            return True
            
        except Exception as e:
            db.session.rollback()
            raise Exception(f"Failed to delete event: {str(e)}")
    
    @staticmethod
    def get_events_by_date_range(start_date, end_date):
        """Get events within a date range."""
        try:
            events = Event.query.filter(
                Event.date >= start_date,
                Event.date <= end_date
            ).all()
            return [event.to_dict() for event in events]
        except Exception as e:
            raise Exception(f"Failed to get events by date range: {str(e)}")
    
    @staticmethod
    def get_events_by_coordinator(coordinator):
        """Get events by coordinator."""
        try:
            events = Event.query.filter(Event.coordinator.ilike(f'%{coordinator}%')).all()
            return [event.to_dict() for event in events]
        except Exception as e:
            raise Exception(f"Failed to get events by coordinator: {str(e)}")
    
    @staticmethod
    def search_events(query):
        """Search events by title, agenda, or location."""
        try:
            events = Event.query.filter(
                db.or_(
                    Event.title.ilike(f'%{query}%'),
                    Event.agenda.ilike(f'%{query}%'),
                    Event.location.ilike(f'%{query}%')
                )
            ).all()
            return [event.to_dict() for event in events]
        except Exception as e:
            raise Exception(f"Failed to search events: {str(e)}")