import os
import datetime
import time
import shutil
import ctypes
import sys
import json
import tkinter as tk
import sqlite3
from admin import AdminPanelWindow
import database
import pdf_creation
import mount_system
import framing_math
import pandas as pd
from database import get_db_path, resource_path
from tkinter import messagebox, ttk, filedialog
from admin import AdminPanelWindow
from search_window import SearchWindow
from order_system import OrderSystemWindow
from mount_designer import MountDesignerWindow

class FramingAppUI:

    def center_window(self, win, width, height):
        win.update_idletasks()
        screen_width = win.winfo_screenwidth()
        screen_height = win.winfo_screenheight()
        x = (screen_width // 2) - (width // 2)
        y = (screen_height // 2) - (height // 2)
        win.geometry(f'{width}x{height}+{x}+{y}')

    def __init__(self, root):
        self.root = root
        self.root.title("Made 2 Measure")
        self.db_path = database.get_db_path()
        self.current_tid = None
        self.current_mount_data = None
        self.check_initial_state()
        try:
            self.root.iconbitmap(resource_path("logo_icon.ico"))
        except Exception:
            try:
                img = tk.PhotoImage(file=resource_path('logo.png'))
                self.root.iconphoto(True, img)
            except Exception:
                pass

    def check_initial_state(self):
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT branch_number, branch_name FROM branch_setup LIMIT 1")
                row = cursor.fetchone()
            if row:
                self.branch_info = row 
                self.show_main_menu()
            else:
                self.show_setup_screen()
        except sqlite3.OperationalError:
            self.show_setup_screen()

    def clear_screen(self):
        for w in self.root.winfo_children(): w.destroy()

    def show_setup_screen(self):
        self.clear_screen()
        self.center_window(self.root, 450, 400)
        tk.Label(self.root, text="Branch Setup", font=("Arial", 16, "bold")).pack(pady=20)

        def validate_number(P, placeholder):
            if P == "" or P == placeholder: 
                return True
            return P.isdigit() and len(P) <= 4

        def setup_entry(placeholder, is_number_only=False):
            vcmd = (self.root.register(lambda P: validate_number(P, placeholder)), '%P')
            ent = tk.Entry(self.root, fg='grey', width=35, font=("Arial", 10))
            if is_number_only:
                ent.config(validate='key', validatecommand=vcmd)
            ent.insert(0, placeholder)

            def on_first_type(event):
                if ent.get() == placeholder and len(event.char) > 0:
                    ent.delete(0, tk.END)
                    ent.config(fg='black')
                    ent.unbind("<KeyPress>") 

            def handle_focus_in(event):
                if ent.get() == placeholder:
                    ent.icursor(0)
                ent.bind("<KeyPress>", on_first_type)

            def handle_focus_out(event):
                if not ent.get().strip():
                    ent.delete(0, tk.END)
                    ent.insert(0, placeholder)
                    ent.config(fg='grey')
                    ent.bind("<KeyPress>", on_first_type) 

            ent.bind("<FocusIn>", handle_focus_in)
            ent.bind("<FocusOut>", handle_focus_out)
            ent.bind("<Button-1>", lambda e: ent.after(1, lambda: ent.icursor(0) if ent.get()==placeholder else None))
            ent.pack(pady=10)
            return ent

        self.e_bn = setup_entry("Enter Branch Number (4 Digits)", is_number_only=True)
        self.e_bm = setup_entry("Enter Branch Name")
        self.root.after(100, lambda: self.e_bn.focus_set())

        def validate_and_save(event=None):
            bn = self.e_bn.get().strip()
            bm = self.e_bm.get().strip()
            if bm == "Enter Branch Name" or not bm:
                messagebox.showerror("Error", "Branch Name is required.")
                return
            if not (bn.isdigit() and len(bn) == 4):
                messagebox.showerror("Error", "Branch Number must be exactly 4 digits.")
                return
            try:
                with sqlite3.connect(self.db_path) as conn:
                    conn.execute("DROP TABLE IF EXISTS branch_setup")
                    conn.execute("CREATE TABLE branch_setup (id INTEGER PRIMARY KEY, branch_number TEXT, branch_name TEXT)")
                    conn.execute("INSERT INTO branch_setup (branch_number, branch_name) VALUES (?,?)", (bn, bm))
                    conn.commit()
                self.root.unbind("<Return>")
                self.check_initial_state()
            except Exception as e:
                messagebox.showerror("Database Error", f"{e}")

        self.root.bind("<Return>", validate_and_save)
        tk.Button(self.root, text="Save & Start App", command=validate_and_save, 
                  bg="#2ecc71", fg="white", font=("Arial", 10, "bold"), width=20).pack(pady=20)

    def show_main_menu(self):
        self.clear_screen()
        self.center_window(self.root, 850, 600)
        header = tk.Frame(self.root, bg="#004F91", pady=10)
        header.pack(fill="x")
        try:
            self.logo_img = tk.PhotoImage(file=resource_path("logo.png"))
            self.logo_small = self.logo_img.subsample(4, 4)
            logo_label = tk.Label(header, image=self.logo_small, bg="#004F91")
            logo_label.pack(side="right", padx=20)
        except Exception as e:
            print(f"logo not found: {e}")
        tk.Label(header, text=f"STORE: {self.branch_info[1]}", bg="#004F91", fg="white", font=("Arial", 16, "bold")).pack(side="left", padx=40)
        center_f = tk.Frame(self.root)
        center_f.pack(expand=True)
        btn_cfg = {"width": 25, "height": 5, "font": ("Arial", 14, "bold"), "bd": 5, "relief": "raised"}
        tk.Button(center_f, text="FIND FRAME", bg="#3498db", fg="white", command=self.open_search, **btn_cfg).grid(row=0, column=0, padx=30, pady=15)
        tk.Button(center_f, text="QUICK QUOTE", bg="#27ae60", fg="white", command=lambda: self.open_quote("None", "Manual", None), **btn_cfg).grid(row=0, column=1, padx=30, pady=15)
        tk.Button(center_f, text="🛠️ MOUNT DESIGNER", bg="#8e44ad", fg="white", command=self.open_mount_designer, **btn_cfg).grid(row=1, column=0, padx=30, pady=15)
        future_btn = tk.Button(center_f, text="[ Future Feature Slot ]", bg="#ecf0f1", fg="grey", state="disabled", **btn_cfg)
        future_btn.grid(row=1, column=1, padx=30, pady=15)
        admin_footer = tk.Frame(self.root)
        admin_footer.pack(side="bottom", fill="x", padx=20, pady=20)
        tk.Button(admin_footer, text="⚙️ ADMIN LOGIN", command=self.show_admin_login, font=("Arial", 9), relief="flat", fg="grey").pack(side="right")

    def open_search(self):
        """Launches our modular, decoupled search catalog directory panel window layer."""

        def process_search_selection(frame_id, description, table_id):
            # When a row is double-clicked, open the quote screen with the selection data points!
            self.open_quote(frame_id, description, table_id)

        SearchWindow(
            parent=self.root,
            db_path=self.db_path,
            on_select_callback=process_search_selection,
        )

    def open_mount_designer(self, caller_width=None, caller_height=None, update_callback=None):
        """Launches the standalone Pro Mount Grid Designer component container."""

        def handle_designer_return(price, total_w, total_h, packaged_data):
            self.current_mount_data = packaged_data
            if update_callback:
                update_callback(price, total_w, total_h)

        MountDesignerWindow(
            parent=self.root,
            db_path=self.db_path,
            branch_info=self.branch_info,
            caller_width=caller_width,
            caller_height=caller_height,
            update_callback=handle_designer_return,
        )

    def open_quote(self, fid="None", desc="Manual", tid=None):
        
        OrderSystemWindow(
            parent=self.root,
            db_path=self.db_path,
            branch_info=self.branch_info,
            ui_instance=self,
            fid=fid,
            fdesc=desc,
            tid=tid
        )

    def show_admin_login(self):
        lwin = tk.Toplevel(self.root)
        self.center_window(lwin, 300, 250)
        tk.Label(lwin, text="Admin Login", font=("Arial", 12, "bold")).pack(pady=10)
        tk.Label(lwin, text="Username:").pack(); u = tk.Entry(lwin); u.pack()
        tk.Label(lwin, text="Password:").pack(); p = tk.Entry(lwin, show="*"); p.pack()

        def check():
            hashed_input = database.hash_password(p.get())
            with sqlite3.connect(self.db_path) as conn:
                res = conn.execute("SELECT privilege_level, username FROM users WHERE username=? AND password_text=?", (u.get(), hashed_input)).fetchone()
            if res: 
                level = res[0]
                name = res[1]
                self.active_user = name 
                database.log_action(self.active_user, "ADMIN_LOGIN", f"User '{name}' (Level {level}) accessed Admin Panel.")
                lwin.destroy()
                self.open_admin_panel(level, name) 
            else: 
                messagebox.showerror("Error", "Invalid Credentials")
                lwin.lift(); lwin.focus_force()

        tk.Button(lwin, text="Login", command=check, bg="#2980b9", fg="white").pack(pady=20)
        lwin.bind('<Return>', lambda e: check())

    def open_admin_panel(self, priv_level, current_user):
       
        AdminPanelWindow(
            parent=self.root,
            ui_instance=self,
            priv_level=priv_level,
            current_user=current_user,
            db_path=self.db_path,
        )