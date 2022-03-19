import logging
from http.server import SimpleHTTPRequestHandler
import socket
import socketserver
import qrcode
import os

logger = logging.getLogger(__name__)


class GetHandler(SimpleHTTPRequestHandler):
    def __init__(self, request, client_address, server):
        SimpleHTTPRequestHandler.__init__(self, request, client_address, server)

    def do_GET(self):
        SimpleHTTPRequestHandler.do_GET(self)
        logger.error(f'{self.client_address[0]} - [{self.log_date_time_string()}] "{self.requestline}"')


class HTTPServer:
    def __init__(self, path, port):
        self.path = path
        self.port = int(port)

        handler = GetHandler
        socketserver.TCPServer.allow_reuse_address = True
        self.httpd = socketserver.TCPServer(("", self.port), handler)
        self.QR_code()

    def find_IP(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("10.255.255.255", 1))
        IP = "http://" + s.getsockname()[0] + ":" + str(self.port)
        return IP

    def QR_code(self):
        qr = qrcode.QRCode(version=1, error_correction=qrcode.constants.ERROR_CORRECT_L, box_size=8, border=0, )
        qr.add_data(self.find_IP())
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="transparent")
        return img

    def run_server(self):
        os.chdir(self.path)
        logger.error("[?] Changing directory...")
        try:
            logger.error("[+] Server is running...")
            self.httpd.serve_forever()
        except OSError:
            pass
        finally:
            logger.error("[-] Server is closed...")
            self.httpd.server_close()

    def stop_(self):
        self.httpd.server_close()
        self.httpd.shutdown()

    def logs(self):
        return f"Serving http server at port {self.port}\nType this IP address in your browser {self.find_IP()} or scan the QRCode"


if __name__ == '__main__':
    h = HTTPServer(r"C:\\", 8010)

    h.run_server()

