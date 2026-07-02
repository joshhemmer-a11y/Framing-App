import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import sqlite3
import pandas as pd
import logging

logger = logging.getLogger("MadeToMeasure")

class AdminPanelWindow:

    #Admin panel: 2 user levels: Admin: can edit database and view logs, reset branch and add remove users. Manager: Can reset Branch
    
    def __init__(self, parent, ui_instance, priv_level, current_user, db_path):
        self.parent = parent
        self.ui_instance = ui_instance
        self.priv_level = priv_level
        self.active_user = current_user
        self.db_path = db_path
        
        # Spawn an independent Toplevel window container
        self.window = tk.Toplevel(parent)
        self.window.title(f"Admin Portal - {self.active_user}")
        self.window.lift()
        self.window.focus_force()
        
        # Centralized geometry calculation helper method context
        self._center_window(500, 600)
        
        # Build out UI Elements
        self.main_container = tk.Frame(self.window, padx=20, pady=10)
        self.main_container.pack(fill="both", expand=True)
        
        self._build_ui()

    def _center_window(self, width, height):
        self.window.update_idletasks()
        screen_width = self.window.winfo_screenwidth()
        screen_height = self.window.winfo_screenheight()
        x = (screen_width // 2) - (width // 2)
        y = (screen_height // 2) - (height // 2)
        self.window.geometry(f'{width}x{height}+{x}+{y}')

    def _build_ui(self):
        # Import local database functions safely inside the module
        import database

        if self.priv_level >= 2:
            tk.Label(self.main_container, text="🛠️ ADMIN DATA MANAGEMENT", font=("Arial", 11, "bold"), fg="#2980b9").pack(pady=10)
            
            u_f = tk.LabelFrame(self.main_container, text="Admin Tools", padx=10, pady=10)
            u_f.pack(fill="x", pady=5)
            
            tk.Button(u_f, text="👤 MANAGE USERS", width=30, bg="#34495e", fg="white", 
                      command=self.open_user_manager).pack(pady=5)
            
            tk.Label(u_f, text="Sync Options:", font=("Arial", 9, "bold")).pack()
            tk.Button(u_f, text="Export Catalog", width=30, command=lambda: self.export_table("frame_catalog")).pack(pady=2)
            tk.Button(u_f, text="Export Price Grids", width=30, command=lambda: self.export_table("price_grids")).pack(pady=2)
            tk.Button(u_f, text="Export Mount Pricing", width=30, command=lambda: self.export_table("mount_pricing")).pack(pady=2)
            
            tk.Label(u_f, text="Import Data:", font=("Arial", 9, "bold")).pack(pady=(10,0))
            tk.Button(u_f, text="Import Catalog", width=30, bg="#e8f6ed", command=lambda: self.run_import("frame_catalog")).pack(pady=2)
            tk.Button(u_f, text="Import Price Grids", width=30, bg="#e8f6ed", command=lambda: self.run_import("price_grids")).pack(pady=2)
            tk.Button(u_f, text="Import Mount Pricing", width=30, bg="#e8f6ed", command=lambda: self.run_import("mount_pricing")).pack(pady=2)
            
            tk.Frame(self.main_container, height=2, bd=1, relief="sunken").pack(fill="x", padx=50, pady=15)
            tk.Label(self.main_container, text="📜 SYSTEM AUDIT", font=("Arial", 11, "bold")).pack(pady=5)
            tk.Button(self.main_container, text="View Change Logs", width=30, bg="#f39c12", fg="white", 
                      command=self.view_audit_logs).pack(pady=5)
            
        tk.Frame(self.main_container, height=2, bd=1, relief="sunken").pack(fill="x", padx=50, pady=15)
        tk.Label(self.main_container, text="⚠️ BRANCH CONTROL", font=("Arial", 11, "bold"), fg="red").pack(pady=5)
        tk.Button(self.main_container, text="♻️ RESET BRANCH SETUP", width=30, fg="white", bg="#c0392b", 
                  command=self.reset_branch).pack(pady=5)
        
        if self.priv_level < 2:
            tk.Label(self.main_container, text="Staff Access: Data Management Hidden.", fg="grey", font=("Arial", 8, "italic")).pack(pady=20)

    def export_table(self, table_name):
        import database
        try:
            with sqlite3.connect(self.db_path) as conn:
                df = pd.read_sql_query(f"SELECT * FROM {table_name}", conn)
            f_path = filedialog.asksaveasfilename(defaultextension=".xlsx", initialfile=f"{table_name}_backup")
            if f_path:
                if f_path.endswith('.xlsx'): 
                    df.to_excel(f_path, index=False)
                else: 
                    df.to_csv(f_path, index=False)
                messagebox.showinfo("Success", "Data exported successfully.")
                database.log_action(self.active_user, "DATA_EXPORT", f"Exported {table_name} to Excel/CSV")
        except Exception as e: 
            messagebox.showerror("Export Error", str(e))
        finally: 
            self.window.lift(); self.window.focus_force()

    def run_import(self, table_name):
        import database
        try:
            f_path = filedialog.askopenfilename(filetypes=[("Data Files", "*.xlsx *.csv")])
            if not f_path: return
            if not messagebox.askyesno("Confirm Import", f"DELETE all current {table_name} data?"): return
            df = pd.read_excel(f_path) if f_path.endswith('.xlsx') else pd.read_csv(f_path)
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(f"DELETE FROM {table_name}")
                df.to_sql(table_name, conn, if_exists='append', index=False)
            messagebox.showinfo("Success", f"Imported {len(df)} records.")
            database.log_action(self.active_user, "DATA_IMPORT", f"Imported {len(df)} records into {table_name} from file.")
        except Exception as e: 
            messagebox.showerror("Import Error", f"{e}")
        finally: 
            self.window.lift(); self.window.focus_force()

    def view_audit_logs(self):
        vwin = tk.Toplevel(self.window)
        vwin.title("System Audit Logs")
        self._center_sub_window(vwin, 850, 500)
        frame = tk.Frame(vwin)
        frame.pack(fill="both", expand=True, padx=10, pady=10)
        tr = ttk.Treeview(frame, columns=("ID", "User", "Action", "Details", "Time"), show="headings")
        tr.heading("ID", text="Log ID")
        tr.heading("User", text="User")
        tr.heading("Action", text="Action")
        tr.heading("Details", text="Details")
        tr.heading("Time", text="Time")
        tr.pack(fill="both", expand=True)
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("SELECT log_id, user_name, action_performed, change_details, timestamp FROM audit_logs ORDER BY timestamp DESC")
            for row in cursor: tr.insert("", "end", values=row)

    def reset_branch(self):
        if messagebox.askyesno("Warning", "Wipe Store Data?"):
            with sqlite3.connect(self.db_path) as conn: 
                conn.execute("DROP TABLE IF EXISTS branch_setup")
            # Clear window container elements safely
            self.window.destroy()
            if hasattr(self.parent, 'check_initial_state'):
                self.parent.check_initial_state()

    def open_user_manager(self):
        import database
        uwin = tk.Toplevel(self.window)
        uwin.title("User Management")
        self._center_sub_window(uwin, 750, 500)
        uwin.grab_set()
        
        l_f = tk.LabelFrame(uwin, text="Active Users", padx=10, pady=10)
        l_f.pack(side="left", fill="both", expand=True, padx=10, pady=10)
        tr = ttk.Treeview(l_f, columns=("User", "Level"), show="headings")
        tr.heading("User", text="Username")
        tr.heading("Level", text="Level")
        tr.pack(fill="both", expand=True)
        
        btn_f = tk.Frame(l_f)
        btn_f.pack(fill="x", pady=5)
        
        def delete_user():
            sel = tr.selection()
            if sel:
                uname = tr.item(sel[0], 'values')[0]
                if uname == self.active_user:
                    messagebox.showerror("Access Denied", "You cannot delete yourself.")
                    return
                if messagebox.askyesno("Confirm", f"Delete user {uname}?"):
                    with sqlite3.connect(self.db_path) as conn:
                        conn.execute("DELETE FROM users WHERE username=?", (uname,))
                        conn.commit() 
                    refresh_list()
                    database.log_action(self.active_user, "USER_DELETED", f"Deleted user: {uname}")
            else:
                messagebox.showwarning("Warning", "Select a user to delete")
        
        tk.Button(btn_f, text="DELETE USER", bg="#e74c3c", fg="white", font=("Arial", 9, "bold"), command=delete_user).pack(side="left")
        
        r_f = tk.LabelFrame(uwin, text="Add / Update User", padx=10, pady=10)
        r_f.pack(side="right", fill="both", padx=10, pady=10)
        tk.Label(r_f, text="Username:").pack(anchor="w")
        en_user = tk.Entry(r_f); en_user.pack(pady=5, fill="x")
        tk.Label(r_f, text="Password:").pack(anchor="w")
        en_pass = tk.Entry(r_f, show="*"); en_pass.pack(pady=5, fill="x")
        tk.Label(r_f, text="Permission Level:").pack(anchor="w")
        level_var = tk.StringVar(value="1")
        level_cb = ttk.Combobox(r_f, textvariable=level_var, values=["1", "2"], state="readonly")
        level_cb.pack(pady=5, fill="x")

        def save_user():
            if not en_user.get() or not en_pass.get():
                messagebox.showerror("Error", "Fields cannot be empty")
                return
            hashed = database.hash_password(en_pass.get())
            priv_level = int(level_var.get())
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("INSERT OR REPLACE INTO users (username, password_text, privilege_level) VALUES (?, ?, ?)", (en_user.get(), hashed, priv_level))
            database.log_action(self.active_user, "USER_CREATED", f"Created/Updated user: {en_user.get()} at Level {priv_level}")
            refresh_list()
            en_user.delete(0, tk.END); en_pass.delete(0, tk.END)
        
        tk.Button(r_f, text="SAVE USER", bg="#27ae60", fg="white", command=save_user, height=2).pack(pady=20, fill="x")

        def refresh_list():
            for item in tr.get_children(): tr.delete(item)
            with sqlite3.connect(self.db_path) as conn:
                res = conn.execute("SELECT username, privilege_level FROM users").fetchall()
                for row in res: tr.insert("", "end", values=row)
        
        refresh_list()

    def _center_sub_window(self, win, width, height):
        win.update_idletasks()
        screen_width = win.winfo_screenwidth()
        screen_height = win.winfo_screenheight()
        x = (screen_width // 2) - (width // 2)
        y = (screen_height // 2) - (height // 2)
        win.geometry(f'{width}x{height}+{x}+{y}')
