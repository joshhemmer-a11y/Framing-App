import tkinter as tk
import database
from ui_layout import FramingAppUI

def main():
    database.sync_database() 
    database.run_migrations()
    database.setup_pricing_table()

    root = tk.Tk()
    app = FramingAppUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()