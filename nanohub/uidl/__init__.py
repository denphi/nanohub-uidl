#  Copyright 2019 HUBzero Foundation, LLC.

#  Permission is hereby granted, free of charge, to any person obtaining a copy
#  of this software and associated documentation files (the "Software"), to deal
#  in the Software without restriction, including without limitation the rights
#  to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
#  copies of the Software, and to permit persons to whom the Software is
#  furnished to do so, subject to the following conditions:
#
#  The above copyright notice and this permission notice shall be included in
#  all copies or substantial portions of the Software.
#
#  THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#  IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#  FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
#  AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
#  LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
#  OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
#  THE SOFTWARE.

#  HUBzero is a registered trademark of Purdue University.

#  Authors:
#  Daniel Mejia (denphi), Purdue University (denphi@denphi.com)


from .app import *
from .teleport import *
from .material import *
from .nanohub import *
from .plotly import *
from .rappture import *

from ._version import __version__, version_info


import http.client
import io
import os
import posixpath
import shutil
import socketserver
import sys
import time
import json
from http import HTTPStatus
import http.server
import requests
from urllib.parse import parse_qsl
import urllib
import re
import argparse

class UIDLRequestHandler(http.server.BaseHTTPRequestHandler):

    filename = ""
    hub_url = ""
    session = ""
    app = ""
    token = ""
    path = ""
    
    def __init__(self, *args, directory=None, **kwargs):
        if directory is None:
            directory = os.getcwd()
        self.directory = directory
        super().__init__(*args, **kwargs)

    def do_REQUEST(self, method):
        path = self.translate_path(self.path)
        status = HTTPStatus.OK

        close =  UIDLRequestHandler.hub_url + '/tools/anonymous/stop?sess=' + UIDLRequestHandler.session
        text = '''<!DOCTYPE html>
            <html>
                <body>
                    <p>''' + path +''' Not Found</p>
                    <p>''' + UIDLRequestHandler.filename +''' Not Found</p>
                    <div style="position: fixed;z-index: 1000000;top: 0px;right: 170px;"><button class="btn btn-sm navbar-btn" title="Terminate this notebook or tool and any others in the session" onclick="window.location.href=\'''' + close + '''\'" style="color: #333;padding: 7px 15px;border: 0px;">Terminate Session</button></div>
                </body>
            </html>'''

        if os.path.exists(UIDLRequestHandler.filename) is False:
            status = HTTPStatus(404)
        
        elif path in ["", "/", "index.htm", "index.html", UIDLRequestHandler.filename ] :
            with open(UIDLRequestHandler.filename) as file:
                text = file.read()
                
            text = text.replace("url = '" + UIDLRequestHandler.hub_url + "/api/", "url = '" + UIDLRequestHandler.path + "api/")
            
            
            ticket =  UIDLRequestHandler.hub_url + '/feedback/report_problems?group=app-' + UIDLRequestHandler.app
            header = '<div style="position: fixed;z-index: 1000000;top: 0px;right: 170px;"><button title="Report a problem" onclick="window.open(\'' + ticket + '\')" style="color: #333;padding: 7px 15px;border: 0px;">Submit a ticket</button>&nbsp;&nbsp;<button class="btn btn-sm navbar-btn" title="Terminate this notebook or tool and any others in the session" onclick="window.location.href=\'' + close + '\'" style="color: #333;padding: 7px 15px;border: 0px;">Terminate Session</button></div>'
            res = re.search("<body(?:\"[^\"]*\"['\"]*|'[^']*'['\"]*|[^'\">])+>", text)
            if res is not None:
                index = res.end() + 1
                text = text[:index] + header + text[index:]
            res = re.search("sessiontoken=([0-9a-zA-Z])+&", text)
            if res is not None:
                text = text[:res.start()] + "sessiontoken=" + UIDLRequestHandler.token + "&" + text[res.end():]
            res = re.search("sessionnum=([0-9])+&", text)
            if res is not None:
                text = text[:res.start()] + "sessionnum=" + UIDLRequestHandler.session + "&" + text[res.end():]
        elif path.startswith("api/"):
            try :
                headers = {}
                contentlength = 0
                data = {}
                url = UIDLRequestHandler.hub_url + "/" + path
                for h in str(self.headers).splitlines():
                    sub = h.split(":", 1)
                    if len(sub) == 2:
                        sub[0] = sub[0].strip()
                        sub[1] = sub[1].strip()
                        if sub[0].lower() in ['host', 'connection', 'referer', 'origin', 'x-real-ip']:
                            pass
                        elif sub[0].lower() == "content-length":
                            contentlength = int(sub[1])
                        else:
                            headers[sub[0]] = sub[1]
                if contentlength > 0:
                    field_data = self.rfile.read(contentlength)
                    try:
                        json.loads(field_data.decode())
                        data = field_data
                    except:  
                        data = dict(parse_qsl(field_data))
                if method == "post":
                    res = requests.post(url, headers=headers, data=data, allow_redirects=False)
                else:
                    res = requests.get(url, headers=headers, data=data, allow_redirects=False)
                status = HTTPStatus(res.status_code)
                text = res.text
            except:
                status = HTTPStatus.INTERNAL_SERVER_ERROR
                raise
        else:
            status = HTTPStatus(404)

        try:
            f = io.BytesIO()
            f.write(bytes(text, 'utf-8'))
            f.seek(0)
            self.send_response(status)
            self.send_header("Content-type", "text/html")
            self.send_header("Content-Length", str(len(text)))
            self.send_header("Last-Modified", self.date_time_string(time.time()))
            self.end_headers()
            if f:
                try:
                    shutil.copyfileobj(f, self.wfile)
                finally:
                    f.close()
        except:
            f.close()
            status = HTTPStatus.INTERNAL_SERVER_ERROR
            self.send_response(status)
            self.end_headers()

    def do_GET(self):
        self.do_REQUEST("get")
        

    def do_POST(self):
        self.do_REQUEST("post")

   
            
    def translate_path(self, path):
        # abandon query parameters
        path = path.split('?',1)[0]
        path = path.split('#',1)[0]
        # Don't forget explicit trailing slash when normalizing. Issue17324
        trailing_slash = path.rstrip().endswith('/')
        try:
            path = urllib.parse.unquote(path, errors='surrogatepass')
        except UnicodeDecodeError:
            path = urllib.parse.unquote(path)
        path = posixpath.normpath(path)
        words = path.split('/')
        if words[1] == "weber":
            words = words[5:]
        else:
            words = words[1:]
        words = [w for w in words if w is not None]
        path = "/".join(words)
        if trailing_slash:
            path += '/'
        return path

