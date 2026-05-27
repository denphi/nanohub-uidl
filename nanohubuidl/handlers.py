"""API handlers for the notebook server extension."""
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

REQUEST_TIMEOUT = 30
SCHEMA_CACHE_TTL = 60
SIMTOOL_ENV_KEYS = [
    "DISPLAY",
    "SESSIONDIR",
    "RESULTSDIR",
    "SESSION",
    "LANG",
    "LANGUAGE",
    "LC_ALL",
    "TIMEOUT",
    "SUBMIT_JOB",
    "RAPPTURE_CACHE_SQUID",
    "SIM2L_CACHE_SQUID",
]

class Singleton(object):
    _instance = None
    def __new__(class_, *args, **kwargs):
        if not isinstance(class_._instance, class_):
            class_._instance = object.__new__(class_, *args, **kwargs)
        return class_._instance

class SubmitLocal(Singleton):
    def __init__(self, *args, jobspath=None, **kwargs):
        if getattr(self, "_initialized", False):
            if jobspath is not None and os.path.abspath(jobspath) != os.path.abspath(self.jobspath):
                raise ValueError("SubmitLocal is already initialized with a different jobspath")
            return
        self._initialized = True
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
        self.session = None
        self.http_session = requests.Session()
        self._schema_cache = {}
        self._input_schema_cache = {}
        self._final_status_cache = {}
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

    def __getstate__(self):
        state = self.__dict__.copy()
        state.pop("http_session", None)
        state.pop("session", None)
        state.pop("_schema_cache", None)
        state.pop("_input_schema_cache", None)
        state.pop("_final_status_cache", None)
        return state

    def __setstate__(self, state):
        self.__dict__.update(state)
        self.session = None
        self.http_session = requests.Session()
        self._schema_cache = {}
        self._input_schema_cache = {}
        self._final_status_cache = {}

    def handle(self, url, data=None):
        if data is None:
            data = {}
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

    def _revision_key(self, revision):
        if revision is None:
            return None
        revision = str(revision)
        if revision == "0":
            return None
        if revision.startswith("r"):
            return revision
        return "r" + revision

    def _tool_cache_key(self, tool, revision):
        return (tool.replace("+", "/"), self._revision_key(revision))

    def _cache_get(self, cache, key):
        cached = cache.get(key)
        if cached is None:
            return None
        cached_at, value = cached
        if time.time() - cached_at > SCHEMA_CACHE_TTL:
            cache.pop(key, None)
            return None
        return value

    def _cache_set(self, cache, key, value):
        cache[key] = (time.time(), value)
        return value

    def _tool_mtime(self, location):
        path = location.get("notebookPath")
        if path is None or not os.path.exists(path):
            return None
        return os.path.getmtime(path)

    def _get_tool_location(self, tool, revision):
        key = self._tool_cache_key(tool, revision)
        cached = self._cache_get(self._schema_cache, key)
        if cached is not None:
            location, mtime = cached
            if mtime == self._tool_mtime(location):
                return location
            self._schema_cache.pop(key, None)
            self._schema_cache.pop(("response", key), None)
            self._input_schema_cache.pop(key, None)
        location = searchForSimTool(key[0], key[1])
        return self._cache_set(self._schema_cache, key, (location, self._tool_mtime(location)))[0]

    def _get_input_schema(self, tool, revision, location):
        key = self._tool_cache_key(tool, revision)
        cached = self._cache_get(self._input_schema_cache, key)
        if cached is not None:
            inputs, mtime = cached
            if mtime == self._tool_mtime(location):
                return inputs
            self._input_schema_cache.pop(key, None)
        inputs = getSimToolInputs(location)
        return self._cache_set(self._input_schema_cache, key, (inputs, self._tool_mtime(location)))[0]

    def _schema_response(self, tool, revision):
        key = self._tool_cache_key(tool, revision)
        simToolLocation = self._get_tool_location(tool, revision)
        if simToolLocation["notebookPath"] is None:
            return None

        cached = self._cache_get(self._schema_cache, ("response", key))
        if cached is not None:
            response, mtime = cached
            if mtime == self._tool_mtime(simToolLocation):
                return response
            self._schema_cache.pop(("response", key), None)

        inputs = self._get_input_schema(tool, revision, simToolLocation)
        outputs = getSimToolOutputs(simToolLocation)
        response = {
            "inputs": self._json_safe_schema(inputs),
            "outputs": self._json_safe_schema(outputs),
            "message": None,
            "success": True,
            "state": "published" if simToolLocation["published"] else "installed",
            "name": str(key[0]),
            "revision": str(simToolLocation["simToolRevision"]).replace("r", ""),
            "path": simToolLocation["notebookPath"],
            "type": "simtool",
        }
        return self._cache_set(self._schema_cache, ("response", key), (response, self._tool_mtime(simToolLocation)))[0]

    def _json_safe_schema(self, schema):
        response = {}
        for k in schema:
            response[k] = {}
            for k2 in schema[k]:
                try:
                    json.dumps(schema[k][k2])
                    response[k][k2] = schema[k][k2]
                except:
                    response[k][k2] = str(schema[k][k2])
        return response

    @staticmethod
    def _serialize_output(output):
        try:
            json.dumps(output)
            return output
        except:
            if isinstance(output, PIL.Image.Image):
                buffered = io.BytesIO()
                iformat = "PNG"
                imime = "image/png"
                if output.format is not None:
                    iformat = output.format
                    imime = output.get_format_mimetype()
                output.save(buffered, format=iformat)
                return "data:" + imime + ";base64," + base64.b64encode(buffered.getvalue()).decode()
            if isinstance(output, (bytes, bytearray)):
                return "data:application/octet-stream;base64," + base64.b64encode(output).decode()
            raise

    def schemaTask(self, tool, revision):
        obj = Response()
        t = time.time()
        response = self._schema_response(tool, revision)
        if response is None:
            obj = Response()
            obj._content = bytes("Tool not Found", "utf8")
            obj.status_code = 404
            return obj;

        response = response.copy()
        response["response_time"] = time.time() - t

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
        simToolLocation = self._get_tool_location(simToolName, simToolRevision)
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

        inputsSchema = self._get_input_schema(simToolName, request["revision"], simToolLocation)
        
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
        squid = None
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
            with open(os.path.join(self.jobspath, "." + str(jobid)), "w") as f:
                f.write("Setting up Sim2L\n")
                
            thread = Process(
                target=SubmitLocal.runJobState,
                args=(
                    self.basepath,
                    self.jobspath,
                    self.squidmap,
                    {k: os.environ[k] for k in SIMTOOL_ENV_KEYS if k in os.environ},
                    jobid,
                    simToolLocation,
                    inputs,
                    request["outputs"],
                ),
            )
            try:
                thread.start()
            except Exception as e:
                if not os.path.exists(jobpath):
                    os.makedirs(jobpath)
                with open(os.path.join(jobpath, ".error"), "w") as outfile:
                    json.dump({"message": str(e), "code": 500}, outfile)
            response["message"] = ""
            response["status"] = "QUEUED"
            response["id"] = jobid
            if squid is not None:
                response = self.checkResultsDB(squid, request, response)
            response["response_time"] = time.time() - t
            response["success"] = True
            obj.status_code = 200
            obj._content = bytes(json.dumps(response), "utf8")
            return obj

    def checkResultsDB(self, squid, request, response):
        try:
            if self.session is None:
                return response
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
                        if "output." + o in req_json["results"][0]:
                            out[o] = req_json["results"][0]["output." + o]
                        elif o in req_json["results"][0]:
                            out[o.replace("output.","",1)] = req_json["results"][0][o]
                        else:
                            print(o)
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
        return SubmitLocal.runJobState(
            self.basepath,
            self.jobspath,
            self.squidmap,
            {k: os.environ[k] for k in SIMTOOL_ENV_KEYS if k in os.environ},
            jobid,
            simToolLocation,
            inputs,
            outputs,
        )

    @staticmethod
    def runJobState(basepath, jobspath, squidmap, env, jobid, simToolLocation, inputs, outputs):
        jobpath = os.path.join(jobspath, "_" + str(jobid))
        try:
            with open(
                os.path.join(jobspath, "." + str(jobid)), "a", buffering=1
            ) as sys.stdout:
                with sys.stdout as sys.stderr:
                    os.environ.update(env)
                    SubmitLocal._runJobState(basepath, jobspath, squidmap, env, jobid, simToolLocation, inputs, outputs)
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

    @staticmethod
    def _runJobState(basepath, jobspath, squidmap, env, jobid, simToolLocation, inputs, outputs):
        jobpath = os.path.join(jobspath, "_" + str(jobid))
        try:
            dictionary = {}
            os.chdir(basepath)
            print("UIDL worker pid = " + str(os.getpid()))
            print("UIDL worker cwd = " + str(os.getcwd()))
            print("UIDL jobpath = " + str(jobpath))
            print("UIDL env keys = " + json.dumps(sorted(env.keys())))
            print("UIDL outputs requested = " + json.dumps(outputs))
            print("UIDL input keys = " + json.dumps(list(inputs.keys())))
            r = Run(simToolLocation, inputs, "_" + str(jobid))
            all_outputs = r.db.getSavedOutputs()
            output_names = [o for o in outputs if o in all_outputs]
            if len(output_names) == 0:
                output_names = all_outputs
            for o in output_names:
                try:
                    out = r.read(o)
                    dictionary[o] = SubmitLocal._serialize_output(out)
                except:
                    traceback.print_exc()
                    print (o + "can not be serialized")

            with open(os.path.join(jobspath, "." + str(jobid)), "r") as file:
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
                    with open(os.path.join(jobpath, ".done"), "w") as outfile:
                        json.dump("done", outfile)
                    if os.path.isfile(os.path.join(jobpath, ".squidid")):
                        id = open(os.path.join(jobpath, ".squidid"), "r").read().strip()
                        for k in inputs:
                            v = inputs[k].value
                            if isinstance(v, str) and v.startswith("file://") and ".tmp." in v:
                                tmp_path = v[7:]
                                if os.path.exists(tmp_path):
                                    os.unlink(tmp_path)
                        squidmap[id] = jobid

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
            jobidpath = os.path.join(self.jobspath, "." + str(jobid))
            jobpath = os.path.join(self.jobspath, "_" + str(jobid))
            if os.path.exists(jobpath):
                response["status"] = "RUNNING"
                errorpath = os.path.join(jobpath, ".error")
                if os.path.isfile(errorpath):
                    with open(errorpath, "r") as file:
                        er = json.load(file)
                    response["message"] = er["message"]
                    response["status"] = "ERROR"
                    obj.status_code = er["code"]
                else:
                    done = os.path.join(jobpath, ".done")
                    results = os.path.join(jobpath, ".results")
                    if os.path.isfile(done) and os.path.isfile(results):
                        cached = self._final_status_response(jobid, jobpath)
                        if cached is not None:
                            response.update(cached)
                    elif os.path.exists(jobidpath):
                        response["message"] = self.lastSim2lLog(jobidpath, response["status"])
                        response["status"] = response["message"]
            elif os.path.exists(jobidpath):
                response["status"] = "STAGGING"
                response["message"] = self.lastSim2lLog(jobidpath, response["status"])
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

    def _final_status_response(self, jobid, jobpath):
        outputs = os.path.join(jobpath, ".outputs")
        results = os.path.join(jobpath, ".results")
        squid = os.path.join(jobpath, ".squidid")

        mtimes = (
            os.path.getmtime(outputs) if os.path.isfile(outputs) else None,
            os.path.getmtime(results),
            os.path.getmtime(squid) if os.path.isfile(squid) else None,
        )
        cached = self._final_status_cache.get(jobid)
        if cached is not None and cached[0] == mtimes:
            return cached[1]

        out = {}
        with open(results, "r") as file:
            res = json.load(file)
        if os.path.isfile(outputs):
            with open(outputs, "r") as file:
                outl = json.load(file)
        else:
            outl = list(res.keys())
        for o in outl:
            if o in res:
                out[o] = res[o]

        if "_id_" not in out and os.path.isfile(squid):
            with open(squid, "r") as file:
                out["_id_"] = file.read()

        response = {
            "message": None,
            "outputs": out,
            "status": "CACHED",
        }
        self._final_status_cache[jobid] = (mtimes, response)
        return response

    def lastSim2lLog(self, log, default):
        if hasattr(log, "name"):
            log = log.name
        with open(log, "rb") as file:
            file.seek(0, os.SEEK_END)
            size = file.tell()
            file.seek(max(size - 8192, 0), os.SEEK_SET)
            logs = file.read().decode("utf8", errors="replace")
        lastlog = default
        for line in re.split(r"[\r\n]+", logs):
            line = self.cleanSim2lLogLine(line)
            if len(line.strip()) > 5:
                lastlog = line
        return lastlog

    def cleanSim2lLogLine(self, line):
        line = re.sub(r"\x1b\[[0-9;?]*[A-Za-z]", "", line)
        line = line.replace("\x00", "").strip()
        if line.startswith("Executing:"):
            line = re.sub(r"\s+", " ", line)
        return line

    def authTask(self, request):
        obj = Response()
        obj.status_code = 200
        try:
            sessionid = "0";
            if "sessionid" in os.environ:
                sessionid = os.environ["sessionid"]
            response = {
                "access_token": "session" + str(sessionid),
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

    def __init__(self, *args, directory=None, **kwargs):
        self.submit = SubmitLocal()
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

            appl = (
                UIDLRequestHandler.hub_url
                + "/tools/"
                + UIDLRequestHandler.app.replace('"', "")
            )           

            header = (
                '<div style="position: fixed;z-index: 1000000;top: 0px;right: 170px;"><button title="Report a problem" onclick="window.open(\''
                + ticket
                + '\')" style="color: #333;padding: 7px 15px;border: 0px;">Submit a ticket</button>&nbsp;&nbsp;<button class="btn btn-sm navbar-btn" title="Go Back to Tool Page, Keep session for later" onclick="window.location.href=\''
                + appl
                + '\'" style="color: #333;padding: 7px 15px;border: 0px;">Keep for later</button>&nbsp;&nbsp;<button class="btn btn-sm navbar-btn" title="Terminate this notebook or tool and any others in the session" onclick="window.location.href=\''
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
                    res = self.submit.handle(url, data)
                else:
                    if method == "post":
                        res = self.submit.http_session.post(
                            url, headers=headers, data=data, allow_redirects=False, timeout=REQUEST_TIMEOUT
                        )
                    else:
                        res = self.submit.http_session.get(
                            url, headers=headers, data=data, allow_redirects=False, timeout=REQUEST_TIMEOUT
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
    if "SESSIONDIR" in os.environ:
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
    else:
        settings['hub_url'] = "https://nanohub.org"
        settings['path'] = "/"
        settings['session'] = 0
        settings['token'] = "000"
        settings['app'] = ""

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

        text = text.replace(
            "Axios.request(url,",
            "Axios.request(url + '?_xsrf=' + getCookie('_xsrf'),",
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
    @tornado.web.authenticated
    def post(self, *args, **kwargs):
        self.log.info('UIDLLocalHandler gets (POST): %s -  %s', args[0], args[1])
        self.get(*args, **kwargs)
        
    @tornado.web.authenticated
    def get(self, *args, **kwargs):
        submit = SubmitLocal()

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
                res = submit.handle(path, self.filter_data())
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
        submit = SubmitLocal()
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
                res = submit.http_session.get(
                    url, headers=self.filter_headers(), data=self.filter_data(), allow_redirects=False, timeout=REQUEST_TIMEOUT
                )
                self.set_status(res.status_code)
                self.finish(res.text)
            except:
                raise tornado.web.HTTPError(500, 'Error')
        else:
            return FilesRedirectHandler.redirect_to_files(self, path)

    def post(self, *args, **kwargs):
        submit = SubmitLocal()
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
                res = submit.http_session.post(
                    url, headers=self.filter_headers(), data=self.filter_data(), allow_redirects=False, timeout=REQUEST_TIMEOUT
                )
                self.set_status(res.status_code)
                self.finish(res.text)
            except:
                raise tornado.web.HTTPError(500, 'Error')
        else:
            return FilesRedirectHandler.redirect_to_files(self, path)       
