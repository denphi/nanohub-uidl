import json
import uuid
import os
import requests
import warnings
import psutil
from IPython.display import HTML, Javascript, display
from .core import TeleportNode, TeleportGlobals
from .elements import TeleportElement, TeleportContent
from .utils import NanohubUtils

class TeleportComponent:
    def __init__(self, name_component, node, *args, **kwargs):
        self.name_component = name_component
        self.propDefinitions = {}
        self.stateDefinitions = {}
        self.node = node

    def __json__(self):
        return {
            "name": self.name_component,
            "propDefinitions": self.propDefinitions,
            "stateDefinitions": self.stateDefinitions,
            "node": self.node.__json__(),
        }

    def __str__(self):
        return json.dumps(self.__json__())

    def getNodeTypes(self):
        return self.node.content.getNodeTypes()

    def addNode(self, child):
        if isinstance(child, TeleportNode):
            self.node.addContent(child)
        else:
            raise AttributeError("children have to be TeleportNode types")

    def addStateVariable(self, state, definition={"type": "string", "defaultValue": ""}):
        if isinstance(definition, dict):
            if "type" in definition and "defaultValue" in definition:
                self.stateDefinitions[state] = {
                    "type": definition["type"],
                    "defaultValue": definition["defaultValue"],
                }
            else:
                raise AttributeError(
                    "type and/or defaultValue are missing on the definition"
                )

        else:
            raise AttributeError("definition should be a dict")

    def addPropVariable(self, state, definition={"type": "string", "defaultValue": ""}):
        if isinstance(definition, dict):
            if "type" in definition and definition["type"] == "func":
                if "defaultValue" not in definition:
                    definition["defaultValue"] = "() => {}"
                self.propDefinitions[state] = {
                    "type": definition["type"],
                    "defaultValue": definition["defaultValue"],
                }
            elif "type" in definition and "defaultValue" in definition:
                self.propDefinitions[state] = {
                    "type": definition["type"],
                    "defaultValue": definition["defaultValue"],
                }
            else:
                raise AttributeError(
                    "type and/or defaultValue are missing on the definition"
                )

        else:
            raise AttributeError("definition should be a dict")

    def buildReact(self, componentName):
        react = ""
        react += "class " + componentName + " extends React.Component {\n"
        react += "constructor(props) {\n"
        react += "super(props);\n"
        react += "let self=this;\n"
        react += "this.state = {\n"
        for k, s in self.stateDefinitions.items():
            v = s["defaultValue"]
            if isinstance(v, dict) and "type" in v and v["type"] == "dynamic":
                if "content" in v:
                    content = v["content"]
                    if (
                        "referenceType" in content
                        and content["referenceType"] == "state"
                    ):
                        raise Exception("state circular references")
                    elif (
                        "referenceType" in content
                        and content["referenceType"] == "prop"
                    ):
                        v = "self.props." + content["id"] + ""
                    elif (
                        "referenceType" in content
                        and content["referenceType"] == "local"
                    ):
                        v = "" + content["id"] + ""
            elif "type" in s:
                if isinstance(v, str) and v.startswith("$"):
                    v = v.replace("$", "")
                elif s["type"] == "object":
                    v = str(json.dumps(v))
                elif s["type"] == "string":
                    v = str(json.dumps(str(v)))
                elif s["type"] == "boolean":
                    v = str(json.dumps(bool(v)))
                elif s["type"] == "number":
                    v = str(float(v))
                elif s["type"] == "func":
                    v = str(v)
                elif s["type"] == "array":
                    v = str(json.dumps(list(v)))
                elif s["type"] == "router":
                    v = None
                else:
                    v = str(json.dumps(v))
            else:
                v = str(json.dumps(v))
            react += "'" + str(k) + "' : " + v + ", \n"
        react += "};\n"
        react += "} \n"
        react += "componentDidMount(){\n"
        react += "  let self=this;\n"
        react += "  if (this.props.onLoad){\n"
        react += "    this.props.onLoad(self);\n"
        react += "  }\n"
        react += "}\n"
        react += "componentDidUpdate(){\n"
        react += "  let self=this;\n"
        react += "  if (this.props.onUpdate){\n"
        react += "    this.props.onUpdate(self);\n"
        react += "  }\n"
        react += "}\n"
        react += "render(){\n"
        react += "  let self=this;\n"
        react += "  return " + self.node.buildReact() + ";\n"
        react += "}\n"
        react += "}\n"
        react += componentName + ".defaultProps = {\n"
        for k, s in self.propDefinitions.items():
            if "type" in s and s["type"] == "func":
                if "defaultValue" in s:
                    react += "'" + str(k) + "' : " + (s["defaultValue"]) + ", \n"
                else:
                    react += "'" + str(k) + "' : ()=>{}, \n"
            else:
                if "defaultValue" in s:
                    react += (
                        "'" + str(k) + "' : " + json.dumps(s["defaultValue"]) + ",\n"
                    )
        react += "}\n"
        return react


