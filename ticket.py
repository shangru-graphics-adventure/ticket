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

    def remaining_time(self):
        delta = self.due - datetime.now()
        return max(delta, timedelta(0))

class FridgeItem:
    def __init__(self, name, added_at):
        self.name = name
        self.added_at = added_at

    def age(self):
        delta = datetime.now() - self.added_at
        return delta

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

        self.desc_label = tk.Label(self.input_frame, text="Description:")
        self.desc_label.pack(side=tk.LEFT)

        self.desc_var = tk.StringVar()
        self.desc_combobox = ttk.Combobox(self.input_frame, textvariable=self.desc_var, width=40)
        self.desc_combobox.pack(side=tk.LEFT, padx=5)
        self.desc_combobox['values'] = self.description_history
        self.desc_combobox.bind("<KeyRelease>", self.update_autocomplete)

        self.add_button = tk.Button(self.input_frame, text="Add Ticket", command=self.add_ticket)
        self.add_button.pack(side=tk.LEFT, padx=5)

        self.fridge_label = tk.Label(self.input_frame, text="Fridge Item:")
        self.fridge_label.pack(side=tk.LEFT)

        self.fridge_var = tk.StringVar()
        self.fridge_entry = tk.Entry(self.input_frame, textvariable=self.fridge_var, width=20)
        self.fridge_entry.pack(side=tk.LEFT, padx=5)

        self.add_fridge_button = tk.Button(self.input_frame, text="Add Item", command=self.add_fridge_item)
        self.add_fridge_button.pack(side=tk.LEFT)

        self.ticket_frame = tk.Frame(root)
        self.ticket_frame.pack(pady=10)

        self.fridge_frame = tk.Frame(root)
        self.fridge_frame.pack(pady=10)

        self.build_ticket_ui()
        self.build_fridge_ui()
        self.update_ui()

    def setup_database(self):
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS tickets (
            title TEXT, description TEXT, created_at TEXT, due TEXT
        )''')
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS fridge_items (
            name TEXT, added_at TEXT
        )''')
        self.conn.commit()

    def load_tickets(self):
        self.cursor.execute("SELECT title, description, created_at, due FROM tickets")
        rows = self.cursor.fetchall()
        return [Ticket(title, desc, datetime.fromisoformat(created), datetime.fromisoformat(due)) for title, desc, created, due in rows]

    def load_fridge_items(self):
        self.cursor.execute("SELECT name, added_at FROM fridge_items")
        rows = self.cursor.fetchall()
        return [FridgeItem(name, datetime.fromisoformat(added)) for name, added in rows]

    def update_autocomplete(self, event):
        typed = self.desc_var.get().lower()
        if typed == '':
            self.desc_combobox['values'] = self.description_history
        else:
            filtered = [desc for desc in self.description_history if typed in desc.lower()]
            self.desc_combobox['values'] = filtered

    def add_ticket(self):
        desc = self.desc_var.get().strip()
        if not desc:
            desc = "No Description"
        if desc not in self.description_history:
            self.description_history.append(desc)

        created_at = datetime.now()
        due = created_at + timedelta(minutes=5)
        title = f"Ticket #{len(self.tickets)+1}"

        ticket = Ticket(title, desc, created_at, due)
        self.tickets.append(ticket)

        self.cursor.execute("INSERT INTO tickets VALUES (?, ?, ?, ?)", (title, desc, created_at.isoformat(), due.isoformat()))
        self.conn.commit()

        self.desc_combobox.set('')
        self.desc_combobox['values'] = self.description_history

        self.build_ticket_ui()

    def add_fridge_item(self):
        name = self.fridge_var.get().strip()
        if not name:
            return

        added_at = datetime.now()
        item = FridgeItem(name, added_at)
        self.fridge_items.append(item)

        self.cursor.execute("INSERT INTO fridge_items VALUES (?, ?)", (name, added_at.isoformat()))
        self.conn.commit()

        self.fridge_var.set('')
        self.build_fridge_ui()

    def delete_ticket(self, index):
        ticket = self.tickets.pop(index)
        self.cursor.execute("DELETE FROM tickets WHERE title = ?", (ticket.title,))
        self.conn.commit()
        self.build_ticket_ui()

    def move_ticket_up(self, index):
        if index > 0:
            self.tickets[index - 1], self.tickets[index] = self.tickets[index], self.tickets[index - 1]
            self.build_ticket_ui()

    def move_ticket_down(self, index):
        if index < len(self.tickets) - 1:
            self.tickets[index + 1], self.tickets[index] = self.tickets[index], self.tickets[index + 1]
            self.build_ticket_ui()

    def delete_fridge_item(self, index):
        item = self.fridge_items.pop(index)
        self.cursor.execute("DELETE FROM fridge_items WHERE name = ? AND added_at = ?", (item.name, item.added_at.isoformat()))
        self.conn.commit()
        self.build_fridge_ui()

    def build_ticket_ui(self):
        for widget in self.ticket_frame.winfo_children():
            widget.destroy()
        self.ticket_labels.clear()
        tk.Label(self.ticket_frame, text="Tickets:", font=("Arial", 12, "bold")).pack()
        for i, ticket in enumerate(self.tickets):
            frame = tk.Frame(self.ticket_frame)
            frame.pack(fill=tk.X)
            lbl = tk.Label(frame, anchor='w')
            lbl.pack(side=tk.LEFT, expand=True, fill=tk.X)
            self.ticket_labels.append((lbl, ticket))
            tk.Button(frame, text="↑", command=lambda i=i: self.move_ticket_up(i)).pack(side=tk.LEFT)
            tk.Button(frame, text="↓", command=lambda i=i: self.move_ticket_down(i)).pack(side=tk.LEFT)
            tk.Button(frame, text="✕", command=lambda i=i: self.delete_ticket(i)).pack(side=tk.LEFT)

    def build_fridge_ui(self):
        for widget in self.fridge_frame.winfo_children():
            widget.destroy()
        self.fridge_labels.clear()
        tk.Label(self.fridge_frame, text="Fridge Items:", font=("Arial", 12, "bold")).pack()
        for i, item in enumerate(self.fridge_items):
            frame = tk.Frame(self.fridge_frame)
            frame.pack(fill=tk.X)
            lbl = tk.Label(frame, anchor='w')
            lbl.pack(side=tk.LEFT, expand=True, fill=tk.X)
            self.fridge_labels.append((lbl, item))
            tk.Button(frame, text="✕", command=lambda i=i: self.delete_fridge_item(i)).pack(side=tk.LEFT)

    def update_ui(self):
        for lbl, ticket in self.ticket_labels:
            rem = ticket.remaining_time()
            lbl.config(text=f"{ticket.title} | Created: {ticket.created_at.strftime('%H:%M:%S')} | Due in: {rem.seconds//60:02}:{rem.seconds%60:02} | Desc: {ticket.description}")

        for lbl, item in self.fridge_labels:
            age = item.age()
            lbl.config(text=f"{item.name} | Added: {item.added_at.strftime('%H:%M:%S')} | Age: {age.days}d {age.seconds//3600:02}:{(age.seconds//60)%60:02}:{age.seconds%60:02}")

        self.root.after(1000, self.update_ui)

if __name__ == '__main__':
    root = tk.Tk()
    app = TicketApp(root)
    root.mainloop()
