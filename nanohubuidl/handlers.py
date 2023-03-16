"""API handlers for the Jupyter Server example."""
from jupyter_server.extension.handler import ExtensionHandlerJinjaMixin, ExtensionHandlerMixin
from jupyter_server.utils import url_escape
from notebook.base.handlers import IPythonHandler, FilesRedirectHandler, path_regex
import tornado
import re
import os
import io
import random
import shutil
import datetime as dt
from threading import Thread
from multiprocessing import Process, Manager
import requests
from requests.models import Response
import nanohubremote as nr
from http import HTTPStatus
import http.server
import json
import time
from urllib.parse import parse_qsl
import urllib
from simtool import findInstalledSimToolNotebooks, searchForSimTool
from simtool import getSimToolInputs, getSimToolOutputs, Run
from simtool.utils import (
    _get_inputs_dict,
    _get_inputs_cache_dict,
    getParamsFromDictionary,
)
import simtool
import sys
import http.client
import email.utils
import mimetypes
import posixpath
import base64
import traceback

import tempfile
from PIL import Image
import PIL

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
                if pos == len(elements) - 3:
                    obj = self.schemaTask(elements[pos + 1], elements[pos + 2])
                elif pos == len(elements) - 2:
                    obj = self.schemaTask(elements[pos + 1], None)
                else:
                    obj._content = bytes("Not Found", "utf8")
                    obj.status_code = 404
            except Exception as e:
                traceback.print_exc()
                obj._content = bytes(str(e), "utf8")
                obj.status_code = 500
            except:
                traceback.print_exc()
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
        tool = tool.replace("+","/")
        obj = Response()
        response = {}
        t = time.time()
        simToolName = tool
        simToolRevision = revision
        if simToolRevision is not None:
            simToolRevision = "r"+str(simToolRevision)
        simToolLocation = searchForSimTool(simToolName, simToolRevision)
        if(simToolLocation["notebookPath"] is None):
            obj = Response()
            obj._content = bytes("Tool not Found", "utf8")
            obj.status_code = 404
            return obj;
        
        inputs = getSimToolInputs(simToolLocation)
        outputs = getSimToolOutputs(simToolLocation)
        response["inputs"] = {}
        for k in inputs:
            response["inputs"][k] = {}
            for k2 in inputs[k]:
                try:
                    json.dumps(inputs[k][k2])
                    response["inputs"][k][k2] = inputs[k][k2]
                except:
                    response["inputs"][k][k2] = str(inputs[k][k2])
        response["outputs"] = {}
        for k in outputs:
            response["outputs"][k] = {}
            for k2 in outputs[k]:
                try:
                    json.dumps(outputs[k][k2])
                    response["outputs"][k][k2] = outputs[k][k2]
                except:
                    response["outputs"][k][k2] = str(outputs[k][k2])
        response["message"] = None
        response["response_time"] = time.time() - t
        response["success"] = True
        if simToolLocation["published"]:
            response["state"] = "published"
        else:
            response["state"] = "installed"
        response["name"] = str(simToolName)
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
        simToolName = request["name"].replace("+","/")
        simToolRevision = request["revision"]
        if simToolRevision is not None:
            simToolRevision = "r"+str(simToolRevision)
        simToolLocation = searchForSimTool(simToolName, simToolRevision)
        print(simToolLocation)
        if(simToolLocation["notebookPath"] is None):
            obj = Response()
            obj._content = bytes("Tool not Found", "utf8")
            obj.status_code = 404
            return obj;
        
        simToolName = request["name"]
        if request["revision"] == "0":
            simToolRevision = None
        else:
            simToolRevision = "r" + request["revision"]

        inputsSchema = getSimToolInputs(simToolLocation)
        
        for k,v in request["inputs"].items():
            if isinstance(v, str) and v.startswith('base64://'):
                #if inputsSchema[k].type == "Image":
                #    request["inputs"][k] = Image.open(io.BytesIO(base64.b64decode(v[9:])))
                if inputsSchema[k].type == "Image" or inputsSchema[k].type == "File":
                    fname = os.path.join(self.jobspath, ".tmp." + next(tempfile._get_candidate_names()))
                    while (os.path.exists(fname)):
                        fname = os.path.join(self.jobspath, ".tmp." + next(tempfile._get_candidate_names()))
                    with open(fname, "wb") as f:
                        f.write(base64.b64decode(v[9:]))
                    request["inputs"][k] = "file://" + fname
        inputs = getParamsFromDictionary(inputsSchema, request["inputs"])
        hashableInputs = _get_inputs_cache_dict(inputs)
        response["userinputs"] = _get_inputs_dict(inputs)
        try:
            ds = simtool.datastore.WSDataStore(
                simToolName, simToolRevision, hashableInputs, self.squiddb
            )
            squid = ds.getSimToolSquidId()
            jobid = self.searchJobId(squid.replace("/r", "/"))
        except:
            jobid = None
            
        if jobid is not None:
            jobpath = os.path.join(self.jobspath, "_" + str(jobid))
            with open(os.path.join(jobpath, ".outputs"), "w") as outfile:
                json.dump(request["outputs"], outfile)
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
                    out = {}
                    complete = True
                    for o in request["outputs"]:
                        if o in req_json["results"][0]:
                            out[o.replace("output.", "", 1)] = req_json["results"][0][o]
                        else:
                            complete = False
                    if complete:
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
                    all_outputs = r.db.getSavedOutputs()
                    for o in all_outputs:
                        try:
                            out = r.read(o)
                            json.dumps(out)
                            dictionary[o] = out
                        except:
                            try:
                                out = r.read(o)
                                if isinstance(out, PIL.Image.Image):
                                    buffered = io.BytesIO()
                                    iformat = "PNG"
                                    imime = "image/png"
                                    if out.format is not None:
                                        iformat = out.format
                                        imime = out.get_format_mimetype()
                                    out.save(buffered, format=iformat)
                                    out = "data:" + imime + ";base64," + base64.b64encode(buffered.getvalue()).decode() 
                                    dictionary[o] = out
                                elif isinstance(out, (bytes, bytearray)):
                                    print (o, out)
                                    out = "data:application/octet-stream;base64," + base64.b64encode(out).decode()               
                                    dictionary[o] = out

                            except:
                                traceback.print_exc()
                                print (o + "can not be serialized")
                                    
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
                    with open(os.path.join(jobpath, ".outputs"), "w") as outfile:
                        json.dump(outputs, outfile)
                    with open(os.path.join(jobpath, ".results"), "w") as outfile:
                        json.dump(dictionary, outfile)
                    if os.path.isfile(os.path.join(jobpath, ".squidid")):
                        id = open(os.path.join(jobpath, ".squidid"), "r").read().strip()
                        for k in inputs:
                            v = inputs[k].value
                            if isinstance(v, str) and ".tmp." in v :
                                os.unlink(f.name)
                        self.squidmap[id] = jobid

        except Exception as e:
            traceback.print_exc()
            error = {"message": str(e), "code": 500}
            with open(os.path.join(jobpath, ".error"), "w") as outfile:
                json.dump(error, outfile)
        except:
            traceback.print_exc()
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
                    if os.path.isfile(results):
                        outputs = os.path.join(jobpath, ".outputs")
                        if os.path.isfile(outputs):
                            out = {}
                            outl = json.load(open(outputs, "r"))
                            res = json.load(open(results, "r"))
                            for o in outl:
                                if o in res:
                                    out[o] = res[o]
                                    
                            if "_id_" not in out:
                                if os.path.isfile(os.path.join(jobpath, ".squidid")):
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
            traceback.print_exc()
            obj.status_code = 500
            obj._content = bytes(str(e), "utf8")
        except:
            traceback.print_exc()
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
            parent = os.path.dirname(os.path.abspath(UIDLRequestHandler.filename))
            path = os.path.join(parent, path)
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
    