class TeleportProject:
    def __init__(self, name, *args, **kwargs):
        self.project_name = name
        self.globals = TeleportGlobals()
        content = kwargs.get(
            "content", TeleportElement(TeleportContent(elementType="container"))
        )
        self.root = TeleportComponent("MainComponent", content)
        self.components = {}
        self.ref = uuid.uuid4()
        self.libraries = {
            "require": "https://cdnjs.cloudflare.com/ajax/libs/require.js/2.3.6/require.min.js",
            "React": "https://unpkg.com/react@18.2.0/umd/react.production.min.js",
            "ReactDOM": "https://unpkg.com/react-dom@18.2.0/umd/react-dom.production.min.js",
            "Material": "https://unpkg.com/@mui/material@5.3.1/umd/material-ui.production.min.js",
            "PlotlyComponent": "https://unpkg.com/react-plotly.js@2.6.0/dist/create-plotly-component.js",
            "Plotly": "https://cdn.plot.ly/plotly-latest.min.js",
            "math": "https://cdnjs.cloudflare.com/ajax/libs/mathjs/6.6.1/math.min.js",
            "Axios": "https://unpkg.com/axios/dist/axios.min.js",
            "LocalForage": "https://www.unpkg.com/localforage@1.7.3/dist/localforage.min.js",
            "Format": "https://unpkg.com/react-number-format@4.3.1/dist/react-number-format.js",
            "PropTypes": "https://unpkg.com/prop-types@15.6/prop-types.min.js",
        }

        
    def addComponent(self, name, comp, *args, **kwargs):
        if name not in self.components:
            self.components[name] = comp

    def __json__(self):
        return {
            "$schema": "https://docs.teleporthq.io/uidl-schema/v1/project.json",
            "name": self.project_name,
            "globals": self.globals.__json__(),
            "root": self.root.__json__(),
            "components": {k: v.__json__() for k, v in self.components.items()},
        }

    def __str__(self):
        return json.dumps(self.__json__())

    def validate(self):
        return True
        # Teleport json has been deprecated and does not exist anymore

    def buildReact(self, filename="tempreact.html", **kwargs):
        r"""Build a react Web application using UMD modules

        :param filename:
            Name of the file to dump the HTML output
        :type first: ``str``
        :param \**kwargs:
            See below

        :Keyword Arguments:
            * *copy_libraries* (``bool``) --
              Download remote libraries and replace path to local version
            * *force_download* (``bool``) --
              Force to download libraries if they already exists

        """
        libraries = self.libraries
        copy_libraries = kwargs.get("copy_libraries", False)
        force_download = kwargs.get("force_download", False)
        if copy_libraries:
            for lib, link in libraries.items():
                print("copying " + libraries[lib])
                if not os.path.exists(lib + ".js") or force_download:
                    r = requests.get(libraries[lib], allow_redirects=True)
                    if r.ok:
                        try:
                            open(lib + ".js", "wt").write(r.content.decode())
                            libraries[lib] = lib
                            print("done with " + lib)
                        except:
                            warnings.warn(
                                "library " + lib + " can not be copied locally",
                                ResourceWarning,
                            )
                    else:
                        warnings.warn(
                            "library " + lib + " can not be copied locally",
                            ResourceWarning,
                        )
                else:
                    libraries[lib] = lib
                    print("already downloaded " + lib)

        print("building HTML ")
        react = ""
        react += "<!DOCTYPE html>\n"
        react += "<html style='height:100%'>\n"
        react += "<head>\n"
        react += "<meta charset='UTF-8'/>\n"
        react += "<meta name='viewport' content='initial-scale=1, maximum-scale=1, user-scalable=no, width=device-width'/>\n"
        react += "<title>" + self.project_name + "</title>\n"
        react += (
            "<script crossorigin src='"
            + libraries["React"][::-1].replace("sj.","",1)[::-1]
            + ".js'></script>\n"
        )       
        react += (
            "<script crossorigin src='"
            + libraries["ReactDOM"][::-1].replace("sj.","",1)[::-1]
            + ".js'></script>\n"
        )
        react += (
            "<script src='"
            + libraries["require"][::-1].replace("sj.","",1)[::-1]
            + ".js'></script>\n"
        )    
        react += "<link rel='stylesheet' href='https://fonts.googleapis.com/icon?family=Material+Icons'/>\n"
        react += "<script type='text/javascript'>\n"
        react += self.globals.customCode["head"].buildReact() + "\n"
        react += "</script>\n"
        react += "</head>\n"
        react += "  <body style='padding:0;margin:0;height:100%'>\n"
        react += "    <div id='root' class='loader'></div>\n"
        react += "<script type='text/javascript'>\n"
        react += self.globals.buildReact()
        react += "define('react', [], function(){ return React });\n"
        react += "define('react-dom', [], function(){ return ReactDOM });\n"
        react += "requirejs.config({\n"
        react += "    waitSeconds: 200,\n"
        react += "    paths: {\n"

        for k, v in libraries.items():
            if k not in ["require","React","ReactDOM"]:
                react += "        '" + k + "': '" + v[::-1].replace("sj.","",1)[::-1] + "',\n"
        react += "    }\n"
        react += "});\n"
        react += "window.React = React\n"
        react += "let _react = React\n"
        libnames = [json.dumps(k) for k,v in libraries.items() if k not in ["require","React","ReactDOM"]]
        libobjects = [k for k,v in libraries.items() if k not in ["require","React","ReactDOM"]]
        react += "requirejs(["+",".join(libnames)+"], function("+",".join(libobjects)+") {\n"
        #react += "    _react.PropTypes = PropTypes\n"
        react += "  const Plot = PlotlyComponent.default(Plotly);\n"
        react += self.globals.customCode["body"].buildReact()
        react += self.root.buildReact(self.root.name_component)
        for k, v in self.components.items():
            react += v.buildReact(k)
        react += "  const container = document.getElementById('root');\n"
        react += "  const root = ReactDOM.createRoot(container);\n"
        react += "  root.render(\n"
        react += (
            "        React.createElement("
            + self.root.name_component
            + ", {key:'"
            + str(self.ref)
            + "'})\n"
        )
        react += "  );\n"
        react += "})    \n"
        react += "</script>\n"
        react += "  </body>\n"
        react += "</html>\n"
        f = open(filename, "w")
        f.write(react)
        f.close()

        print("done!")

        run_uidl = kwargs.get("run_uidl", None)
        jupyter_notebook_url = kwargs.get("jupyter_notebook_url", None)
        if run_uidl in ["local", "redirect", "direct"]:
            if jupyter_notebook_url is not None:
                if os.path.exists(filename):
                        p = psutil.Process(int(os.environ['JPY_PARENT_PID']))
                        bp = os.path.abspath(p.cwd())
                        ap = os.path.abspath(filename)
                        if ap.startswith(bp):
                            link = "/".join(jupyter_notebook_url.split("/", 8)[:7])
                            link += "/uidl/" + filename + "/" +run_uidl + "/" + os.path.relpath(ap, bp)
                            print(link)
                        else:
                            print(" Dont have access to the file")
                else:
                    print(filepath + " does not exists")
            else:
                print("jupyter_notebook_url parameters is required")

    def displayWidget(self, *args, **kwargs):
        filename = "__TMPReactBuld.dat"
        self.buildReact(filename)
        file1 = open(filename, "r")
        lines = file1.readlines()
        component = ""
        append = False
        for line in lines:
            if line.startswith("<script type='text/javascript'>"):
                append = True
                continue
            if append:
                if line.startswith("</script>"):
                    append = False
                else:
                    component += line

        display(
            HTML(
                "<link rel='stylesheet' href='https://fonts.googleapis.com/icon?family=Material+Icons'/>"
            )
        )
        display(HTML("<style>div#root p {font-size:unset}</style>"))
        display(HTML("<style>div#root label {font-size:1.5rem}</style>"))
        display(HTML("<style>div#root div {font-size:unset}</style>"))
        display(HTML("<style>div#root svg {font-size:x-large}</style>"))
        display(HTML("<style>div#root h6 {margin-top:0px}</style>"))
        display(HTML("<style>div#root img {margin-top:0px}</style>"))
        display(
            HTML(
                "<div id='root' style='height:"
                + str(kwargs.get("height", "900px"))
                + ";width:"
                + str(kwargs.get("width", "100%"))
                + ";padding:0px;position:relative'></div>"
            )
        )
        display(Javascript(component))
