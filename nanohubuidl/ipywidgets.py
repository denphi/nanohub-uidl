from .teleport import *
from .material import *
from .rappture import *
from .plotly import *
import re
import copy

import ipywidgets as widgets
import anywidget
from traitlets import (
    Unicode,
    Integer,
    validate,
    Bool,
    Float,
    TraitError,
    Dict,
    List,
    Any,
    Instance,
)
import xml, re, json, uuid
from IPython.display import HTML, Javascript, display


def buildWidget(proj, *args, **kwargs):
    
    Project = copy.deepcopy(proj)
    component = Project.project_name
    component = re.sub("[^a-zA-Z]+", "", component)
    Project.root.name_component = component

    eol = "\n"

    attrs = {}

    default = {}

    functions = {}

    for i, d in Project.root.propDefinitions.items():
        if d["type"] == "func":
            attrs[i] = lambda s, c, r=False, m=i: getattr(
                s, "_handlers_" + m
            ).register_callback(c, r)
            functions[i] = d["defaultValue"]
            Project.root.propDefinitions[i]["type"] = "func"
            if (
                "defaultValue" not in Project.root.propDefinitions[i]
                or Project.root.propDefinitions[i]["defaultValue"]
                == "(e)=>{return e; }"
            ):
                Project.root.propDefinitions[i]["defaultValue"] = (
                    "(e)=>{ if (event) event.preventDefault(); backbone.send({ event: '"
                    + i
                    + "', 'params' : ("
                    + d["defaultValue"]
                    + ")(e) });}"
                )
    parseState = ""
    serializers = []
    for i, d in Project.root.stateDefinitions.items():
        parseState += "        if('" + i + "' in state){" + eol
        if d["type"] == "string":
            parseState += (
                "          state['" + i + "'] = String(state['" + i + "']);" + eol
            )
            default[i] = str(d["defaultValue"])
            attrs[i] = Unicode(default[i]).tag(sync=True)
            Project.root.stateDefinitions[i]["type"] = "func"
            Project.root.stateDefinitions[i]["defaultValue"] = (
                "backbone.model.get('" + i + "')"
            )
        elif d["type"] == "boolean":
            parseState += (
                "          state['"
                + i
                + "'] = [true, 'true', 'True', 'on', 'yes', 'Yes', 'TRUE', 1, 'ON'].includes(state['"
                + i
                + "']);"
                + eol
            )
            default[i] = d["defaultValue"] in [
                True,
                "true",
                "True",
                "on",
                "yes",
                "Yes",
                "TRUE",
                1,
                "ON",
            ]
            attrs[i] = Bool(default[i]).tag(sync=True)
            Project.root.stateDefinitions[i]["type"] = "func"
            Project.root.stateDefinitions[i]["defaultValue"] = (
                "backbone.model.get('" + i + "')"
            )

        elif d["type"] == "number":
            parseState += (
                "          state['" + i + "'] = parseFloat(state['" + i + "']);" + eol
            )
            default[i] = float(d["defaultValue"])
            attrs[i] = Float(default[i]).tag(sync=True)
            Project.root.stateDefinitions[i]["type"] = "func"
            Project.root.stateDefinitions[i]["defaultValue"] = (
                "backbone.model.get('" + i + "')"
            )

        elif d["type"] == "integer":
            parseState += (
                "          state['" + i + "'] = parseInt(state['" + i + "']);" + eol
            )
            default[i] = int(d["defaultValue"])
            attrs[i] = Integer(default[i]).tag(sync=True)
            Project.root.stateDefinitions[i]["type"] = "func"
            Project.root.stateDefinitions[i]["defaultValue"] = (
                "backbone.model.get('" + i + "')"
            )

        elif d["type"] == "object":
            parseState += "          state['" + i + "'] = (state['" + i + "']);" + eol
            default[i] = dict(d["defaultValue"])
            attrs[i] = Dict(default[i]).tag(sync=True)
            Project.root.stateDefinitions[i]["type"] = "func"
            Project.root.stateDefinitions[i]["defaultValue"] = (
                "backbone.model.get('" + i + "')"
            )

        elif d["type"] == "array":
            parseState += "          state['" + i + "'] = (state['" + i + "']);" + eol
            default[i] = list(d["defaultValue"])
            attrs[i] = List(default[i]).tag(sync=True)
            Project.root.stateDefinitions[i]["type"] = "func"
            Project.root.stateDefinitions[i]["defaultValue"] = (
                "backbone.model.get('" + i + "')"
            )

        elif d["type"] == "router":  # missuse of router to mark widgets arrays
            parseState += "          state['" + i + "'] = (state['" + i + "']);" + eol
            default[i] = list()
            attrs[i] = widgets.trait_types.TypedTuple(
                trait=Instance(widgets.Widget)
            ).tag(sync=True, **widgets.widget_serialization)
            Project.root.stateDefinitions[i]["type"] = "array"
            Project.root.stateDefinitions[i]["defaultValue"] = []
            serializers.append(i)
        parseState += "        }" + eol

    js = ""
    js += "require.config({" + eol
    js += "  paths: {" + eol
    for k, v in Project.libraries.items():
        if k not in ["require"]:
            if kwargs.get("jupyter_axios", False) == False or k != "Axios":
                js += "    '" + k + "': '" + v[::-1].replace("sj.","",1)[::-1] + "',\n"
    js += "  }" + eol
    js += "});" + eol
    js += "require.undef('" + component + "');" + eol

    js += "define('react', [" + eol
    js += "    'React'" + eol
    js += "  ], function(" + eol
    js += "    React" + eol
    js += "  ){" + eol
    js += "      window.React = React;" + eol
    js += "      return React;" + eol
    js += "  }" + eol
    js += ");" + eol
    js += "define('react-dom', [" + eol
    js += "    'ReactDOM'" + eol
    js += "  ], function(" + eol
    js += "    ReactDOM" + eol
    js += "  ){" + eol
    js += "      window.ReactDOM = ReactDOM;" + eol
    js += "      return ReactDOM;" + eol
    js += "  }" + eol
    js += ");" + eol
    if kwargs.get("jupyter_axios", False):
        js += "define('Axios', [],function() {" + eol
        js += "  function fixedEncodeURI(str) {" + eol
        js += "    return str.replace(/'/g, \"\\\\'\");" + eol
        js += "  }" + eol
        js += "  return {" + eol
        js += "    'request' : (url, options) => {" + eol
        js += "       var promise = new Promise( (callback,error) => {" + eol
        js += "         let code_input = 'import json;import requests;';" + eol
        js += "         if (options.method && options.method == 'GET') {" + eol
        js += "           code_input += 'r=requests.get(\\'' + url + '\\'';" + eol
        js += "         } else if (options.method && options.method == 'POST') {" + eol
        js += "           code_input += 'r=requests.post(\\'' + url + '\\'';" + eol
        js += "         } else {" + eol
        js += "           error('only post or get are supported');" + eol
        js += "           return; " + eol
        js += "         }" + eol
        js += "         if (options.headers) {" + eol
        js += (
            "           code_input += ', headers=json.loads(\\'' + JSON.stringify(options.headers) + '\\')';"
            + eol
        )
        js += "         }" + eol
        js += "         if (options.data) {" + eol
        js += "           if (typeof options.data === 'string'){" + eol
        js += (
            "             code_input += ', data=\\'' + fixedEncodeURI(options.data) + '\\'';"
            + eol
        )
        js += "           } else {" + eol
        js += (
            "             code_input += ', data=\\'' + JSON.stringify(options.data) + '\\'';"
            + eol
        )
        js += "           }" + eol
        js += "         }" + eol
        js += "         code_input += ');print(r.text)';" + eol
        # js += "         console.log(code_input);" + eol
        js += "         let callbacks = {" + eol
        js += "           iopub : { output : (response) =>{" + eol
        # js += "             debugger;" + eol
        js += "             let obj_r = response.content;" + eol
        # js += "             console.log(obj_r);" + eol
        js += "             try {" + eol
        js += "               obj_r = JSON.parse(obj_r.text);" + eol
        js += "               if (obj_r.code && obj_r.code > 200){" + eol
        js += "                 error(obj_r.message);" + eol
        js += "                 return;" + eol
        js += "               }" + eol
        js += "             } catch (e) {" + eol
        js += "               obj_r = obj_r.text;" + eol
        js += (
            "               if (options.handleAs && options.handleAs == 'json') {" + eol
        )
        js += "                 error('invalid json response');" + eol
        js += "                 return;" + eol
        js += "               }" + eol
        js += "             }" + eol
        js += "             if (options.handleAs && options.handleAs == 'json') {" + eol
        js += "               callback({'data':obj_r});" + eol
        js += "             } else {" + eol
        js += "               callback({'data':response.content.text});" + eol
        js += "             }" + eol
        js += "           }}" + eol
        js += "         }" + eol
        js += "         let kernel = IPython.notebook.kernel;" + eol
        js += (
            "         let msg_id = kernel.execute(code_input, callbacks, {silent:false});"
            + eol
        )
        js += "       });" + eol
        js += "       return promise;" + eol
        js += "     }" + eol
        js += "  };" + eol
        js += "});" + eol

    libnames = ["'@jupyter-widgets/base'","'underscore'"]
    libobjects = ["widgets", "_"]
    libnames = libnames + [json.dumps(k) for k,v in Project.libraries.items() if k not in ["require","React", "ReactDOM"]]
    libobjects = libobjects + [k for k,v in Project.libraries.items() if k not in ["require","React", "ReactDOM"]]
    print
    js += "define('" + component + "', ["+(",".join(libnames))+"], function("+(",".join(libobjects))+") {" + eol
    if kwargs.get("debugger", False):
        js += "        debugger;" + eol

    js += "    const Plot = PlotlyComponent.default(Plotly);\n"

    js += "    const " + component + "Model = widgets.DOMWidgetModel.extend({" + eol
    js += "    }, {" + eol
    js += "        serializers: _.extend({" + eol
    for i in serializers:
        js += "            " + i + ": { deserialize: widgets.unpack_models }," + eol
    js += "        }, widgets.DOMWidgetModel.serializers)" + eol
    js += "    });" + eol

    js += "    const " + component + "View = widgets.DOMWidgetView.extend({" + eol
    js += "      initialize() {" + eol

    js += "        const backbone = this;" + eol
    for i in serializers:
        js += (
            "        backbone."
            + i
            + "_views = new widgets.ViewList(backbone.add_child_model.bind(backbone), null, backbone);"
            + eol
        )
        js += "        backbone._" + i + " = [];" + eol
        js += "        backbone." + i + "Ref = React.createRef();" + eol
    js += "        backbone.options = {};" + eol

    for k, v in Project.components.items():
        js += v.buildReact(k)
        js += "  " + k + ".getDerivedStateFromProps = function(props, state){" + eol
        js += "  let self = {'props':props,'state':state};" + eol
        js += "  return {" + eol
        for k1, s1 in v.stateDefinitions.items():
            v1 = s1["defaultValue"]
            if isinstance(v1, dict) and "type" in v1 and v1["type"] == "dynamic":
                if "content" in v1:
                    content1 = v1["content"]
                    if (
                        "referenceType" in content1
                        and content1["referenceType"] == "prop"
                    ):
                        v1 = "props." + content1["id"] + ""
                    else:
                        v1 = "state." + k1 + ""
                else:
                    v1 = "state." + k1 + ""
            else:
                v1 = "state." + k1 + ""
            js += "  '" + str(k1) + "' : " + v1 + ", " + eol
        js += "  };" + eol
        js += "}" + eol

    js += Project.globals.customCode["body"].buildReact()
    js += Project.globals.buildReact()
    js += Project.root.buildReact(Project.root.name_component)
    js += (
        "        const orig = "
        + Project.root.name_component
        + ".prototype.setState;"
        + eol
    )
    js += (
        "        "
        + Project.root.name_component
        + ".prototype.onChange = function (model){"
        + eol
    )
    js += "          orig.apply(this, [Object.assign({},model.changed)]);" + eol
    js += "        }" + eol
    js += (
        "        "
        + Project.root.name_component
        + ".prototype.componentDidUpdate = function(){"
        + eol
    )
    for i in serializers:
        js += "          if(backbone." + i + "Ref.current){" + eol
        js += "            backbone._" + i + ".forEach((e)=>{" + eol
        js += "              backbone." + i + "Ref.current.appendChild(e);" + eol
        js += "            });" + eol
        js += "          }" + eol
    js += "        }" + eol
    js += (
        "        "
        + Project.root.name_component
        + ".getDerivedStateFromProps = function(props, state){"
        + eol
    )
    js += "          return state;" + eol
    js += "        }" + eol
    js += (
        "        "
        + Project.root.name_component
        + ".prototype.componentDidMount = function(){"
        + eol
    )
    js += (
        "          backbone.listenTo(backbone.model, 'change', this.onChange.bind(this));"
        + eol
    )
    for i in serializers:
        js += (
            "          backbone.listenTo(backbone.model, 'change:"
            + i
            + "', this.update"
            + i
            + ".bind(this));"
            + eol
        )
        js += "          if(backbone." + i + "Ref.current){" + eol
        js += (
            "            this.update"
            + i
            + "(null, backbone.model.get('"
            + i
            + "'));"
            + eol
        )
        js += "            backbone._" + i + ".forEach((e)=>{" + eol
        js += "              backbone." + i + "Ref.current.appendChild(e);" + eol
        js += "            });" + eol
        js += "          }" + eol
    js += "        }" + eol
    js += (
        "        "
        + Project.root.name_component
        + ".prototype.setState = function(state, callback){"
        + eol
    )
    js += parseState
    js += "          for (let [key, value] of Object.entries(state)) {" + eol
    js += "            backbone.model.set(key, value);" + eol
    js += "          }" + eol
    js += "          try {;" + eol
    js += "            backbone.model.save_changes();" + eol
    js += "          } catch (error) {" + eol
    # js += "            console.log(error); " + eol
    js += "          }" + eol
    js += "          orig.apply(this, [state, callback]);" + eol
    js += "        }" + eol
    for i in serializers:
        js += (
            "        "
            + Project.root.name_component
            + ".prototype.update"
            + i
            + " = function(m, v){"
            + eol
        )
        js += "          if (backbone." + i + "_views){" + eol
        js += "            backbone._" + i + " = [];" + eol
        js += "            backbone." + i + "_views.update(v).then((views)=>{" + eol
        js += "              views.forEach(view => {" + eol
        js += "                backbone._" + i + ".push(view.el);" + eol
        js += "              });" + eol
        js += "              this.forceUpdate()" + eol
        js += "            });" + eol
        js += "          }" + eol
        js += "        }" + eol
    js += "        backbone.app = document.createElement('div');" + eol
    js += "        backbone.app.className = 'loader';" + eol
    js += "        backbone.app.style.padding = '10px';" + eol
    js += (
        "        const App = React.createElement("
        + Project.root.name_component
        + ");"
        + eol
    )
    js += "        const container = backbone.app;" + eol
    js += "        const root = ReactDOM.createRoot(container);" + eol
    js += "        root.render(App);" + eol
    js += "        backbone.el.append(backbone.app);" + eol
    js += "      }," + eol

    js += "      add_child_model: function(model) {" + eol
    js += "        return this.create_child_view(model).then((view) => {" + eol
    js += "          view.setLayout(view.model.get('layout'));" + eol
    js += "          let lview=view;" + eol
    js += "          lview.listenTo(lview.model,'change:layout',(m, v) => {" + eol
    js += "            this.update_children()" + eol
    js += "          });" + eol
    js += "          return view;" + eol
    js += "        });" + eol
    js += "      }, " + eol

    js += "      update_children: function () {" + eol
    js += (
        "          this.children_views.update(this.model.get('children')).then(function (views) {"
        + eol
    )
    js += "              views.forEach(function (view) {" + eol
    js += (
        "                  messaging_1.MessageLoop.postMessage(view.pWidget, widgets_1.Widget.ResizeMessage.UnknownSize);"
        + eol
    )
    js += "              });" + eol
    js += "          });" + eol
    js += "      }, " + eol

    js += "    });" + eol

    js += "    return {" + eol
    js += "      " + component + "View," + eol
    js += "      " + component + "Model" + eol
    js += "    };" + eol
    js += "});" + eol
    if kwargs.get("verbose", False):
        print(js)
    
    # Convert AMD module to ESM for anywidget
    def convert_amd_to_esm(js_amd, component_name, libraries):
        """Convert AMD module definition to ESM format for anywidget"""
        
        # Build import statements for libraries
        imports = []
        # Use esm.sh with pinned dependencies to ensure Backbone loads correctly
        imports.append('import * as widgets from "https://esm.sh/@jupyter-widgets/base@6?deps=underscore@1.13.6,backbone@1.4.1,jquery@3.7.1";')
        imports.append('import _ from "https://esm.sh/underscore@1.13.6";')
        
        # Add other library imports - use CDN URLs for ESM
        for lib_name in libraries.keys():
            if lib_name not in ["require", "React", "ReactDOM"]:
                lib_url = libraries[lib_name]
                
                # Try to convert unpkg/cdnjs URLs to ESM-friendly esm.sh URLs
                # This fixes "does not provide an export named 'default'" errors
                if "unpkg.com" in lib_url:
                    # Extract package name and version
                    # Matches: unpkg.com/@scope/pkg@version/... or unpkg.com/pkg@version/...
                    match = re.search(r"unpkg\.com/((?:@[^/]+/[^@/]+)|(?:[^@/]+))(?:@([^/]+))?", lib_url)
                    if match:
                        pkg = match.group(1)
                        ver = match.group(2)
                        lib_url = f"https://esm.sh/{pkg}"
                        if ver:
                            lib_url += f"@{ver}"
                
                elif "cdnjs.cloudflare.com" in lib_url:
                    # Extract package name
                    # Matches: cdnjs.../ajax/libs/package/version/...
                    match = re.search(r"/ajax/libs/([^/]+)/([^/]+)/", lib_url)
                    if match:
                        pkg = match.group(1)
                        ver = match.group(2)
                        lib_url = f"https://esm.sh/{pkg}@{ver}"

                elif "cdn.plot.ly" in lib_url:
                    # Plotly CDN doesn't support ESM default exports directly
                    # Use esm.sh version of the minified dist
                    lib_url = "https://esm.sh/plotly.js-dist-min"

                # Fallback: Ensure .js extension if not using esm.sh (which doesn't need it)
                elif not lib_url.endswith('.js') and "esm.sh" not in lib_url:
                    lib_url += '.js'
                    
                # Determine import style
                # Some libraries (like @mui/material) don't have a default export, so we must use "import * as"
                if "@mui" in lib_url or "@material-ui" in lib_url:
                    imports.append(f"import * as {lib_name} from \"{lib_url}\";")
                else:
                    imports.append(f"import {lib_name} from \"{lib_url}\";")
        
        # Remove require.config() block
        module_body = re.sub(
            r"require\.config\(\{.*?\}\);",
            "",
            js_amd,
            flags=re.DOTALL
        )
        
        # Remove require.undef() calls
        module_body = re.sub(
            r"require\.undef\(['\"].*?['\"]\);",
            "",
            module_body
        )
        
        # Remove define() wrapper
        # Regex to match define('name', ['deps'], function(deps) { ... })
        define_pattern = r"define\(['\"]" + re.escape(component_name) + r"['\"],\s*\[.*?\],\s*function\(.*?\)\s*\{"
        
        match = re.search(define_pattern, module_body, flags=re.DOTALL)
        
        if match:
            # Extract just the body of the define function
            module_body = match.group(1)
        else:
            # Fallback: try to remove define wrapper more aggressively
            module_body = re.sub(
                r"define\(['\"]" + re.escape(component_name) + r"['\"],\s*\[.*?\],\s*function\(.*?\)\s*\{",
                "",
                module_body,
                flags=re.DOTALL
            )
            # Remove the AMD closing sequence from the end
            module_body = re.sub(r"\}\);\s*$", "", module_body)
        
        # Remove the return statement (which returns the Model/View classes)
        # This needs to be removed because we are replacing it with ESM exports
        module_body = re.sub(r"return\s*\{[^}]*\}\s*;?\s*$", "", module_body, flags=re.DOTALL)
        
        # Build ESM module
        esm = "\n".join(imports) + "\n\n"
        
        # Add debug logging for base widgets
        esm += "console.log('Loaded widgets module:', widgets);\n"
        esm += "try {\n"
        esm += "    console.log('DOMWidgetView:', widgets.DOMWidgetView);\n"
        esm += "} catch (e) {\n"
        esm += "    console.error('Error accessing DOMWidgetView:', e);\n"
        esm += "}\n\n"
        
        esm += module_body.strip() + "\n\n"
        
        # Add anywidget bridge
        # We export the Model and View for reference, but the default export is what anywidget uses
        esm += f"export {{ {component_name}Model, {component_name}View }};\n\n"
        
        # Bridge Backbone View to anywidget render function
        esm += "export default {\n"
        esm += "    render: function({ model, el }) {\n"
        esm += f"        console.log('Rendering widget {component_name}');\n"
        esm += f"        try {{\n"
        esm += f"            const view = new {component_name}View({{ model: model, el: el }});\n"
        esm += "            view.render();\n"
        esm += "        } catch (e) {\n"
        esm += f"            console.error('Error rendering widget {component_name}:', e);\n"
        esm += "            console.log('Widgets module:', widgets);\n"
        esm += "            throw e;\n"
        esm += "        }\n"
        esm += "    }\n"
        esm += "};\n"
        
        return esm
    
    # Generate ESM version for anywidget
    js_esm = convert_amd_to_esm(js, component, Project.libraries)
    
    # out = widgets.Output()
    # display(out)
    # with out:
    #    print("DEBUG")
    def do_handle_msg(s, d, f, c, b):
        for i, j in f.items():
            if c.get("event", "") == i:
                getattr(s, i + "_call")(s, obj=s, buf=c.get("params", ""))
                return
        # widgets.Widget._handle_msg(s,c,b)

    def do_init(s, v, f, **k):
        default_styles = "<link rel='stylesheet' href='https://fonts.googleapis.com/icon?family=Material+Icons'/>"
        default_styles += "<style>.p-Widget * {font-size: unset;}</style>"
        default_styles += "<style>div.output_subarea {padding: 0px;}</style>"

        display(
            widgets.HTML(
                kwargs.get("styles", default_styles),
                layout=widgets.Layout(display="none"),
            )
        )
        
        # anywidget handles JavaScript loading automatically via _esm trait
        anywidget.AnyWidget.__init__(s, **k)
        
        for i, j in f.items():
            setattr(s, "_handlers_" + i, widgets.CallbackDispatcher())
            setattr(
                s,
                i,
                lambda c, r=False, m=i: getattr(s, "_handlers_" + m).register_callback(
                    c, r
                ),
            )
            setattr(
                s,
                i + "_call",
                lambda s, m=i, obj=s, buf=[]: getattr(s, "_handlers_" + m)(
                    obj=obj, buf=buf
                ),
            )
            if k.get(i, None) is not None and hasattr(k.get(i, None), "__call__"):
                getattr(s, i)(s, k.get(i, None))
        s.on_msg(lambda s1, c, b,: s1._handle_uidl_msg(c, b))
        s.__validate = True

        for i, j in v.items():
            setattr(s, i, k.get(i, j))

    def do__setattr(s, n, v, d):
        if hasattr(s, "__validate"):
            if n in d:
                if isinstance(d[n], str):
                    anywidget.AnyWidget.__setattr__(s, n, str(v))
                elif type(d[n]) == bool:
                    anywidget.AnyWidget.__setattr__(
                        s,
                        n,
                        v
                        in [True, "true", "True", "on", "yes", "Yes", "TRUE", 1, "ON"],
                    )
                elif isinstance(d[n], list):
                    anywidget.AnyWidget.__setattr__(s, n, list(v))
                elif isinstance(d[n], dict):
                    vc = dict(getattr(s, n))
                    vc.update(v)
                    anywidget.AnyWidget.__setattr__(s, n, vc)
                elif isinstance(d[n], int):
                    anywidget.AnyWidget.__setattr__(s, n, int(v))
                elif isinstance(d[n], float):
                    anywidget.AnyWidget.__setattr__(s, n, float(v))
                else:
                    anywidget.AnyWidget.__setattr__(s, n, v)
            else:
                anywidget.AnyWidget.__setattr__(s, n, v)

        else:
            anywidget.AnyWidget.__setattr__(s, n, v)

    # Use anywidget for remote compatibility
    # Store ESM JavaScript module code
    attrs["_esm"] = Unicode(js_esm).tag(sync=True)
    
    # anywidget handles model/view names automatically (AnyModel/AnyView)
    # We don't need to set _model_name/_view_name because we are using the render() bridge
    
    attrs["__init__"] = lambda s, **k: do_init(s, default, functions, **k)
    attrs["_handle_uidl_msg"] = lambda s, c, b,: do_handle_msg(
        s, default, functions, c, b
    )
    attrs["__setattr__"] = lambda s, n, v, d=default: do__setattr(s, n, v, d)

    return type(component + "Widget", (anywidget.AnyWidget,), attrs)


