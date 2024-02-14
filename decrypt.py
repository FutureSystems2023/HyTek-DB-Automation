import os

from cryptography.fernet import Fernet
from dotenv import load_dotenv


def main():
    load_dotenv()
    key = os.getenv("DECRYPTION_KEY")
    cipher_suite = Fernet(key)  # Initialize the Fernet cipher with the loaded key
    with open('encrypted_credentials.bin', 'rb') as file:  # Load the encrypted data from the file
        encrypted_data = file.read()
    decrypted_data = cipher_suite.decrypt(encrypted_data)  # Decrypt the data and parse as json string
    data = decrypted_data.decode('utf-8')
    return data


if __name__ == "__main__":
    main()
