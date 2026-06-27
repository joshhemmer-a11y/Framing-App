def calculate_order_dimensions(item_width, item_height, mount_required=False, mount_width=0, mount_height=0):

   #NOTE: The mount width and height is not doubled here because the mount dimensions are already the total size of the mount.

  try:
      item_w = float(item_width or 0.0)
      item_h = float(item_height or 0.0)

      if mount_required:
         return item_w + float(mount_width or 0.0), item_h + float(mount_height or 0.0)
      
      return item_w, item_h
  except (ValueError, TypeError) as e:
      print(f"Error calculating order dimensions: {e}")
      return 0.0, 0.0

def calculate_extra_fees(mount_required, current_mount_data, delivery_required, base_mount_price: float = 20.0, extra_aperture_fee: float = 2.0) -> tuple:

   mount_fee = 0.0
   delivery_fee = 5.0 if delivery_required else 0.0

   if mount_required:
      total_apertures = 1
      if current_mount_data and 'rows' in current_mount_data and 'cols' in current_mount_data:
         try:
            rows = int(current_mount_data['rows'] or 1)
            cols = int(current_mount_data['cols'] or 1)
            total_apertures = rows * cols
         except (ValueError, TypeError) as e:
            print(f"Error calculating total apertures: {e}")
            total_apertures = 1
   
      extra_apertures = max(0, total_apertures - 1)
      mount_fee = base_mount_price + (extra_apertures * extra_aperture_fee)

   return mount_fee, delivery_fee