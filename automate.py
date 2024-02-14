import config
import json
import modifyDB
import os
import shutil
import sftp
import uploadDB


def main():
    # Connect to hytek SFTP server to download zipped database file
    config.logging.info("Commencing SFTP operations...")
    print("Commencing SFTP operations...")
    sftp_res = sftp.main()
    if sftp_res.get('status') == False:
        print("Aborting automation...")
        return False

    # Unzip zipped database file
    try:
        destination_db_zipped_file = sftp_res.get('db_file_path')
        upload_dir = os.path.join(os.getcwd(), 'uploads')
        print(f"Unzipping zipped database file {destination_db_zipped_file} to {upload_dir}...", end=" ")
        shutil.unpack_archive(destination_db_zipped_file, upload_dir)
        destination_db_file = os.path.join(upload_dir, 'Virtual SNAG_TMNet.MDB')
        print("Success!")
    except Exception as e:
        print("Failed!")
        print(e)

    # Retrieving stroke id mapping from json. If fail, exit. Stroke id mapping will be used for database operations
    try:
        f = open(config.config["DEFAULT"]["STROKE_ID_MAPPING_JSON"])
        stroke_id_mapping = json.load(f)
    except Exception as e:
        print("Failed to load stroke id mapping json file ({})".format(config.config["DEFAULT"]['STROKE_ID_MAPPING_JSON']))
        print(e)

    # Database Operations
    config.logging.info("Commencing database operations...")
    print("Commencing database operations...")
    password = config.config["DEFAULT"]["DB_PASS"]
    ath_table_name = "Athlete"
    column_to_remove = "ID_NO"
    ath_info_table_name = "AthInfo"

    db_operations = modifyDB.main(destination_db_file, password, ath_table_name, column_to_remove, ath_info_table_name, stroke_id_mapping)

    # Check if database operations are successful
    if db_operations["status"] == True:
        print("Success: ", f"Modified database file saved to {destination_db_file}")
    else:
        print("Error:", f"An error occurred during database operations: {str(db_operations['error'])}")

    # Upload Operations
    config.logging.info("Commencing upload to Google Drive using Drive API...")
    print("Commencing upload to Google Drive using Drive API...")
    upload_operations = uploadDB.main(destination_db_file)
    if upload_operations["status"] == True:
        print("Success: Upload successfully completed!")
    else:
        print(f"Error: An error occurred during upload operations: {str(upload_operations['error'])}")

    config.logging.info("Automation End")
    return

if __name__ == "__main__":
    main()