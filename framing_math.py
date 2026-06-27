def calculate_order_dimensions(item_width, item_height, mount_required=False, mount_width=0, mount_height=0):
   
   iwv = float(item_width or 0)
   ihv = float(item_height or 0)
   mwv = float(mount_width or 0) if mount_required else 0
   mhv = float(mount_height or 0) if mount_required else 0
   return iwv + mwv, ihv + mhv

def calculate_extra_fees(mount_required, current_mount_data, delivery_required):
   extra_mount_fee = 0.0
   if mount_required and current_mount_data:
      qty = int(current_mount_data['rows']) * int(current_mount_data['cols'])
      extra_mount_fee = (qty-1) * 2.0

   mount_fee = 20.0 + extra_mount_fee if mount_required else 0.0
   delivery_fee = 5.0 if delivery_required else 0.0
   return mount_fee, delivery_fee
    