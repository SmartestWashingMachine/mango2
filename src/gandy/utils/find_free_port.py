import socket

# Finds a free port for use with llama.cpp binaries & Flask servers.
# Note there is a slight race condition here - right after tcp.close() that port can be yoinked by another app ._.
def find_tcp_port():
    tcp = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    tcp.bind(('', 0)) # 0.0.0.0
    _, port = tcp.getsockname()
    tcp.close()
    return port
