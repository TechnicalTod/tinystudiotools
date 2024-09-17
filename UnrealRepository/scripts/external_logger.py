import socket
import sys

def start_server():
    # Create a socket server to listen for progress updates
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind(('localhost', 65432))
    server_socket.listen(1)
    print("Server listening on port 65432...")

    while True:
        conn, addr = server_socket.accept()
        with conn:
            while True:
                data = conn.recv(1024)
                if not data:
                    break
                sys.stdout.write(data.decode() + "\n")
                sys.stdout.flush()  # Ensure immediate output to the terminal

if __name__ == "__main__":
    start_server()
