import socket
import threading
import os
import time
from datetime import datetime

# Configuration
HOST = '127.0.0.1'
PORT = 8080
WEB_ROOT = './www'
BUF_SIZE = 4096
TIMEOUT = 5  # keep-alive timeout

# Ensure the web root directory exists
if not os.path.exists(WEB_ROOT):
    os.mkdir(WEB_ROOT)

# Define a function to write server access logs
def log_write(client_ip, filename, status):

    # Get current system time
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    # Construct a single log line
    log_line = f"{now} | {client_ip} | {filename} | {status}\n"
    # Write the constructed log line to the log file
    with open('server.log', 'a', encoding='utf-8') as f:
        f.write(log_line)

# Get MIME content type
def get_content_type(path):
    ext = os.path.splitext(path)[1].lower()
    if ext in ['.html', '.htm']:
        return 'text/html'
    elif ext == '.txt':
        return 'text/plain'
    elif ext == '.jpg' or ext == '.jpeg':
        return 'image/jpeg'
    elif ext == '.png':
        return 'image/png'
    elif ext == '.gif':
        return 'image/gif'
    else:
        return 'application/octet-stream'

# Handle a single client connection
def handle_client(client_socket, client_ip):
    try:
        # Set timeout for client socket
        client_socket.settimeout(TIMEOUT)
        while True:
            try:
                # Receive data from client
                request = client_socket.recv(BUF_SIZE).decode('utf-8', errors='ignore')

                # If no data received, client closed the connection, exit loop
                if not request:
                    break

                # Parse request line
                lines = request.split('\r\n')
                # If the request line is empty, skip this iteration
                if len(lines) < 1:
                    continue
                # Split the first request line into parts by spaces
                first_line = lines[0].split()
                # If the request line does not have at least method, path, version, it is invalid
                if len(first_line) < 3:
                    continue

                # Extract method, requested resourse path and HTTP version
                method = first_line[0]
                path = first_line[1]
                http_version = first_line[2]

                # Default page
                if path == '/':
                    path = '/index.html'
                file_path = WEB_ROOT + path

                # Initialize connection status to 'close'
                connection = 'close'
                # Initialize If-Modified-Since header value to None
                if_modified_since = None
                # Iterate through all lines in the HTTP request headers
                for line in lines:
                    if line.startswith('Connection:'):
                        connection = line.split(':', 1)[1].strip().lower()
                    if line.startswith('If-Modified-Since:'):
                        if_modified_since = line.split(':', 1)[1].strip()

                # ==================== Status Code ====================
                # 400 Bad Request
                if method not in ['GET', 'HEAD']:
                    status = '400 Bad Request'
                    body = b'<h1>400 Bad Request</h1>'
                    content_type = 'text/html'
                    content_len = len(body)
                    log_write(client_ip, path, status)

                # 403 Forbidden
                elif '..' in file_path or not file_path.startswith(WEB_ROOT):
                    status = '403 Forbidden'
                    body = b'<h1>403 Forbidden</h1>'
                    content_type = 'text/html'
                    content_len = len(body)
                    log_write(client_ip, path, status)

                # 404 Not found
                elif not os.path.exists(file_path) or not os.path.isfile(file_path):
                    status = '404 Not Found'
                    body = b'<h1>404 Not Found</h1>'
                    content_type = 'text/html'
                    content_len = len(body)
                    log_write(client_ip, path, status)

                else:
                    # Get the last modification timestamp
                    mtime = os.path.getmtime(file_path)
                    last_modified = time.gmtime(mtime)
                    last_modified_str = time.strftime('%a, %d %b %Y %H:%M:%S GMT', last_modified)

                    # 304 Not Modified
                    if if_modified_since:
                        try:
                            if_modified_time = time.strptime(if_modified_since, '%a, %d %b %Y %H:%M:%S GMT')
                            if mtime <= time.mktime(if_modified_time):
                                status = '304 Not Modified'
                                log_write(client_ip, path, status)
                                response_header = (
                                    f'{http_version} {status}\r\n'
                                    f'Connection: {connection}\r\n'
                                    f'Last-Modified: {last_modified_str}\r\n'
                                    '\r\n'
                                )
                                client_socket.send(response_header.encode())
                                continue
                        except:
                            pass

                    # 200 OK
                    status = '200 OK'
                    content_type = get_content_type(file_path)
                    if method == 'GET':
                        with open(file_path, 'rb') as f:
                            body = f.read()
                    else:
                        body = b''
                    content_len = len(body)
                    log_write(client_ip, path, status)

                # Response header
                response_header = (
                    f'{http_version} {status}\r\n'
                    f'Content-Type: {content_type}\r\n'
                    f'Content-Length: {content_len}\r\n'
                    f'Connection: {connection}\r\n'
                    f'Last-Modified: {time.strftime("%a, %d %b %Y %H:%M:%S GMT", time.gmtime())}\r\n'
                    '\r\n'
                )

                # Encode the response header string to bytes and send it to the client
                client_socket.send(response_header.encode())
                # Check if the request method is GET and there is a response body to send
                if method == 'GET' and body:
                    client_socket.send(body)

                # If the connection mode is set to close exit the loop and close the connection
                if connection == 'close':
                    break

            # If no request is received within the timeout period, close the connection
            except socket.timeout:
                break
            # If any other unexpected error occurs, close the connection
            except Exception:
                break
    # Close the client socket
    finally:
        client_socket.close()

# Main server function
def main():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind((HOST, PORT))
    server_socket.listen(5)
    print(f' Multi-thread Web Server running on http://{HOST}:{PORT}')
    print(f' Web root: {WEB_ROOT}')
    print(f' Log: server.log')
    print('Press Ctrl+F2 to stop\n')

    while True:
        client_sock, addr = server_socket.accept()
        thread = threading.Thread(target=handle_client, args=(client_sock, addr[0]))
        thread.start()

if __name__ == '__main__':
    main()