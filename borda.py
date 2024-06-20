from xmlrpc.server import SimpleXMLRPCServer
import threading
import xmlrpc.client
import time

nodes = {}
files = {}

def register_node(node_host, node_port, node_files):
    nodes[(node_host, node_port)] = node_files
    return True

def register_file(node_host, node_port, filename, checksum):
    if filename not in files:
        files[filename] = []
    files[filename].append((node_host, node_port, checksum))
    return True

def find_file(filename):
    if filename in files:
        return files[filename]
    return []

def periodic_file_check():
    while True:
        print("Checking files on registered nodes:")
        for (node_host, node_port), node_files in nodes.items():
            print(f"Node at {node_host}:{node_port} has files:")
            for filename, checksum in node_files.items():
                print(f"- {filename}")
        print("")
        time.sleep(5)

def find_node_with_file(filename):
    for (node_host, node_port), node_files in nodes.items():
        if filename in node_files:
            return (node_host, node_port)
    return None

def start_edge_node(edge_node_host, edge_node_port):
    server = SimpleXMLRPCServer((edge_node_host, edge_node_port), allow_none=True)
    server.register_function(register_node, "register_node")
    server.register_function(register_file, "register_file")
    server.register_function(find_file, "find_file")
    server.register_function(find_node_with_file, "find_node_with_file")
    
    threading.Thread(target=server.serve_forever).start()
    threading.Thread(target=periodic_file_check).start()
    print(f"Edge node running on {edge_node_host}:{edge_node_port}")

if __name__ == "__main__":
    edge_node_host = 'localhost'
    edge_node_port = 8000
    start_edge_node(edge_node_host, edge_node_port)
    input("Press Enter to exit...\n")
