import socket
import re
from threading import Thread
from termcolor import colored
import json
from bs4 import BeautifulSoup


def indent_json(json_str):
    try:
        json_obj = json.loads(json_str)
        return json.dumps(json_obj, indent=4)
    except:
        return json_str

def handle_request(client_socket):
    request = client_socket.recv(4096)
    host_header = re.search(b'Host: ([^\r\n]*)\r\n', request)
    if host_header:
        target_host = host_header.group(1).decode()
        target_port = 80
        target_path = re.search(b'GET ([^\r\n]*) HTTP/1.[01]', request).group(1).decode()
    else:
        print(colored('[!] Could not extract target server information from request\n', 'red'))
        client_socket.close()
        return

    target_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    target_socket.connect((target_host, target_port))
    target_socket.send(request)

    response = b''
    while True:
        chunk = target_socket.recv(4096)
        if not chunk:
            break
        response += chunk

    response_headers, response_body = response.split(b'\r\n\r\n', 1)

    content_type_header = re.search(b'Content-Type: ([^\r\n]*)\r\n', response_headers)
    if content_type_header:
        content_type = content_type_header.group(1).decode()
        if 'html' in content_type:
            soup = BeautifulSoup(response_body, 'html.parser')
            response_body = soup.prettify().encode()
        elif 'json' in content_type:
            response_body = indent_json(response_body.decode()).encode()

    print(colored('-'*20 + 'REQUEST' + '-'*20, 'green'))
    print(colored(request.decode().split('\r\n\r\n')[0], 'cyan'))
    print(colored(request.decode().split('\r\n\r\n')[1], 'yellow'))
    print(colored('-'*20 + 'RESPONSE' + '-'*20, 'green'))
    print(colored(response_headers.decode(), 'cyan'))
    print(colored(response_body.decode(), 'yellow'))

    client_socket.send(response)

    target_socket.close()
    client_socket.close()



def start_proxy():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind(('localhost', 8080))
    server_socket.listen()
    print(colored('[!] Proxy server listening on port 8080...\n\n', 'green'))
    try:
        while True:
            client_socket, client_address = server_socket.accept()
            t = Thread(target=handle_request, args=(client_socket,))
            t.start()
    except KeyboardInterrupt:
        print(colored('\n[!] Stopping proxy server...\n\n', 'red'))
        server_socket.close()


if __name__ == '__main__':
    start_proxy()
