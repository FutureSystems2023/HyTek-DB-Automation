import json
import os
import paramiko

from dotenv import load_dotenv
from json.decoder import JSONDecodeError
from time import strftime, localtime


def main():
    # Load environment variables
    load_dotenv(override=True)

    # Instantiate SSH Client with parameters
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    print(f"Connecting to SFTP server {os.environ.get('SFTP_HOSTNAME')} with username ({os.environ.get('SFTP_USERNAME')})...")
    ssh.connect(
        hostname=os.environ.get('SFTP_HOSTNAME'),
        username=os.environ.get('SFTP_USERNAME'),
        password=os.environ.get('SFTP_PASSWORD'),
        timeout=10
    )
    sftp = ssh.open_sftp()
    remote_db_file_path = os.environ.get('SFTP_FOLDER_PATH') + os.environ.get('SFTP_ZIPPED_DB_FILE')
    print(f"Remote zipped database file full path: {remote_db_file_path}")

    # Check remote zipped db file's metadata. If no changes to file, abort SFTP download.
    info = sftp.stat(remote_db_file_path)
    modified_time = strftime('%Y-%m-%d %H:%M:%S', localtime(info.st_mtime))
    print(f'File size: {info.st_size/1000000} MB, Modified Time: {modified_time}')
    metadata = {}
    try:
        # Attempt to read metadata json file
        metadata_file_path = os.path.join(
            os.getcwd(),
            os.environ.get('SFTP_LOCAL_DOWNLOAD_DIR'),
            os.environ.get('SFTP_ZIPPED_DB_FILE_METADATA')
        )
        if os.path.exists(metadata_file_path):
            json_file = open(metadata_file_path, 'r')
            metadata = json.load(json_file)
    except JSONDecodeError:
        pass
    if info.st_size == metadata.get('file_size') and modified_time == metadata.get('modified_time'):
        print("File metadata did not change, aborting SFTP download...")
        sftp.close()
        ssh.close()
        return {'status': False}
    elif metadata.get('file_size') == None and metadata.get('modified_time') == None:
        print("No existing metadata json found, attempting zipped database file download via SFTP...")
    else:
        print("File metadata has changed, attempting zipped database file download via SFTP...")

    # Get database file
    print(f"Getting database file ({remote_db_file_path})...")
    try:
        local_db_file_save_path = os.path.join(
            os.getcwd(),
            os.environ.get('SFTP_LOCAL_DOWNLOAD_DIR'),
            os.environ.get('SFTP_ZIPPED_DB_FILE')
        )
        sftp.get(
            remotepath=remote_db_file_path, 
            localpath=local_db_file_save_path, 
            callback=printTransferred
        )
        print("Database file downloaded successfully! SFTP client will disconnect now...")
    except Exception as e:
        print(e)
        return {'status': False}

    # Update metadata
    print("Updating metadata json file...")
    metadata['file_size'], metadata['modified_time'] = info.st_size, modified_time
    json_object = json.dumps(metadata, indent=4)
    with open(metadata_file_path, "w+") as outfile:
        outfile.write(json_object)

    # Close SFTP & SSH session
    sftp.close()
    ssh.close()

    print("SFTP operations completed succesfully!")
    return {'status': True, 'db_file_path': local_db_file_save_path}


def printTransferred(transferred, toBeTransferred):
    print(f"Transferred: {transferred}\tOut of: {toBeTransferred}", end='\r', flush=True)


if __name__ == "__main__":
    main()