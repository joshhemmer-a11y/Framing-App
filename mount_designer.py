import tkinter as tk
from tkinter import ttk, messagebox
import os
import datetime
import sqlite3
import time

import database
import pdf_creation
import mount_system

class MountDesignerWindow:
    """
    A standalone view class that completely handles the Pro Mount Grid Designer canvas,
    interactive previews, and stand-alone mount-only processing.
    """
    def __init__(self, parent, db_path, branch_info, caller_width=None, caller_height=None, update_callback=None):
        self.parent = parent
        self.db_path = db_path
        self.branch_info = branch_info
        self.update_callback = update_callback
        
        # Spawn an independent Toplevel window container
        self.window = tk.Toplevel(parent)
        self.window.title("Pro Mount Grid Designer")
        self.window.grab_set()  # Lock focus to this window
        
        self._center_window(1000, 750)
        
        # Initialize Tkinter tracing/state variables
        self.orient_var = tk.StringVar(value="Portrait")
        self.mount_color_var = tk.StringVar(value="Standard White")
        
        # UI Component Frames
        self.left_ctrl = tk.Frame(self.window, width=350, padx=20, pady=10)
        self.left_ctrl.pack(side="left", fill="y")
        
        self.preview_frame = tk.Frame(self.window, bg="#dcdde1")
        self.preview_frame.pack(side="right", expand=True, fill="both", padx=10, pady=10)
        
        self.canvas = tk.Canvas(self.preview_frame, bg="white", width=600, height=600, bd=2, relief="sunken")
        self.canvas.pack(expand=True)
        
        self._build_controls(caller_width, caller_height)
        self.update_drawing()

    def _center_window(self, width, height):
        self.window.update_idletasks()
        screen_width = self.window.winfo_screenwidth()
        screen_height = self.window.winfo_screenheight()
        x = (screen_width // 2) - (width // 2)
        y = (screen_height // 2) - (height // 2)
        self.window.geometry(f'{width}x{height}+{x}+{y}')

    def _build_controls(self, caller_width, caller_height):
        # Orientation Group
        o_frame = tk.LabelFrame(self.left_ctrl, text="Orientation", padx=5, pady=5)
        o_frame.pack(fill="x", pady=5)
        tk.Radiobutton(o_frame, text="Portrait", variable=self.orient_var, value="Portrait", command=self.update_drawing).pack(side="left")
        tk.Radiobutton(o_frame, text="Landscape", variable=self.orient_var, value="Landscape", command=self.update_drawing).pack(side="left")
        
        # Dimensions Helper Group
        tk.Label(self.left_ctrl, text="Board Dimensions (mm)", font=("Arial", 10, "bold")).pack(anchor="w")
        self.ent_tw = self._create_input(self.left_ctrl, "Total Width:", caller_width or "500")
        self.ent_th = self._create_input(self.left_ctrl, "Total Height:", caller_height or "400")
        
        # Apertures Group
        tk.Label(self.left_ctrl, text="Aperture Size (mm)", font=("Arial", 10, "bold")).pack(anchor="w", pady=(10,0))
        self.ent_aw = self._create_input(self.left_ctrl, "Aperture W:", "150")
        self.ent_ah = self._create_input(self.left_ctrl, "Aperture H:", "100")
        
        # Matrix Rows/Cols Group
        tk.Label(self.left_ctrl, text="Grid Layout", font=("Arial", 10, "bold")).pack(anchor="w", pady=(10,0))
        f_grid = tk.Frame(self.left_ctrl); f_grid.pack(fill="x", pady=5)
        tk.Label(f_grid, text="Cols:").pack(side="left")
        self.spin_cols = tk.Spinbox(f_grid, from_=1, to=10, width=5, command=self.update_drawing)
        self.spin_cols.delete(0, "end"); self.spin_cols.insert(0, "2"); self.spin_cols.pack(side="left", padx=5)
        
        tk.Label(f_grid, text="Rows:").pack(side="left")
        self.spin_rows = tk.Spinbox(f_grid, from_=1, to=10, width=5, command=self.update_drawing)
        self.spin_rows.delete(0, "end"); self.spin_rows.insert(0, "2"); self.spin_rows.pack(side="left")
        
        self.ent_bridge = self._create_input(self.left_ctrl, "Gap (mm):", "20")
        self.ent_off = self._create_input(self.left_ctrl, "Bottom Weight:", "0")
        
        # Commercial Quantity & Colors
        tk.Label(self.left_ctrl, text="Order Quantity", font=("Arial", 10, "bold")).pack(anchor="w", pady=(10,0))
        self.qty_entry = tk.Entry(self.left_ctrl); self.qty_entry.insert(0, "1"); self.qty_entry.pack(fill="x", pady=5)
        
        tk.Label(self.left_ctrl, text="Mount Material/Color", font=("Arial", 10, "bold")).pack(anchor="w", pady=(10,0))
        color_menu = ttk.Combobox(self.left_ctrl, textvariable=self.mount_color_var, state="readonly")
        color_menu['values'] = ("Standard White", "Antique White", "Black Core", "Deep Red", "Royal Blue", "Slate Grey")
        color_menu.pack(fill="x", pady=5)
        
        # Standalone Mount Options Panel Group
        tk.Frame(self.left_ctrl, height=2, bd=1, relief="sunken").pack(fill="x", pady=10)
        tk.Label(self.left_ctrl, text="STAND-ALONE ORDER (Optional)", font=("Arial", 10, "bold"), fg="#2980b9").pack(anchor="w")
        tk.Label(self.left_ctrl, text="Cust Name:").pack(anchor="w")
        self.ent_cust_name = tk.Entry(self.left_ctrl); self.ent_cust_name.pack(fill="x")
        tk.Label(self.left_ctrl, text="Cust Mobile:").pack(anchor="w")
        self.ent_cust_mob = tk.Entry(self.left_ctrl); self.ent_cust_mob.pack(fill="x")
        
        self.price_lbl = tk.Label(self.left_ctrl, text="Price: £20.00", font=("Arial", 12, "bold"), fg="green")
        self.price_lbl.pack(pady=5)
        
        tk.Button(self.left_ctrl, text="🔄 Refresh Drawing", command=self.update_drawing, font=("Arial", 10)).pack(fill="x", pady=5)
        tk.Button(self.left_ctrl, text="✅ Confirm / Generate PDF", command=self.confirm, bg="#27ae60", fg="white", font=("Arial", 11, "bold"), height=2).pack(fill="x", pady=15)

    def _create_input(self, parent, label, default):
        f = tk.Frame(parent); f.pack(fill="x", pady=2)
        tk.Label(f, text=label, width=15, anchor="w").pack(side="left")
        e = tk.Entry(f, width=10); e.insert(0, str(default)); e.pack(side="right")
        return e

    def update_drawing(self, event=None):
        self.canvas.delete("all")
        try:
            raw_aw = float(self.ent_aw.get())
            raw_ah = float(self.ent_ah.get())
            raw_tw = float(self.ent_tw.get())
            raw_th = float(self.ent_th.get())
            raw_rows = int(self.spin_rows.get())
            raw_cols = int(self.spin_cols.get())
            br = float(self.ent_bridge.get())
            off = float(self.ent_off.get())
            
            geo = mount_system.calculate_mount_geometry(
                self.orient_var.get(), raw_aw, raw_ah, raw_tw, raw_th, raw_rows, raw_cols, br, off
            )
            u_p = database.get_tiered_price(geo["tw"], geo["th"], geo["d_rows"] * geo["d_cols"])
            try:
                q = int(self.qty_entry.get() or 1)
            except: 
                q = 1
                
            self.price_lbl.config(text=f"Unit: £{u_p:.2f} | Total: £{u_p * q:.2f}")
            scale = min(500 / geo["tw"], 500 / geo["th"])
            ox, oy = 50, 50 
            
            self.canvas.create_rectangle(ox, oy, ox + (geo["tw"] * scale), oy + (geo["th"] * scale), fill="#f5f6fa", outline="black", width=2)
            if geo["grid_w"] > geo["tw"] or geo["grid_h"] > geo["th"]:
                self.canvas.create_text(300, 300, text="TOO BIG FOR BOARD", fill="red", font=("Arial", 14, "bold"))
                return u_p, geo["tw"], geo["th"]
                
            for r in range(geo["d_rows"]):
                for c in range(geo["d_cols"]):
                    x1 = ox + (geo["start_x"] + (c * (geo["aw"] + br))) * scale
                    y1 = oy + (geo["start_y"] + (r * (geo["ah"] + br))) * scale
                    self.canvas.create_rectangle(x1, y1, x1 + (geo["aw"] * scale), y1 + (geo["ah"] * scale), fill="white", outline="#3498db", width=1)
            return u_p, geo["tw"], geo["th"]
        except Exception as e: 
            print(f"Drawing Error: {e}")
            return 20.00, 500.0, 400.0

    def process_mount_only_order(self, name, mob, price, complex_mount_summary):
        q = int(self.qty_entry.get() or 1)
        mount_only_data = {
            "order_id": "M-" + datetime.datetime.now().strftime("%H%M%S"),
            "customer_name": f"{name} (MOUNT ONLY)",
            "mobile_number": mob,
            "frame_id": "N/A",                
            "frame_description": "CUSTOM MOUNT ONLY", 
            "depth_mm": "N/A",               
            "item_width": 0, 
            "item_height": 0,
            "mount_required": True,
            "mount_width": float(self.ent_tw.get()), 
            "mount_height": float(self.ent_th.get()),
            "mount_total_w": float(self.ent_tw.get()),
            "mount_total_h": float(self.ent_th.get()),
            "mount_colour": self.mount_color_var.get(),
            "orientation": self.orient_var.get(),
            "quantity": q,
            "delivery_required": False,
            "base_price": 0.0, 
            "total_price": price, 
            "amount_paid": price * q,
            "order_date": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
            "branch_name": self.branch_info[1], 
            "branch_number": self.branch_info[0],
            "complex_mount": complex_mount_summary
        }
        path = pdf_creation.generate_order_pdf(mount_only_data)
        os.startfile(path)

    def confirm(self):
        u_p, tw, th = self.update_drawing()
        name = self.ent_cust_name.get().strip()
        q = int(self.qty_entry.get() or 1)
        
        # Package structure dictionary
        packaged_mount_data = {
            'rows': self.spin_rows.get(), 'cols': self.spin_cols.get(),
            'ap_w': self.ent_aw.get(), 'ap_h': self.ent_ah.get(),
            'bridge': self.ent_bridge.get(), 'offset': self.ent_off.get(),
            'mount_total_w': self.ent_tw.get(), 'mount_total_h': self.ent_th.get(),
            'color': self.mount_color_var.get(),
            'orientation': self.orient_var.get(),
            'quantity': q
        }
        
        if name:
            self.process_mount_only_order(name, self.ent_cust_mob.get(), u_p, packaged_mount_data)
            
        if self.update_callback:
            self.update_callback(u_p, self.ent_tw.get(), self.ent_th.get(), packaged_mount_data)
            
        self.window.destroy()