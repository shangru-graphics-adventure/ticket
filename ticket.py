import tkinter as tk
from tkinter import ttk
from datetime import datetime, timedelta
import sqlite3

class Ticket:
    def __init__(self, title, description, created_at, due):
        self.title = title
        self.description = description
        self.created_at = created_at
        self.due = due
        self.completed = False
        self.completed_time = None

    def remaining_time(self):
        return self.due - datetime.now()

class FridgeItem:
    def __init__(self, name, added_at):
        self.name = name
        self.added_at = added_at

    def age(self):
        return datetime.now() - self.added_at

class TicketApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Ticket System")

        self.conn = sqlite3.connect("ticket_data.db")
        self.cursor = self.conn.cursor()
        self.setup_database()

        self.tickets = self.load_tickets()
        self.description_history = list({t.description for t in self.tickets})
        self.fridge_items = self.load_fridge_items()

        self.ticket_labels = []
        self.fridge_labels = []

        self.input_frame = tk.Frame(root)
        self.input_frame.pack(pady=10)

        # Ticket input fields
        self.desc_var = tk.StringVar()
        ttk.Combobox(self.input_frame, textvariable=self.desc_var, width=30, values=self.description_history).pack(side=tk.LEFT)

        self.day_var = tk.StringVar(value="0")
        tk.Entry(self.input_frame, textvariable=self.day_var, width=3).pack(side=tk.LEFT)
        tk.Label(self.input_frame, text="d").pack(side=tk.LEFT)

        self.hour_var = tk.StringVar(value="0")
        tk.Entry(self.input_frame, textvariable=self.hour_var, width=3).pack(side=tk.LEFT)
        tk.Label(self.input_frame, text="h").pack(side=tk.LEFT)

        self.min_var = tk.StringVar(value="5")
        tk.Entry(self.input_frame, textvariable=self.min_var, width=3).pack(side=tk.LEFT)
        tk.Label(self.input_frame, text="m").pack(side=tk.LEFT)

        self.sec_var = tk.StringVar(value="0")
        tk.Entry(self.input_frame, textvariable=self.sec_var, width=3).pack(side=tk.LEFT)
        tk.Label(self.input_frame, text="s").pack(side=tk.LEFT)

        tk.Button(self.input_frame, text="Add Ticket", command=self.add_ticket).pack(side=tk.LEFT, padx=5)

        # Fridge input fields
        self.fridge_var = tk.StringVar()
        tk.Entry(self.input_frame, textvariable=self.fridge_var, width=20).pack(side=tk.LEFT, padx=5)

        self.fridge_day_var = tk.StringVar(value="0")
        tk.Entry(self.input_frame, textvariable=self.fridge_day_var, width=3).pack(side=tk.LEFT)
        tk.Label(self.input_frame, text="d").pack(side=tk.LEFT)

        self.fridge_hour_var = tk.StringVar(value="0")
        tk.Entry(self.input_frame, textvariable=self.fridge_hour_var, width=3).pack(side=tk.LEFT)
        tk.Label(self.input_frame, text="h").pack(side=tk.LEFT)

        self.fridge_min_var = tk.StringVar(value="0")
        tk.Entry(self.input_frame, textvariable=self.fridge_min_var, width=3).pack(side=tk.LEFT)
        tk.Label(self.input_frame, text="m").pack(side=tk.LEFT)

        self.fridge_sec_var = tk.StringVar(value="0")
        tk.Entry(self.input_frame, textvariable=self.fridge_sec_var, width=3).pack(side=tk.LEFT)
        tk.Label(self.input_frame, text="s").pack(side=tk.LEFT)

        tk.Button(self.input_frame, text="Add Item", command=self.add_fridge_item).pack(side=tk.LEFT)

        self.ticket_frame = tk.Frame(root)
        self.ticket_frame.pack(pady=10)

        self.fridge_frame = tk.Frame(root)
        self.fridge_frame.pack(pady=10)

        self.build_ticket_ui()
        self.build_fridge_ui()
        self.update_ui()

    def setup_database(self):
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS tickets (title TEXT, description TEXT, created_at TEXT, due TEXT)''')
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS fridge_items (name TEXT, added_at TEXT)''')
        self.conn.commit()

    def load_tickets(self):
        self.cursor.execute("SELECT title, description, created_at, due FROM tickets")
        rows = self.cursor.fetchall()
        return [Ticket(title, desc, datetime.fromisoformat(created), datetime.fromisoformat(due)) for title, desc, created, due in rows]

    def load_fridge_items(self):
        self.cursor.execute("SELECT name, added_at FROM fridge_items")
        rows = self.cursor.fetchall()
        return [FridgeItem(name, datetime.fromisoformat(added)) for name, added in rows]

    def add_ticket(self):
        desc = self.desc_var.get().strip() or "No Description"
        if desc not in self.description_history:
            self.description_history.append(desc)

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

        ticket = Ticket(title, desc, created_at, due)
        self.tickets.append(ticket)

        self.cursor.execute("INSERT INTO tickets VALUES (?, ?, ?, ?)", (title, desc, created_at.isoformat(), due.isoformat()))
        self.conn.commit()

        self.build_ticket_ui()

    def add_fridge_item(self):
        name = self.fridge_var.get().strip()
        if not name:
            return

        try:
            days = int(self.fridge_day_var.get())
            hours = int(self.fridge_hour_var.get())
            minutes = int(self.fridge_min_var.get())
            seconds = int(self.fridge_sec_var.get())
        except ValueError:
            days, hours, minutes, seconds = 0, 0, 0, 0

        added_at = datetime.now() - timedelta(days=days, hours=hours, minutes=minutes, seconds=seconds)
        item = FridgeItem(name, added_at)
        self.fridge_items.append(item)

        self.cursor.execute("INSERT INTO fridge_items VALUES (?, ?)", (name, added_at.isoformat()))
        self.conn.commit()

        self.build_fridge_ui()

    def build_ticket_ui(self):
        for widget in self.ticket_frame.winfo_children():
            widget.destroy()
        self.ticket_labels = []
        tk.Label(self.ticket_frame, text="Tickets:", font=("Arial", 12, "bold")).pack()
        for i, ticket in enumerate(self.tickets):
            frame = tk.Frame(self.ticket_frame)
            frame.pack(fill=tk.X)
            lbl = tk.Label(frame, anchor='w')
            lbl.pack(side=tk.LEFT, expand=True, fill=tk.X)
            self.ticket_labels.append((lbl, ticket))
            tk.Button(frame, text="✔", command=lambda i=i: self.complete_ticket(i)).pack(side=tk.LEFT)
            tk.Button(frame, text="✕", command=lambda i=i: self.delete_ticket(i)).pack(side=tk.LEFT)

    def build_fridge_ui(self):
        for widget in self.fridge_frame.winfo_children():
            widget.destroy()
        self.fridge_labels = []
        tk.Label(self.fridge_frame, text="Fridge Items:", font=("Arial", 12, "bold")).pack()
        for i, item in enumerate(self.fridge_items):
            frame = tk.Frame(self.fridge_frame)
            frame.pack(fill=tk.X)
            lbl = tk.Label(frame, anchor='w')
            lbl.pack(side=tk.LEFT, expand=True, fill=tk.X)
            self.fridge_labels.append((lbl, item))
            tk.Button(frame, text="✕", command=lambda i=i: self.delete_fridge_item(i)).pack(side=tk.LEFT)

    def complete_ticket(self, index):
        ticket = self.tickets[index]
        if not ticket.completed:
            ticket.completed = True
            ticket.completed_time = datetime.now().strftime('%H:%M:%S')
            ticket.title += f" [Done @ {ticket.completed_time}]"
            self.build_ticket_ui()

    def delete_ticket(self, index):
        ticket = self.tickets.pop(index)
        self.cursor.execute("DELETE FROM tickets WHERE title = ?", (ticket.title,))
        self.conn.commit()
        self.build_ticket_ui()

    def delete_fridge_item(self, index):
        item = self.fridge_items.pop(index)
        self.cursor.execute("DELETE FROM fridge_items WHERE name = ? AND added_at = ?", (item.name, item.added_at.isoformat()))
        self.conn.commit()
        self.build_fridge_ui()

    def update_ui(self):
        for lbl, ticket in self.ticket_labels:
            rem = ticket.remaining_time()
            sign = "-" if rem.total_seconds() < 0 else ""
            total_seconds = abs(int(rem.total_seconds()))
            days = total_seconds // 86400
            hours = (total_seconds % 86400) // 3600
            minutes = (total_seconds % 3600) // 60
            seconds = total_seconds % 60
            text = f"{ticket.title} | Created: {ticket.created_at.strftime('%Y-%m-%d %H:%M:%S')}"
            if not ticket.completed:
                text += f" | Due in: {sign}{days}d {hours:02}:{minutes:02}:{seconds:02} | Desc: {ticket.description}"
            else:
                text += f" | Completed"
            lbl.config(text=text)

        for lbl, item in self.fridge_labels:
            age = item.age()
            total_seconds = int(age.total_seconds())
            days = total_seconds // 86400
            hours = (total_seconds % 86400) // 3600
            minutes = (total_seconds % 3600) // 60
            seconds = total_seconds % 60
            lbl.config(text=f"{item.name} | Added: {item.added_at.strftime('%Y-%m-%d %H:%M:%S')} | Age: {days}d {hours:02}:{minutes:02}:{seconds:02}")

        self.root.after(1000, self.update_ui)

if __name__ == '__main__':
    root = tk.Tk()
    app = TicketApp(root)
    root.mainloop()
