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
import email.utils
import mimetypes
import io
import os
import posixpath
import shutil
import socketserver
import sys
import time
import json
import datetime as dt
from http import HTTPStatus
import http.server
import requests
from urllib.parse import parse_qsl
import urllib
import re
import argparse
import simtool
import nanohubremote as nr

from simtool import findInstalledSimToolNotebooks, searchForSimTool
from simtool import getSimToolInputs, getSimToolOutputs, Run
from simtool.utils import (
    _get_inputs_dict,
    _get_inputs_cache_dict,
    getParamsFromDictionary,
)
import random
from threading import Thread
from multiprocessing import Process, Manager
from requests.models import Response


class SubmitLocal:
    def __init__(self, *args, jobspath=None, **kwargs):
        self.basepath = os.getcwd()
        if "RESULTSDIR" in os.environ:
            self.basepath = os.environ["RESULTSDIR"]
            if not os.path.exists(self.basepath):
                os.makedirs(self.basepath)
        if jobspath is None:
            jobspath = os.path.join(self.basepath, "RUNS")

        if not os.path.exists(jobspath):
            os.makedirs(jobspath)
        self.jobspath = jobspath
        manager = Manager()
        self.squidmap = manager.dict()
        self.squiddb = ""
        for subdir, dirs, files in os.walk(jobspath):
            for file in files:
                if file == ".squidid":
                    jobid = subdir.split("_", 1)
                    if len(jobid) == 2:
                        id = open(os.path.join(subdir, file), "r").read().strip()
                        self.squidmap[id] = jobid[1]

        if "rpath_user" in os.environ:
            resourcePath = os.environ["rpath_user"]

            with open(resourcePath) as file:
                records = file.readlines()
                lines = [r.split(" ", 1) for r in records]
                properties = {l[0].strip(): l[1].strip() for l in lines if len(l) == 2}
                self.squiddb = properties["squiddb"]
                auth_data = {
                    "grant_type": "tool",
                    "sessiontoken": properties["session_token"],
                    "sessionnum": properties["sessionid"],
                }
                self.session = nr.Session(auth_data)

    def handle(self, url, data={}):
        obj = Response()
        if "api/developer/oauth/token" in url:
            obj = self.authTask(data)
        elif "api/results/simtools/get" in url:
            elements = url.split("/")
            try:
                pos = elements.index("get")
                if pos == len(elements) - 2:
                    obj = self.schemaTask(elements[pos + 1], elements[pos + 2])
                elif pos == len(elements) - 3:
                    obj = self.schemaTask(elements[pos + 1], None)
                else:
                    obj._content = bytes("Not Found", "utf8")
                    obj.status_code = 404
            except Exception as e:
                obj._content = bytes(str(e), "utf8")
                obj.status_code = 500
            except:
                obj._content = bytes("Server Error", "utf8")
                obj.status_code = 500
        elif "api/results/simtools/run" in url:
            elements = url.split("/")
            try:
                pos = elements.index("run")
                if pos == len(elements) - 1:
                    obj = self.runTask(json.loads(data.decode("utf8")))
                elif pos == len(elements) - 2:
                    obj = self.statusTask(elements[pos + 1])
                else:
                    obj._content = bytes("Not Found", "utf8")
                    obj.status_code = 404
            except Exception as e:
                obj._content = bytes(str(e), "utf8")
                obj.status_code = 500
            except:
                obj._content = bytes("Server Error", "utf8")
                obj.status_code = 500
        else:
            obj = Response()
            obj._content = bytes("Not Found", "utf8")
            obj.status_code = 404
        return obj

    def schemaTask(self, tool, revision):
        obj = Response()
        response = {}
        t = time.time()
        simToolName = tool
        simToolRevision = revision
        simToolLocation = searchForSimTool(simToolName)
        inputs = getSimToolInputs(simToolLocation)
        outputs = getSimToolOutputs(simToolLocation)
        response["inputs"] = {}
        for k in inputs:
            response["inputs"][k] = {}
            for k2 in inputs[k]:
                response["inputs"][k][k2] = str(inputs[k][k2])
        response["outputs"] = {}
        for k in outputs:
            response["outputs"][k] = {}
            for k2 in outputs[k]:
                response["outputs"][k][k2] = str(outputs[k][k2])
        response["message"] = None
        response["response_time"] = time.time() - t
        response["success"] = True
        if simToolLocation["published"]:
            response["state"] = "published"
        else:
            response["state"] = "installed"
        response["name"] = str(simToolLocation["simToolName"])
        response["revision"] = str(simToolLocation["simToolRevision"]).replace("r", "")
        response["path"] = simToolLocation["notebookPath"]
        response["type"] = "simtool"

        obj.status_code = 200
        obj._content = bytes(json.dumps({"tool": response}), "utf8")
        return obj

    def searchJobId(self, squidid):
        if str(squidid) in self.squidmap.keys():
            return self.squidmap[squidid]
        else:
            return None

    def runTask(self, request):
        obj = Response()
        response = {}
        t = time.time()
        simToolName = request["name"]
        simToolRevision = request["revision"]
        simToolLocation = searchForSimTool(simToolName)
        simToolName = request["name"]
        simToolRevision = "r" + request["revision"]
        simToolLocation = searchForSimTool(simToolName, simToolRevision)
        inputsSchema = getSimToolInputs(simToolLocation)
        inputs = getParamsFromDictionary(inputsSchema, request["inputs"])
        hashableInputs = _get_inputs_cache_dict(inputs)
        response["userinputs"] = _get_inputs_dict(inputs)
        ds = simtool.datastore.WSDataStore(
            simToolName, simToolRevision, hashableInputs, self.squiddb
        )
        squid = ds.getSimToolSquidId()
        jobid = self.searchJobId(squid.replace("/r", "/"))
        if jobid is not None:
            return self.statusTask(jobid)
        else:
            jobid = random.randint(1, 100000)
            created = False
            while created == False:
                jobpath = os.path.join(self.jobspath, "_" + str(jobid))
                if os.path.exists(jobpath):
                    jobid = random.randint(1, 100000)
                    created = False
                else:
                    created = True
            thread = Process(
                target=SubmitLocal.runJob,
                args=(self, jobid, simToolLocation, inputs, request["outputs"]),
            )
            thread.start()
            response["message"] = ""
            response["status"] = "QUEUED"
            response["id"] = jobid
            response = self.checkResultsDB(squid, request, response)
            response["response_time"] = time.time() - t
            response["success"] = True
            obj.status_code = 200
            obj._content = bytes(json.dumps(response), "utf8")
            return obj

    def checkResultsDB(self, squid, request, response):
        try:
            search = {
                "tool": request["name"],
                "revision": request["revision"],
                "filters": json.dumps(
                    [
                        {"field": "squid", "operation": "=", "value": squid},
                    ]
                ),
                "results": json.dumps(
                    ["output." + o for o in request["outputs"]],
                ),
                "simtool": True,
                "limit": 1,
            }
            req_json = self.session.requestPost(
                "results/dbexplorer/search", data=search
            )
            req_json = req_json.json()
            if "results" in req_json:
                if len(req_json["results"]) == 1:
                    out = {
                        k.replace("output.", "", 1): v
                        for k, v in req_json["results"][0].items()
                    }
                    out["_id_"] = squid
                    response["message"] = None
                    response["outputs"] = out
                    response["status"] = "INDEXED"
        except:
            pass
        return response

    def runJob(self, jobid, simToolLocation, inputs, outputs):
        try:
            jobpath = os.path.join(self.jobspath, "_" + str(jobid))
            with open(
                os.path.join(self.jobspath, "." + str(jobid)), "w", buffering=1
            ) as sys.stdout:
                with sys.stdout as sys.stderr:
                    dictionary = {}
                    os.chdir(self.basepath)
                    r = Run(simToolLocation, inputs, "_" + str(jobid))
                    for o in outputs:
                        try:
                            dictionary[o] = r.read(o)
                        except:
                            pass
            with open(os.path.join(self.jobspath, "." + str(jobid)), "r") as file:
                logs = file.read()
                if "SimTool execution failed" in logs:
                    with open(os.path.join(jobpath, ".error"), "w") as outfile:
                        error = {
                            "message": "SimTool execution failed (" + jobpath + ")",
                            "code": 500,
                        }
                        json.dump(error, outfile)
                else:
                    with open(os.path.join(jobpath, ".results"), "w") as outfile:
                        json.dump(dictionary, outfile)
                    id = open(os.path.join(jobpath, ".squidid"), "r").read().strip()
                    self.squidmap[id] = jobid

        except Exception as e:
            error = {"message": e.message(), "code": 500}
            with open(os.path.join(jobpath, ".error"), "w") as outfile:
                json.dump(error, outfile)
        except:
            error = {"message": "Server Error", "code": 500}
            with open(os.path.join(jobpath, ".error"), "w") as outfile:
                json.dump(error, outfile)
        return

    def statusTask(self, jobid):
        obj = Response()
        obj.status_code = 200
        try:
            response = {}
            response["id"] = jobid
            t = time.time()
            jobpath = os.path.join(self.jobspath, "_" + str(jobid))
            if os.path.exists(jobpath):
                response["status"] = "RUNNING"
                errorpath = os.path.join(jobpath, ".error")
                if os.path.isfile(errorpath):
                    er = json.load(
                        open(
                            errorpath,
                        )
                    )
                    response["message"] = er["message"]
                    response["status"] = "ERROR"
                    obj.status_code = er["code"]
                else:
                    results = os.path.join(jobpath, ".results")
                    print(results)
                    if os.path.isfile(results):
                        out = json.load(open(results, "r"))
                        out["_id_"] = open(
                            os.path.join(jobpath, ".squidid"), "r"
                        ).read()
                        response["message"] = None
                        response["outputs"] = out
                        response["status"] = "CACHED"
                    else:
                        jobidpath = os.path.join(self.jobspath, "." + str(jobid))
                        with open(jobidpath, "r") as log:
                            response["message"] = self.lastSim2lLog(
                                log, response["status"]
                            )
                            response["status"] = response["message"]
            else:
                response["message"] = ""
                response["status"] = "NOT FOUND"
                obj.status_code = 404

            response["response_time"] = time.time() - t
            response["success"] = True
            obj._content = bytes(json.dumps(response), "utf8")
        except Exception as e:
            print(e)
            obj.status_code = 500
            obj._content = bytes(str(e), "utf8")
        except:
            obj.status_code = 500
            obj._content = bytes("Unknown", "utf8")
        return obj

    def lastSim2lLog(self, log, default):
        logs = log.read()
        logs = logs.split("\n")
        lastlog = default
        for l in logs:
            if len(l.strip()) > 5:
                lastlog = l
        return lastlog

    def authTask(self, request):
        obj = Response()
        obj.status_code = 200
        try:
            response = {
                "access_token": "session" + os.environ["sessionid"],
                "expires_in": 3600,
                "token_type": "Bearer",
                "scope": None,
            }
            obj._content = bytes(json.dumps(response), "utf8")
        except Exception as e:
            obj.status_code = 500
            obj._content = bytes(str(e), "utf8")
        except:
            obj.status_code = 500
            obj._content = bytes("Unknown", "utf8")

        return obj


