from xmlrpc.server import SimpleXMLRPCServer
import threading
import json

# Configurações
SERVER_HOST = '127.0.0.1'
SERVER_PORT = 5001

nodes_info = {}

def register(node_ip, node_port):
    nodes_info[(node_ip, node_port)] = {"info": (node_ip, node_port), "files": []}
    return "Registrado com sucesso."

def search(filename):
    response = [data["info"] for node, data in nodes_info.items() if filename in [file.split()[0] for file in data["files"]]]
    return json.dumps(response)

def update(node_ip, node_port, file_list):
    node_key = (node_ip, node_port)
    if node_key in nodes_info:
        nodes_info[node_key]["files"] = json.loads(file_list)
        return "Lista de arquivos atualizada com sucesso."
    else:
        return "Erro: Nó não registrado."

def list_files():
    all_files = [{"node": data["info"], "files": data["files"]} for data in nodes_info.values()]
    return json.dumps(all_files)

def main():
    server = SimpleXMLRPCServer((SERVER_HOST, SERVER_PORT), allow_none=True)
    server.register_function(register, "register")
    server.register_function(search, "search")
    server.register_function(update, "update")
    server.register_function(list_files, "list_files")

    print(f"[*] Super peer ouvindo em {SERVER_HOST}:{SERVER_PORT}")
    server.serve_forever()

if __name__ == "__main__":
    main()
