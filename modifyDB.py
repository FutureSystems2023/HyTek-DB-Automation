import config
import os
import pyodbc


def main(target_db_file, password, ath_table_name, column_to_remove, ath_info_table_name, stroke_id_mapping):
    """Modify Database by connecting to target db, dropping NRIC column, deleting athInfo table, and map stroke category IDs.

    Args:
        target_db_file (str): Filepath of target database to be modified
        password (str): Password to conenct to target database
        ath_table_name (str): Name of athlete table
        column_to_remove (str): Name of column to be removed from athlete table
        ath_info_table_name (str): Name of athlete info table
        stroke_id_mapping (dict): Dictionary object that is the json for defining and mapping stroke category IDs

    Returns:
        dict: Dictionary object that defines status of database operations
    """
    try:
        # Establish a connection to the Access database
        target_conn = pyodbc.connect(r'DRIVER={Microsoft Access Driver (*.mdb, *.accdb)};DBQ=' + target_db_file + ';PWD=' + password)

        # Create a cursor for the destination connection
        target_cursor = target_conn.cursor()

        # Create a new table without the unwanted column
        config.logging.debug(f"Copying {ath_table_name} table and dropping {column_to_remove} column...")
        target_cursor.execute(f"SELECT * INTO {ath_table_name}New FROM {ath_table_name}")
        target_cursor.execute(f"ALTER TABLE {ath_table_name}New DROP COLUMN {column_to_remove}")

        # Drop the old table and duplicating new table with old table's name. Renaming directly is not possible.
        config.logging.debug(f"Dropping old {ath_table_name} table...")
        target_cursor.execute(f"DROP TABLE {ath_table_name}")
        config.logging.debug(f"Duplicating {ath_table_name}New table under the name {ath_table_name}...")
        target_cursor.execute(f"SELECT * INTO {ath_table_name} FROM {ath_table_name}New")
        config.logging.debug(f"Dropping {ath_table_name}New table...")
        target_cursor.execute(f"DROP TABLE {ath_table_name}New")

        # Drop the 'AthInfo' table 
        config.logging.debug(f"Dropping {ath_info_table_name} table...")
        target_cursor.execute(f"DROP TABLE {ath_info_table_name}")

        # Add the new column to the 'StrokeCategory' table 
        config.logging.debug("Adding stroke id column to StrokeCategory table and mapping it with stroke id json...")
        target_cursor.execute(f"ALTER TABLE StrokeCategory ADD COLUMN stroke_id INT")
        for stroke_name, stroke_id in stroke_id_mapping.items():
            target_cursor.execute(f"UPDATE StrokeCategory SET stroke_id = {stroke_id} WHERE stroke_name = '{stroke_name}'")

        # Commit changes and close connections
        config.logging.debug(f"Commiting database changes...")
        target_conn.commit()
        target_cursor.close()
        target_conn.close()
        config.logging.info(f"Success! Modified database file saved to {target_db_file}")
        return {"status": True}

    except Exception as e:
        config.logging.error(f"An error occurred: {str(e)}")
        # Delete the copied database if an error occurs
        if os.path.exists(target_db_file):
            os.remove(target_db_file)
        return {"status": False, "error": "Something went wrong."}