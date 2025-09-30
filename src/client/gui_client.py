import tkinter as tk
from tkinter import ttk, messagebox
from zeep import Client
from zeep.exceptions import Fault
from datetime import date, time

# --- Configuration ---
SERVICE_URL = 'http://localhost:8000/soap?wsdl'
# ---

class EventServiceClientGUI(tk.Tk):
    """GUI Client for the Event Scheduling SOAP Service."""
    
    def __init__(self):
        super().__init__()
        self.title("SOAP Event Scheduling Client (CRUD Demo)")
        self.geometry("800x600")
        
        # Initialize Zeep Client
        try:
            self.client = Client(SERVICE_URL)
            self.event_factory = self.client.get_type('ns0:EventType')
            self.status_message = "Client Ready."
        except Exception as e:
            self.client = None
            self.status_message = f"ERROR: Failed to connect to service. Ensure server is running. {e}"
            messagebox.showerror("Connection Error", self.status_message)
            
        self.create_widgets()
        self.update_status(self.status_message)

    def create_widgets(self):
        """Sets up the main GUI structure (Tabs and Status Bar)."""
        
        # --- Status Bar ---
        self.status_label = tk.Label(self, text="", bd=1, relief=tk.SUNKEN, anchor=tk.W)
        self.status_label.pack(side=tk.BOTTOM, fill=tk.X)

        # --- Tab Control ---
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(pady=10, padx=10, expand=True, fill="both")

        # Create tabs
        self.create_tab = ttk.Frame(self.notebook)
        self.read_tab = ttk.Frame(self.notebook)
        self.delete_tab = ttk.Frame(self.notebook)
        
        self.notebook.add(self.create_tab, text='1. Add/Update Event (C/U)')
        self.notebook.add(self.read_tab, text='2. View Events (R)')
        self.notebook.add(self.delete_tab, text='3. Delete Event (D)')

        # Populate tabs
        self._setup_create_update_tab()
        self._setup_read_tab()
        self._setup_delete_tab()

    def update_status(self, message):
        """Updates the status bar message."""
        self.status_label.config(text=message)
        print(f"STATUS: {message}")

    # --- TAB 1: CREATE/UPDATE ---
    def _setup_create_update_tab(self):
        """Sets up widgets for the AddEvent and UpdateEvent operations."""
        frame = ttk.Frame(self.create_tab, padding="10")
        frame.pack(expand=True, fill="both")
        
        labels = ['ID (for Update)', 'Title *', 'Agenda', 'Date (YYYY-MM-DD) *', 'Time (HH:MM:SS) *', 
                  'Importance *', 'Location *', 'Coordinator *', 'Participants (comma-separated)', 'Recurrence *']
        self.entries = {}
        row = 0
        
        # Default values for an easy test
        default_data = {
            'ID (for Update)': '',
            'Title *': 'Team Huddle',
            'Agenda': 'Quick 15-minute sync',
            'Date (YYYY-MM-DD) *': date.today().strftime('%Y-%m-%d'),
            'Time (HH:MM:SS) *': '10:00:00',
            'Importance *': 'medium',
            'Location *': 'Zoom',
            'Coordinator *': 'GUI Client',
            'Participants (comma-separated)': 'Alice, Bob, Charlie',
            'Recurrence *': 'daily'
        }
        
        # Create input fields
        for label_text in labels:
            label = ttk.Label(frame, text=label_text)
            label.grid(row=row, column=0, sticky='w', pady=5, padx=5)
            
            if label_text in ['Importance *', 'Recurrence *']:
                entry = ttk.Combobox(frame, width=50, state='readonly')
                if label_text == 'Importance *':
                    entry['values'] = ('low', 'medium', 'high')
                else:
                    entry['values'] = ('none', 'daily', 'weekly', 'monthly', 'annually')
                entry.set(default_data.get(label_text, entry['values'][0]))
            else:
                entry = ttk.Entry(frame, width=50)
                entry.insert(0, default_data.get(label_text, ''))

            entry.grid(row=row, column=1, pady=5, padx=5)
            self.entries[label_text] = entry
            row += 1
            
        # Operation Buttons
        ttk.Button(frame, text="1. Add Event (CREATE)", command=lambda: self._handle_crud_op('AddEvent')).grid(row=row, column=0, pady=10, padx=5, sticky='ew')
        ttk.Button(frame, text="2. Update Event (UPDATE)", command=lambda: self._handle_crud_op('UpdateEvent')).grid(row=row, column=1, pady=10, padx=5, sticky='ew')

    def _get_event_data_from_entries(self, require_id=False):
        """Collects and validates data from input fields."""
        data = {}
        try:
            # Mandatory fields
            data['title'] = self.entries['Title *'].get().strip()
            data['date'] = self.entries['Date (YYYY-MM-DD) *'].get().strip()
            data['time'] = self.entries['Time (HH:MM:SS) *'].get().strip()
            data['importance'] = self.entries['Importance *'].get().strip()
            data['location'] = self.entries['Location *'].get().strip()
            data['coordinator'] = self.entries['Coordinator *'].get().strip()
            data['recurrence'] = self.entries['Recurrence *'].get().strip()

            # Optional/Update fields
            data['id'] = self.entries['ID (for Update)'].get().strip() or '0'
            data['agenda'] = self.entries['Agenda'].get().strip() or ''
            
            participants_str = self.entries['Participants (comma-separated)'].get().strip()
            participants_list = [p.strip() for p in participants_str.split(',') if p.strip()]
            data['participants'] = {'participant': participants_list} if participants_list else None
            
            # Validation
            if not all([data['title'], data['date'], data['time'], data['importance'], data['location'], data['coordinator'], data['recurrence']]):
                raise ValueError("All fields marked with '*' must be filled.")
            if require_id and data['id'] == '0':
                 raise ValueError("ID is required for the Update operation.")

            # Basic format validation (Spyne/Zeep handle full XSD validation)
            date.fromisoformat(data['date'])
            time.fromisoformat(data['time'])
            
            return data
            
        except ValueError as e:
            messagebox.showerror("Input Error", str(e))
            return None
        except Exception as e:
            messagebox.showerror("Error", f"An unexpected error occurred during data collection: {e}")
            return None

    def _handle_crud_op(self, operation):
        """Generic handler for AddEvent and UpdateEvent."""
        if not self.client:
            messagebox.showerror("Error", "Client is not connected to the SOAP service.")
            return

        require_id = (operation == 'UpdateEvent')
        event_data = self._get_event_data_from_entries(require_id)
        if not event_data:
            return

        try:
            # Create the Zeep complex type object
            zeep_event = self.event_factory(**event_data)

            if operation == 'AddEvent':
                # Remove the placeholder ID
                event_data.pop('id') 
                
                new_id = self.client.service.AddEvent(zeep_event)
                self.update_status(f"✅ {operation} Successful. New ID: {new_id}")
                # Update the ID field in the GUI for immediate follow-up
                self.entries['ID (for Update)'].delete(0, tk.END)
                self.entries['ID (for Update)'].insert(0, new_id)

            elif operation == 'UpdateEvent':
                success = self.client.service.UpdateEvent(zeep_event)
                if success:
                    self.update_status(f"✅ {operation} Successful for ID: {event_data['id']}")
                else:
                    self.update_status(f"❌ {operation} Failed. Event ID not found: {event_data['id']}")

        except Fault as f:
            messagebox.showerror("SOAP Fault", f"Operation failed: {f.message}")
            self.update_status(f"❌ SOAP Fault during {operation}.")
        except Exception as e:
            messagebox.showerror("Communication Error", str(e))
            self.update_status(f"❌ Communication Error during {operation}.")
            
    # --- TAB 2: READ ---
    def _setup_read_tab(self):
        """Sets up widgets for GetEvent (single) and GetAllEvents (list)."""
        
        # --- Frame for Single Event (GetEvent) ---
        single_frame = ttk.LabelFrame(self.read_tab, text="Read Single Event (by ID)", padding="10")
        single_frame.pack(pady=10, padx=10, fill="x")
        
        ttk.Label(single_frame, text="Event ID:").pack(side=tk.LEFT, padx=5)
        self.read_id_entry = ttk.Entry(single_frame, width=40)
        self.read_id_entry.pack(side=tk.LEFT, padx=5, fill="x", expand=True)
        ttk.Button(single_frame, text="Get Event", command=self._read_single_event).pack(side=tk.LEFT, padx=5)

        # --- Frame for All Events / Output ---
        output_frame = ttk.LabelFrame(self.read_tab, text="Query Results", padding="10")
        output_frame.pack(pady=10, padx=10, expand=True, fill="both")
        
        # Text area for output
        self.output_text = tk.Text(output_frame, wrap=tk.WORD, height=15)
        self.output_text.pack(expand=True, fill="both", padx=5, pady=5)
        
        # Button to read all
        ttk.Button(self.read_tab, text="Read All Events (GetAllEvents)", command=self._read_all_events).pack(pady=10)

    def _read_single_event(self):
        """Handles the GetEvent operation."""
        event_id = self.read_id_entry.get().strip()
        self.output_text.delete(1.0, tk.END)
        
        if not self.client: return
        if not event_id:
            self.output_text.insert(tk.END, "Please enter an Event ID.")
            return

        try:
            event = self.client.service.GetEvent(event_id)
            if event:
                self.output_text.insert(tk.END, "--- EVENT DETAILS ---\n")
                # Iterate through event attributes for display
                for attr, value in event.__dict__.items():
                    # Format participants nicely
                    if attr == 'participants' and value is not None and hasattr(value, 'participant'):
                        participants = ', '.join(value.participant)
                        self.output_text.insert(tk.END, f"{attr.capitalize()}: {participants}\n")
                    elif attr != 'participants': # Avoid printing the object reference if not handled
                        self.output_text.insert(tk.END, f"{attr.capitalize()}: {value}\n")
                self.update_status(f"✅ GetEvent Successful for ID: {event_id}")
            else:
                self.output_text.insert(tk.END, f"Event with ID '{event_id}' not found.")
                self.update_status(f"❌ GetEvent Failed: Event ID not found.")

        except Fault as f:
            self.output_text.insert(tk.END, f"SOAP Fault: {f.message}")
            self.update_status("❌ SOAP Fault during GetEvent.")
        except Exception as e:
            self.output_text.insert(tk.END, f"Communication Error: {e}")
            self.update_status("❌ Communication Error during GetEvent.")


    def _read_all_events(self):
        """Handles the GetAllEvents operation."""
        self.output_text.delete(1.0, tk.END)
        if not self.client: return

        try:
            events = self.client.service.GetAllEvents()
            self.output_text.insert(tk.END, f"--- ALL EVENTS ({len(events)} Total) ---\n")
            
            for i, event in enumerate(events, 1):
                self.output_text.insert(tk.END, f"\n[{i}] ID: {event.id}\n")
                self.output_text.insert(tk.END, f"    Title: {event.title}\n")
                self.output_text.insert(tk.END, f"    Date/Time: {event.date} @ {event.time}\n")
                self.output_text.insert(tk.END, f"    Recurrence: {event.recurrence}\n")
                if event.participants and hasattr(event.participants, 'participant'):
                    participants = ', '.join(event.participants.participant)
                    self.output_text.insert(tk.END, f"    Participants: {participants}\n")
            
            self.update_status(f"✅ GetAllEvents Successful. Total: {len(events)}")

        except Fault as f:
            self.output_text.insert(tk.END, f"SOAP Fault: {f.message}")
            self.update_status("❌ SOAP Fault during GetAllEvents.")
        except Exception as e:
            self.output_text.insert(tk.END, f"Communication Error: {e}")
            self.update_status("❌ Communication Error during GetAllEvents.")

    # --- TAB 3: DELETE ---
    def _setup_delete_tab(self):
        """Sets up widgets for the DeleteEvent operation."""
        frame = ttk.Frame(self.delete_tab, padding="10")
        frame.pack(expand=True, fill="x", pady=50)

        ttk.Label(frame, text="Event ID to Delete:").pack(pady=5)
        self.delete_id_entry = ttk.Entry(frame, width=50)
        self.delete_id_entry.pack(pady=5, padx=10, fill='x')
        
        ttk.Button(frame, text="Delete Event (DELETE)", command=self._delete_event).pack(pady=20)
        
    def _delete_event(self):
        """Handles the DeleteEvent operation."""
        if not self.client: return

        event_id = self.delete_id_entry.get().strip()
        if not event_id:
            messagebox.showwarning("Input Required", "Please enter the ID of the event to delete.")
            return

        # Confirmation dialog
        if not messagebox.askyesno("Confirm Delete", f"Are you sure you want to delete event ID: {event_id}?"):
            return

        try:
            success = self.client.service.DeleteEvent(event_id)
            if success:
                messagebox.showinfo("Success", f"Event ID {event_id} deleted successfully.")
                self.update_status(f"✅ DeleteEvent Successful for ID: {event_id}")
                self.delete_id_entry.delete(0, tk.END)
            else:
                messagebox.showerror("Failure", f"Event ID {event_id} not found or deletion failed.")
                self.update_status(f"❌ DeleteEvent Failed: ID not found.")
                
        except Fault as f:
            messagebox.showerror("SOAP Fault", f"Operation failed: {f.message}")
            self.update_status("❌ SOAP Fault during DeleteEvent.")
        except Exception as e:
            messagebox.showerror("Communication Error", str(e))
            self.update_status("❌ Communication Error during DeleteEvent.")


if __name__ == '__main__':
    # Add a mandatory check before running the GUI
    try:
        # We need to explicitly handle date/time objects for default data
        _ = Client(SERVICE_URL)
        app = EventServiceClientGUI()
        app.mainloop()
    except Exception as e:
        print("\n" + "="*50)
        print("!!! ERROR STARTING GUI CLIENT !!!")
        print("Please ensure the SOAP Server (run_server.py) is running on http://localhost:8000/soap")
        print(f"Original Error: {e}")
        print("="*50)