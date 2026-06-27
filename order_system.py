import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
import datetime
import json
import time
import os
import framing_math
import pdf_creation
import database
from database import resource_path

class OrderSystemWindow:
    """
    A standalone view class that handles calculating quick frame quotes, 
    gathering comprehensive customer/delivery specs, and finalizing checkout orders.
    """
    def __init__(self, parent, db_path, branch_info, ui_instance, fid="None", fdesc="Manual", tid=None):
        self.parent = parent
        self.db_path = db_path
        self.branch_info = branch_info
        self.ui_instance = ui_instance  # Reference to main UI layout for callback handling
        
        # State tracking variables
        self.current_tid = tid
        self.current_fid = fid
        self.current_fdesc = fdesc
        
        # Open the Quick Quote window
        self.qwin = tk.Toplevel(parent)
        self.qwin.title("Quick Quote")
        self._center_window(self.qwin, 550, 700)
        
        self.qwin.columnconfigure((0, 3), weight=1) 
        self.qwin.columnconfigure((1, 2), weight=0)
        self.qwin.lift()
        self.qwin.focus_force()
        
        self.total_price_var = tk.StringVar(value="0.00")
        self.mount_info_var = tk.StringVar(value="Standard Mount")
        
        self._build_quote_ui()

    def _center_window(self, win, width, height):
        win.update_idletasks()
        screen_width = win.winfo_screenwidth()
        screen_height = win.winfo_screenheight()
        x = (screen_width // 2) - (width // 2)
        y = (screen_height // 2) - (height // 2)
        win.geometry(f'{width}x{height}+{x}+{y}')

    def _build_quote_ui(self):
        self.m_req = tk.BooleanVar()
        self.sv_fid = tk.StringVar(value=self.current_fid)
        self.sv_w, self.sv_h = tk.StringVar(), tk.StringVar()
        self.sv_mw, self.sv_mh = tk.StringVar(value="0"), tk.StringVar(value="0")
        self.sv_title = tk.StringVar(value=f"Quote: {self.current_fdesc}")
        
        tk.Label(self.qwin, text="Frame ID:").grid(row=0, column=0, pady=10, sticky="e")
        self.efid = tk.Entry(self.qwin, textvariable=self.sv_fid, width=15)
        self.efid.config(fg='grey' if self.sv_fid.get() == "None" else 'black')
        self.efid.grid(row=0, column=1, sticky="w")
        
        self.efid.bind('<FocusIn>', lambda e: [self.sv_fid.set("") if self.sv_fid.get()=="None" else None, self.efid.config(fg='black')])
        self.efid.bind('<FocusOut>', lambda e: [self.sv_fid.set("None") if not self.sv_fid.get().strip() else None, self.efid.config(fg='grey' if self.sv_fid.get()=="None" else 'black')])
        
        tk.Button(self.qwin, text="Find", command=self.lookup_frame).grid(row=0, column=2, padx=5)
        
        tk.Label(self.qwin, textvariable=self.sv_title, font=("Arial", 12, "bold")).grid(row=1, column=0, columnspan=4, pady=10)
        
        tk.Label(self.qwin, text="Width:").grid(row=2, column=0, sticky="e")
        tk.Entry(self.qwin, textvariable=self.sv_w, width=10).grid(row=2, column=1, sticky="w")
        tk.Label(self.qwin, text="Height:").grid(row=2, column=2, sticky="e")
        tk.Entry(self.qwin, textvariable=self.sv_h, width=10).grid(row=2, column=3, sticky="w")
        
        self.mf = tk.Frame(self.qwin)
        self.btn_multi = tk.Button(self.qwin, text="🛠️ Design Multi-Aperture", command=self.launch_multi_designer, bg="#8e44ad", fg="white", font=("Arial", 9, "bold"))
        
        tk.Checkbutton(self.qwin, text="Add Mount? (+£20)", variable=self.m_req, command=self.toggle_mount_ui).grid(row=3, column=0, columnspan=4, pady=10)
        
        tk.Label(self.mf, text="MW:").grid(row=0, column=0)
        tk.Entry(self.mf, textvariable=self.sv_mw, width=8).grid(row=0, column=1, padx=5)
        tk.Label(self.mf, text="MH:").grid(row=0, column=2)
        tk.Entry(self.mf, textvariable=self.sv_mh, width=8).grid(row=0, column=3, padx=5)
        
        self.rlbl = tk.Label(self.qwin, text="Price: £0.00", font=("Arial", 16, "bold"), fg="blue")
        self.rlbl.grid(row=6, column=0, columnspan=4, pady=20)
        
        self.btn_prcd = tk.Button(self.qwin, text="PROCEED TO ORDER", bg="gray", fg="white", font=("Arial", 12, "bold"), width=30, state="disabled")
        self.btn_prcd.grid(row=7, column=0, columnspan=4, pady=10)
        
        for v in [self.sv_w, self.sv_h, self.sv_mw, self.sv_mh]: 
            v.trace_add("write", self.calc_quote_price)

    def launch_multi_designer(self):
        try:
            curr_tw = float(self.sv_w.get() or 0) + float(self.sv_mw.get() or 0)
            curr_th = float(self.sv_h.get() or 0) + float(self.sv_mh.get() or 0)
        except:
            curr_tw, curr_th = 500, 400
            
        self.ui_instance.open_mount_designer(
            caller_width=curr_tw, 
            caller_height=curr_th,
            update_callback=lambda p, tw, th: [
                self.sv_mw.set(float(tw) - float(self.sv_w.get() or 0)),
                self.sv_mh.set(float(th) - float(self.sv_h.get() or 0)),
                self.calc_quote_price()
            ]
        )

    def toggle_mount_ui(self):
        if self.m_req.get():
            self.mf.grid(row=4, column=0, columnspan=4)
            self.btn_multi.grid(row=5, column=0, columnspan=4, pady=5)
        else:
            self.mf.grid_forget()
            self.btn_multi.grid_forget()
            self.ui_instance.current_mount_data = None
        self.calc_quote_price()

    def lookup_frame(self):
        cid = self.sv_fid.get().strip()
        if cid == "None" or not cid: return
        with sqlite3.connect(self.db_path) as conn:
            res = conn.execute("SELECT description, table_id FROM frame_catalog WHERE frame_id = ? COLLATE NOCASE", (cid,)).fetchone()
        if res:
            self.current_fdesc = res[0]
            self.current_fid = cid
            self.sv_title.set(f"Quote: {res[0]} ({cid})")
            self.current_tid = res[1]
            self.calc_quote_price()
        else:
            self.sv_title.set("ID Not Found")
            self.current_tid = None
            self.calc_quote_price()

    def calc_quote_price(self, *args):
        try:
            if not self.sv_w.get() or not self.sv_h.get(): return
            tw = float(self.sv_w.get() or 0) + float(self.sv_mw.get() or 0)
            th = float(self.sv_h.get() or 0) + float(self.sv_mh.get() or 0)
            if self.current_tid:
                with sqlite3.connect(self.db_path) as conn:
                    res = conn.execute("SELECT price_gbp FROM price_grids WHERE table_id=? AND (?>=min_width_mm AND ?<=max_width_mm) AND (?>=min_height_mm AND ?<=max_height_mm)", 
                                        (self.current_tid, tw, tw, th, th)).fetchone()
                if res:
                    extra_fee = 0.0
                    if self.ui_instance.current_mount_data:
                        qty = int(self.ui_instance.current_mount_data['rows']) * int(self.ui_instance.current_mount_data['cols'])
                        extra_fee = (qty - 1) * 2.0
                    final_p = res[0] + (20.0 if self.m_req.get() else 0.0) + extra_fee
                    self.rlbl.config(text=f"£{final_p:.2f}", fg="green")
                    self.btn_prcd.config(
                        state="normal", bg="#27ae60", 
                        command=lambda: [self.qwin.destroy(), self.open_order_form(res[0])]
                    )
                else:
                    self.rlbl.config(text="Frame too big", fg="red")
                    self.btn_prcd.config(state="disabled", bg="gray")
            else:
                self.rlbl.config(text="Enter valid Frame ID", fg="orange")
                self.btn_prcd.config(state="disabled", bg="gray")
        except: 
            pass

    def open_order_form(self, base_grid_price):
        self.owin = tk.Toplevel(self.parent)
        self.owin.title("Workshop Order Intake")
        self._center_window(self.owin, 800, 980)
        
        self.order_m_req = tk.BooleanVar(value=self.m_req.get())
        self.order_d_req = tk.BooleanVar()
        
        self.sv_iw = tk.StringVar(value=self.sv_w.get())
        self.sv_ih = tk.StringVar(value=self.sv_h.get())
        self.sv_order_mw = tk.StringVar(value=self.sv_mw.get())
        self.sv_order_mh = tk.StringVar(value=self.sv_mh.get())
        
        tk.Label(self.owin, text=f"Order: {self.current_fdesc}", font=("Arial", 14, "bold")).pack(pady=10)
        
        # Frame Inputs
        f1 = tk.LabelFrame(self.owin, text="Sizes (mm)", padx=10, pady=10); f1.pack(fill="x", padx=20, pady=5)
        tk.Label(f1, text="Item Width:").grid(row=0, column=0)
        tk.Entry(f1, textvariable=self.sv_iw, width=10).grid(row=0, column=1)
        tk.Label(f1, text="Item Height:").grid(row=0, column=2)
        tk.Entry(f1, textvariable=self.sv_ih, width=10).grid(row=0, column=3)
        
        f2 = tk.LabelFrame(self.owin, text="Specs", padx=10, pady=10); f2.pack(fill="x", padx=20, pady=5)
        tk.Label(f2, text="Frame Depth:").grid(row=0, column=0)
        self.ed = tk.Entry(f2, width=10); self.ed.grid(row=0, column=1)
        self.eo = ttk.Combobox(f2, values=["Portrait", "Landscape"], width=12); self.eo.set("Portrait"); self.eo.grid(row=0, column=3)
        
        # Mount Group Subpanel
        f3 = tk.LabelFrame(self.owin, text="Mount", padx=10, pady=10); f3.pack(fill="x", padx=20, pady=5)
        self.mi = tk.Frame(f3)
        tk.Checkbutton(f3, text="Mount?", variable=self.order_m_req, command=lambda: [self.mi.pack() if self.order_m_req.get() else self.mi.pack_forget(), self.update_summary(base_grid_price)]).pack(anchor="w")
        
        tk.Label(self.mi, text="Total Mount Width:").grid(row=0, column=0)
        tk.Entry(self.mi, textvariable=self.sv_order_mw, width=8).grid(row=0, column=1)
        tk.Label(self.mi, text="Total Mount Height:").grid(row=0, column=2)
        tk.Entry(self.mi, textvariable=self.sv_order_mh, width=8).grid(row=0, column=3)
        
        self.mc = ttk.Combobox(self.mi, values=["White", "Cream", "Black", "Grey"], width=10); self.mc.set("White"); self.mc.grid(row=0, column=4)
        if self.order_m_req.get(): self.mi.pack()
        
        # Customer Section
        f4 = tk.LabelFrame(self.owin, text="Customer", padx=10, pady=10); f4.pack(fill="x", padx=20, pady=5)
        tk.Label(f4, text="Name:").grid(row=0, column=0); self.en = tk.Entry(f4, width=30); self.en.grid(row=0, column=1)
        tk.Label(f4, text="Mobile Number:").grid(row=1, column=0); self.em = tk.Entry(f4, width=30); self.em.grid(row=1, column=1)
        
        self.af = tk.Frame(f4)
        tk.Checkbutton(f4, text="Home Delivery?", variable=self.order_d_req, command=lambda: [self.af.grid(row=4, column=0, columnspan=2) if self.order_d_req.get() else self.af.grid_forget(), self.update_summary(base_grid_price)]).grid(row=2, column=1)
        
        tk.Label(self.af, text="Address Line 1:").grid(row=0, column=0); self.ea1 = tk.Entry(self.af, width=50); self.ea1.grid(row=0, column=1)
        tk.Label(self.af, text="Address Line 2:").grid(row=1, column=0); self.ea2 = tk.Entry(self.af, width=50); self.ea2.grid(row=1, column=1)
        tk.Label(self.af, text="Address Line 3:").grid(row=2, column=0); self.ea3 = tk.Entry(self.af, width=50); self.ea3.grid(row=2, column=1)
        tk.Label(self.af, text="Postcode:").grid(row=3, column=0); self.epc = tk.Entry(self.af, width=20); self.epc.grid(row=3, column=1)
        
        # Commercial Display Totalizers
        f5 = tk.LabelFrame(self.owin, text="Breakdown", padx=10, pady=10); f5.pack(fill="x", padx=20, pady=10)
        self.sum_lbl = tk.Label(f5, text="", font=("Courier", 10, "bold"), justify="left"); self.sum_lbl.pack(side="left")
        
        pf = tk.Frame(f5); pf.pack(side="right")
        tk.Label(pf, text="Paid: £").grid(row=0, column=0); self.epaid = tk.Entry(pf, width=10); self.epaid.insert(0,"0.00"); self.epaid.grid(row=0, column=1)
        
        self.owin.lift()
        self.owin.focus_force()

        tk.Button(pf, text="Paid Full", command=lambda: [self.epaid.delete(0, tk.END), self.epaid.insert(0, f"{self.update_summary(base_grid_price)[0]:.2f}")]).grid(row=1, column=0, columnspan=2, pady=5)
        
        for v in [self.sv_iw, self.sv_ih, self.sv_order_mw, self.sv_order_mh]: 
            v.trace_add("write", lambda *a: self.update_summary(base_grid_price))
            
        self.update_summary(base_grid_price)
        
        tk.Button(self.owin, text="SAVE & PRINT PDF", bg="#27ae60", fg="white", font=("Arial", 12, "bold"), height=2, command=lambda: self.trigger_save(base_grid_price)).pack(pady=20)

    def update_summary(self, base_grid_price):
        if not self.owin.winfo_exists(): return
        try:
            iwv = float(self.sv_iw.get() or 0)
            ihv = float(self.sv_ih.get() or 0)
            mwv = float(self.sv_order_mw.get() or 0) if self.order_m_req.get() else 0
            mhv = float(self.sv_order_mh.get() or 0) if self.order_m_req.get() else 0
            tw, th = iwv + mwv, ihv + mhv
            current_base = float(base_grid_price)
            
            if self.current_tid and self.current_tid != "None":
                with sqlite3.connect(self.db_path) as conn:
                    res = conn.execute(
                        "SELECT price_gbp FROM price_grids WHERE table_id=? AND "
                        "(?>=min_width_mm AND ?<=max_width_mm) AND "
                        "(?>=min_height_mm AND ?<=max_height_mm)", 
                        (self.current_tid, tw, tw, th, th)    
                    ).fetchone()
                    if res: current_base = res[0]
                    
            mount_fee, delivery_fee = framing_math.calculate_extra_fees(
                mount_required=self.order_m_req.get(),
                current_mount_data=self.ui_instance.current_mount_data,
                delivery_required=self.order_d_req.get()
            )
            total_price = current_base + mount_fee + delivery_fee
            self.sum_lbl.config(text=(
                f"GLASS SIZE: {tw}x{th}mm\n"
                f"FRAME ({self.current_fid}): £{current_base:>7.2f}\n"
                f"MOUNT:      £{mount_fee:>7.2f}\n"
                f"DELIVERY:   £{delivery_fee:>7.2f}\n"
                f"----------------------\n"
                f"TOTAL:      £{total_price:>7.2f}"
            ))
            return total_price, current_base
        except Exception as e:
            self.sum_lbl.config(text="Error calculating price...")
            return 0.0, 0.0

    def trigger_save(self, base_grid_price):
        live_tot, live_base = self.update_summary(base_grid_price)
        try:
            cust_name = self.en.get().strip()
            cust_mob = self.em.get().strip()
            frame_depth = self.ed.get().strip()
            if not cust_name or not cust_mob or not frame_depth:
                messagebox.showerror("Error", "Name, Mobile, and Depth are required.")
                self.owin.lift(), self.owin.focus_force()
                return
            mwf = float(self.sv_order_mw.get() or 0) if self.order_m_req.get() else 0
            mhf = float(self.sv_order_mh.get() or 0) if self.order_m_req.get() else 0
            p_amt = float(self.epaid.get() or 0)
            tot = float(live_tot)
            if self.order_d_req.get():
                if p_amt < (tot - 0.01):
                    messagebox.showerror("Payment Required", f"Home Delivery requires payment in full.\n\nTotal: £{tot:.2f}\nPaid: £{p_amt:.2f}")
                    self.owin.lift(), self.owin.focus_force()
                    return
            mount_json = None
            if self.order_m_req.get() and self.ui_instance.current_mount_data:
                mount_json = json.dumps(self.ui_instance.current_mount_data)
                
            with sqlite3.connect(self.db_path) as conn:
                cur = conn.cursor()
                order_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
                cur.execute("""INSERT INTO orders (customer_name, mobile_number, frame_description, item_width, item_height, 
                    mount_required, mount_width, mount_height, mount_colour, orientation, depth_mm, delivery_required, 
                    addr_l1, addr_l2, addr_l3, postcode, total_price, amount_paid, order_date, mount_data) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                    (cust_name, cust_mob, self.current_fdesc, self.sv_iw.get(), self.sv_ih.get(), (1 if self.order_m_req.get() else 0), mwf, mhf, self.mc.get(), self.eo.get(), frame_depth, (1 if self.order_d_req.get() else 0), self.ea1.get(), self.ea2.get(), self.ea3.get(), self.epc.get(), tot, p_amt, order_time, mount_json))
                oid = cur.lastrowid
                
                pdf_data = {
                    "order_id": oid, "frame_id": self.current_fid, "customer_name": cust_name, "mobile_number": cust_mob, "frame_description": self.current_fdesc,
                    "item_width": self.sv_iw.get(), "item_height": self.sv_ih.get(), "mount_required": self.order_m_req.get(), "mount_width": mwf,
                    "mount_height": mhf, "mount_colour": self.mc.get(), "orientation": self.eo.get(), "depth_mm": frame_depth,
                    "delivery_required": self.order_d_req.get(), "addr_l1": self.ea1.get(), "addr_l2": self.ea2.get(), "addr_l3": self.ea3.get(), 
                    "postcode": self.epc.get(), "base_price": live_base, "total_price": live_tot, "amount_paid": p_amt, 
                    "order_date": order_time, "branch_name": self.branch_info[1], "branch_number": self.branch_info[0],
                    "complex_mount": self.ui_instance.current_mount_data,
                    "mount_total_w": float(self.sv_iw.get() or 0) + float(self.sv_order_mw.get() or 0),
                    "mount_total_h": float(self.sv_ih.get() or 0) + float(self.sv_order_mh.get() or 0),
                    "quantity": (self.ui_instance.current_mount_data.get('quantity', 1) if self.ui_instance.current_mount_data else 1)
                }
                path = pdf_creation.generate_order_pdf(pdf_data)
                conn.execute("UPDATE orders SET pdf_path=? WHERE order_id=?", (path, oid))
                conn.commit()
                log_details = f"New Order #{oid} created for {cust_name}. Total: £{tot:.2f}"
                database.log_action(self.branch_info[0], "ORDER_CREATED", log_details)
                
            self.owin.withdraw(); self.owin.destroy(); time.sleep(0.5); os.startfile(path)
            self.ui_instance.current_mount_data = None
        except Exception as e: 
            messagebox.showerror("Error", str(e))