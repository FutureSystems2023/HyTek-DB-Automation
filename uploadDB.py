import config
import json
import os
import shutil

from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload


def main(database_file):
    # Instantiate api by defining scope and drive api parameters
    config.logging.info("Instantiating Drive API...")
    scope = ['https://www.googleapis.com/auth/drive']
    service_account_json_key = os.path.join(os.getcwd(), "credentials.json")
    credentials = service_account.Credentials.from_service_account_file(
                                filename=service_account_json_key, 
                                scopes=scope)
    service = build('drive', 'v3', credentials=credentials)
    parent_id = config.config["DEFAULT"]["DRIVE_FOLDER_PARENT_ID"]

    # Getting File List using Drive API and search for "Modified_DB.zip"
    config.logging.info(f"Retreiving files in shared folder (ID: {parent_id})...")
    results = service.files().list(q=f"(name='Modified_DB.zip' or name='debug.log') and '{parent_id}' in parents", 
                                   pageSize=1000, 
                                   fields="nextPageToken, files(id, name, parents, mimeType, size, modifiedTime)").execute()
    
    # Check if database file and log file exists. If exists, it will be an update operation. Otherwise perform a create operation instead.
    is_new_upload_db = True
    is_new_upload_log = True
    items = results.get('files', [])
    for item in items:
        if item.get("name") == "Modified_DB.zip":
            config.logging.debug(f"Database file (ID: {item.get('id')}) already exists, performing an update operation...")
            is_new_upload_db = False
            database_file_id = item.get("id")  # Get database file id to do an update operation
        elif item.get("name") == "debug.log":
            config.logging.debug(f"Log file (ID: {item.get('id')}) already exists, performing an update operation...")
            is_new_upload_log = False
            log_file_id = item.get("id")  # Get log file id to do an update operation

    # Zip and Compress .MDB File for upload to Shared Folder
    config.logging.info("Compressing database file...")
    archived = shutil.make_archive(os.path.join(os.getcwd(), config.config["DEFAULT"]["UPLOAD_DIR"], "Modified_DB"), "zip", database_file)

    # Uploading Database file to Google Drive using Drive API
    config.logging.info("Preparing files for upload...")
    if is_new_upload_db:
        db_file_metadata = {
            'name': 'Modified_DB.zip',
            'mimeType': 'application/zip',
            'parents': [parent_id]
        }
    else:
        db_file_metadata = {
            'name': 'Modified_DB.zip',
            'mimeType': 'application/zip',
        }
    db_media = MediaFileUpload(archived, chunksize=5 * 1024 * 1024, mimetype='application/octet-stream', resumable=True)
    if is_new_upload_log:
        log_file_metadata = {
            'name': 'debug.log',
            'mimeType': 'application/text',
            'parents': [parent_id]
        }
    else:
        log_file_metadata = {
            'name': 'debug.log',
            'mimeType': 'application/text',
        }
    log_file_path = os.path.join(os.getcwd(), config.config["DEFAULT"]["LOG_FILE"])
    log_media = MediaFileUpload(log_file_path, chunksize=5 * 1024 * 1024, mimetype='application/octet-stream', resumable=True)
    try:
        # Try uploading database file
        config.logging.info("Uploading database...")
        if is_new_upload_db:
            database_file = service.files().create(body=db_file_metadata, media_body=db_media, fields='id').execute()
        else:
            database_file = service.files().update(fileId=database_file_id, body=db_file_metadata, media_body=db_media, fields='id').execute()
        # Try uploading log file
        config.logging.info("Uploading logs...")
        if is_new_upload_log:
            log_file = service.files().create(body=log_file_metadata, media_body=log_media, fields='id').execute()
        else:
            log_file = service.files().update(fileId=log_file_id, body=log_file_metadata, media_body=log_media, fields='id').execute()
        # Log successful completion
        config.logging.info(f"Upload completed successfully! (database_file_id: {database_file.get('id')}, log_file_id, {log_file.get('id')})")
        return {"status": True, "database_file_id": database_file.get("id"), "log_file_id": log_file.get("id")}
    except HttpError as e:
        if e.resp.get('content-type', '').startswith('application/json'):
            reason = json.loads(e.content).get('error').get('errors')[0].get('reason')
            config.logging.error(f"An error occurred during upload: {reason}")
            return {"status": False, "error": reason}
        else:
            config.logging.error(f"An error occurred during upload: {e}")
            return {"status": False, "error": e}
    except Exception as e:
        config.logging.error(f"An error occurred during upload: {e}")
        return {"status": False, "error": e}


if __file__ == "__main__":
    main()
