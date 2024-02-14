import config
import json
import modifyDB
import os
import shutil
import sys
import tkinter as tk
import uploadDB

from tkinter import filedialog, messagebox, ttk


try:
    # Create a Tkinter GUI window for selecting the destination directory
    app = tk.Tk()
    # app.withdraw()  # Hide the main window
    config.logging.info("Program Start")
    app.geometry('350x120')
    app.iconbitmap("app.ico")
    app.title('HyTek Database Automation')
    app.grid()

    # Tkinter progressbar to show loading to users
    pb = ttk.Progressbar(
        app,
        orient='horizontal',
        mode='indeterminate',
        length=330
    )
    pb.grid(column=0, row=0, columnspan=2, padx=10, pady=20)
    app_status_lbl = ttk.Label(app, text="Program starting...")
    app_status_lbl.grid(column=0, row=1, columnspan=2)
    pb.start()
except Exception as e:
    config.logging.error(f"Unable to start program: {e}")
    sys.exit()

# By default, destination directory of modified database will be in uploads subfolder of program's root directory
destination_directory = os.path.join(os.getcwd(), config.config["DEFAULT"]["UPLOAD_DIR"])

# Define path of HyTek Database file
source_db_file = config.config["DEFAULT"]["DB_PATH"]
destination_db_file = os.path.join(f"{destination_directory}", "Modified_DB.MDB")

# Check if the source database file exists
while not os.path.exists(source_db_file):
    config.logging.error(f"Source Database file ({source_db_file}) does not exist.")
    messagebox.showerror("Error", f"HyTek Database file not found. Unable to locate path '{source_db_file}'. Please define it manually in file dialog.")
    filetypes = [('Microsoft Access', '*.mdb *.accdb')]
    source_db_file = filedialog.askopenfilename(filetypes=filetypes, title="Select HyTek Database File")
    if not source_db_file:
        config.logging.debug("User cancelled file dialog")
        sys.exit()
    else:
        config.logging.debug(f"User defined database source path as {source_db_file}")

# Copy the modified database to the destination
config.logging.debug(f"Copying database file from {source_db_file} to {destination_db_file}")
shutil.copyfile(source_db_file, destination_db_file)

# Retrieving stroke id mapping from json. If fail, exit.
config.logging.info("Loading stroke id mapping json file...")
try:
    f = open(config.config["DEFAULT"]["STROKE_ID_MAPPING_JSON"])
    stroke_id_mapping = json.load(f)
except Exception as e:
    messagebox.showerror("Error", "Failed to load stroke id mapping json file ({}). Check if path exists.".format(config.config["DEFAULT"]['STROKE_ID_MAPPING_JSON']))
    config.logging.error("Failed to load stroke id mapping json file ({})".format(config.config["DEFAULT"]['STROKE_ID_MAPPING_JSON']))
    sys.exit()

try:
    # Database Operations
    config.logging.info("Commencing database operations...")
    app_status_lbl["text"] = "Commencing database operations..."
    app.update()
    password = config.config["DEFAULT"]["DB_PASS"]
    ath_table_name = "Athlete"
    column_to_remove = "ID_NO"
    ath_info_table_name = "AthInfo"

    db_operations = modifyDB.main(destination_db_file, password, ath_table_name, column_to_remove, ath_info_table_name, stroke_id_mapping)

    # Show a pop-up message indicating successful completion. Else, dsiplay error.
    if db_operations["status"] == True:
        messagebox.showinfo("Success", f"Modified database file saved to {destination_db_file}")
    else:
        messagebox.showerror("Error", f"An error occurred during database operations: {str(db_operations['error'])}")

    # Upload Operations
    config.logging.info("Commencing upload to Google Drive using Drive API...")
    app_status_lbl["text"] = "Uploading to Google Drive using Drive API..."
    app.update()
    upload_operations = uploadDB.main(destination_db_file, app_status_lbl)
    # Show a pop-up message indicating successful completion. Else, display error.
    if upload_operations["status"] == True:
        messagebox.showinfo("Success", f"Upload successfully completed!")
    else:
        messagebox.showerror("Error", f"An error occurred during upload operations: {str(upload_operations['error'])}")

except Exception as e:
    config.logging.error(f"An error has occured: {e}")
    messagebox.showerror("Error", f"An error occurred: {e}")

finally:
    app.destroy()  # Close the GUI window
    config.logging.info("Program End")