from http.server import HTTPServer, BaseHTTPRequestHandler
from io import BytesIO
import json


class WebServerHandler(BaseHTTPRequestHandler):

    def do_POST(self):
        self.send_response(200)
        content_length = int(self.headers['Content-Length'])
        content_type = self.headers['Content-Type']

        if content_type != 'application/json':
            print("Wrong content type,json expected!")
            return

        body = self.rfile.read(content_length)
        response = BytesIO()
        response.write(b'Received: ' + body + b'\n')
        self.end_headers()
        self.wfile.write(response.getvalue())

        content_string = body.decode('utf-8')
        content_json_array = json.loads(content_string)

        if self.path == "/application":
            content_dict = endpoint_application(content_json_array)
            print(content_dict)

        if self.path == "/interface":
            content_dict = endpoint_interface(content_json_array)
            print(content_dict)

    def do_GET(self):
        self.send_response(200)
        self.end_headers()


def endpoint_application(content_json_array):
    content_dict = {}
    try:
        content_dict['timestamp'] = content_json_array[0]['timestamp']
        content_dict['name'] = content_json_array[0]['data']['name']
        content_dict['cpu'] = content_json_array[0]['data']['cpu']
        content_dict['memory'] = content_json_array[0]['data']['memory']
    except KeyError:
        pass

    return content_dict


def endpoint_interface(content_json_array):
    content_dict = {}
    try:
        content_dict['timestamp'] = content_json_array[0]['timestamp']
        content_dict['id'] = content_json_array[0]['data']['id']
        content_dict['active'] = content_json_array[0]['data']['active']
        content_dict['bandwidth'] = content_json_array[0]['data']['bandwidth']
    except KeyError:
        pass

    return content_dict


# def schedule_application(content_dict):
#     agent.Docker.update_cpu_shares(content_dict['name'], content_dict['cpu'])
#     agent.docker.update_memory_limit(content_dict['name'], content_dict['memory'])


def main():
    try:
        port = 8080
        server = HTTPServer(('', port), WebServerHandler)
        print("Web server is running on port {}".format(port))
        server.serve_forever()

    except KeyboardInterrupt:
        print(" ^C entered, stopping web server....")
        server.socket.close()


if __name__ == '__main__':
    main()
