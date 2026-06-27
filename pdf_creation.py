import os
import sys
import logging
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib import colors

logger = logging.getLogger("MadeToMeasure")

def generate_order_pdf(data: dict) -> str:
    """Generates a professional 1 or 2-page workshop order blueprint PDF."""
    
    # 1. Environment & Path Resolution
    exe_dir = os.path.dirname(sys.executable) if hasattr(sys, '_MEIPASS') else os.getcwd()
    orders_dir = os.path.join(exe_dir, "Orders")
    os.makedirs(orders_dir, exist_ok=True)
    
    # Extract logo path safely using our centralized mapping function
    from database import resource_path
    logo_path = resource_path("logo.png")
    
    safe_customer_name = str(data.get('customer_name', 'Guest')).replace(' ', '_')
    filename = f"Order_{data.get('order_id', '0000')}_{safe_customer_name}.pdf"
    file_path = os.path.abspath(os.path.join(orders_dir, filename))
    
    # 2. Canvas Setup
    c = canvas.Canvas(file_path, pagesize=A4)
    w, h = A4

    # Determine visual scheme based on customer category flags
    title_text = "MADE TO MEASURE - ORDER FORM"
    header_color = colors.black
    
    if "MOUNT ONLY" in str(data.get('customer_name', '')).upper():
        title_text = "SPECIALIST MOUNT ORDER"
        header_color = colors.red

    # 3. Header & Brand Assets
    if os.path.exists(logo_path):
        try:
            c.drawImage(logo_path, 400, h - 85, width=150, height=75, preserveAspectRatio=True, mask='auto')
        except Exception as e:
            logger.error(f"Failed to render branding asset to PDF: {e}")
    
    c.setFillColor(header_color)
    c.setFont("Helvetica-Bold", 16)
    c.drawString(50, h - 50, title_text)
    
    c.setFillColor(colors.black) 
    c.setFont("Helvetica-Bold", 10)
    c.drawString(50, h - 75, f"STORE: {data.get('branch_name', 'Main')} | ID: {data.get('branch_number', '1')}")
    c.setFont("Helvetica", 10)
    c.drawString(50, h - 100, f"Date: {data.get('order_date', 'N/A')}")
    c.drawRightString(w - 50, h - 100, f"Order ID: #{data.get('order_id', '0000')}")
    c.line(50, h - 105, w - 50, h - 105)

    # 4. Customer Metadata Section
    curr_y = h - 125
    c.setFont("Helvetica-Bold", 11)
    c.drawString(50, curr_y, "CUSTOMER DETAILS")
    
    c.setFont("Helvetica", 11)
    curr_y -= 15
    c.drawString(60, curr_y, f"Name: {data.get('customer_name', 'N/A')}")
    curr_y -= 15
    c.drawString(60, curr_y, f"Contact Number: {data.get('mobile_number', 'N/A')}")
    curr_y -= 25 

    # 5. Workshop Physical Target Specs
    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, curr_y, "WORKSHOP SPECIFICATIONS")
    curr_y -= 20
    
    item_w = float(data.get('item_width') or 0.0)
    item_h = float(data.get('item_height') or 0.0)
    mount_required = data.get('mount_required', False)
    
    m_w = float(data.get('mount_width') or 0.0) if mount_required else 0.0
    m_h = float(data.get('mount_height') or 0.0) if mount_required else 0.0
    
    total_w = float(data.get('mount_total_w') or (item_w + m_w))
    total_h = float(data.get('mount_total_h') or (item_h + m_h))
    qty = int(data.get('quantity') or 1)
    orientation = str(data.get('orientation', 'Portrait')).upper()

    c.setFillColor(colors.blue)
    c.setFont("Helvetica-Bold", 13)
    c.drawString(60, curr_y, f"TOTAL CUT SIZE (Glass/Back): {total_w}mm x {total_h}mm")
    curr_y -= 15
    c.drawString(60, curr_y, f"LAYOUT ORIENTATION: {orientation}")
    
    c.setFillColor(colors.black)
    curr_y -= 25
    c.setFont("Helvetica", 10)
    c.drawString(60, curr_y, f"Item Size: {item_w}mm x {item_h}mm")
    
    frame_str = f"Frame: {data.get('frame_id', 'N/A')} - {data.get('frame_description', 'N/A')} | Depth: {data.get('depth_mm', 'N/A')}mm"
    c.drawString(60, curr_y - 15, frame_str)
    curr_y -= 45

    if mount_required:
        c.setFont("Helvetica-Bold", 11)
        c.drawString(50, curr_y, "MOUNT SPECIFICATION")
        curr_y -= 15
        
        c.setFont("Helvetica", 10)
        c.drawString(60, curr_y, f"Colour: {data.get('mount_colour', 'Standard White')}")
        
        if data.get('complex_mount'):
            c.setFillColor(colors.blue)
            c.drawString(60, curr_y - 15, "Layout: CUSTOM MULTI-APERTURE (See Drawing Page 2)")
            c.setFillColor(colors.black)
        else:
            c.drawString(60, curr_y - 15, f"Added Border: {m_w}mm (W) x {m_h}mm (H)")
        curr_y -= 40

    if data.get('delivery_required'):
        c.setFont("Helvetica-Bold", 11)
        c.drawString(50, curr_y, "DELIVERY ADDRESS")
        curr_y -= 15
        
        c.setFont("Helvetica", 10)
        for field in ['addr_l1', 'addr_l2', 'addr_l3']:
            if data.get(field):
                c.drawString(60, curr_y, str(data[field]))
                curr_y -= 13
        c.drawString(60, curr_y, f"Postcode: {data.get('postcode', '')}")
        curr_y -= 30

    # 6. Commercial Financial Summary
    c.line(50, curr_y, w - 50, curr_y)
    curr_y -= 20
    
    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, curr_y, "PAYMENT SUMMARY")
    curr_y -= 20
    
    c.setFont("Helvetica", 11)
    unit_price = float(data.get('total_price') or 0.0)
    line_total = unit_price * qty

    c.drawString(60, curr_y, "Unit Price:")
    c.drawRightString(w - 70, curr_y, f"£{unit_price:.2f}")
    curr_y -= 15
    c.drawString(60, curr_y, "Quantity:")
    c.drawRightString(w - 70, curr_y, f"x{qty}")
    curr_y -= 25
    
    c.setFont("Helvetica-Bold", 12)
    c.drawString(60, curr_y, "TOTAL ORDER VALUE:")
    c.drawRightString(w - 70, curr_y, f"£{line_total:.2f}")
    curr_y -= 20
    
    amount_paid = float(data.get('amount_paid') or 0.0)
    c.drawString(60, curr_y, "AMOUNT PAID:")
    c.drawRightString(w - 70, curr_y, f"£{amount_paid:.2f}")
    curr_y -= 20
    
    balance = line_total - amount_paid
    if balance > 0.01:
        c.setFillColor(colors.red)
        c.drawString(60, curr_y, "OUTSTANDING BALANCE:")
        c.drawRightString(w - 70, curr_y, f"£{balance:.2f}")
    else:
        c.setFillColor(colors.green)
        c.drawRightString(w - 70, curr_y, "PAID IN FULL")

    # 7. Page 2: Schematic Mount Blueprint Rendering Engine
    if data.get('complex_mount'):
        cm = data['complex_mount']
        c.showPage() 
        
        c.setFont("Helvetica-Bold", 14)
        c.setFillColor(colors.black)
        c.drawString(50, h - 50, f"WORKSHOP CUT SHEET - ORDER #{data.get('order_id', '0000')}")
        
        # Dimensions Setup
        tw, th = float(cm.get('mount_total_w', 0)), float(cm.get('mount_total_h', 0))
        rows, cols = int(cm.get('rows', 1)), int(cm.get('cols', 1))
        aw, ah = float(cm.get('ap_w', 0)), float(cm.get('ap_h', 0))
        bridge, offset = float(cm.get('bridge', 0)), float(cm.get('offset', 0))
        
        # Scale Boundary Configuration
        draw_w, draw_h = 380.0, 380.0
        ox, oy = 110.0, h - 520.0   
        scale = min(draw_w / tw, draw_h / th)
        
        # Centering Geometry calculations
        grid_w = (cols * aw) + ((cols - 1) * bridge)
        grid_h = (rows * ah) + ((rows - 1) * bridge)
        margin_x = (tw - grid_w) / 2
        margin_y_bottom = ((th - grid_h) / 2) + (offset / 2)
        margin_y_top = th - grid_h - margin_y_bottom

        # Render Main Outer Matrix Frame
        c.setStrokeColor(colors.black)
        c.setLineWidth(1.2)
        c.rect(ox, oy, tw * scale, th * scale, stroke=1, fill=0)

        # Drawing Dimension Notation Ticks
        c.setLineWidth(0.5)
        c.setFont("Helvetica-Bold", 9)
        
        # Render Width Rule Lines
        c.line(ox, oy + (th * scale) + 10, ox + (tw * scale), oy + (th * scale) + 10)
        c.line(ox, oy + (th * scale) + 8, ox, oy + (th * scale) + 12)
        c.line(ox + (tw * scale), oy + (th * scale) + 8, ox + (tw * scale), oy + (th * scale) + 12)
        c.drawCentredString(ox + (tw * scale / 2), oy + (th * scale) + 18, f"TOTAL WIDTH: {tw}mm")

        # Render Height Rule Lines (Rotated Label Context)
        c.saveState()
        c.translate(ox - 25, oy + (th * scale / 2))
        c.rotate(90)
        c.drawCentredString(0, 0, f"TOTAL HEIGHT: {th}mm")
        c.restoreState()
        
        c.line(ox - 15, oy, ox - 15, oy + (th * scale))
        c.line(ox - 17, oy, ox - 13, oy)
        c.line(ox - 17, oy + (th * scale), ox - 13, oy + (th * scale))

        # Iterative Aperture Rendering Sub-Engine
        c.setStrokeColor(colors.blue)
        c.setLineWidth(0.7)
        for r in range(rows):
            for col in range(cols):
                curr_x = ox + (margin_x + (col * (aw + bridge))) * scale
                curr_y = oy + (margin_y_bottom + (r * (ah + bridge))) * scale
                c.rect(curr_x, curr_y, aw * scale, ah * scale, stroke=1, fill=0)
                
                # Annotate dimension blueprint spec to origin block only
                if r == rows - 1 and col == 0:
                    c.setFont("Helvetica-Bold", 7)
                    c.drawCentredString(curr_x + (aw * scale / 2), curr_y + (ah * scale / 2) - 3, f"{aw} x {ah}")

        # Summary Annotation Sidebar Notes
        c.setStrokeColor(colors.black)
        c.setFont("Helvetica", 8)
        c.drawString(ox + (tw * scale) + 10, oy + (margin_y_bottom * scale / 2), f"Bottom: {margin_y_bottom:.1f}mm")
        c.drawString(ox + (tw * scale) + 10, oy + (th * scale) - (margin_y_top * scale / 2), f"Top: {margin_y_top:.1f}mm")

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