#!/usr/bin/env python3
"""
Database initialization script for Event Scheduling System.
This script creates the database tables and optionally adds sample data.
"""

import os
import sys
from datetime import datetime, date, time

# Add the project root to the Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from src.server.event_service import app, db
from src.server.models import Event, Participant

def init_database():
    """Initialize the database with tables."""
    with app.app_context():
        # Create all tables
        db.create_all()
        print("Database tables created successfully!")

def add_sample_data():
    """Add sample events to the database."""
    with app.app_context():
        # Check if we already have data
        if Event.query.count() > 0:
            print("Database already has data. Skipping sample data insertion.")
            return
        
        # Sample events
        sample_events = [
            {
                'title': 'Team Meeting',
                'agenda': 'Weekly team sync and project updates',
                'date': date(2025, 10, 5),
                'time': time(10, 0),
                'importance': 'medium',
                'location': 'Conference Room A',
                'coordinator': 'John Smith',
                'recurrence': 'weekly',
                'participants': ['Alice Johnson', 'Bob Wilson', 'Carol Brown']
            },
            {
                'title': 'Product Launch',
                'agenda': 'Launch event for new product line',
                'date': date(2025, 10, 15),
                'time': time(14, 30),
                'importance': 'high',
                'location': 'Main Auditorium',
                'coordinator': 'Sarah Davis',
                'recurrence': 'none',
                'participants': ['Marketing Team', 'Development Team', 'Sales Team']
            },
            {
                'title': 'Training Session',
                'agenda': 'New employee orientation and training',
                'date': date(2025, 10, 8),
                'time': time(9, 0),
                'importance': 'medium',
                'location': 'Training Room B',
                'coordinator': 'Mike Johnson',
                'recurrence': 'monthly',
                'participants': ['New Employees', 'HR Team']
            }
        ]
        
        for event_data in sample_events:
            # Create event
            event = Event.from_dict(event_data)
            db.session.add(event)
            db.session.flush()  # Get the ID
            
            # Add participants
            if 'participants' in event_data:
                for participant_name in event_data['participants']:
                    participant = Participant(name=participant_name, event_id=event.id)
                    db.session.add(participant)
        
        db.session.commit()
        print(f"Added {len(sample_events)} sample events to the database!")

def reset_database():
    """Drop all tables and recreate them."""
    with app.app_context():
        db.drop_all()
        db.create_all()
        print("Database reset successfully!")

if __name__ == '__main__':
    if len(sys.argv) > 1:
        if sys.argv[1] == 'reset':
            reset_database()
            add_sample_data()
        elif sys.argv[1] == 'sample':
            add_sample_data()
        elif sys.argv[1] == 'init':
            init_database()
        else:
            print("Usage: python init_db.py [init|sample|reset]")
            print("  init  - Initialize database tables")
            print("  sample - Add sample data")
            print("  reset - Reset database and add sample data")
    else:
        init_database()
        add_sample_data()