def parse_cmd_line():
    hub_url = ""
    app = ""
    sessionid = ""
    fn = os.path.join(os.environ['SESSIONDIR'], 'resources')
    with open(fn, 'r') as f:
        res = f.read()
    for line in res.split('\n'):
        if line.startswith('hub_url'):
            hub_url = line.split()[1]
        elif line.startswith('sessionid'):
            sessionid = int(line.split()[1])
        elif line.startswith('application_name'):
            app = line.split()[1]
        elif line.startswith('session_token'):
            token = line.split()[1]    
        elif line.startswith('filexfer_cookie'):
            cookie = line.split()[1]
        elif line.startswith('filexfer_port'):
            cookieport = line.split()[1]  
    path = "/weber/" + str(sessionid) + "/" + cookie + "/" + str(int(cookieport)%1000) + "/"
    parser = argparse.ArgumentParser(
        usage="""usage: [-h] [--host] [--port] [--hub] [--session] [--app] [--token] [name]
Start a Jupyter notebook-based tool
positional arguments:
  name        Name of html file to run.
optional arguments:
  -h, --help  show this help message and exit.
  --host set hostname.
  --port set running port.
  --hub set running port.
  --session set running port.
  --app set running port.
  --dir set folder to start.
""",
        prog="start_server",
        add_help=False)
    parser.add_argument('-h', '--help', dest='help', action='store_true')
    parser.add_argument('-o', '--host', dest='host', action='store', default='0.0.0.0')
    parser.add_argument('-p', '--port', dest='port', type=int, action='store', default=8001)
    parser.add_argument('-b', '--hub', dest='hub_url', action='store', default=hub_url)
    parser.add_argument('-s', '--session', dest='session', type=int, action='store', default=sessionid)
    parser.add_argument('-a', '--app', dest='app', action='store', default=app)
    parser.add_argument('-t', '--token', dest='token', action='store', default=token)
    parser.add_argument('-w', '--path', dest='path', action='store', default=path)
    parser.add_argument('-d', '--dir', dest='dir', action='store', default=os.environ['SESSIONDIR'])
    parser.add_argument('name')
    return parser

def main():

    if os.getuid() == 0:
        print("Do not run this as root.", file=sys.stderr)
        sys.exit(1)    
    
    parser = parse_cmd_line()
    args = parser.parse_args()
    if args.help:
        pass
    else:
            
        os.environ['DISPLAY'] = ""
        socketserver.TCPServer.allow_reuse_address = True
        UIDLRequestHandler.filename = args.dir + "/" + args.name
        UIDLRequestHandler.hub_url = args.hub_url
        UIDLRequestHandler.session = str(args.session)
        UIDLRequestHandler.app = args.app
        UIDLRequestHandler.token = args.token
        UIDLRequestHandler.path = args.path
        with socketserver.TCPServer((args.host, args.port), UIDLRequestHandler) as httpd:
            print("Nanohub UIDL Server started at port", args.port, "using filename", args.name)
            try:
                # Run the web server
                httpd.serve_forever()
            except KeyboardInterrupt:
                httpd.server_close()
                print("Nanohub UIDL server has stopped.")
    
