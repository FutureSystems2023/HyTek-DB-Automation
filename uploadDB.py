import config
import decrypt
import json
import os
import shutil

from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload

from tkinter import Widget


def main(db_file, app_progress_label=None):
    """Initialize Drive API by first decrypting encrypted credentials. After initialization, Upload DB file and log file.

    Args:
        db_file (str): Filepath of database file to be uploaded
        app_progress_label (object, optional): Tkinter label widget to show the progress of operations.

    Returns:
        dict: Dictionary object that defines status of upload and file IDs of uploaded files
    """
    # Instantiate api by defining scope and drive api parameters
    config.logging.info("Instantiating Drive API...")
    scope = ['https://www.googleapis.com/auth/drive']
    service_account_info = json.loads(decrypt.main())
    credentials = service_account.Credentials.from_service_account_info(
                                service_account_info,
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
            db_file_id = item.get("id")  # Get database file id to do an update operation
        elif item.get("name") == "debug.log":
            config.logging.debug(f"Log file (ID: {item.get('id')}) already exists, performing an update operation...")
            is_new_upload_log = False
            log_file_id = item.get("id")  # Get log file id to do an update operation

    # Zip and Compress .MDB File for upload to Shared Folder
    config.logging.info("Compressing database file...")
    archived = shutil.make_archive(
        base_name=os.path.join(os.getcwd(), config.config["DEFAULT"]["UPLOAD_DIR"], "Modified_DB"), 
        format="zip",
        root_dir=os.path.join(os.getcwd(), config.config["DEFAULT"]["UPLOAD_DIR"]),
        base_dir=os.path.basename(db_file)
    )
    config.logging.debug(f"Database file size compressed from {os.path.getsize(db_file)} bytes to {os.path.getsize(archived)} bytes")

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
    db_media = MediaFileUpload(archived, chunksize=1 * 1024 * 1024, mimetype='application/octet-stream', resumable=True)
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
    log_file_path = os.path.join(os.path.dirname(__file__), config.config["DEFAULT"]["LOG_FILE"])
    log_media = MediaFileUpload(log_file_path, chunksize=1 * 1024 * 1024, mimetype='application/octet-stream', resumable=True)
    try:
        # Try uploading database file
        config.logging.info("Uploading database...")
        if app_progress_label is not None:
            app_progress_label["text"] = "Uploading database..."
        else:
            print("Uploading database...")
        if is_new_upload_db:
            db_file = service.files().create(body=db_file_metadata, media_body=db_media, fields='id')
        else:
            db_file = service.files().update(fileId=db_file_id, body=db_file_metadata, media_body=db_media, fields='id')
        response = None
        while response is None:
            if app_progress_label is not None:
                app_progress_label.master.update()
            status, response = db_file.next_chunk()
            if status:
                if app_progress_label is not None:
                    app_progress_label["text"] = "Uploading database (%d%%)..." % int(status.progress() * 100)
                else:
                    print("Uploading database (%d%%)..." % int(status.progress() * 100))
        uploaded_db_file_id = response["id"]
        # Try uploading log file
        config.logging.info("Uploading logs...")
        if app_progress_label is not None:
            app_progress_label["text"] = "Uploading logs..."
        else:
            print("Uploading logs...")
        if is_new_upload_log:
            log_file = service.files().create(body=log_file_metadata, media_body=log_media, fields='id')
        else:
            log_file = service.files().update(fileId=log_file_id, body=log_file_metadata, media_body=log_media, fields='id')
        response = None
        while response is None:
            if app_progress_label is not None:
                app_progress_label.master.update()
            status, response = log_file.next_chunk()
            if status:
                if app_progress_label is not None:
                    app_progress_label["text"] = "Uploading logs (%d%%)..." % int(status.progress() * 100)
                else:
                    print("Uploading logs (%d%%)..." % int(status.progress() * 100))
        uploaded_log_file_id = response["id"]
        # Log successful completion
        config.logging.info(f"Upload completed successfully! (db_file_id: {uploaded_db_file_id}, log_file_id, {uploaded_log_file_id})")
        return {"status": True, "db_file_id": uploaded_db_file_id, "log_file_id": uploaded_log_file_id}
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


if __name__ == "__main__":
    main()
