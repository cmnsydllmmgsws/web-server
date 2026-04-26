import socket

HOST = '127.0.0.1'
PORT = 8080

def client_test(path='/'):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((HOST, PORT))
    request = f'GET {path} HTTP/1.1\r\nHost: {HOST}\r\nConnection: keep-alive\r\n\r\n'
    s.send(request.encode())
    response = s.recv(4096).decode('utf-8', errors='ignore')
    print('===== server response =====')
    print(response)
    s.close()

if __name__ == '__main__':
    client_test('/index.html')