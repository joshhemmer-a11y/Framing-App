def calculate_mount_geometry(orientation, raw_aw, raw_ah, raw_tw, raw_th, raw_rows, raw_cols, raw_br, raw_off):
    #Layout calculations based on orientation and provided dimensions
    if orientation == "Portrait":
        aw, ah = raw_ah, raw_aw
        tw, th = raw_th, raw_tw
        d_rows, d_cols = raw_cols, raw_rows
    else:
        aw, ah = raw_aw, raw_ah
        tw, th = raw_tw, raw_th
        d_rows, d_cols = raw_rows, raw_cols

    grid_w = (d_cols * aw) + ((d_cols - 1) * raw_br)
    grid_h = (d_rows * ah) + ((d_rows - 1) * raw_br)
    
    start_x = (tw - grid_w) / 2
    start_y = ((th - grid_h) / 2) - (raw_off / 2)

    geometry_results = {
        "aw": aw,
        "ah": ah,
        "tw": tw,
        "th": th,
        "d_rows": d_rows,
        "d_cols": d_cols,
        "grid_w": grid_w,
        "grid_h": grid_h,
        "start_x": start_x,
        "start_y": start_y
    }
    
    return geometry_results