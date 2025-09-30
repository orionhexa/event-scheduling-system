import tkinter as tk
from tkinter import ttk, messagebox
import requests
import json
from datetime import date, datetime

class RestEventClientGUI(tk.Tk):
    """REST API Client for the Event Scheduling System."""
    
    def __init__(self):
        super().__init__()
        self.title("REST Event Scheduling Client")
        self.geometry("900x700")
        
        # Configuration
        self.base_url = 'http://localhost:8000/api'
        
        # Test connection
        self.test_connection()
        
        self.create_widgets()
    
    def test_connection(self):
        """Test connection to the server."""
        try:
            response = requests.get(f'{self.base_url}/health', timeout=5)
            if response.status_code == 200:
                self.connection_status = "✅ Connected to server"
            else:
                self.connection_status = f"⚠️ Server responded with status {response.status_code}"
        except requests.exceptions.RequestException as e:
            self.connection_status = f"❌ Cannot connect to server: {str(e)}"
    
    def create_widgets(self):
        """Create the main GUI widgets."""
        # Status bar
        self.status_label = tk.Label(self, text=self.connection_status, bd=1, relief=tk.SUNKEN, anchor=tk.W)
        self.status_label.pack(side=tk.BOTTOM, fill=tk.X)
        
        # Main notebook for tabs
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(pady=10, padx=10, expand=True, fill="both")
        
        # Create tabs
        self.create_events_tab()
        self.view_events_tab()
        self.update_delete_tab()
    
    def create_events_tab(self):
        """Create the tab for adding new events."""
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text='Create Event')
        
        # Form fields
        form_frame = ttk.LabelFrame(frame, text="Event Details", padding="10")
        form_frame.pack(fill="x", padx=10, pady=10)
        
        self.create_entries = {}
        fields = [
            ('Title *', 'Team Meeting'),
            ('Agenda', 'Weekly team sync and project updates'),
            ('Date (YYYY-MM-DD) *', date.today().strftime('%Y-%m-%d')),
            ('Time (HH:MM:SS) *', '10:00:00'),
            ('Location', 'Conference Room A'),
            ('Coordinator *', 'John Doe'),
            ('Participants (comma-separated)', 'Alice, Bob, Charlie')
        ]
        
        for i, (label_text, default_value) in enumerate(fields):
            ttk.Label(form_frame, text=label_text).grid(row=i, column=0, sticky='w', pady=5, padx=5)
            entry = ttk.Entry(form_frame, width=50)
            entry.grid(row=i, column=1, sticky='ew', pady=5, padx=5)
            entry.insert(0, default_value)
            self.create_entries[label_text] = entry
        
        # Importance dropdown
        ttk.Label(form_frame, text="Importance *").grid(row=len(fields), column=0, sticky='w', pady=5, padx=5)
        self.importance_var = tk.StringVar(value='medium')
        importance_combo = ttk.Combobox(form_frame, textvariable=self.importance_var, values=['low', 'medium', 'high'], state='readonly')
        importance_combo.grid(row=len(fields), column=1, sticky='ew', pady=5, padx=5)
        
        # Recurrence dropdown
        ttk.Label(form_frame, text="Recurrence *").grid(row=len(fields)+1, column=0, sticky='w', pady=5, padx=5)
        self.recurrence_var = tk.StringVar(value='none')
        recurrence_combo = ttk.Combobox(form_frame, textvariable=self.recurrence_var, values=['none', 'daily', 'weekly', 'monthly', 'annually'], state='readonly')
        recurrence_combo.grid(row=len(fields)+1, column=1, sticky='ew', pady=5, padx=5)
        
        form_frame.columnconfigure(1, weight=1)
        
        # Buttons
        button_frame = ttk.Frame(frame)
        button_frame.pack(fill="x", padx=10, pady=10)
        
        ttk.Button(button_frame, text="Create Event", command=self.create_event).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Clear Form", command=self.clear_create_form).pack(side=tk.LEFT, padx=5)
    
    def view_events_tab(self):
        """Create the tab for viewing events."""
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text='View Events')
        
        # Controls
        control_frame = ttk.Frame(frame)
        control_frame.pack(fill="x", padx=10, pady=10)
        
        ttk.Button(control_frame, text="Refresh Events", command=self.refresh_events).pack(side=tk.LEFT, padx=5)
        ttk.Button(control_frame, text="Get Event by ID", command=self.get_event_by_id).pack(side=tk.LEFT, padx=5)
        
        self.event_id_entry = ttk.Entry(control_frame, width=20)
        self.event_id_entry.pack(side=tk.LEFT, padx=5)
        ttk.Label(control_frame, text="Event ID").pack(side=tk.LEFT, padx=2)
        
        # Events display
        display_frame = ttk.LabelFrame(frame, text="Events", padding="10")
        display_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Treeview for events
        columns = ('ID', 'Title', 'Date', 'Time', 'Importance', 'Location', 'Coordinator')
        self.events_tree = ttk.Treeview(display_frame, columns=columns, show='headings', height=15)
        
        for col in columns:
            self.events_tree.heading(col, text=col)
            self.events_tree.column(col, width=100)
        
        # Scrollbars
        v_scrollbar = ttk.Scrollbar(display_frame, orient="vertical", command=self.events_tree.yview)
        h_scrollbar = ttk.Scrollbar(display_frame, orient="horizontal", command=self.events_tree.xview)
        self.events_tree.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)
        
        self.events_tree.pack(side="left", fill="both", expand=True)
        v_scrollbar.pack(side="right", fill="y")
        h_scrollbar.pack(side="bottom", fill="x")
        
        # Event details
        details_frame = ttk.LabelFrame(frame, text="Event Details", padding="10")
        details_frame.pack(fill="x", padx=10, pady=10)
        
        self.details_text = tk.Text(details_frame, height=8, wrap=tk.WORD)
        details_scrollbar = ttk.Scrollbar(details_frame, orient="vertical", command=self.details_text.yview)
        self.details_text.configure(yscrollcommand=details_scrollbar.set)
        
        self.details_text.pack(side="left", fill="both", expand=True)
        details_scrollbar.pack(side="right", fill="y")
        
        # Bind selection event
        self.events_tree.bind('<<TreeviewSelect>>', self.on_event_select)
        
        # Load events initially
        self.refresh_events()
    
    def update_delete_tab(self):
        """Create the tab for updating and deleting events."""
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text='Update/Delete')
        
        # Event ID selection
        id_frame = ttk.LabelFrame(frame, text="Select Event", padding="10")
        id_frame.pack(fill="x", padx=10, pady=10)
        
        ttk.Label(id_frame, text="Event ID:").pack(side=tk.LEFT, padx=5)
        self.update_id_entry = ttk.Entry(id_frame, width=40)
        self.update_id_entry.pack(side=tk.LEFT, padx=5, fill="x", expand=True)
        ttk.Button(id_frame, text="Load Event", command=self.load_event_for_update).pack(side=tk.LEFT, padx=5)
        
        # Update form
        update_frame = ttk.LabelFrame(frame, text="Update Event", padding="10")
        update_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        self.update_entries = {}
        fields = [
            ('Title *', ''),
            ('Agenda', ''),
            ('Date (YYYY-MM-DD) *', ''),
            ('Time (HH:MM:SS) *', ''),
            ('Location', ''),
            ('Coordinator *', ''),
            ('Participants (comma-separated)', '')
        ]
        
        for i, (label_text, default_value) in enumerate(fields):
            ttk.Label(update_frame, text=label_text).grid(row=i, column=0, sticky='w', pady=5, padx=5)
            entry = ttk.Entry(update_frame, width=50)
            entry.grid(row=i, column=1, sticky='ew', pady=5, padx=5)
            self.update_entries[label_text] = entry
        
        # Importance and recurrence dropdowns
        ttk.Label(update_frame, text="Importance *").grid(row=len(fields), column=0, sticky='w', pady=5, padx=5)
        self.update_importance_var = tk.StringVar(value='medium')
        update_importance_combo = ttk.Combobox(update_frame, textvariable=self.update_importance_var, values=['low', 'medium', 'high'], state='readonly')
        update_importance_combo.grid(row=len(fields), column=1, sticky='ew', pady=5, padx=5)
        
        ttk.Label(update_frame, text="Recurrence *").grid(row=len(fields)+1, column=0, sticky='w', pady=5, padx=5)
        self.update_recurrence_var = tk.StringVar(value='none')
        update_recurrence_combo = ttk.Combobox(update_frame, textvariable=self.update_recurrence_var, values=['none', 'daily', 'weekly', 'monthly', 'annually'], state='readonly')
        update_recurrence_combo.grid(row=len(fields)+1, column=1, sticky='ew', pady=5, padx=5)
        
        update_frame.columnconfigure(1, weight=1)
        
        # Buttons
        button_frame = ttk.Frame(frame)
        button_frame.pack(fill="x", padx=10, pady=10)
        
        ttk.Button(button_frame, text="Update Event", command=self.update_event).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Delete Event", command=self.delete_event).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Clear Form", command=self.clear_update_form).pack(side=tk.LEFT, padx=5)
    
    def create_event(self):
        """Create a new event via REST API."""
        try:
            # Collect form data
            event_data = {}
            for label, entry in self.create_entries.items():
                value = entry.get().strip()
                if value:
                    key = label.replace(' *', '').replace(' (YYYY-MM-DD)', '').replace(' (HH:MM:SS)', '').replace(' (comma-separated)', '').lower()
                    event_data[key] = value
            
            event_data['importance'] = self.importance_var.get()
            event_data['recurrence'] = self.recurrence_var.get()
            
            # Handle participants
            if 'participants' in event_data:
                participants = [p.strip() for p in event_data['participants'].split(',') if p.strip()]
                event_data['participants'] = participants
            
            # Validate required fields
            required = ['title', 'date', 'time', 'coordinator']
            missing = [field for field in required if not event_data.get(field)]
            if missing:
                messagebox.showerror("Error", f"Missing required fields: {', '.join(missing)}")
                return
            
            # Send request
            response = requests.post(f'{self.base_url}/events', json=event_data, timeout=10)
            
            if response.status_code == 201:
                result = response.json()
                messagebox.showinfo("Success", f"Event created successfully! ID: {result['event_id']}")
                self.update_status("✅ Event created successfully")
                self.refresh_events()
            else:
                error_data = response.json()
                messagebox.showerror("Error", f"Failed to create event: {error_data.get('error', 'Unknown error')}")
                self.update_status("❌ Failed to create event")
        
        except requests.exceptions.RequestException as e:
            messagebox.showerror("Connection Error", f"Cannot connect to server: {str(e)}")
            self.update_status("❌ Connection error")
        except Exception as e:
            messagebox.showerror("Error", f"Unexpected error: {str(e)}")
            self.update_status("❌ Unexpected error")
    
    def refresh_events(self):
        """Refresh the events list."""
        try:
            response = requests.get(f'{self.base_url}/events', timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                events = data.get('events', [])
                
                # Clear existing items
                for item in self.events_tree.get_children():
                    self.events_tree.delete(item)
                
                # Add events to tree
                for event in events:
                    values = (
                        event.get('id', '')[:8] + '...' if len(event.get('id', '')) > 8 else event.get('id', ''),
                        event.get('title', ''),
                        event.get('date', ''),
                        event.get('time', ''),
                        event.get('importance', ''),
                        event.get('location', ''),
                        event.get('coordinator', '')
                    )
                    self.events_tree.insert('', 'end', values=values, tags=(event.get('id'),))
                
                self.update_status(f"✅ Loaded {len(events)} events")
            else:
                error_data = response.json()
                messagebox.showerror("Error", f"Failed to load events: {error_data.get('error', 'Unknown error')}")
                self.update_status("❌ Failed to load events")
        
        except requests.exceptions.RequestException as e:
            messagebox.showerror("Connection Error", f"Cannot connect to server: {str(e)}")
            self.update_status("❌ Connection error")
        except Exception as e:
            messagebox.showerror("Error", f"Unexpected error: {str(e)}")
            self.update_status("❌ Unexpected error")
    
    def get_event_by_id(self):
        """Get a specific event by ID."""
        event_id = self.event_id_entry.get().strip()
        if not event_id:
            messagebox.showerror("Error", "Please enter an Event ID")
            return
        
        try:
            response = requests.get(f'{self.base_url}/events/{event_id}', timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                event = data.get('event')
                if event:
                    self.display_event_details(event)
                    self.update_status(f"✅ Loaded event {event_id}")
            elif response.status_code == 404:
                messagebox.showerror("Error", "Event not found")
                self.update_status("❌ Event not found")
            else:
                error_data = response.json()
                messagebox.showerror("Error", f"Failed to load event: {error_data.get('error', 'Unknown error')}")
                self.update_status("❌ Failed to load event")
        
        except requests.exceptions.RequestException as e:
            messagebox.showerror("Connection Error", f"Cannot connect to server: {str(e)}")
            self.update_status("❌ Connection error")
        except Exception as e:
            messagebox.showerror("Error", f"Unexpected error: {str(e)}")
            self.update_status("❌ Unexpected error")
    
    def on_event_select(self, event):
        """Handle event selection in the tree."""
        selection = self.events_tree.selection()
        if selection:
            item = selection[0]
            tags = self.events_tree.item(item, 'tags')
            if tags:
                event_id = tags[0]
                self.get_event_details(event_id)
    
    def get_event_details(self, event_id):
        """Get and display event details."""
        try:
            response = requests.get(f'{self.base_url}/events/{event_id}', timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                event = data.get('event')
                if event:
                    self.display_event_details(event)
        
        except Exception as e:
            print(f"Error getting event details: {e}")
    
    def display_event_details(self, event):
        """Display event details in the text widget."""
        self.details_text.delete('1.0', tk.END)
        
        details = f"""Event Details:
ID: {event.get('id', 'N/A')}
Title: {event.get('title', 'N/A')}
Agenda: {event.get('agenda', 'N/A')}
Date: {event.get('date', 'N/A')}
Time: {event.get('time', 'N/A')}
Importance: {event.get('importance', 'N/A')}
Location: {event.get('location', 'N/A')}
Coordinator: {event.get('coordinator', 'N/A')}
Recurrence: {event.get('recurrence', 'N/A')}
Participants: {', '.join(event.get('participants', []))}
Created: {event.get('created_at', 'N/A')}
Updated: {event.get('updated_at', 'N/A')}"""
        
        self.details_text.insert('1.0', details)
    
    def load_event_for_update(self):
        """Load an event for updating."""
        event_id = self.update_id_entry.get().strip()
        if not event_id:
            messagebox.showerror("Error", "Please enter an Event ID")
            return
        
        try:
            response = requests.get(f'{self.base_url}/events/{event_id}', timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                event = data.get('event')
                if event:
                    # Populate update form
                    self.update_entries['Title *'].delete(0, tk.END)
                    self.update_entries['Title *'].insert(0, event.get('title', ''))
                    
                    self.update_entries['Agenda'].delete(0, tk.END)
                    self.update_entries['Agenda'].insert(0, event.get('agenda', ''))
                    
                    self.update_entries['Date (YYYY-MM-DD) *'].delete(0, tk.END)
                    self.update_entries['Date (YYYY-MM-DD) *'].insert(0, event.get('date', ''))
                    
                    self.update_entries['Time (HH:MM:SS) *'].delete(0, tk.END)
                    self.update_entries['Time (HH:MM:SS) *'].insert(0, event.get('time', ''))
                    
                    self.update_entries['Location'].delete(0, tk.END)
                    self.update_entries['Location'].insert(0, event.get('location', ''))
                    
                    self.update_entries['Coordinator *'].delete(0, tk.END)
                    self.update_entries['Coordinator *'].insert(0, event.get('coordinator', ''))
                    
                    self.update_entries['Participants (comma-separated)'].delete(0, tk.END)
                    self.update_entries['Participants (comma-separated)'].insert(0, ', '.join(event.get('participants', [])))
                    
                    self.update_importance_var.set(event.get('importance', 'medium'))
                    self.update_recurrence_var.set(event.get('recurrence', 'none'))
                    
                    self.update_status(f"✅ Loaded event {event_id} for editing")
            elif response.status_code == 404:
                messagebox.showerror("Error", "Event not found")
                self.update_status("❌ Event not found")
            else:
                error_data = response.json()
                messagebox.showerror("Error", f"Failed to load event: {error_data.get('error', 'Unknown error')}")
                self.update_status("❌ Failed to load event")
        
        except requests.exceptions.RequestException as e:
            messagebox.showerror("Connection Error", f"Cannot connect to server: {str(e)}")
            self.update_status("❌ Connection error")
        except Exception as e:
            messagebox.showerror("Error", f"Unexpected error: {str(e)}")
            self.update_status("❌ Unexpected error")
    
    def update_event(self):
        """Update an event."""
        event_id = self.update_id_entry.get().strip()
        if not event_id:
            messagebox.showerror("Error", "Please enter an Event ID")
            return
        
        try:
            # Collect form data
            event_data = {}
            for label, entry in self.update_entries.items():
                value = entry.get().strip()
                if value:
                    key = label.replace(' *', '').replace(' (YYYY-MM-DD)', '').replace(' (HH:MM:SS)', '').replace(' (comma-separated)', '').lower()
                    event_data[key] = value
            
            event_data['importance'] = self.update_importance_var.get()
            event_data['recurrence'] = self.update_recurrence_var.get()
            
            # Handle participants
            if 'participants' in event_data:
                participants = [p.strip() for p in event_data['participants'].split(',') if p.strip()]
                event_data['participants'] = participants
            
            # Send request
            response = requests.put(f'{self.base_url}/events/{event_id}', json=event_data, timeout=10)
            
            if response.status_code == 200:
                messagebox.showinfo("Success", "Event updated successfully!")
                self.update_status("✅ Event updated successfully")
                self.refresh_events()
            elif response.status_code == 404:
                messagebox.showerror("Error", "Event not found")
                self.update_status("❌ Event not found")
            else:
                error_data = response.json()
                messagebox.showerror("Error", f"Failed to update event: {error_data.get('error', 'Unknown error')}")
                self.update_status("❌ Failed to update event")
        
        except requests.exceptions.RequestException as e:
            messagebox.showerror("Connection Error", f"Cannot connect to server: {str(e)}")
            self.update_status("❌ Connection error")
        except Exception as e:
            messagebox.showerror("Error", f"Unexpected error: {str(e)}")
            self.update_status("❌ Unexpected error")
    
    def delete_event(self):
        """Delete an event."""
        event_id = self.update_id_entry.get().strip()
        if not event_id:
            messagebox.showerror("Error", "Please enter an Event ID")
            return
        
        # Confirm deletion
        if not messagebox.askyesno("Confirm Delete", f"Are you sure you want to delete event {event_id}?"):
            return
        
        try:
            response = requests.delete(f'{self.base_url}/events/{event_id}', timeout=10)
            
            if response.status_code == 200:
                messagebox.showinfo("Success", "Event deleted successfully!")
                self.update_status("✅ Event deleted successfully")
                self.clear_update_form()
                self.refresh_events()
            elif response.status_code == 404:
                messagebox.showerror("Error", "Event not found")
                self.update_status("❌ Event not found")
            else:
                error_data = response.json()
                messagebox.showerror("Error", f"Failed to delete event: {error_data.get('error', 'Unknown error')}")
                self.update_status("❌ Failed to delete event")
        
        except requests.exceptions.RequestException as e:
            messagebox.showerror("Connection Error", f"Cannot connect to server: {str(e)}")
            self.update_status("❌ Connection error")
        except Exception as e:
            messagebox.showerror("Error", f"Unexpected error: {str(e)}")
            self.update_status("❌ Unexpected error")
    
    def clear_create_form(self):
        """Clear the create event form."""
        for entry in self.create_entries.values():
            entry.delete(0, tk.END)
        self.importance_var.set('medium')
        self.recurrence_var.set('none')
    
    def clear_update_form(self):
        """Clear the update event form."""
        self.update_id_entry.delete(0, tk.END)
        for entry in self.update_entries.values():
            entry.delete(0, tk.END)
        self.update_importance_var.set('medium')
        self.update_recurrence_var.set('none')
    
    def update_status(self, message):
        """Update the status bar."""
        self.status_label.config(text=message)
        print(f"STATUS: {message}")

if __name__ == '__main__':
    app = RestEventClientGUI()
    app.mainloop()