def UIDLLocalHandlerSettings():
    settings = {}
    fn = os.path.join(os.environ["SESSIONDIR"], "resources")
    with open(fn, "r") as f:
        res = f.read()
    for line in res.split("\n"):
        if line.startswith("hub_url"):
            settings['hub_url'] = line.split()[1]
        elif line.startswith("sessionid"):
            settings['session'] = int(line.split()[1])
        elif line.startswith("application_name"):
            settings['app'] = line.split(" ", 1)[1]
        elif line.startswith("session_token"):
            settings['token'] = line.split()[1]
        elif line.startswith("filexfer_cookie"):
            settings['cookie'] = line.split()[1]
        elif line.startswith("filexfer_port"):
            settings['cookieport'] = line.split()[1]
    settings['path'] = (
        "/weber/"
        + str(settings['session'])
        + "/"
        + str(settings['cookie'])
        + "/"
        + str(int(settings['cookieport']) % 1000)
        + "/"
    )
    return settings

class UIDLHandler(IPythonHandler):
    _settings = UIDLLocalHandlerSettings()
    
    def filter_data(self):
        field_data = self.request.body
        try:
            json.loads(field_data.decode())
            data = field_data
        except:
            data = dict(parse_qsl(field_data))
        return data
    
    def rewrite(self, text, basefile, method="local"):
        
        text = text.replace(
                "url = '" + UIDLHandler._settings['hub_url'] + "/api/",
                "url = '" + UIDLHandler._settings['path'] + "uidl/" + basefile + "/" + method + "/api/",
            )

        ticket = (
            str(UIDLHandler._settings['hub_url'])
            + "/feedback/report_problems?group=app-"
            + str(UIDLHandler._settings['app'].replace('"', "").replace(" ", "_"))
        )
        close = (
            str(UIDLHandler._settings['hub_url'])
            + "/tools/anonymous/stop?sess="
            + str(UIDLHandler._settings['session'])
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
                + UIDLHandler._settings['token']
                + "&"
                + text[res.end() :]
            )
        res = re.search("sessionnum=([0-9])+&", text)
        if res is not None:
            text = (
                text[: res.start()]
                + "sessionnum="
                + str(UIDLHandler._settings['session'])
                + "&"
                + text[res.end() :]
            )
        return text;

    @tornado.web.authenticated
    def post(self, *args, **kwargs):
        self.log.info('UIDLLocalHandler gets (POST): %s -  %s', args[0], args[1])
        self.get(*args, **kwargs)

    def get(self, *args, **kwargs):
        self.log.info('UIDLLocalHandler gets (GET): %s -  %s', args[0], args[1])
        basefile = args[0]
        path = args[1]
        return FilesRedirectHandler.redirect_to_files(self, path)

