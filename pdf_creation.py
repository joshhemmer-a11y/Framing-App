import os
import shutil
import sys
import datetime
import reportlab
import pandas as pd

from database import get_db_path, resource_path
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib import colors

def generate_order_pdf(data):
    # Setup Directories and File Paths
    exe_dir = os.path.dirname(sys.executable) if hasattr(sys, '_MEIPASS') else os.getcwd()
    orders_dir = os.path.join(exe_dir, "Orders")
    logo_path = resource_path("logo.png")
    if not os.path.exists(orders_dir): os.makedirs(orders_dir)
    
    filename = f"Order_{data['order_id']}_{data['customer_name'].replace(' ', '_')}.pdf"
    file_path = os.path.abspath(os.path.join(orders_dir, filename))
    
    # Set Page Size and Create Canvas
    c = canvas.Canvas(file_path, pagesize=A4)
    w, h = A4

    # Title and Header
    title_text = "MADE TO MEASURE - ORDER FORM"
    header_color = colors.black
    
    if "MOUNT ONLY" in str(data.get('customer_name', '')):
        title_text = " SPECIALIST MOUNT ORDER "
        header_color = colors.red

    # 4. Draw Logo
    if os.path.exists(logo_path):
        try:
            c.drawImage(logo_path, 400, h - 85, width=150, height=75, 
                        preserveAspectRatio=True, mask='auto')
        except Exception as e:
            print(f"PDF Logo Error: {e}")
    
    # 5. Draw Header
    c.setFillColor(header_color)
    c.setFont("Helvetica-Bold", 16)
    c.drawString(50, h-50, title_text)
    
    c.setFillColor(colors.black) 
    c.setFont("Helvetica-Bold", 10)
    c.drawString(50, h-75, f"STORE: {data['branch_name']} | ID: {data['branch_number']}")
    c.setFont("Helvetica", 10); c.drawString(50, h-100, f"Date: {data['order_date']}")
    c.drawRightString(w-50, h-100, f"Order ID: #{data['order_id']}")
    c.line(50, h-105, w-50, h-105)

    #  Customers Details
    curr_y = h-125
    c.setFont("Helvetica-Bold", 11); c.drawString(50, curr_y, "CUSTOMER DETAILS")
    curr_y -= 15
    c.setFont("Helvetica", 11)
    c.drawString(60, curr_y, f"Name: {data.get('customer_name', 'N/A')}")
    curr_y -= 15
    c.drawString(60, curr_y, f"Contact Number: {data.get('mobile_number', 'N/A')}")
    curr_y -= 25 

    # Workshop Specifications
    c.setFont("Helvetica-Bold", 12); c.drawString(50, curr_y, "WORKSHOP SPECIFICATIONS"); curr_y -= 20
    
    it_w, it_h = float(data.get('item_width') or 0), float(data.get('item_height') or 0)
    m_req = data.get('mount_required', False)
    m_w = float(data.get('mount_width') or 0) if m_req else 0
    m_h = float(data.get('mount_height') or 0) if m_req else 0
    total_w, total_h = float(data.get('mount_total_w') or (it_w + m_w)), float(data.get('mount_total_h') or (it_h + m_h))
    
    # Quantity and Orientation
    qty = int(data.get('quantity') or 1)
    orient = str(data.get('orientation', 'Portrait')).upper()

    c.setFillColor(colors.blue); c.setFont("Helvetica-Bold", 13)
    c.drawString(60, curr_y, f"TOTAL CUT SIZE (Glass/Back): {total_w}mm x {total_h}mm")
    curr_y -= 15
    c.drawString(60, curr_y, f"LAYOUT ORIENTATION: {orient}")
    c.setFillColor(colors.black); curr_y -= 25
    c.setFont("Helvetica", 10)
    
    f_id = data.get('frame_id', 'N/A')
    f_desc = data.get('frame_description', 'N/A')
    f_depth = data.get('depth_mm', 'N/A')

    c.drawString(60, curr_y, f"Item Size: {it_w}mm x {it_h}mm")
    c.drawString(60, curr_y - 15, f"Frame: {f_id} - {f_desc} | Depth: {f_depth}mm")
    curr_y -= 45

    if m_req:
        c.setFont("Helvetica-Bold", 11); c.drawString(50, curr_y, "MOUNT SPECIFICATION"); curr_y -= 15
        c.setFont("Helvetica", 10)
        c.drawString(60, curr_y, f"Colour: {data.get('mount_colour', 'Standard White')}")
        
        # --- Reference Drawing if complex ---
        if data.get('complex_mount'):
            c.setFillColor(colors.blue)
            c.drawString(60, curr_y - 15, "Layout: CUSTOM MULTI-APERTURE (See Drawing Page 2)")
            c.setFillColor(colors.black)
        else:
            c.drawString(60, curr_y - 15, f"Added Border: {m_w}mm (W) x {m_h}mm (H)")
        curr_y -= 40

    if data.get('delivery_required'):
        c.setFont("Helvetica-Bold", 11); c.drawString(50, curr_y, "DELIVERY ADDRESS"); curr_y -= 15
        c.setFont("Helvetica", 10)
        for line in ['addr_l1', 'addr_l2', 'addr_l3']:
            if data.get(line):
                c.drawString(60, curr_y, data[line]); curr_y -= 13
        c.drawString(60, curr_y, f"Postcode: {data.get('postcode', '')}"); curr_y -= 30

    # Payment Summary
    c.line(50, curr_y, w-50, curr_y); curr_y -= 20
    c.setFont("Helvetica-Bold", 12); c.drawString(50, curr_y, "PAYMENT SUMMARY"); curr_y -= 20
    c.setFont("Helvetica", 11)
    
    unit_p = float(data.get('total_price') or 0)
    line_total = unit_p * qty

    c.drawString(60, curr_y, "Unit Price:"); c.drawRightString(w-70, curr_y, f"£{unit_p:.2f}"); curr_y -= 15
    c.drawString(60, curr_y, "Quantity:"); c.drawRightString(w-70, curr_y, f"x{qty}"); curr_y -= 25
    
    c.setFont("Helvetica-Bold", 12)
    c.drawString(60, curr_y, "TOTAL ORDER VALUE:"); c.drawRightString(w-70, curr_y, f"£{line_total:.2f}"); curr_y -= 20
    c.drawString(60, curr_y, "AMOUNT PAID:"); c.drawRightString(w-70, curr_y, f"£{float(data.get('amount_paid') or 0):.2f}"); curr_y -= 20
    
    balance = line_total - float(data.get('amount_paid') or 0)
    if balance > 0.01:
        c.setFillColor(colors.red); c.drawString(60, curr_y, "OUTSTANDING BALANCE:"); c.drawRightString(w-70, curr_y, f"£{balance:.2f}")
    else:
        c.setFillColor(colors.green); c.drawRightString(w-70, curr_y, "PAID IN FULL")

    # Page 2 Complex Mount Drawing (if applicable)
    if data.get('complex_mount'):
        cm = data['complex_mount']
        c.showPage() 
        c.setFont("Helvetica-Bold", 14)
        c.drawString(50, h - 50, f"WORKSHOP CUT SHEET - ORDER #{data['order_id']}")
        
        # 1. Dimensions and Prep
        tw, th = float(cm['mount_total_w']), float(cm['mount_total_h'])
        rows, cols = int(cm['rows']), int(cm['cols'])
        aw, ah = float(cm['ap_w']), float(cm['ap_h'])
        bridge, offset = float(cm['bridge']), float(cm['offset'])
        
        # Draw Area Constants
        draw_w, draw_h = 380, 380
        ox, oy = 110, h - 520   
        scale = min(draw_w/tw, draw_h/th)
        
        # Math for centering
        grid_w = (cols * aw) + ((cols - 1) * bridge)
        grid_h = (rows * ah) + ((rows - 1) * bridge)
        margin_x = (tw - grid_w) / 2
        margin_y_bottom = ((th - grid_h) / 2) + (offset / 2) # The weighted margin
        margin_y_top = th - grid_h - margin_y_bottom

        # 2. Draw External Board
        c.setStrokeColor(colors.black)
        c.setLineWidth(1.2)
        c.rect(ox, oy, tw*scale, th*scale, stroke=1, fill=0)

        # 3. External Dimension Lines 
        c.setLineWidth(0.5)
        c.setFont("Helvetica-Bold", 9)
        
        # Width Dimension (Top)
        c.line(ox, oy + (th*scale) + 10, ox + (tw*scale), oy + (th*scale) + 10) # Horizontal line
        c.line(ox, oy + (th*scale) + 8, ox, oy + (th*scale) + 12) # Left tick
        c.line(ox + (tw*scale), oy + (th*scale) + 8, ox + (tw*scale), oy + (th*scale) + 12) # Right tick
        c.drawCentredString(ox + (tw*scale/2), oy + (th*scale) + 18, f"TOTAL WIDTH: {tw}mm")

        # Height Dimension (Left)
        c.saveState()
        c.translate(ox - 25, oy + (th*scale/2))
        c.rotate(90)
        c.drawCentredString(0, 0, f"TOTAL HEIGHT: {th}mm")
        c.restoreState()
        c.line(ox - 15, oy, ox - 15, oy + (th*scale)) # Vertical line
        c.line(ox - 17, oy, ox - 13, oy) # Bottom tick
        c.line(ox - 17, oy + (th*scale), ox - 13, oy + (th*scale)) # Top tick

        # 4. Draw Apertures
        c.setStrokeColor(colors.blue)
        c.setLineWidth(0.7)
        for r in range(rows):
            for col in range(cols):
                # Calculate coordinates
                curr_x = ox + (margin_x + (col * (aw + bridge))) * scale
                curr_y = oy + (margin_y_bottom + (r * (ah + bridge))) * scale
                c.rect(curr_x, curr_y, aw*scale, ah*scale, stroke=1, fill=0)
                
                # Tag the first aperture only to keep it clean
                if r == rows-1 and col == 0:
                    c.setFont("Helvetica-Bold", 7)
                    c.drawCentredString(curr_x + (aw*scale/2), curr_y + (ah*scale/2) - 3, f"{aw} x {ah}")

        # 5. Internal Dimension Notes (Bridges/Margins)
        c.setStrokeColor(colors.black)
        c.setFont("Helvetica", 8)
        
        c.drawString(ox + (tw*scale) + 10, oy + (margin_y_bottom*scale/2), f"Bottom: {margin_y_bottom:.1f}mm")
        c.drawString(ox + (tw*scale) + 10, oy + (th*scale) - (margin_y_top*scale/2), f"Top: {margin_y_top:.1f}mm")

        # Summary
        c.setDash([]) # Reset line style
        c.setFont("Helvetica-Bold", 11)
        c.drawString(50, oy - 80, "TECHNICAL SPECIFICATIONS (Aperture Layout)")
        
        c.setFont("Helvetica", 10)
        notes = [
            f"Configuration:   {cols} Columns x {rows} Rows",
            f"Aperture Size:   {aw}mm (W) x {ah}mm (H)",
            f"Internal Bridge: {bridge}mm (Gap between apertures)",
            f"Bottom Weight:   {offset}mm (Vertical offset)",
            f"Side Margins:    {margin_x:.1f}mm",
            f"Top Margin:      {margin_y_top:.1f}mm",
            f"Bottom Margin:   {margin_y_bottom:.1f}mm"
        ]
        
        ny = oy - 105
        for note in notes:
            c.drawString(60, ny, f"- {note}")
            ny -= 15

    c.save()
    return file_path