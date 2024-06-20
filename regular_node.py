import xmlrpc.client
import xmlrpc.server
import threading
import hashlib
import os
import time
import json

# Configurations
SERVER_HOST = '127.0.0.1'
SERVER_PORT = 5000
BUFFER_SIZE = 262144 

SUPER_PEER_HOST = '127.0.0.1'
SUPER_PEER_PORT = 5001

# Connect to Super Peer
super_peer = xmlrpc.client.ServerProxy(f"http://{SUPER_PEER_HOST}:{SUPER_PEER_PORT}", allow_none=True)

# Function to calculate the checksum of a file
def calculate_checksum(file_path):
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

# Function to handle file reception
def receive_file(filename, filesize, checksum, file_data):
    try:
        filename = os.path.basename(filename)
        with open(filename, "wb") as f:
            f.write(file_data.data)
        
        received_checksum = calculate_checksum(filename)
        if received_checksum == checksum:
            return f"{filename} received and verified successfully."
        else:
            return f"File transfer error for {filename}."
    except Exception as e:
        return f"Error receiving the file: {e}"

# Function to handle file sending
def send_file(filename):
    try:
        if not os.path.exists(filename):
            return f"Error: File {filename} not found."

        filesize = os.path.getsize(filename)
        checksum = calculate_checksum(filename)
        with open(filename, "rb") as f:
            file_data = xmlrpc.client.Binary(f.read())
        return (filename, filesize, checksum, file_data)
    except Exception as e:
        return f"Error sending the file: {e}"

# Function to list all files
def list_all_files():
    try:
        response = super_peer.list_files()
        nodes = json.loads(response)
        file_list = []
        for node in nodes:
            ip, port = node["node"]
            for file_info in node["files"]:
                filename, checksum = file_info.split()
                file_list.append({"filename": filename, "address": f"{ip}:{port}"})
        return file_list
    except Exception as e:
        return f"Error listing all files: {e}"

# Function to search for a file
def search_file(filename):
    try:
        response = super_peer.search(filename)
        nodes = json.loads(response)
        return nodes
    except Exception as e:
        return f"Error searching for file '{filename}': {e}"

# Function to update the file list
def update_file_list():
    while True:
        try:
            file_list = [f"{f} {calculate_checksum(f)}" for f in os.listdir() if os.path.isfile(f)]
            response = super_peer.update(SERVER_HOST, SERVER_PORT, json.dumps(file_list))
            time.sleep(60)
        except Exception as e:
            print(f"Error updating the file list: {e}")
            time.sleep(5)

def main():
    try:
        print(super_peer.register(SERVER_HOST, SERVER_PORT))
        threading.Thread(target=update_file_list).start()

        all_files = list_all_files()
        if not all_files:
            print("No files available.")
            return

        print("Available files:")
        for i, file_info in enumerate(all_files, start=1):
            print(f"{i}. {file_info['filename']} available at {file_info['address']}")

        while True:
            file_choice = input("Enter the name of the file you want to download (or 'exit' to leave): ")
            if file_choice.lower() == 'exit':
                break
            
            filename = None
            for file_info in all_files:
                if file_choice.lower() == file_info['filename'].lower():
                    filename = file_info['filename']
                    break
            
            if filename:
                nodes = search_file(filename)
                for node in nodes:
                    ip, port = node["node"]
                    if (ip, port) == (SERVER_HOST, SERVER_PORT):
                        continue
                    try:
                        with xmlrpc.client.ServerProxy(f"http://{ip}:{port}", allow_none=True) as client:
                            result = client.download_file(filename)
                            if isinstance(result, tuple):
                                _, _, _, file_data = result
                                message = receive_file(filename, 0, "", file_data)
                                print(message)
                                return
                    except Exception as e:
                        print(f"Error connecting to {ip}:{port} - {e}")
            else:
                print("File not found in the list. Please choose a valid file.")

    except Exception as e:
        print(f"Initialization error: {e}")

class FileServer(xmlrpc.server.SimpleXMLRPCServer):
    def __init__(self, host, port):
        super().__init__((host, port), allow_none=True)
        self.register_function(receive_file, 'receive_file')
        self.register_function(send_file, 'send_file')
        self.register_function(list_all_files, 'list_all_files')
        self.register_function(search_file, 'search_file')

if __name__ == "__main__":
    server = FileServer(SERVER_HOST, SERVER_PORT)
    print(f"Starting XML-RPC server on {SERVER_HOST}:{SERVER_PORT}")
    try:
        threading.Thread(target=main).start()
        server.serve_forever()
    except Exception as e:
        print(f"Server error: {e}")
