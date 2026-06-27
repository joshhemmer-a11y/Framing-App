import os
import datetime
import time
import shutil
import ctypes
import sys
import json
import tkinter as tk
import sqlite3
import database
import pdf_creation
import mount_system
import framing_math
import pandas as pd
from database import get_db_path, resource_path
from tkinter import messagebox, ttk, filedialog

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
        except:
            try:
                img = tk.PhotoImage(file=resource_path('logo.png'))
                self.root.tk.call('wm', 'iconphoto', self.root._w, img)
            except:
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

    def open_mount_designer(self, caller_width=None, caller_height=None, update_callback=None):
        mwin = tk.Toplevel(self.root)
        mwin.title("Pro Mount Grid Designer")
        self.center_window(mwin, 1000, 750) 
        mwin.grab_set()
        left_ctrl = tk.Frame(mwin, width=350, padx=20, pady=10)
        left_ctrl.pack(side="left", fill="y")
        preview_frame = tk.Frame(mwin, bg="#dcdde1")
        preview_frame.pack(side="right", expand=True, fill="both", padx=10, pady=10)
        canvas = tk.Canvas(preview_frame, bg="white", width=600, height=600, bd=2, relief="sunken")
        canvas.pack(expand=True)

        self.orient_var = tk.StringVar(value="Portrait")
        o_frame = tk.LabelFrame(left_ctrl, text="Orientation", padx=5, pady=5)
        o_frame.pack(fill="x", pady=5)
        tk.Radiobutton(o_frame, text="Portrait", variable=self.orient_var, value="Portrait", command=lambda: update_drawing()).pack(side="left")
        tk.Radiobutton(o_frame, text="Landscape", variable=self.orient_var, value="Landscape", command=lambda: update_drawing()).pack(side="left")
        tk.Label(left_ctrl, text="Board Dimensions (mm)", font=("Arial", 10, "bold")).pack(anchor="w")
        
        def create_input(parent, label, default):
            f = tk.Frame(parent); f.pack(fill="x", pady=2)
            tk.Label(f, text=label, width=15, anchor="w").pack(side="left")
            e = tk.Entry(f, width=10); e.insert(0, str(default)); e.pack(side="right")
            return e

        ent_tw = create_input(left_ctrl, "Total Width:", caller_width or "500")
        ent_th = create_input(left_ctrl, "Total Height:", caller_height or "400")
        tk.Label(left_ctrl, text="Aperture Size (mm)", font=("Arial", 10, "bold")).pack(anchor="w", pady=(10,0))
        ent_aw = create_input(left_ctrl, "Aperture W:", "150")
        ent_ah = create_input(left_ctrl, "Aperture H:", "100")
        tk.Label(left_ctrl, text="Grid Layout", font=("Arial", 10, "bold")).pack(anchor="w", pady=(10,0))
        f_grid = tk.Frame(left_ctrl); f_grid.pack(fill="x", pady=5)
        tk.Label(f_grid, text="Cols:").pack(side="left")
        spin_cols = tk.Spinbox(f_grid, from_=1, to=10, width=5, command=lambda: update_drawing())
        spin_cols.delete(0, "end"); spin_cols.insert(0, "2"); spin_cols.pack(side="left", padx=5)
        tk.Label(f_grid, text="Rows:").pack(side="left")
        spin_rows = tk.Spinbox(f_grid, from_=1, to=10, width=5, command=lambda: update_drawing())
        spin_rows.delete(0, "end"); spin_rows.insert(0, "2"); spin_rows.pack(side="left")
        ent_bridge = create_input(left_ctrl, "Gap (mm):", "20")
        ent_off = create_input(left_ctrl, "Bottom Weight:", "0")
        tk.Label(left_ctrl, text="Order Quantity", font=("Arial", 10, "bold")).pack(anchor="w", pady=(10,0))
        qty_entry = tk.Entry(left_ctrl); qty_entry.insert(0, "1"); qty_entry.pack(fill="x", pady=5)
        tk.Label(left_ctrl, text="Mount Material/Color", font=("Arial", 10, "bold")).pack(anchor="w", pady=(10,0))
        self.mount_color_var = tk.StringVar(value="Standard White")
        color_menu = ttk.Combobox(left_ctrl, textvariable=self.mount_color_var, state="readonly")
        color_menu['values'] = ("Standard White", "Antique White", "Black Core", "Deep Red", "Royal Blue", "Slate Grey")
        color_menu.pack(fill="x", pady=5)
        tk.Frame(left_ctrl, height=2, bd=1, relief="sunken").pack(fill="x", pady=10)
        tk.Label(left_ctrl, text="STAND-ALONE ORDER (Optional)", font=("Arial", 10, "bold"), fg="#2980b9").pack(anchor="w")
        tk.Label(left_ctrl, text="Cust Name:").pack(anchor="w")
        ent_cust_name = tk.Entry(left_ctrl); ent_cust_name.pack(fill="x")
        tk.Label(left_ctrl, text="Cust Mobile:").pack(anchor="w")
        ent_cust_mob = tk.Entry(left_ctrl); ent_cust_mob.pack(fill="x")
        price_lbl = tk.Label(left_ctrl, text="Price: £20.00", font=("Arial", 12, "bold"), fg="green")
        price_lbl.pack(pady=5)

        def update_drawing(event=None):
            canvas.delete("all")
            try:
                raw_aw = float(ent_aw.get())
                raw_ah = float(ent_ah.get())
                raw_tw = float(ent_tw.get())
                raw_th = float(ent_th.get())
                raw_rows = int(spin_rows.get())
                raw_cols = int(spin_cols.get())
                br = float(ent_bridge.get())
                off = float(ent_off.get())
                geo = mount_system.calculate_mount_geometry(
                    self.orient_var.get(), raw_aw, raw_ah, raw_tw, raw_th, raw_rows, raw_cols, br, off
                )
                u_p = database.get_tiered_price(geo["tw"], geo["th"], geo["d_rows"] * geo["d_cols"])
                try:
                    q = int(qty_entry.get() or 1)
                except: q = 1
                price_lbl.config(text=f"Unit: £{u_p:.2f} | Total: £{u_p * q:.2f}")
                scale = min(500 / geo["tw"], 500 / geo["th"])
                ox, oy = 50, 50 
                canvas.create_rectangle(ox, oy, ox + (geo["tw"] * scale), oy + (geo["th"] * scale), fill="#f5f6fa", outline="black", width=2)
                if geo["grid_w"] > geo["tw"] or geo["grid_h"] > geo["th"]:
                    canvas.create_text(300, 300, text="TOO BIG FOR BOARD", fill="red", font=("Arial", 14, "bold"))
                    return
                for r in range(geo["d_rows"]):
                    for c in range(geo["d_cols"]):
                        x1 = ox + (geo["start_x"] + (c * (geo["aw"] + br))) * scale
                        y1 = oy + (geo["start_y"] + (r * (geo["ah"] + br))) * scale
                        canvas.create_rectangle(x1, y1, x1 + (geo["aw"] * scale), y1 + (geo["ah"] * scale), fill="white", outline="#3498db", width=1)
                return u_p, geo["tw"], geo["th"]
            except Exception as e: 
                print(f"Drawing Error: {e}")
        
        def process_mount_only_order(name, mob, price):
            q = int(qty_entry.get() or 1)
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
                "mount_width": float(ent_tw.get()), 
                "mount_height": float(ent_th.get()),
                "mount_total_w": float(ent_tw.get()),
                "mount_total_h": float(ent_th.get()),
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
                "complex_mount": self.current_mount_data
            }
            path = pdf_creation.generate_order_pdf(mount_only_data)
            os.startfile(path)

        def confirm():
            u_p, tw, th = update_drawing()
            name = ent_cust_name.get().strip()
            q = int(qty_entry.get() or 1)
            self.current_mount_data = {
                'rows': spin_rows.get(), 'cols': spin_cols.get(),
                'ap_w': ent_aw.get(), 'ap_h': ent_ah.get(),
                'bridge': ent_bridge.get(), 'offset': ent_off.get(),
                'mount_total_w': ent_tw.get(), 'mount_total_h': ent_th.get(),
                'color': self.mount_color_var.get(),
                'orientation': self.orient_var.get(),
                'quantity': q
            }
            if name:
                process_mount_only_order(name, ent_cust_mob.get(), u_p)
            if update_callback:
                update_callback(u_p, ent_tw.get(), ent_th.get())
            mwin.destroy()

        tk.Button(left_ctrl, text="🔄 Refresh Drawing", command=update_drawing, font=("Arial", 10)).pack(fill="x", pady=5)
        tk.Button(left_ctrl, text="✅ Confirm / Generate PDF", command=confirm, bg="#27ae60", fg="white", font=("Arial", 11, "bold"), height=2).pack(fill="x", pady=15)
        update_drawing()

    def open_quote(self, fid="None", desc="Manual", tid=None):
        qwin = tk.Toplevel(self.root)
        qwin.title("Quick Quote")
        self.center_window(qwin, 550, 700)
        qwin.columnconfigure((0, 3), weight=1) 
        qwin.columnconfigure((1, 2), weight=0)
        qwin.lift()
        qwin.focus_force()
        self.total_price_var = tk.StringVar(value="0.00")
        self.mount_info_var = tk.StringVar(value="Standard Mount")
        self.current_tid = tid
        m_req = tk.BooleanVar()
        sv_fid = tk.StringVar(value=fid)
        sv_w, sv_h = tk.StringVar(), tk.StringVar()
        sv_mw, sv_mh = tk.StringVar(value="0"), tk.StringVar(value="0")
        sv_title = tk.StringVar(value=f"Quote: {desc}")
        tk.Label(qwin, text="Frame ID:").grid(row=0, column=0, pady=10, sticky="e")
        efid = tk.Entry(qwin, textvariable=sv_fid, width=15)
        efid.config(fg='grey' if sv_fid.get() == "None" else 'black')
        efid.grid(row=0, column=1, sticky="w")
        efid.bind('<FocusIn>', lambda e: [sv_fid.set("") if sv_fid.get()=="None" else None, efid.config(fg='black')])
        efid.bind('<FocusOut>', lambda e: [sv_fid.set("None") if not sv_fid.get().strip() else None, efid.config(fg='grey' if sv_fid.get()=="None" else 'black')])
        tk.Label(qwin, textvariable=sv_title, font=("Arial", 12, "bold")).grid(row=1, column=0, columnspan=4, pady=10)
        tk.Label(qwin, text="Width:").grid(row=2, column=0, sticky="e")
        tk.Entry(qwin, textvariable=sv_w, width=10).grid(row=2, column=1, sticky="w")
        tk.Label(qwin, text="Height:").grid(row=2, column=2, sticky="e")
        tk.Entry(qwin, textvariable=sv_h, width=10).grid(row=2, column=3, sticky="w")
        mf = tk.Frame(qwin)
        
        def launch_multi_designer():
            try:
                curr_tw = float(sv_w.get() or 0) + float(sv_mw.get() or 0)
                curr_th = float(sv_h.get() or 0) + float(sv_mh.get() or 0)
            except:
                curr_tw, curr_th = 500, 400
            self.open_mount_designer(
                caller_width=curr_tw, 
                caller_height=curr_th,
                update_callback=lambda p, tw, th: [
                    sv_mw.set(float(tw) - float(sv_w.get() or 0)),
                    sv_mh.set(float(th) - float(sv_h.get() or 0)),
                    calc()
                ]
            )

        btn_multi = tk.Button(qwin, text="🛠️ Design Multi-Aperture", command=launch_multi_designer, bg="#8e44ad", fg="white", font=("Arial", 9, "bold"))

        def toggle_mount_ui():
            if m_req.get():
                mf.grid(row=4, column=0, columnspan=4)
                btn_multi.grid(row=5, column=0, columnspan=4, pady=5)
            else:
                mf.grid_forget()
                btn_multi.grid_forget()
                self.current_mount_data = None
            calc()

        tk.Checkbutton(qwin, text="Add Mount? (+£20)", variable=m_req, command=toggle_mount_ui).grid(row=3, column=0, columnspan=4, pady=10)
        tk.Label(mf, text="MW:").grid(row=0, column=0); tk.Entry(mf, textvariable=sv_mw, width=8).grid(row=0, column=1, padx=5)
        tk.Label(mf, text="MH:").grid(row=0, column=2); tk.Entry(mf, textvariable=sv_mh, width=8).grid(row=0, column=3, padx=5)
        rlbl = tk.Label(qwin, text="Price: £0.00", font=("Arial", 16, "bold"), fg="blue")
        rlbl.grid(row=6, column=0, columnspan=4, pady=20)
        btn_prcd = tk.Button(qwin, text="PROCEED TO ORDER", bg="gray", fg="white", font=("Arial", 12, "bold"), width=30, state="disabled")
        btn_prcd.grid(row=7, column=0, columnspan=4, pady=10)

        def calc(*args):
            try:
                if not sv_w.get() or not sv_h.get(): return
                tw = float(sv_w.get() or 0) + float(sv_mw.get() or 0)
                th = float(sv_h.get() or 0) + float(sv_mh.get() or 0)
                if self.current_tid:
                    with sqlite3.connect(self.db_path) as conn:
                        res = conn.execute("SELECT price_gbp FROM price_grids WHERE table_id=? AND (?>=min_width_mm AND ?<=max_width_mm) AND (?>=min_height_mm AND ?<=max_height_mm)", 
                                            (self.current_tid, tw, tw, th, th)).fetchone()
                    if res:
                        extra_fee = 0.0
                        if self.current_mount_data:
                            qty = int(self.current_mount_data['rows']) * int(self.current_mount_data['cols'])
                            extra_fee = (qty - 1) * 2.0
                        final_p = res[0] + (20.0 if m_req.get() else 0.0) + extra_fee
                        rlbl.config(text=f"£{final_p:.2f}", fg="green")
                        btn_prcd.config(state="normal", bg="#27ae60", 
                                        command=lambda: [qwin.destroy(), self.open_order(sv_fid.get(), sv_title.get(), res[0], sv_w.get(), sv_h.get(), sv_mw.get(), sv_mh.get(), m_req.get(), self.current_tid)])
                    else:
                        rlbl.config(text="Frame too big", fg="red"); btn_prcd.config(state="disabled", bg="gray")
                else:
                    rlbl.config(text="Enter valid Frame ID", fg="orange"); btn_prcd.config(state="disabled", bg="gray")
            except: pass

        def lookup_frame():
            cid = sv_fid.get().strip()
            if cid == "None" or not cid: return
            with sqlite3.connect(self.db_path) as conn:
                res = conn.execute("SELECT description, table_id FROM frame_catalog WHERE frame_id = ? COLLATE NOCASE", (cid,)).fetchone()
            if res:
                sv_title.set(f"Quote: {res[0]} ({cid})")
                self.current_tid = res[1]; calc()
            else:
                sv_title.set("ID Not Found"); self.current_tid = None; calc()

        tk.Button(qwin, text="Find", command=lookup_frame).grid(row=0, column=2, padx=5)
        for v in [sv_w, sv_h, sv_mw, sv_mh]: v.trace_add("write", calc)

    def open_search(self):
        swin = tk.Toplevel(self.root)
        self.center_window(swin, 650, 500)
        swin.title("Find Frame")
        sv = tk.StringVar()
        tk.Label(swin, text="Search by ID or Description:").pack(pady=10)
        search_entry = tk.Entry(swin, textvariable=sv, width=40)
        search_entry.pack(pady=10)
        tk.Label(swin, text="Double-click a row to open the Quote/Order window", fg="#004F91", font=("Arial", 10, "italic")).pack(pady=5)
        tr = ttk.Treeview(swin, columns=("ID", "Desc", "Table"), show="headings")
        swin.lift()
        swin.focus_force()
        search_entry.focus_set()
        for c in ("ID", "Desc", "Table"): tr.heading(c, text=c); tr.column(c, width=120)
        tr.pack(fill="both", expand=True, padx=10, pady=10)
        def search(*a):
            for i in tr.get_children(): tr.delete(i)
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("SELECT frame_id, description, table_id FROM frame_catalog WHERE frame_id LIKE ? OR description LIKE ?", (f"%{sv.get()}%", f"%{sv.get()}%"))
                for r in cursor: tr.insert("", "end", values=r)
        sv.trace_add("write", search)
        tr.bind("<Double-1>", lambda e: [self.open_quote(tr.item(tr.selection()[0], 'values')[0], tr.item(tr.selection()[0], 'values')[1], tr.item(tr.selection()[0], 'values')[2]), swin.destroy()])

    def open_order(self, fid, fdesc, basep, iw, ih, mw, mh, hasm, tid):
        owin = tk.Toplevel(self.root)
        self.center_window(owin, 800, 980)
        m_req, d_req = tk.BooleanVar(value=hasm), tk.BooleanVar()
        sv_iw, sv_ih, sv_mw, sv_mh = tk.StringVar(value=iw), tk.StringVar(value=ih), tk.StringVar(value=mw), tk.StringVar(value=mh)
        tk.Label(owin, text=f"Order: {fdesc}", font=("Arial", 14, "bold")).pack(pady=10)
        f1 = tk.LabelFrame(owin, text="Sizes (mm)", padx=10, pady=10); f1.pack(fill="x", padx=20, pady=5)
        tk.Label(f1, text="Item Width:").grid(row=0, column=0); eiw = tk.Entry(f1, textvariable=sv_iw, width=10); eiw.grid(row=0, column=1)
        tk.Label(f1, text="Item Height:").grid(row=0, column=2); eih = tk.Entry(f1, textvariable=sv_ih, width=10); eih.grid(row=0, column=3)
        f2 = tk.LabelFrame(owin, text="Specs", padx=10, pady=10); f2.pack(fill="x", padx=20, pady=5)
        tk.Label(f2, text="Frame Depth:").grid(row=0, column=0); ed = tk.Entry(f2, width=10); ed.grid(row=0, column=1)
        eo = ttk.Combobox(f2, values=["Portrait", "Landscape"], width=12); eo.set("Portrait"); eo.grid(row=0, column=3)
        f3 = tk.LabelFrame(owin, text="Mount", padx=10, pady=10); f3.pack(fill="x", padx=20, pady=5)
        mi = tk.Frame(f3); tk.Checkbutton(f3, text="Mount?", variable=m_req, command=lambda: [mi.pack() if m_req.get() else mi.pack_forget(), update_summary()]).pack(anchor="w")
        tk.Label(mi, text="Total Mount Width:").grid(row=0, column=0); emw = tk.Entry(mi, textvariable=sv_mw, width=8); emw.grid(row=0, column=1)
        tk.Label(mi, text="Total Mount Height:").grid(row=0, column=2); emh = tk.Entry(mi, textvariable=sv_mh, width=8); emh.grid(row=0, column=3)
        mc = ttk.Combobox(mi, values=["White", "Cream", "Black", "Grey"], width=10); mc.set("White"); mc.grid(row=0, column=4)
        if hasm: mi.pack()
        f4 = tk.LabelFrame(owin, text="Customer", padx=10, pady=10); f4.pack(fill="x", padx=20, pady=5)
        tk.Label(f4, text="Name:").grid(row=0, column=0); en = tk.Entry(f4, width=30); en.grid(row=0, column=1)
        tk.Label(f4, text="Mobile Number:").grid(row=1, column=0); em = tk.Entry(f4, width=30); em.grid(row=1, column=1)
        af = tk.Frame(f4); tk.Checkbutton(f4, text="Home Delivery?", variable=d_req, command=lambda: [af.grid(row=4, column=0, columnspan=2) if d_req.get() else af.grid_forget(), update_summary()]).grid(row=2, column=1)
        tk.Label(af, text="Address Line 1:").grid(row=0, column=0); ea1 = tk.Entry(af, width=50); ea1.grid(row=0, column=1)
        tk.Label(af, text="Address Line 2:").grid(row=1, column=0); ea2 = tk.Entry(af, width=50); ea2.grid(row=1, column=1)
        tk.Label(af, text="Address Line 3:").grid(row=2, column=0); ea3 = tk.Entry(af, width=50); ea3.grid(row=2, column=1)
        tk.Label(af, text="Postcode:").grid(row=3, column=0); epc = tk.Entry(af, width=20); epc.grid(row=3, column=1)
        f5 = tk.LabelFrame(owin, text="Breakdown", padx=10, pady=10); f5.pack(fill="x", padx=20, pady=10)
        sum_lbl = tk.Label(f5, text="", font=("Courier", 10, "bold"), justify="left"); sum_lbl.pack(side="left")
        pf = tk.Frame(f5); pf.pack(side="right")
        tk.Label(pf, text="Paid: £").grid(row=0, column=0); epaid = tk.Entry(pf, width=10); epaid.insert(0,"0.00"); epaid.grid(row=0, column=1)
        owin.lift()
        owin.focus_force()

        def update_summary(*args):
            if not owin.winfo_exists(): return
            try:
                iwv = float(sv_iw.get() or 0)
                ihv = float(sv_ih.get() or 0)
                mwv = float(sv_mw.get() or 0) if m_req.get() else 0
                mhv = float(sv_mh.get() or 0) if m_req.get() else 0
                tw, th, = iwv + mwv, ihv + mhv
                current_base = float(basep)
                if tid and tid != "None":
                    with sqlite3.connect(self.db_path) as conn:
                        res = conn.execute(
                            "SELECT price_gbp FROM price_grids WHERE table_id=? AND "
                            "(?>=min_width_mm AND ?<=max_width_mm) AND "
                            "(?>=min_height_mm AND ?<=max_height_mm)", 
                            (tid, tw, tw, th, th)    
                        ).fetchone()
                        if res: 
                            current_base = res[0]
                mount_fee, delivery_fee = framing_math.calculate_extra_fees(
                    mount_required=m_req.get(),
                    current_mount_data=self.current_mount_data,
                    delivery_required=d_req.get()
                )
                total_price = current_base + mount_fee + delivery_fee
                sum_lbl.config(text=(
                    f"GLASS SIZE: {tw}x{th}mm\n"
                    f"FRAME ({fid}): £{current_base:>7.2f}\n"
                    f"MOUNT:      £{mount_fee:>7.2f}\n"
                    f"DELIVERY:   £{delivery_fee:>7.2f}\n"
                    f"----------------------\n"
                    f"TOTAL:      £{total_price:>7.2f}"
                ))
                return total_price, current_base
            except Exception as e:
                sum_lbl.config(text="Error calculating price...")
                return 0.0, 0.0

        tk.Button(pf, text="Paid Full", 
                command=lambda: [
                    epaid.delete(0, tk.END), 
                    epaid.insert(0, f"{update_summary()[0]:.2f}")
                ]).grid(row=1, column=0, columnspan=2, pady=5)
        for v in [sv_iw, sv_ih, sv_mw, sv_mh]: v.trace_add("write", update_summary)
        update_summary()

        def trigger_save():
            live_tot, live_base = update_summary()
            self.save_final(
                fid, fdesc, live_base, 
                sv_iw, sv_ih, m_req, sv_mw, sv_mh, 
                en, em, d_req, ea1, ea2, ea3, epc, 
                mc, eo, ed, epaid, owin, live_tot
            )

        tk.Button(owin, text="SAVE & PRINT PDF", bg="#27ae60", fg="white", font=("Arial", 12, "bold"), height=2, command=trigger_save).pack(pady=20)

    def save_final(self, fid, fdesc, live_base, sv_iw, sv_ih, m_req, sv_mw, sv_mh, 
                   en, em, d_req, ea1, ea2, ea3, epc, mc, eo, ed, epaid, owin, live_tot):
        try:
            cust_name = en.get().strip()
            cust_mob = em.get().strip()
            frame_depth = ed.get().strip()
            if not cust_name or not cust_mob or not frame_depth:
                messagebox.showerror("Error", "Name, Mobile, and Depth are required.")
                owin.lift(), owin.focus_force()
                return
            mwf = float(sv_mw.get() or 0) if m_req.get() else 0
            mhf = float(sv_mh.get() or 0) if m_req.get() else 0
            p_amt = float(epaid.get() or 0)
            tot = float(live_tot)
            if d_req.get():
                if p_amt < (tot - 0.01):
                    messagebox.showerror("Payment Required", f"Home Delivery requires payment in full.\n\nTotal: £{tot:.2f}\nPaid: £{p_amt:.2f}")
                    owin.lift(), owin.focus_force()
                    return
            mount_json = None
            if m_req.get() and self.current_mount_data:
                mount_json = json.dumps(self.current_mount_data)
            with sqlite3.connect(self.db_path) as conn:
                cur = conn.cursor()
                order_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
                cur.execute("""INSERT INTO orders (customer_name, mobile_number, frame_description, item_width, item_height, 
                    mount_required, mount_width, mount_height, mount_colour, orientation, depth_mm, delivery_required, 
                    addr_l1, addr_l2, addr_l3, postcode, total_price, amount_paid, order_date, mount_data) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                    (cust_name, cust_mob, fdesc, sv_iw.get(), sv_ih.get(), (1 if m_req.get() else 0), mwf, mhf, mc.get(), eo.get(), ed.get(), (1 if d_req.get() else 0), ea1.get(), ea2.get(), ea3.get(), epc.get(), tot, p_amt, order_time, mount_json))
                oid = cur.lastrowid
                pdf_data = {
                    "order_id": oid, "frame_id": fid, "customer_name": cust_name, "mobile_number": cust_mob, "frame_description": fdesc,
                    "item_width": sv_iw.get(), "item_height": sv_ih.get(), "mount_required": m_req.get(), "mount_width": mwf,
                    "mount_height": mhf, "mount_colour": mc.get(), "orientation": eo.get(), "depth_mm": ed.get(),
                    "delivery_required": d_req.get(), "addr_l1": ea1.get(), "addr_l2": ea2.get(), "addr_l3": ea3.get(), 
                    "postcode": epc.get(), "base_price": live_base, "total_price": live_tot, "amount_paid": p_amt, 
                    "order_date": order_time, "branch_name": self.branch_info[1], "branch_number": self.branch_info[0],
                    "complex_mount": self.current_mount_data,
                    "mount_total_w": float(sv_iw.get() or 0) + float(sv_mw.get() or 0),
                    "mount_total_h": float(sv_ih.get() or 0) + float(sv_mh.get() or 0),
                    "quantity": (self.current_mount_data.get('quantity', 1) if self.current_mount_data else 1)
                }
                path = pdf_creation.generate_order_pdf(pdf_data)
                conn.execute("UPDATE orders SET pdf_path=? WHERE order_id=?", (path, oid))
                conn.commit()
                log_details = f"New Order #{oid} created for {cust_name}. Total: £{tot:.2f}"
                database.log_action(self.branch_info[0], "ORDER_CREATED", log_details)
            owin.withdraw(); owin.destroy(); time.sleep(0.5); os.startfile(path)
            self.current_mount_data = None
        except Exception as e: 
            messagebox.showerror("Error", str(e))

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
        awin = tk.Toplevel(self.root)
        awin.title(f"Admin Portal - {current_user}")
        self.center_window(awin, 500, 600)
        awin.lift()
        awin.focus_force()
        main_c = tk.Frame(awin, padx=20, pady=10)
        main_c.pack(fill="both", expand=True)
        if priv_level >= 2:
            tk.Label(main_c, text="🛠️ ADMIN DATA MANAGEMENT", font=("Arial", 11, "bold"), fg="#2980b9").pack(pady=10)
            u_f = tk.LabelFrame(main_c, text="Admin Tools", padx=10, pady=10)
            u_f.pack(fill="x", pady=5)
            tk.Button(u_f, text="👤 MANAGE USERS", width=30, bg="#34495e", fg="white", command=lambda: self.open_user_manager(awin)).pack(pady=5)
            tk.Label(u_f, text="Sync Options:", font=("Arial", 9, "bold")).pack()
            tk.Button(u_f, text="Export Catalog", width=30, command=lambda: self.export_table("frame_catalog", current_user, awin)).pack(pady=2)
            tk.Button(u_f, text="Export Price Grids", width=30, command=lambda: self.export_table("price_grids", current_user, awin)).pack(pady=2)
            tk.Button(u_f, text="Export Mount Pricing", width=30, command=lambda: self.export_table("mount_pricing", current_user, awin)).pack(pady=2)
            tk.Label(u_f, text="Import Data:", font=("Arial", 9, "bold")).pack(pady=(10,0))
            tk.Button(u_f, text="Import Catalog", width=30, bg="#e8f6ed", command=lambda: self.run_import("frame_catalog", current_user, awin)).pack(pady=2)
            tk.Button(u_f, text="Import Price Grids", width=30, bg="#e8f6ed", command=lambda: self.run_import("price_grids", current_user, awin)).pack(pady=2)
            tk.Button(u_f, text="Import Mount Pricing", width=30, bg="#e8f6ed", command=lambda: self.run_import("mount_pricing", current_user, awin)).pack(pady=2)
            tk.Frame(main_c, height=2, bd=1, relief="sunken").pack(fill="x", padx=50, pady=15)
            tk.Label(main_c, text="📜 SYSTEM AUDIT", font=("Arial", 11, "bold")).pack(pady=5)
            tk.Button(main_c, text="View Change Logs", width=30, bg="#f39c12", fg="white", command=self.view_audit_logs).pack(pady=5)
        tk.Frame(main_c, height=2, bd=1, relief="sunken").pack(fill="x", padx=50, pady=15)
        tk.Label(main_c, text="⚠️ BRANCH CONTROL", font=("Arial", 11, "bold"), fg="red").pack(pady=5)
        tk.Button(main_c, text="♻️ RESET BRANCH SETUP", width=30, fg="white", bg="#c0392b", command=lambda: self.reset_branch(current_user)).pack(pady=5)
        if priv_level < 2:
            tk.Label(main_c, text="Staff Access: Data Management Hidden.", fg="grey", font=("Arial", 8, "italic")).pack(pady=20)

    def export_table(self, table_name, current_user, awin):
        try:
            with sqlite3.connect(self.db_path) as conn:
                df = pd.read_sql_query(f"SELECT * FROM {table_name}", conn)
            f_path = filedialog.asksaveasfilename(defaultextension=".xlsx", initialfile=f"{table_name}_backup")
            if f_path:
                if f_path.endswith('.xlsx'): df.to_excel(f_path, index=False)
                else: df.to_csv(f_path, index=False)
                messagebox.showinfo("Success", f"Data exported successfully.")
                database.log_action(current_user, "DATA_EXPORT", f"Exported {table_name} to Excel/CSV")
        except Exception as e: messagebox.showerror("Export Error", str(e))
        finally: awin.lift(); awin.focus_force()

    def run_import(self, table_name, current_user, awin):
        try:
            f_path = filedialog.askopenfilename(filetypes=[("Data Files", "*.xlsx *.csv")])
            if not f_path: return
            if not messagebox.askyesno("Confirm Import", f"DELETE all current {table_name} data?"): return
            df = pd.read_excel(f_path) if f_path.endswith('.xlsx') else pd.read_csv(f_path)
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(f"DELETE FROM {table_name}")
                df.to_sql(table_name, conn, if_exists='append', index=False)
            messagebox.showinfo("Success", f"Imported {len(df)} records.")
            database.log_action(current_user, "DATA_IMPORT", f"Imported {len(df)} records into {table_name} from file.")
        except Exception as e: messagebox.showerror("Import Error", f"{e}")
        finally: awin.lift(); awin.focus_force()

    def view_audit_logs(self):
        vwin = tk.Toplevel(self.root)
        vwin.title("System Audit Logs")
        self.center_window(vwin, 850, 500)
        frame = tk.Frame(vwin); frame.pack(fill="both", expand=True, padx=10, pady=10)
        tr = ttk.Treeview(frame, columns=("ID", "User", "Action", "Details", "Time"), show="headings")
        tr.heading("ID", text="Log ID"); tr.heading("User", text="User"); tr.heading("Action", text="Action"); tr.heading("Details", text="Details"); tr.heading("Time", text="Time")
        tr.pack(fill="both", expand=True)
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("SELECT log_id, user_name, action_performed, change_details, timestamp FROM audit_logs ORDER BY timestamp DESC")
            for row in cursor: tr.insert("", "end", values=row)

    def reset_branch(self, current_user):
        if messagebox.askyesno("Warning", "Wipe Store Data?"):
            with sqlite3.connect(self.db_path) as conn: conn.execute("DROP TABLE IF EXISTS branch_setup")
            self.check_initial_state()

    def open_user_manager(self, awin):
        uwin = tk.Toplevel(awin); uwin.title("User Management"); self.center_window(uwin, 750, 500); uwin.grab_set()
        l_f = tk.LabelFrame(uwin, text="Active Users", padx=10, pady=10)
        l_f.pack(side="left", fill="both", expand=True, padx=10, pady=10)
        tr = ttk.Treeview(l_f, columns=("User", "Level"), show="headings")
        tr.heading("User", text="Username"); tr.heading("Level", text="Level")
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