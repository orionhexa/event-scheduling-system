#!/usr/bin/env python3
"""
Test script to validate database operations for Event Scheduling System.
"""

import os
import sys
from datetime import datetime, date, time
import requests
import json

# Add the project root to the Python path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

from src.server.event_service import app, db
from src.server.database_service import EventService

def test_database_operations():
    """Test database operations directly."""
    print("=" * 50)
    print("Testing Database Operations")
    print("=" * 50)
    
    with app.app_context():
        try:
            # Test adding an event
            print("\n1. Testing Add Event...")
            event_data = {
                'title': 'Database Test Event',
                'agenda': 'Testing database operations',
                'date': '2025-10-10',
                'time': '15:30:00',
                'importance': 'high',
                'location': 'Test Room',
                'coordinator': 'Test User',
                'recurrence': 'none',
                'participants': ['Tester 1', 'Tester 2']
            }
            
            event_id = EventService.add_event(event_data)
            print(f"✅ Event added successfully! ID: {event_id}")
            
            # Test getting the event
            print("\n2. Testing Get Event...")
            retrieved_event = EventService.get_event(event_id)
            if retrieved_event:
                print(f"✅ Event retrieved successfully!")
                print(f"   Title: {retrieved_event['title']}")
                print(f"   Participants: {retrieved_event['participants']}")
            else:
                print("❌ Failed to retrieve event")
                return False
            
            # Test getting all events
            print("\n3. Testing Get All Events...")
            all_events = EventService.get_all_events()
            print(f"✅ Retrieved {len(all_events)} events")
            
            # Test updating the event
            print("\n4. Testing Update Event...")
            event_data['id'] = event_id
            event_data['title'] = 'Updated Database Test Event'
            event_data['participants'] = ['Updated Tester 1', 'Updated Tester 2', 'New Tester']
            
            success = EventService.update_event(event_data)
            if success:
                print("✅ Event updated successfully!")
                
                # Verify update
                updated_event = EventService.get_event(event_id)
                if updated_event and updated_event['title'] == 'Updated Database Test Event':
                    print("✅ Update verified!")
                    print(f"   New participants: {updated_event['participants']}")
                else:
                    print("❌ Update verification failed")
            else:
                print("❌ Failed to update event")
            
            # Test deleting the event
            print("\n5. Testing Delete Event...")
            success = EventService.delete_event(event_id)
            if success:
                print("✅ Event deleted successfully!")
                
                # Verify deletion
                deleted_event = EventService.get_event(event_id)
                if not deleted_event:
                    print("✅ Deletion verified!")
                else:
                    print("❌ Deletion verification failed")
            else:
                print("❌ Failed to delete event")
            
            return True
            
        except Exception as e:
            print(f"❌ Database test failed: {str(e)}")
            return False

def test_rest_api():
    """Test REST API endpoints."""
    print("\n" + "=" * 50)
    print("Testing REST API Endpoints")
    print("=" * 50)
    
    base_url = 'http://localhost:8000/api'
    
    try:
        # Test health check
        print("\n1. Testing Health Check...")
        response = requests.get(f'{base_url}/health', timeout=5)
        if response.status_code == 200:
            print("✅ Health check passed!")
            print(f"   Response: {response.json()}")
        else:
            print(f"❌ Health check failed with status {response.status_code}")
            return False
        
        # Test creating an event
        print("\n2. Testing Create Event API...")
        event_data = {
            'title': 'REST API Test Event',
            'agenda': 'Testing REST API operations',
            'date': '2025-10-12',
            'time': '16:00:00',
            'importance': 'medium',
            'location': 'API Test Room',
            'coordinator': 'API Tester',
            'recurrence': 'weekly',
            'participants': ['API Tester 1', 'API Tester 2']
        }
        
        response = requests.post(f'{base_url}/events', json=event_data, timeout=10)
        if response.status_code == 201:
            result = response.json()
            event_id = result['event_id']
            print(f"✅ Event created via API! ID: {event_id}")
        else:
            print(f"❌ Failed to create event via API: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
        
        # Test getting all events
        print("\n3. Testing Get All Events API...")
        response = requests.get(f'{base_url}/events', timeout=10)
        if response.status_code == 200:
            data = response.json()
            events = data.get('events', [])
            print(f"✅ Retrieved {len(events)} events via API")
        else:
            print(f"❌ Failed to get events via API: {response.status_code}")
        
        # Test getting specific event
        print("\n4. Testing Get Specific Event API...")
        response = requests.get(f'{base_url}/events/{event_id}', timeout=10)
        if response.status_code == 200:
            data = response.json()
            event = data.get('event')
            print("✅ Retrieved specific event via API")
            print(f"   Title: {event['title']}")
        else:
            print(f"❌ Failed to get specific event via API: {response.status_code}")
        
        # Test updating event
        print("\n5. Testing Update Event API...")
        update_data = {
            'title': 'Updated REST API Test Event',
            'participants': ['Updated API Tester 1', 'Updated API Tester 2', 'New API Tester']
        }
        
        response = requests.put(f'{base_url}/events/{event_id}', json=update_data, timeout=10)
        if response.status_code == 200:
            print("✅ Event updated via API!")
        else:
            print(f"❌ Failed to update event via API: {response.status_code}")
        
        # Test deleting event
        print("\n6. Testing Delete Event API...")
        response = requests.delete(f'{base_url}/events/{event_id}', timeout=10)
        if response.status_code == 200:
            print("✅ Event deleted via API!")
        else:
            print(f"❌ Failed to delete event via API: {response.status_code}")
        
        return True
        
    except requests.exceptions.RequestException as e:
        print(f"❌ REST API test failed: Connection error - {str(e)}")
        print("   Make sure the server is running on http://localhost:8000")
        return False
    except Exception as e:
        print(f"❌ REST API test failed: {str(e)}")
        return False

def main():
    """Run all tests."""
    print("Event Scheduling System - Database Integration Test")
    print("Make sure the server is running before running REST API tests!")
    
    # Test database operations
    db_success = test_database_operations()
    
    # Test REST API
    api_success = test_rest_api()
    
    print("\n" + "=" * 50)
    print("Test Results Summary")
    print("=" * 50)
    print(f"Database Operations: {'✅ PASSED' if db_success else '❌ FAILED'}")
    print(f"REST API Endpoints:  {'✅ PASSED' if api_success else '❌ FAILED'}")
    
    if db_success and api_success:
        print("\n🎉 All tests passed! Database integration is working correctly!")
    else:
        print("\n⚠️  Some tests failed. Check the output above for details.")

if __name__ == '__main__':
    main()