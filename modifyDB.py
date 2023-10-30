import config
import os
import pyodbc

def main(destination_database_file, password, ath_table_name, column_to_remove, ath_info_table_name, stroke_id_mapping):
    try:
        # Establish a connection to the Access database
        destination_conn = pyodbc.connect(r'DRIVER={Microsoft Access Driver (*.mdb, *.accdb)};DBQ=' + destination_database_file + ';PWD=' + password)

        # Create a cursor for the destination connection
        destination_cursor = destination_conn.cursor()

        # Create a new table without the unwanted column
        config.logging.debug(f"Copying {ath_table_name} table and dropping {column_to_remove} column...")
        destination_cursor.execute(f"SELECT * INTO {ath_table_name}New FROM {ath_table_name}")
        destination_cursor.execute(f"ALTER TABLE {ath_table_name}New DROP COLUMN {column_to_remove}")

        # Drop the old table and duplicating new table with old table's name. Renaming directly is not possible.
        config.logging.debug(f"Dropping old {ath_table_name} table...")
        destination_cursor.execute(f"DROP TABLE {ath_table_name}")
        config.logging.debug(f"Duplicating {ath_table_name}New table under the name {ath_table_name}...")
        destination_cursor.execute(f"SELECT * INTO {ath_table_name} FROM {ath_table_name}New")
        config.logging.debug(f"Dropping {ath_table_name}New table...")
        destination_cursor.execute(f"DROP TABLE {ath_table_name}New")

        # Drop the 'AthInfo' table 
        config.logging.debug(f"Dropping {ath_info_table_name} table...")
        destination_cursor.execute(f"DROP TABLE {ath_info_table_name}")

        # Add the new column to the 'StrokeCategory' table 
        config.logging.debug("Adding stroke id column to StrokeCategory table and mapping it with stroke id json...")
        destination_cursor.execute(f"ALTER TABLE StrokeCategory ADD COLUMN stroke_id INT")
        for stroke_name, stroke_id in stroke_id_mapping.items():
            destination_cursor.execute(f"UPDATE StrokeCategory SET stroke_id = {stroke_id} WHERE stroke_name = '{stroke_name}'")

        # Commit changes and close connections
        config.logging.debug(f"Commiting database changes...")
        destination_conn.commit()
        destination_cursor.close()
        destination_conn.close()
        config.logging.info(f"Success! Modified database file saved to {destination_database_file}")
        return {"status": True}

    except Exception as e:
        config.logging.error(f"An error occurred: {str(e)}")
        # Delete the copied database if an error occurs
        if os.path.exists(destination_database_file):
            os.remove(destination_database_file)
        return {"status": False, "error": "Something went wrong."}