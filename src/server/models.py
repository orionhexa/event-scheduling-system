from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, date, time
import uuid

db = SQLAlchemy()

class Event(db.Model):
    """Event model for the database."""
    __tablename__ = 'events'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    title = db.Column(db.String(200), nullable=False)
    agenda = db.Column(db.Text, nullable=True)
    date = db.Column(db.Date, nullable=False)
    time = db.Column(db.Time, nullable=False)
    importance = db.Column(db.Enum('low', 'medium', 'high', name='importance_type'), nullable=False, default='medium')
    location = db.Column(db.String(300), nullable=True)
    coordinator = db.Column(db.String(100), nullable=False)
    recurrence = db.Column(db.Enum('none', 'daily', 'weekly', 'monthly', 'annually', name='recurrence_type'), nullable=False, default='none')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationship with participants
    participants = db.relationship('Participant', backref='event', lazy=True, cascade='all, delete-orphan')
    
    def to_dict(self):
        """Convert event to dictionary for JSON/XML serialization."""
        return {
            'id': self.id,
            'title': self.title,
            'agenda': self.agenda,
            'date': self.date.isoformat() if self.date else None,
            'time': self.time.strftime('%H:%M:%S') if self.time else None,
            'importance': self.importance,
            'location': self.location,
            'coordinator': self.coordinator,
            'recurrence': self.recurrence,
            'participants': [p.name for p in self.participants],
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    @classmethod
    def from_dict(cls, data):
        """Create Event instance from dictionary."""
        event = cls()
        event.title = data.get('title')
        event.agenda = data.get('agenda')
        
        # Handle date conversion
        if data.get('date'):
            if isinstance(data['date'], str):
                event.date = datetime.strptime(data['date'], '%Y-%m-%d').date()
            elif isinstance(data['date'], date):
                event.date = data['date']
        
        # Handle time conversion
        if data.get('time'):
            if isinstance(data['time'], str):
                event.time = datetime.strptime(data['time'], '%H:%M:%S').time()
            elif isinstance(data['time'], time):
                event.time = data['time']
        
        event.importance = data.get('importance', 'medium')
        event.location = data.get('location')
        event.coordinator = data.get('coordinator')
        event.recurrence = data.get('recurrence', 'none')
        
        return event
    
    def update_from_dict(self, data):
        """Update event from dictionary."""
        if 'title' in data:
            self.title = data['title']
        if 'agenda' in data:
            self.agenda = data['agenda']
        if 'date' in data:
            if isinstance(data['date'], str):
                self.date = datetime.strptime(data['date'], '%Y-%m-%d').date()
            elif isinstance(data['date'], date):
                self.date = data['date']
        if 'time' in data:
            if isinstance(data['time'], str):
                self.time = datetime.strptime(data['time'], '%H:%M:%S').time()
            elif isinstance(data['time'], time):
                self.time = data['time']
        if 'importance' in data:
            self.importance = data['importance']
        if 'location' in data:
            self.location = data['location']
        if 'coordinator' in data:
            self.coordinator = data['coordinator']
        if 'recurrence' in data:
            self.recurrence = data['recurrence']
        
        self.updated_at = datetime.utcnow()
    
    def __repr__(self):
        return f'<Event {self.id}: {self.title}>'


class Participant(db.Model):
    """Participant model for events."""
    __tablename__ = 'participants'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    event_id = db.Column(db.String(36), db.ForeignKey('events.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Participant {self.name}>'