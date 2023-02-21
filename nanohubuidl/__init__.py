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
from .handlers import *
from .application import *

from ._version import __version__, version_info

import os
import socketserver
import sys
import time
import json

import requests
import argparse
import jupyter_server


"""The extension entry point."""

def _jupyter_server_extension_paths():
    return [
        {"module": "nanohubuidl", "app": UIDLmode},
    ]

_jupyter_server_extension_points = _jupyter_server_extension_paths


def load_jupyter_server_extension(serverapp: jupyter_server.serverapp.ServerApp):
    handlers = UIDLmode.handlers(serverapp.web_app.settings['base_url'])
    serverapp.web_app.add_handlers('.*$', handlers)

_load_jupyter_server_extension = load_jupyter_server_extension


def parse_cmd_line():
    hub_url = ""
    app = ""
    sessionid = ""
    fn = os.path.join(os.environ["SESSIONDIR"], "resources")
    with open(fn, "r") as f:
        res = f.read()
    for line in res.split("\n"):
        if line.startswith("hub_url"):
            hub_url = line.split()[1]
        elif line.startswith("sessionid"):
            sessionid = int(line.split()[1])
        elif line.startswith("application_name"):
            app = line.split(" ", 1)[1]
        elif line.startswith("session_token"):
            token = line.split()[1]
        elif line.startswith("filexfer_cookie"):
            cookie = line.split()[1]
        elif line.startswith("filexfer_port"):
            cookieport = line.split()[1]
    path = (
        "/weber/"
        + str(sessionid)
        + "/"
        + cookie
        + "/"
        + str(int(cookieport) % 1000)
        + "/"
    )
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
        add_help=False,
    )
    parser.add_argument("-h", "--help", dest="help", action="store_true")
    parser.add_argument("-o", "--host", dest="host", action="store", default="0.0.0.0")
    parser.add_argument(
        "-p", "--port", dest="port", type=int, action="store", default=8001
    )
    parser.add_argument("-b", "--hub", dest="hub_url", action="store", default=hub_url)
    parser.add_argument(
        "-s", "--session", dest="session", type=int, action="store", default=sessionid
    )
    parser.add_argument("-a", "--app", dest="app", action="store", default=app)
    parser.add_argument("-t", "--token", dest="token", action="store", default=token)
    parser.add_argument("-w", "--path", dest="path", action="store", default=path)
    parser.add_argument(
        "-l", "--local", dest="local", action="store_true", default=False
    )
    parser.add_argument(
        "-d", "--dir", dest="dir", action="store", default=os.environ["SESSIONDIR"]
    )
    parser.add_argument("name")
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
        os.environ["DISPLAY"] = ""
        socketserver.TCPServer.allow_reuse_address = True
        UIDLRequestHandler.filename = args.dir + "/" + args.name
        UIDLRequestHandler.hub_url = args.hub_url
        UIDLRequestHandler.session = str(args.session)
        UIDLRequestHandler.app = args.app
        UIDLRequestHandler.token = args.token
        UIDLRequestHandler.path = args.path
        UIDLRequestHandler.local = args.local
        with socketserver.TCPServer(
            (args.host, args.port), UIDLRequestHandler
        ) as httpd:
            print(
                "Nanohub UIDL Server started at port",
                args.port,
                "using filename",
                args.name,
            )
            print(
                "Server running on "
                + args.hub_url.replace("://", "://proxy.")
                + args.path
            )
            try:
                # Run the web server
                httpd.serve_forever()
            except KeyboardInterrupt:
                httpd.server_close()
                print("Nanohub UIDL server has stopped.")