def parseJSX(document, *args, **kwargs):
    def buildNode(tag, Component):
        Node = None
        if tag.nodeType == tag.TEXT_NODE:
            if tag.data.strip() == "":
                return None
            if tag.data.strip().startswith("{") and tag.data.strip().endswith("}"):
                regex = "^\{([a-zA-Z][a-zA-Z0-9_]+)\:(.+)\((.+)\)\}$"
                m = re.match(regex, tag.data.strip())
                if m is not None:
                    state = m.group(1)
                    if m.group(2) == "string":
                        Component.addStateVariable(
                            state, {"type": m.group(2), "defaultValue": m.group(3)}
                        )
                    elif m.group(2) in [
                        "boolean",
                        "number",
                        "array",
                        "object",
                        "integer",
                    ]:
                        v = m.group(2)
                        if v == "integer":
                            v = "number"
                        Component.addStateVariable(
                            state,
                            {
                                "type": v,
                                "defaultValue": json.loads(
                                    m.group(3).replace("'", '"')
                                ),
                            },
                        )
                    else:
                        raise Exception("not a supported type '" + m.group(2) + "'")
                    Node = TeleportDynamic(
                        content={"referenceType": "state", "id": state}
                    )

                else:
                    raise Exception("not a supported definition" + tag.data.strip())
            else:
                Node = TeleportStatic(content=tag.data.strip().replace("\n", "\\n"))
        else:
            if tag.tagName.startswith("Nanohub"):
                Node = TeleportElement(
                    TeleportContent(elementType=tag.tagName.replace("Nanohub.", ""))
                )
            elif tag.tagName.startswith("Material"):
                Node = TeleportElement(
                    MaterialContent(elementType=tag.tagName.replace("Material.", ""))
                )
            elif tag.tagName.startswith("Plotly"):
                Node = TeleportElement(
                    PlotlyContent(elementType=tag.tagName.replace("Plotly.", ""))
                )
            else:
                Node = TeleportElement(TeleportContent(elementType=tag.tagName))

            for t in tag.childNodes:
                node = buildNode(t, Component)
                if node is not None:
                    Node.addContent(node)
        if tag.attributes is not None:
            for k, v in tag.attributes.items():
                if v.startswith("{") and v.endswith("}"):
                    regex = "^\{([a-zA-Z][a-zA-Z0-9_]+)\:(.+)\((.+)\)\}$"
                    m = re.match(regex, v)
                    if m is not None:
                        state = m.group(1)
                        if k == "_children":
                            if m.group(2) == "array":
                                Component.addStateVariable(
                                    state, {"type": "router", "defaultValue": []}
                                )
                                Node.content.attrs["ref"] = {
                                    "type": "dynamic",
                                    "content": {
                                        "referenceType": "local",
                                        "id": "backbone." + state + "Ref",
                                    },
                                }
                                Node.content.attrs[k] = ""
                            else:
                                raise Exception(
                                    "_children only support array type'"
                                    + m.group(2)
                                    + "'"
                                )
                        else:
                            if m.group(2) == "string":
                                Component.addStateVariable(
                                    state,
                                    {"type": m.group(2), "defaultValue": m.group(3)},
                                )
                            elif m.group(2) in [
                                "boolean",
                                "number",
                                "array",
                                "object",
                                "integer",
                            ]:
                                v = m.group(2)
                                if v == "integer":
                                    v = "number"
                                Component.addStateVariable(
                                    state,
                                    {
                                        "type": m.group(2),
                                        "defaultValue": json.loads(
                                            m.group(3).replace("'", '"')
                                        ),
                                    },
                                )
                            else:
                                raise Exception(
                                    "not a supported type '" + m.group(2) + "'"
                                )
                        Node.content.attrs[k] = {
                            "type": "dynamic",
                            "content": {"referenceType": "state", "id": state},
                        }
                    else:
                        raise Exception("not a supported definition" + v)

                elif v.startswith("[") and v.endswith("]"):
                    regex = "^\[([a-zA-Z][a-zA-Z0-9]+)\((.+),(.+)\)\]$"
                    m = re.match(regex, v)
                    if m is not None:
                        if m.group(1) in ["stateChange"]:
                            Component.addPropVariable(
                                k, {"type": "func", "defaultValue": "(e)=>{return e; }"}
                            )
                            Component.addPropVariable(
                                "onChange",
                                {"type": "func", "defaultValue": "(e)=>{return e; }"},
                            )
                            v = m.group(3)
                            if v == "$toogle":
                                v = "!self.state." + m.group(2)
                            Node.content.events[k] = [
                                {
                                    "type": m.group(1),
                                    "modifies": m.group(2),
                                    "newState": "$" + v,
                                },
                                {
                                    "type": "propCall2",
                                    "calls": "onChange",
                                    "args": [
                                        "{'id':'" + m.group(2) + "', 'value':" + v + "}"
                                    ],
                                },
                            ]
                        elif m.group(1) in ["propCall", "propCall2"]:
                            Component.addPropVariable(
                                m.group(2),
                                {"type": "func", "defaultValue": "(e)=>{return e; }"},
                            )
                            Node.content.events[k] = [
                                {
                                    "type": "propCall2",
                                    "calls": m.group(2),
                                    "args": [m.group(3)],
                                },
                            ]
                        else:
                            raise Exception("not a supported function" + m.group(1))
                    else:
                        raise Exception("not a valid function" + v)
                elif k == "style":
                    Node.content.style = {
                        a[0]: a[1] for a in [t.split(":") for t in v.split(";")]
                    }
                else:
                    Node.content.attrs[k] = v

        return Node

    document = "<uidl>" + document + "</uidl>"
    dom = xml.dom.minidom.parseString(document)
    component = kwargs.get("component_name", str(uuid.uuid4()))
    component = "UIDL" + component.replace("-", "")
    Component = TeleportComponent(
        component, TeleportElement(MaterialContent(elementType="Paper"))
    )

    for node in dom.childNodes[0].childNodes:
        if node.nodeType != node.TEXT_NODE:
            Component.node.addContent(buildNode(node, Component))
    return Component


def buildJSX(document, *args, **kwargs):
    component = kwargs.get(
        "component_name", re.sub("[^a-zA-Z]+", "", str(uuid.uuid4()))
    )
    component = "UIDL" + component.replace("-", "")
    Component = parseJSX(document, *args, **kwargs)
    Project = TeleportProject(component, content=Component)
    Project.root.propDefinitions = Component.propDefinitions
    Project.root.stateDefinitions = Component.stateDefinitions
    Project.root.node = Component.node
    for t in Component.getNodeTypes():
        if t == "FormatCustomNumber":
            MaterialComponents.FormatCustomNumber(Project)
        elif t == "IconListMaterial":
            MaterialComponents.IconList(Project)
        elif t == "IntSwitch":
            MaterialComponents.IntSwitch(Project)
        elif t == "ButtonListMaterial":
            MaterialComponents.ButtonList(Project)
        elif t == "ColorSliders":
            MaterialComponents.ColorSliders(Project)

    if kwargs.get("verbose", False):
        print(Project.root.buildReact(component))
    return buildWidget(Project, override_styles=False, **kwargs)
