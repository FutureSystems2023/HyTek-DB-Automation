import config
import json
import modifyDB
import os
import shutil
import tkinter as tk
from tkinter import filedialog, messagebox
import uploadDB


try:
    # Create a Tkinter GUI window for selecting the destination directory
    app = tk.Tk()
    config.logging.info("Program Start")
    app.withdraw()  # Hide the main window
except Exception as e:
    config.logging.error("Unable to start program")
    exit()

# By default, destination directory of modified database will be in uploads subfolder of program's root directory
destination_directory = os.path.join(os.getcwd(), config.config["DEFAULT"]["UPLOAD_DIR"])

# Define path of HyTek Database file
source_database_file = config.config["DEFAULT"]["DB_PATH"]
destination_database_file = os.path.join(f"{destination_directory}", "Modified_DB.MDB")

# Check if the source database file exists
while not os.path.exists(source_database_file):
    config.logging.error(f"Source Database file ({source_database_file}) does not exist.")
    messagebox.showerror("Error", f"HyTek Database file not found. Unable to locate path '{source_database_file}'. Please define it manually in file dialog.")
    filetypes = [('Microsoft Access', '*.mdb *.accdb')]
    source_database_file = filedialog.askopenfilename(filetypes=filetypes, title="Select HyTek Database File")
    if not source_database_file:
        config.logging.debug("User cancelled file dialog")
        exit()
    else:
        config.logging.debug(f"User defined database source path as {source_database_file}")

# Copy the modified database to the destination
config.logging.debug(f"Copying database file from {source_database_file} to {destination_database_file}")
shutil.copyfile(source_database_file, destination_database_file)

# Retrieving stroke id mapping from json. If fail, exit.
config.logging.info("Loading stroke id mapping json file...")
try:
    f = open(config.config["DEFAULT"]["STROKE_ID_MAPPING_JSON"])
    stroke_id_mapping = json.load(f)
except Exception as e:
    messagebox.showerror("Error", "Failed to load stroke id mapping json file ({}). Check if path exists.".format(config.config["DEFAULT"]['STROKE_ID_MAPPING_JSON']))
    config.logging.error("Failed to load stroke id mapping json file ({})".format(config.config["DEFAULT"]['STROKE_ID_MAPPING_JSON']))
    exit()

try:
    # Database Operations
    config.logging.info("Commencing database operations...")
    password = config.config["DEFAULT"]["DB_PASS"]
    ath_table_name = "Athlete"
    column_to_remove = "ID_NO"
    ath_info_table_name = "AthInfo"

    db_operations = modifyDB.main(destination_database_file, password, ath_table_name, column_to_remove, ath_info_table_name, stroke_id_mapping)

    # Show a pop-up message indicating successful completion. Else, dsiplay error.
    if db_operations["status"] == True:
        messagebox.showinfo("Success", f"Modified database file saved to {destination_database_file}")
    else:
        messagebox.showerror("Error", f"An error occurred during database operations: {str(db_operations['error'])}")

    # Upload Operations
    config.logging.info("Commencing upload to Google Drive using Drive API...")
    upload_operations = uploadDB.main(destination_database_file)
    # Show a pop-up message indicating successful completion. Else, dsiplay error.
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