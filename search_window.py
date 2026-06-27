import tkinter as tk
from tkinter import ttk
import sqlite3

class SearchWindow:
    """
    A standalone view class that handles searching the frame catalog database
    and passing the selected frame metadata back to the main app context.
    """
    def __init__(self, parent, db_path, on_select_callback):
        self.parent = parent
        self.db_path = db_path
        self.on_select_callback = on_select_callback
        
        # Spawn independent Toplevel container
        self.window = tk.Toplevel(parent)
        self.window.title("Find Frame")
        self.window.lift()
        self.window.focus_force()
        
        self._center_window(650, 500)
        
        # Search state tracking variable
        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", self.execute_search)
        
        self._build_ui()
        self.execute_search()  # Run an initial blank search to populate the list

    def _center_window(self, width, height):
        self.window.update_idletasks()
        screen_width = self.window.winfo_screenwidth()
        screen_height = self.window.winfo_screenheight()
        x = (screen_width // 2) - (width // 2)
        y = (screen_height // 2) - (height // 2)
        self.window.geometry(f'{width}x{height}+{x}+{y}')

    def _build_ui(self):
        tk.Label(self.window, text="Search by ID or Description:", font=("Arial", 10)).pack(pady=(10, 0))
        
        self.search_entry = tk.Entry(self.window, textvariable=self.search_var, width=40, font=("Arial", 11))
        self.search_entry.pack(pady=10)
        self.search_entry.focus_set()
        
        tk.Label(self.window, text="Double-click a row to open the Quote/Order window", 
                 fg="#004F91", font=("Arial", 10, "italic")).pack(pady=5)
        
        # Scrollable Data Tree Matrix Panel
        frame = tk.Frame(self.window)
        frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        self.tree = ttk.Treeview(frame, columns=("ID", "Desc", "Table"), show="headings")
        
        # Explicit, clean layout headers instead of a single-line loop
        self.tree.heading("ID", text="Frame ID")
        self.tree.heading("Desc", text="Description")
        self.tree.heading("Table", text="Pricing Grid Tier")
        
        self.tree.column("ID", width=120, anchor="w")
        self.tree.column("Desc", width=350, anchor="w")
        self.tree.column("Table", width=120, anchor="center")
        
        self.tree.pack(fill="both", expand=True)
        
        # Bind double-click event listener to our selection selection dispatcher method
        self.tree.bind("<Double-1>", self.handle_row_selection)

    def execute_search(self, *args):
        """Queries database dynamically using lookahead filters matching entry strings."""
        # Clear existing row collections
        for item in self.tree.get_children():
            self.tree.delete(item)
            
        search_query = f"%{self.search_var.get()}%"
        
        query = """
            SELECT frame_id, description, table_id 
            FROM frame_catalog 
            WHERE frame_id LIKE ? OR description LIKE ?
        """
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute(query, (search_query, search_query))
                for row in cursor:
                    self.tree.insert("", "end", values=row)
        except sqlite3.Error as e:
            print(f"Database search retrieval error: {e}")

    def handle_row_selection(self, event):
        """Extracts values from the highlighted row block and returns them via the callback."""
        selection = self.tree.selection()
        if not selection:
            return
            
        row_values = self.tree.item(selection[0], 'values')
        
        # Fire structural return array up to interceptor loop context pipeline
        if self.on_select_callback:
            self.on_select_callback(row_values[0], row_values[1], row_values[2])
            
        self.window.destroy()