class UIDLRequestHandler(http.server.BaseHTTPRequestHandler):
    # protocol_version = 'HTTP/1.1'
    filename = ""
    hub_url = ""
    session = ""
    app = ""
    token = ""
    path = ""
    local = False
    submit = SubmitLocal()

    def __init__(self, *args, directory=None, **kwargs):
        if directory is None:
            directory = os.getcwd()
        self.directory = directory
        if not mimetypes.inited:
            mimetypes.init()  # try to read system mime.types
        self.extensions_map = mimetypes.types_map.copy()
        self.extensions_map.update(
            {
                "": "application/octet-stream",  # Default
                ".py": "text/plain",
                ".c": "text/plain",
                ".h": "text/plain",
            }
        )
        super().__init__(*args, **kwargs)

    def do_REQUEST(self, method):
        path = self.translate_path(self.path)
        status = HTTPStatus.OK
        contenttype = "text/html"
        close = (
            UIDLRequestHandler.hub_url
            + "/tools/anonymous/stop?sess="
            + UIDLRequestHandler.session
        )
        text = (
            """<!DOCTYPE html>
            <html>
                <body>
                    <p>"""
            + path
            + """ Not Found</p>
                    <p>"""
            + UIDLRequestHandler.filename
            + """ Not Found</p>
                    <div style="position: fixed;z-index: 1000000;top: 0px;right: 170px;"><button class="btn btn-sm navbar-btn" title="Terminate this notebook or tool and any others in the session" onclick="window.location.href=\'"""
            + close
            + """\'" style="color: #333;padding: 7px 15px;border: 0px;">Terminate Session</button></div>
                </body>
            </html>"""
        )

        if os.path.exists(UIDLRequestHandler.filename) is False:
            status = HTTPStatus(404)

        elif path in ["", "/", "index.htm", "index.html", UIDLRequestHandler.filename]:
            with open(UIDLRequestHandler.filename) as file:
                text = file.read()

            text = text.replace(
                "url = '" + UIDLRequestHandler.hub_url + "/api/",
                "url = '" + UIDLRequestHandler.path + "api/",
            )

            ticket = (
                UIDLRequestHandler.hub_url
                + "/feedback/report_problems?group=app-"
                + UIDLRequestHandler.app.replace('"', "").replace(" ", "_")
            )

            header = (
                '<div style="position: fixed;z-index: 1000000;top: 0px;right: 170px;"><button title="Report a problem" onclick="window.open(\''
                + ticket
                + '\')" style="color: #333;padding: 7px 15px;border: 0px;">Submit a ticket</button>&nbsp;&nbsp;<button class="btn btn-sm navbar-btn" title="Terminate this notebook or tool and any others in the session" onclick="window.location.href=\''
                + close
                + '\'" style="color: #333;padding: 7px 15px;border: 0px;">Terminate Session</button></div>'
            )
            res = re.search("<body(?:\"[^\"]*\"['\"]*|'[^']*'['\"]*|[^'\">])+>", text)
            if res is not None:
                index = res.end() + 1
                text = text[:index] + header + text[index:]
            res = re.search("sessiontoken=([0-9a-zA-Z])+&", text)
            if res is not None:
                text = (
                    text[: res.start()]
                    + "sessiontoken="
                    + UIDLRequestHandler.token
                    + "&"
                    + text[res.end() :]
                )
            res = re.search("sessionnum=([0-9])+&", text)
            if res is not None:
                text = (
                    text[: res.start()]
                    + "sessionnum="
                    + UIDLRequestHandler.session
                    + "&"
                    + text[res.end() :]
                )
        elif path.startswith("api/"):
            try:
                headers = {}
                contentlength = 0
                data = {}
                url = UIDLRequestHandler.hub_url + "/" + path
                for h in str(self.headers).splitlines():
                    sub = h.split(":", 1)
                    if len(sub) == 2:
                        sub[0] = sub[0].strip()
                        sub[1] = sub[1].strip()
                        if sub[0].lower() in [
                            "host",
                            "connection",
                            "referer",
                            "origin",
                            "x-real-ip",
                        ]:
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
                if UIDLRequestHandler.local:
                    res = UIDLRequestHandler.submit.handle(url, data)
                else:
                    if method == "post":
                        res = requests.post(
                            url, headers=headers, data=data, allow_redirects=False
                        )
                    else:
                        res = requests.get(
                            url, headers=headers, data=data, allow_redirects=False
                        )
                status = HTTPStatus(res.status_code)
                text = res.text
            except:
                status = HTTPStatus.INTERNAL_SERVER_ERROR
                raise
        else:
            if os.path.exists(path):
                try:
                    ctype = self.guess_type(path)
                    f = open(path, "rb")
                    fs = os.fstat(f.fileno())

                    if (
                        "If-Modified-Since" in self.headers
                        and "If-None-Match" not in self.headers
                    ):
                        try:
                            ims = email.utils.parsedate_to_datetime(
                                self.headers["If-Modified-Since"]
                            )
                        except (TypeError, IndexError, OverflowError, ValueError):
                            pass
                        else:
                            if ims.tzinfo is None:
                                ims = ims.replace(tzinfo=dt.timezone.utc)
                            if ims.tzinfo is dt.timezone.utc:
                                last_modif = dt.datetime.fromtimestamp(
                                    fs.st_mtime, dt.timezone.utc
                                )
                                last_modif = last_modif.replace(microsecond=0)
                                if last_modif <= ims:
                                    self.send_response(HTTPStatus.NOT_MODIFIED)
                                    self.end_headers()
                                    f.close()
                            return None

                    self.send_response(HTTPStatus.OK)
                    self.send_header("Content-type", ctype)
                    self.send_header("Content-Length", str(fs[6]))
                    self.send_header(
                        "Last-Modified", self.date_time_string(fs.st_mtime)
                    )
                    # self.send_header("X-Content-Type-Options", "nosniff")
                    # self.send_header("Accept-Ranges", "bytes")
                    # self.send_header("Cache-Control", "no-cache")
                    self.end_headers()
                    if f:
                        try:
                            shutil.copyfileobj(f, self.wfile)
                        finally:
                            f.close()
                    return
                except:
                    status = HTTPStatus.INTERNAL_SERVER_ERROR
                    raise Exception("Not Supported File")
            else:
                status = HTTPStatus(404)
        try:
            f = io.BytesIO()
            f.write(bytes(text, "utf-8"))
            f.seek(0)
            self.send_response(status)
            self.send_header("Content-type", contenttype)
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

    def guess_type(self, path):

        base, ext = posixpath.splitext(path)
        if ext in self.extensions_map:
            return self.extensions_map[ext]
        ext = ext.lower()
        if ext in self.extensions_map:
            return self.extensions_map[ext]
        else:
            return self.extensions_map[""]

    def do_GET(self):
        self.do_REQUEST("get")

    def do_POST(self):
        self.do_REQUEST("post")

    def translate_path(self, path):
        # abandon query parameters
        path = path.split("?", 1)[0]
        path = path.split("#", 1)[0]
        # Don't forget explicit trailing slash when normalizing. Issue17324
        trailing_slash = path.rstrip().endswith("/")
        try:
            path = urllib.parse.unquote(path, errors="surrogatepass")
        except UnicodeDecodeError:
            path = urllib.parse.unquote(path)
        path = posixpath.normpath(path)
        words = path.split("/")
        if words[1] == "weber":
            words = words[5:]
        else:
            words = words[1:]
        words = [w for w in words if w is not None]
        path = "/".join(words)
        if trailing_slash:
            path += "/"
        return path


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
