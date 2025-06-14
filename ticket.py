import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from datetime import datetime, timedelta
import sqlite3
import os

class Ticket:
    def __init__(self, title, description, created_at, due):
        self.title = title
        self.description = description
        self.created_at = created_at
        self.due = due
        self.completed = False
        self.completed_time = None
        self.paused = False
        self.paused_at = None
        self.frozen_remaining = None

    def remaining_time(self):
        try:
            if self.paused and self.frozen_remaining is not None:
                return self.frozen_remaining
            if not isinstance(self.due, datetime):
                return timedelta(0)
            return self.due - datetime.now()
        except Exception as e:
            print(f"Error calculating remaining time for {self.title}: {e}")
            return timedelta(0)

class FridgeItem:
    def __init__(self, name, added_at):
        self.name = name
        self.added_at = added_at
        self.paused = False
        self.paused_at = None
        self.frozen_age = None

    def age(self):
        try:
            if self.paused and self.frozen_age is not None:
                return self.frozen_age
            if not isinstance(self.added_at, datetime):
                return timedelta(0)
            return datetime.now() - self.added_at
        except Exception as e:
            print(f"Error calculating age for {self.name}: {e}")
            return timedelta(0)

class TicketApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Ticket System")
        
        # Modern color scheme that works well on both platforms
        self.bg_color = "#ffffff"  # Pure white background
        self.frame_bg = "#f8f9fa"  # Light gray for frames
        self.border_color = "#e9ecef"  # Subtle border
        self.text_color = "#212529"  # Dark gray text
        self.accent_color = "#0d6efd"  # Modern blue
        self.success_color = "#198754"  # Modern green
        self.danger_color = "#dc3545"  # Modern red
        self.secondary_color = "#6c757d"  # Secondary gray
        self.hover_color = "#0b5ed7"  # Darker blue for hover
        
        # Button colors for Mac
        self.mac_button_colors = {
            'success': {
                'normal': '#34c759',  # Mac green
                'hover': '#30b753',
                'active': '#2ea043'
            },
            'danger': {
                'normal': '#ff3b30',  # Mac red
                'hover': '#ff2d55',
                'active': '#ff1a1a'
            },
            'accent': {
                'normal': '#007aff',  # Mac blue
                'hover': '#0066cc',
                'active': '#0055b3'
            }
        }
        
        # Detect platform for appropriate fonts and styling
        import platform
        self.is_mac = platform.system() == "Darwin"
        if self.is_mac:
            self.font_family = "SF Pro Text"
            self.button_style = {
                'font': (self.font_family, 11, "bold"),
                'fg': "white",
                'width': 2,
                'relief': "flat",
                'borderwidth': 0,
                'padx': 8,
                'pady': 4,
                'cursor': "pointinghand"  # Mac-style cursor
            }
        else:
            self.font_family = "Segoe UI"
            self.button_style = {
                'font': (self.font_family, 11, "bold"),
                'fg': "white",
                'width': 2,
                'relief': "flat",
                'borderwidth': 0,
                'padx': 6,
                'pady': 3
            }
        
        self.root.configure(bg=self.bg_color)
        
        # Initialize lists first
        self.tickets = []
        self.description_history = []
        self.fridge_items = []
        self.ticket_labels = []
        self.fridge_labels = []
        
        # Configure styles for modern look
        style = ttk.Style()
        style.configure("TButton", 
                       padding=(10, 6),
                       font=(self.font_family, 11))
        style.configure("TCombobox", 
                       padding=(8, 6),
                       font=(self.font_family, 11))
        style.configure("TLabel", 
                       font=(self.font_family, 11),
                       background=self.bg_color)
        style.configure("TLabelframe", 
                       font=(self.font_family, 12, "bold"),
                       background=self.bg_color)
        style.configure("TLabelframe.Label", 
                       font=(self.font_family, 12, "bold"),
                       background=self.bg_color)
        
        # Database management frame with modern styling
        self.db_frame = tk.Frame(root, bg=self.bg_color, padx=12, pady=10)
        self.db_frame.pack(fill=tk.X)
        
        # Database selector with modern styling
        self.db_var = tk.StringVar()
        self.db_combo = ttk.Combobox(self.db_frame, textvariable=self.db_var, width=30)
        self.db_combo.pack(side=tk.LEFT, padx=6)
        self.db_combo.bind('<<ComboboxSelected>>', self.switch_database)
        
        # Database buttons with modern styling
        ttk.Button(self.db_frame, text="New DB", command=self.create_new_database).pack(side=tk.LEFT, padx=4)
        ttk.Button(self.db_frame, text="Open DB", command=self.open_database).pack(side=tk.LEFT, padx=4)
        
        # Create input frame with modern spacing
        self.input_frame = tk.Frame(root, bg=self.bg_color, padx=12, pady=12)
        self.input_frame.pack(fill=tk.X)

        # Input fields with modern styling
        self.desc_var = tk.StringVar()
        self.desc_combo = ttk.Combobox(self.input_frame, textvariable=self.desc_var, width=30)
        self.desc_combo.pack(side=tk.LEFT, padx=6)

        # Time input fields with modern styling
        time_frame = tk.Frame(self.input_frame, bg=self.bg_color)
        time_frame.pack(side=tk.LEFT, padx=12)
        
        # Style for time input fields
        time_entry_style = {
            'font': (self.font_family, 11),
            'width': 3,
            'relief': 'solid',
            'borderwidth': 1
        }
        time_label_style = {
            'font': (self.font_family, 11),
            'bg': self.bg_color,
            'fg': self.text_color
        }
        
        self.day_var = tk.StringVar(value="0")
        tk.Entry(time_frame, textvariable=self.day_var, **time_entry_style).pack(side=tk.LEFT)
        tk.Label(time_frame, text="d", **time_label_style).pack(side=tk.LEFT, padx=(0, 6))

        self.hour_var = tk.StringVar(value="0")
        tk.Entry(time_frame, textvariable=self.hour_var, **time_entry_style).pack(side=tk.LEFT)
        tk.Label(time_frame, text="h", **time_label_style).pack(side=tk.LEFT, padx=(0, 6))

        self.min_var = tk.StringVar(value="5")
        tk.Entry(time_frame, textvariable=self.min_var, **time_entry_style).pack(side=tk.LEFT)
        tk.Label(time_frame, text="m", **time_label_style).pack(side=tk.LEFT, padx=(0, 6))

        self.sec_var = tk.StringVar(value="0")
        tk.Entry(time_frame, textvariable=self.sec_var, **time_entry_style).pack(side=tk.LEFT)
        tk.Label(time_frame, text="s", **time_label_style).pack(side=tk.LEFT, padx=(0, 6))

        # Add Ticket button with modern styling
        ttk.Button(self.input_frame, text="Add Ticket", command=self.add_ticket).pack(side=tk.LEFT, padx=12)

        # Fridge input with modern styling
        self.fridge_var = tk.StringVar()
        tk.Entry(self.input_frame, textvariable=self.fridge_var, width=20, 
                font=(self.font_family, 11), relief='solid', borderwidth=1).pack(side=tk.LEFT, padx=12)
        ttk.Button(self.input_frame, text="Add Item", command=self.add_fridge_item).pack(side=tk.LEFT, padx=4)

        # Ticket frame with modern styling
        self.ticket_frame = tk.LabelFrame(root, text="Tickets", 
                                        font=(self.font_family, 12, "bold"),
                                        bg=self.bg_color,
                                        padx=16, pady=16)
        self.ticket_frame.pack(padx=16, pady=12, fill=tk.BOTH, expand=True)

        # Fridge frame with modern styling
        self.fridge_frame = tk.LabelFrame(root, text="Fridge Items",
                                        font=(self.font_family, 12, "bold"),
                                        bg=self.bg_color,
                                        padx=16, pady=16)
        self.fridge_frame.pack(padx=16, pady=12, fill=tk.BOTH, expand=True)
        
        # Initialize database
        self.current_db = None
        self.update_database_list()
        self.update_ui()

    def clear_ui(self):
        """Clear all UI elements"""
        try:
            # Clear ticket UI
            if hasattr(self, 'ticket_labels'):
                for _, _, frame, _, _ in self.ticket_labels:
                    frame.destroy()
                self.ticket_labels = []
            
            # Clear fridge UI
            if hasattr(self, 'fridge_labels'):
                for _, _, frame, _ in self.fridge_labels:
                    frame.destroy()
                self.fridge_labels = []
        except Exception as e:
            print(f"Error clearing UI: {e}")

    def update_database_list(self):
        """Update the list of available database files"""
        try:
            # Get all .db files in the current directory
            db_files = [f for f in os.listdir('.') if f.endswith('.db')]
            if not db_files:
                # Create default database if none exist
                self.create_default_database()
                db_files = ["ticket_data.db"]
            
            self.db_combo['values'] = db_files
            # Select the first database if none is selected
            if not self.db_var.get() or self.db_var.get() not in db_files:
                self.db_var.set(db_files[0])
                self.load_database(db_files[0])
        except Exception as e:
            print(f"Error updating database list: {e}")
            # Create and use default database if there's an error
            self.create_default_database()
            self.db_var.set("ticket_data.db")
            self.load_database("ticket_data.db")

    def create_default_database(self):
        """Create the default database if it doesn't exist"""
        try:
            if not os.path.exists("ticket_data.db"):
                conn = sqlite3.connect("ticket_data.db")
                cursor = conn.cursor()
                self.setup_database_schema(cursor)
                conn.commit()
                conn.close()
        except Exception as e:
            print(f"Error creating default database: {e}")

    def create_new_database(self):
        """Create a new database file"""
        try:
            # Ask for new database name
            new_db = filedialog.asksaveasfilename(
                defaultextension=".db",
                filetypes=[("Database files", "*.db")],
                title="Create New Database"
            )
            if not new_db:
                return
                
            # Create new database file
            if os.path.exists(new_db):
                if not messagebox.askyesno("Confirm Overwrite", 
                    "Database file already exists. Overwrite?"):
                    return
                os.remove(new_db)
            
            # Initialize new database
            conn = sqlite3.connect(new_db)
            cursor = conn.cursor()
            self.setup_database_schema(cursor)
            conn.commit()
            conn.close()
            
            # Update database list and switch to new database
            self.update_database_list()
            self.current_db = os.path.basename(new_db)
            self.db_var.set(self.current_db)
            self.load_database(self.current_db)
            
        except Exception as e:
            messagebox.showerror("Error", f"Error creating database: {e}")

    def open_database(self):
        """Open an existing database file"""
        try:
            db_file = filedialog.askopenfilename(
                filetypes=[("Database files", "*.db")],
                title="Open Database"
            )
            if not db_file:
                return
                
            # Switch to selected database
            self.current_db = os.path.basename(db_file)
            self.db_var.set(self.current_db)
            self.load_database(self.current_db)
            
        except Exception as e:
            messagebox.showerror("Error", f"Error opening database: {e}")

    def switch_database(self, event=None):
        """Switch to a different database"""
        try:
            new_db = self.db_var.get()
            if new_db and new_db != self.current_db:
                self.load_database(new_db)
        except Exception as e:
            messagebox.showerror("Error", f"Error switching database: {e}")

    def load_database(self, db_name):
        """Load a database and update the UI"""
        try:
            if not db_name:
                return
                
            # Close existing connection if any
            if hasattr(self, 'conn'):
                self.conn.close()
            
            # Connect to new database
            self.conn = sqlite3.connect(db_name)
            self.cursor = self.conn.cursor()
            
            # Setup database schema if needed
            self.setup_database()
            
            # Clear existing UI
            self.clear_ui()
            
            # Load data
            self.tickets = self.load_tickets()
            self.description_history = list({t.description for t in self.tickets})
            self.fridge_items = self.load_fridge_items()
            
            # Update description combobox
            self.desc_combo['values'] = self.description_history
            
            # Update UI
            self.build_ticket_ui()
            self.build_fridge_ui()
            
            # Update window title and current database
            self.root.title(f"Ticket System - {db_name}")
            self.current_db = db_name
            
        except Exception as e:
            messagebox.showerror("Error", f"Error loading database: {e}")
            # Ensure we have a valid connection
            if not hasattr(self, 'conn') or not self.conn:
                self.create_default_database()
                self.conn = sqlite3.connect("ticket_data.db")
                self.cursor = self.conn.cursor()
                self.setup_database()
                self.current_db = "ticket_data.db"
                self.db_var.set("ticket_data.db")

    def setup_database_schema(self, cursor):
        """Setup the database schema for a new database"""
        cursor.execute('''CREATE TABLE IF NOT EXISTS tickets 
            (title TEXT, description TEXT, created_at TEXT, due TEXT,
             completed INTEGER DEFAULT 0, completed_time TEXT,
             paused INTEGER DEFAULT 0, paused_at TEXT, frozen_remaining TEXT)''')
        cursor.execute('''CREATE TABLE IF NOT EXISTS fridge_items 
            (name TEXT, added_at TEXT,
             paused INTEGER DEFAULT 0, paused_at TEXT, frozen_age TEXT)''')

    def __del__(self):
        """Ensure database connection is closed properly"""
        if hasattr(self, 'conn'):
            self.conn.close()

    def setup_database(self):
        # Create tables if they don't exist
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS tickets 
            (title TEXT, description TEXT, created_at TEXT, due TEXT)''')
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS fridge_items 
            (name TEXT, added_at TEXT)''')
        
        # Check and add new columns one by one
        try:
            # Check for completed column
            self.cursor.execute("SELECT completed FROM tickets LIMIT 1")
        except sqlite3.OperationalError:
            # Add completed columns
            self.cursor.execute('ALTER TABLE tickets ADD COLUMN completed INTEGER DEFAULT 0')
            self.cursor.execute('ALTER TABLE tickets ADD COLUMN completed_time TEXT')
        
        try:
            # Check for paused column in tickets
            self.cursor.execute("SELECT paused FROM tickets LIMIT 1")
        except sqlite3.OperationalError:
            # Add pause columns to tickets table
            self.cursor.execute('ALTER TABLE tickets ADD COLUMN paused INTEGER DEFAULT 0')
            self.cursor.execute('ALTER TABLE tickets ADD COLUMN paused_at TEXT')
            self.cursor.execute('ALTER TABLE tickets ADD COLUMN frozen_remaining TEXT')
        
        try:
            # Check for paused column in fridge_items
            self.cursor.execute("SELECT paused FROM fridge_items LIMIT 1")
        except sqlite3.OperationalError:
            # Add pause columns to fridge_items table
            self.cursor.execute('ALTER TABLE fridge_items ADD COLUMN paused INTEGER DEFAULT 0')
            self.cursor.execute('ALTER TABLE fridge_items ADD COLUMN paused_at TEXT')
            self.cursor.execute('ALTER TABLE fridge_items ADD COLUMN frozen_age TEXT')
        
        self.conn.commit()

    def load_tickets(self):
        try:
            # Try to load with all columns
            self.cursor.execute("""
                SELECT title, description, created_at, due, 
                       COALESCE(paused, 0) as paused, 
                       paused_at, 
                       frozen_remaining,
                       COALESCE(completed, 0) as completed, 
                       completed_time 
                FROM tickets
                ORDER BY created_at DESC""")
        except sqlite3.OperationalError:
            # If new columns don't exist yet, load with basic columns
            self.cursor.execute("SELECT title, description, created_at, due FROM tickets ORDER BY created_at DESC")
            rows = self.cursor.fetchall()
            tickets = []
            for row in rows:
                try:
                    title, desc, created, due = row
                    # Handle invalid datetime strings
                    try:
                        created_dt = datetime.fromisoformat(created) if created and created != '0' else datetime.now()
                    except ValueError:
                        created_dt = datetime.now()
                    try:
                        due_dt = datetime.fromisoformat(due) if due and due != '0' else (created_dt + timedelta(minutes=5))
                    except ValueError:
                        due_dt = created_dt + timedelta(minutes=5)
                    
                    ticket = Ticket(title, desc, created_dt, due_dt)
                    tickets.append(ticket)
                except Exception as e:
                    print(f"Error loading ticket {row}: {e}")
                    continue
            return tickets
        
        rows = self.cursor.fetchall()
        tickets = []
        for row in rows:
            try:
                if len(row) == 9:  # New format with all columns
                    title, desc, created, due, paused, paused_at, frozen_remaining, completed, completed_time = row
                    
                    # Handle invalid datetime strings
                    try:
                        created_dt = datetime.fromisoformat(created) if created and created != '0' else datetime.now()
                    except ValueError:
                        created_dt = datetime.now()
                    try:
                        due_dt = datetime.fromisoformat(due) if due and due != '0' else (created_dt + timedelta(minutes=5))
                    except ValueError:
                        due_dt = created_dt + timedelta(minutes=5)
                    
                    ticket = Ticket(title, desc, created_dt, due_dt)
                    ticket.paused = bool(paused)
                    
                    if paused_at and paused_at != '0':
                        try:
                            ticket.paused_at = datetime.fromisoformat(paused_at)
                        except ValueError:
                            ticket.paused_at = None
                    
                    if frozen_remaining and frozen_remaining != '0':
                        try:
                            ticket.frozen_remaining = timedelta(seconds=float(frozen_remaining))
                        except ValueError:
                            ticket.frozen_remaining = None
                    
                    ticket.completed = bool(completed)
                    ticket.completed_time = completed_time if completed_time and completed_time != '0' else None
                else:  # Old format
                    title, desc, created, due = row
                    # Handle invalid datetime strings
                    try:
                        created_dt = datetime.fromisoformat(created) if created and created != '0' else datetime.now()
                    except ValueError:
                        created_dt = datetime.now()
                    try:
                        due_dt = datetime.fromisoformat(due) if due and due != '0' else (created_dt + timedelta(minutes=5))
                    except ValueError:
                        due_dt = created_dt + timedelta(minutes=5)
                    
                    ticket = Ticket(title, desc, created_dt, due_dt)
                tickets.append(ticket)
            except Exception as e:
                print(f"Error loading ticket {row}: {e}")
                continue
        return tickets

    def load_fridge_items(self):
        try:
            # Try to load with all columns
            self.cursor.execute("SELECT name, added_at, paused, paused_at, frozen_age FROM fridge_items")
        except sqlite3.OperationalError:
            # If new columns don't exist yet, load with basic columns
            self.cursor.execute("SELECT name, added_at FROM fridge_items")
            rows = self.cursor.fetchall()
            items = []
            for row in rows:
                try:
                    name, added_at = row
                    # Handle invalid datetime strings
                    try:
                        added_dt = datetime.fromisoformat(added_at) if added_at and added_at != '0' else datetime.now()
                    except ValueError:
                        added_dt = datetime.now()
                    item = FridgeItem(name, added_dt)
                    items.append(item)
                except Exception as e:
                    print(f"Error loading fridge item {row}: {e}")
                    continue
            return items
        
        rows = self.cursor.fetchall()
        items = []
        for row in rows:
            try:
                if len(row) == 5:  # New format with all columns
                    name, added_at, paused, paused_at, frozen_age = row
                    
                    # Handle invalid datetime strings
                    try:
                        added_dt = datetime.fromisoformat(added_at) if added_at and added_at != '0' else datetime.now()
                    except ValueError:
                        added_dt = datetime.now()
                    
                    item = FridgeItem(name, added_dt)
                    item.paused = bool(paused)
                    
                    if paused_at and paused_at != '0':
                        try:
                            item.paused_at = datetime.fromisoformat(paused_at)
                        except ValueError:
                            item.paused_at = None
                    
                    if frozen_age and frozen_age != '0':
                        try:
                            item.frozen_age = timedelta(seconds=float(frozen_age))
                        except ValueError:
                            item.frozen_age = None
                else:  # Old format
                    name, added_at = row
                    # Handle invalid datetime strings
                    try:
                        added_dt = datetime.fromisoformat(added_at) if added_at and added_at != '0' else datetime.now()
                    except ValueError:
                        added_dt = datetime.now()
                    item = FridgeItem(name, added_dt)
                items.append(item)
            except Exception as e:
                print(f"Error loading fridge item {row}: {e}")
                continue
        return items

    def add_ticket(self):
        try:
            desc = self.desc_var.get().strip() or "No Description"
            if desc not in self.description_history:
                self.description_history.append(desc)
                self.desc_combo['values'] = self.description_history  # Update combobox values

            try:
                days = int(self.day_var.get())
                hours = int(self.hour_var.get())
                minutes = int(self.min_var.get())
                seconds = int(self.sec_var.get())
            except ValueError:
                days, hours, minutes, seconds = 0, 0, 5, 0

            created_at = datetime.now()
            due = created_at + timedelta(days=days, hours=hours, minutes=minutes, seconds=seconds)
            title = f"Ticket #{len(self.tickets)+1}"

            # Create ticket object
            ticket = Ticket(title, desc, created_at, due)
            
            # Save to database first
            try:
                self.cursor.execute("INSERT INTO tickets VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)", 
                    (title, desc, created_at.isoformat(), due.isoformat(), 
                     0, None, None, 0, None))  # Initial state: not paused, not completed
                self.conn.commit()
            except sqlite3.Error as e:
                print(f"Error saving ticket to database: {e}")
                self.conn.rollback()
                return

            # Only add to memory if database save was successful
            self.tickets.append(ticket)
            
            # Clear existing UI
            self.clear_ui()
            
            # Rebuild UI with new ticket
            self.build_ticket_ui()
            self.build_fridge_ui()
            
            # Force an immediate UI update
            self.update_ui()

            # Clear input fields
            self.desc_var.set("")
            self.day_var.set("0")
            self.hour_var.set("0")
            self.min_var.set("5")
            self.sec_var.set("0")

        except Exception as e:
            print(f"Error adding ticket: {e}")
            self.conn.rollback()

    def add_fridge_item(self):
        try:
            name = self.fridge_var.get().strip()
            if not name:
                return

            added_at = datetime.now()
            
            # Save to database first
            try:
                self.cursor.execute("INSERT INTO fridge_items VALUES (?, ?, ?, ?, ?)", 
                    (name, added_at.isoformat(), 0, None, None))  # Initial pause state
                self.conn.commit()
            except sqlite3.Error as e:
                print(f"Error saving fridge item to database: {e}")
                self.conn.rollback()
                return

            # Only add to memory if database save was successful
            item = FridgeItem(name, added_at)
            self.fridge_items.append(item)
            self.build_fridge_ui()  # Rebuild UI to include new item with proper styling

            # Clear input field
            self.fridge_var.set("")

        except Exception as e:
            print(f"Error adding fridge item: {e}")
            self.conn.rollback()

    def create_mac_button(self, parent, text, color_type, command):
        """Create a Mac-style button with proper effects"""
        colors = self.mac_button_colors[color_type]
        btn = tk.Button(parent, text=text, command=command, **self.button_style)
        
        def on_enter(e):
            btn.configure(bg=colors['hover'])
            if self.is_mac:
                btn.configure(relief="flat", borderwidth=0)
        
        def on_leave(e):
            btn.configure(bg=colors['normal'])
            if self.is_mac:
                btn.configure(relief="flat", borderwidth=0)
        
        def on_press(e):
            btn.configure(bg=colors['active'])
            if self.is_mac:
                btn.configure(relief="flat", borderwidth=0)
        
        def on_release(e):
            btn.configure(bg=colors['hover'])
            if self.is_mac:
                btn.configure(relief="flat", borderwidth=0)
        
        btn.configure(bg=colors['normal'])
        btn.bind('<Enter>', on_enter)
        btn.bind('<Leave>', on_leave)
        btn.bind('<ButtonPress-1>', on_press)
        btn.bind('<ButtonRelease-1>', on_release)
        
        return btn

    def build_ticket_ui(self):
        # Clear existing UI
        for _, _, frame, _, _ in self.ticket_labels:
            frame.destroy()
        self.ticket_labels = []
        
        # Build UI for all tickets
        for i, ticket in enumerate(self.tickets):
            # Create a frame with modern styling
            frame = tk.Frame(self.ticket_frame, 
                           bg=self.bg_color,
                           highlightbackground=self.border_color,
                           highlightthickness=1,
                           padx=14, pady=10)
            frame.pack(fill=tk.X, pady=5, padx=8)
            
            # Create a container for the label
            label_container = tk.Frame(frame, bg=self.bg_color)
            label_container.pack(side=tk.LEFT, expand=True, fill=tk.X)
            
            lbl = tk.Label(label_container, 
                         anchor='w',
                         bg=self.bg_color,
                         font=(self.font_family, 11),
                         fg=self.text_color)
            lbl.pack(side=tk.LEFT, expand=True, fill=tk.X)
            
            # Style the buttons with modern appearance
            button_frame = tk.Frame(frame, bg=self.bg_color)
            button_frame.pack(side=tk.RIGHT, padx=(10, 0))
            
            # Create Mac-style buttons
            complete_btn = self.create_mac_button(
                button_frame, "✔", 
                'success' if not ticket.completed else 'accent',
                lambda i=i: self.complete_ticket(i)
            )
            complete_btn.pack(side=tk.LEFT, padx=4)
            
            delete_btn = self.create_mac_button(
                button_frame, "✕",
                'danger',
                lambda i=i: self.delete_ticket(i)
            )
            delete_btn.pack(side=tk.LEFT, padx=4)
            
            pause_text = "⏸" if not ticket.paused else "▶"
            pause_btn = self.create_mac_button(
                button_frame, pause_text,
                'accent',
                lambda i=i: self.toggle_ticket_pause(i)
            )
            pause_btn.pack(side=tk.LEFT, padx=4)
            
            self.ticket_labels.append((lbl, ticket, frame, complete_btn, pause_btn))

    def toggle_ticket_pause(self, index):
        try:
            if not self.tickets or index >= len(self.tickets):
                return  # Prevent toggle if no tickets or invalid index
                
            ticket = self.tickets[index]
            now = datetime.now()
            if not ticket.paused:
                # Pausing
                ticket.paused_at = now
                ticket.frozen_remaining = ticket.due - now
            else:
                # Unpausing
                if ticket.paused_at:
                    pause_duration = now - ticket.paused_at
                    ticket.due += pause_duration
                    ticket.paused_at = None
                    ticket.frozen_remaining = None
            ticket.paused = not ticket.paused

            # Update database
            self.cursor.execute("UPDATE tickets SET paused = ?, paused_at = ?, frozen_remaining = ? WHERE title = ?",
                (int(ticket.paused), 
                 ticket.paused_at.isoformat() if ticket.paused_at else None,
                 str(ticket.frozen_remaining.total_seconds()) if ticket.frozen_remaining else None,
                 ticket.title))
            self.conn.commit()

            # Update only the pause button state with proper Mac colors
            if index < len(self.ticket_labels):
                _, _, frame, _, pause_btn = self.ticket_labels[index]
                if ticket.paused:
                    pause_btn.configure(text="▶", bg=self.mac_button_colors['accent']['normal'])
                else:
                    pause_btn.configure(text="⏸", bg=self.mac_button_colors['accent']['normal'])

        except Exception as e:
            print(f"Error toggling ticket pause: {e}")
            self.conn.rollback()

    def toggle_fridge_pause(self, index):
        try:
            if not self.fridge_items or index >= len(self.fridge_items):
                return  # Prevent toggle if no items or invalid index
                
            item = self.fridge_items[index]
            now = datetime.now()
            if not item.paused:
                # Pausing
                item.paused_at = now
                item.frozen_age = now - item.added_at
            else:
                # Unpausing
                if item.paused_at:
                    pause_duration = now - item.paused_at
                    item.added_at -= pause_duration
                    item.paused_at = None
                    item.frozen_age = None
            item.paused = not item.paused

            # Update database
            self.cursor.execute("UPDATE fridge_items SET paused = ?, paused_at = ?, frozen_age = ? WHERE name = ? AND added_at = ?",
                (int(item.paused),
                 item.paused_at.isoformat() if item.paused_at else None,
                 str(item.frozen_age.total_seconds()) if item.frozen_age else None,
                 item.name,
                 item.added_at.isoformat()))
            self.conn.commit()

            # Update only the pause button state with proper Mac colors
            if index < len(self.fridge_labels):
                _, _, _, pause_btn = self.fridge_labels[index]
                if item.paused:
                    pause_btn.configure(text="▶", bg=self.mac_button_colors['accent']['normal'])
                else:
                    pause_btn.configure(text="⏸", bg=self.mac_button_colors['accent']['normal'])

        except Exception as e:
            print(f"Error toggling fridge item pause: {e}")
            self.conn.rollback()

    def complete_ticket(self, index):
        try:
            if not self.tickets or index >= len(self.tickets):
                return  # Prevent completion if no tickets or invalid index
                
            ticket = self.tickets[index]
            if not ticket.completed:
                ticket.completed = True
                ticket.completed_time = datetime.now().strftime('%H:%M:%S')
                ticket.title += f" [Done @ {ticket.completed_time}]"
                
                # Update database
                self.cursor.execute("UPDATE tickets SET completed = ?, completed_time = ? WHERE title = ?",
                    (1, ticket.completed_time, ticket.title.split(" [Done @")[0]))  # Use original title for update
                self.conn.commit()
                
                # Rebuild UI to ensure proper state display
                self.build_ticket_ui()
                
        except Exception as e:
            print(f"Error completing ticket: {e}")
            self.conn.rollback()

    def delete_ticket(self, index):
        try:
            if not self.tickets or index >= len(self.tickets):
                return  # Prevent deletion if no tickets or invalid index
                
            ticket = self.tickets[index]
            # Delete from database first
            self.cursor.execute("DELETE FROM tickets WHERE title = ?", (ticket.title,))
            self.conn.commit()
            
            # Only remove from memory if database delete was successful
            self.tickets.pop(index)
            # Remove the frame and its widgets
            if index < len(self.ticket_labels):
                self.ticket_labels[index][2].destroy()
                self.ticket_labels.pop(index)
            # Rebuild UI to ensure proper indices
            self.build_ticket_ui()
            
        except Exception as e:
            print(f"Error deleting ticket: {e}")
            self.conn.rollback()

    def delete_fridge_item(self, index):
        try:
            if not self.fridge_items or index >= len(self.fridge_items):
                return  # Prevent deletion if no items or invalid index
                
            item = self.fridge_items[index]
            # Delete from database first
            self.cursor.execute("DELETE FROM fridge_items WHERE name = ? AND added_at = ?", 
                (item.name, item.added_at.isoformat()))
            self.conn.commit()
            
            # Only remove from memory if database delete was successful
            self.fridge_items.pop(index)
            # Remove the frame and its widgets
            if index < len(self.fridge_labels):
                self.fridge_labels[index][2].destroy()
                self.fridge_labels.pop(index)
            # Rebuild UI to ensure proper indices
            self.build_fridge_ui()
            
        except Exception as e:
            print(f"Error deleting fridge item: {e}")
            self.conn.rollback()

    def build_fridge_ui(self):
        # Clear existing UI
        for _, _, frame, _ in self.fridge_labels:
            frame.destroy()
        self.fridge_labels = []
        
        # Build UI for all items
        for i, item in enumerate(self.fridge_items):
            # Create a frame with modern styling
            frame = tk.Frame(self.fridge_frame,
                           bg=self.bg_color,
                           highlightbackground=self.border_color,
                           highlightthickness=1,
                           padx=14, pady=10)
            frame.pack(fill=tk.X, pady=5, padx=8)
            
            # Create a container for the label
            label_container = tk.Frame(frame, bg=self.bg_color)
            label_container.pack(side=tk.LEFT, expand=True, fill=tk.X)
            
            lbl = tk.Label(label_container,
                         anchor='w',
                         bg=self.bg_color,
                         font=(self.font_family, 11),
                         fg=self.text_color)
            lbl.pack(side=tk.LEFT, expand=True, fill=tk.X)
            
            # Style the buttons with modern appearance
            button_frame = tk.Frame(frame, bg=self.bg_color)
            button_frame.pack(side=tk.RIGHT, padx=(10, 0))
            
            # Create Mac-style buttons
            delete_btn = self.create_mac_button(
                button_frame, "✕",
                'danger',
                lambda i=i: self.delete_fridge_item(i)
            )
            delete_btn.pack(side=tk.LEFT, padx=4)
            
            pause_text = "⏸" if not item.paused else "▶"
            pause_btn = self.create_mac_button(
                button_frame, pause_text,
                'accent',
                lambda i=i: self.toggle_fridge_pause(i)
            )
            pause_btn.pack(side=tk.LEFT, padx=4)
            
            self.fridge_labels.append((lbl, item, frame, pause_btn))

    def update_ui(self):
        """Update the UI with current ticket and fridge item states"""
        try:
            now = datetime.now()
            for lbl, ticket, frame, complete_btn, pause_btn in self.ticket_labels:
                try:
                    rem = ticket.remaining_time()
                    if not isinstance(rem, timedelta):
                        time_text = "Invalid time"
                    else:
                        total_seconds = int(rem.total_seconds())
                        sign = "-" if total_seconds < 0 else ""
                        total_seconds = abs(total_seconds)
                        days = total_seconds // 86400
                        hours = (total_seconds % 86400) // 3600
                        minutes = (total_seconds % 3600) // 60
                        seconds = total_seconds % 60
                        
                        # Format time with proper handling of zero values
                        if days > 0:
                            time_text = f"{sign}{days}d {hours:02d}:{minutes:02d}:{seconds:02d}"
                        else:
                            time_text = f"{sign}{hours:02d}:{minutes:02d}:{seconds:02d}"
                    
                    # Create single-line text format
                    status = "[PAUSED] " if ticket.paused else ""
                    completion = f"[Done @ {ticket.completed_time}]" if ticket.completed else ""
                    
                    text = f"{ticket.title} | {status}{time_text} | {ticket.description} {completion}"
                    
                    # Update label with new text
                    lbl.config(text=text)
                    
                    # Update button colors based on state
                    if ticket.completed:
                        complete_btn.config(bg="#81C784")  # Lighter green for completed
                    else:
                        complete_btn.config(bg="#4CAF50")  # Normal green for incomplete
                        
                    if ticket.paused:
                        pause_btn.config(text="▶", bg="#64B5F6")  # Lighter blue for paused
                    else:
                        pause_btn.config(text="⏸", bg="#2196F3")  # Normal blue for unpaused
                except Exception as e:
                    print(f"Error updating ticket {ticket.title}: {e}")
                    continue

            for lbl, item, frame, pause_btn in self.fridge_labels:
                try:
                    age = item.age()
                    if not isinstance(age, timedelta):
                        age_text = "Invalid time"
                    else:
                        total_seconds = int(age.total_seconds())
                        days = total_seconds // 86400
                        hours = (total_seconds % 86400) // 3600
                        minutes = (total_seconds % 3600) // 60
                        seconds = total_seconds % 60
                        
                        # Format time with proper handling of zero values
                        if days > 0:
                            age_text = f"{days}d {hours:02d}:{minutes:02d}:{seconds:02d}"
                        else:
                            age_text = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
                    
                    # Create single-line text format
                    status = "[PAUSED] " if item.paused else ""
                    added_time = item.added_at.strftime('%Y-%m-%d %H:%M:%S')
                    
                    text = f"{item.name} | {status}{age_text} | Added: {added_time}"
                    
                    # Update label with new text
                    lbl.config(text=text)
                    
                    # Update pause button appearance
                    if item.paused:
                        pause_btn.config(text="▶", bg="#64B5F6")  # Lighter blue for paused
                    else:
                        pause_btn.config(text="⏸", bg="#2196F3")  # Normal blue for unpaused
                except Exception as e:
                    print(f"Error updating fridge item {item.name}: {e}")
                    continue

            # Schedule next update
            self.root.after(1000, self.update_ui)
            
        except Exception as e:
            print(f"Error updating UI: {e}")
            # Try to recover by scheduling next update
            self.root.after(1000, self.update_ui)



if __name__ == '__main__':
    root = tk.Tk()
    app = TicketApp(root)
    root.mainloop()