class UIDLLocalHandler(UIDLHandler):
    submit = SubmitLocal()
  
    @tornado.web.authenticated
    def post(self, *args, **kwargs):
        self.log.info('UIDLLocalHandler gets (POST): %s -  %s', args[0], args[1])
        self.get(*args, **kwargs)
        
    @tornado.web.authenticated
    def get(self, *args, **kwargs):
        self.log.info('UIDLLocalHandler gets (GET): %s -  %s', args[0], args[1])
        basefile = args[0]
        path = args[1]
        if path.endswith(basefile):
            with open(path) as file:
                text = file.read()
            text = self.rewrite(text, basefile, "local")
            self.finish(text)
        elif path.startswith("api/"):
            try:
                res = UIDLLocalHandler.submit.handle(path, self.filter_data())
                status = HTTPStatus(res.status_code)
                self.set_status(res.status_code)
                self.finish(res.text)
            except:
                raise tornado.web.HTTPError(500, 'Error')
        else:
            return FilesRedirectHandler.redirect_to_files(self, path)
               
        
class UIDLRedirectHandler(UIDLHandler):
    
    def filter_headers(self):
        headers = {}
        for h in str(self.request.headers).splitlines():
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
                else:
                    headers[sub[0]] = sub[1]
        return headers

    @tornado.web.authenticated
    def get(self, *args, **kwargs):
        self.log.info('UIDLRedirectHandler gets (GET): %s -  %s', args[0], args[1])
        basefile = args[0]
        path = args[1]
        if path.endswith(basefile):
            with open(path) as file:
                text = file.read()
            text = self.rewrite(text, basefile, "redirect")
            self.finish(text)
        elif path.startswith("api/"):
            try:
                url = UIDLHandler._settings['hub_url'] + "/" + path
                res = requests.get(
                    url, headers=self.filter_headers(), data=self.filter_data(), allow_redirects=False
                )
                self.set_status(res.status_code)
                self.finish(res.text)
            except:
                raise tornado.web.HTTPError(500, 'Error')
        else:
            return FilesRedirectHandler.redirect_to_files(self, path)

    def post(self, *args, **kwargs):
        self.log.info('UIDLRedirectHandler gets (GET): %s -  %s', args[0], args[1])
        basefile = args[0]
        path = args[1]
        if path.endswith(basefile):
            with open(path) as file:
                text = file.read()
            text = self.rewrite(text, basefile, "redirect")
            self.finish(text)
        elif path.startswith("api/"):
            try:
                url = UIDLHandler._settings['hub_url'] + "/" + path
                res = requests.post(
                    url, headers=self.filter_headers(), data=self.filter_data(), allow_redirects=False
                )
                self.set_status(res.status_code)
                self.finish(res.text)
            except:
                raise tornado.web.HTTPError(500, 'Error')
        else:
            return FilesRedirectHandler.redirect_to_files(self, path)       