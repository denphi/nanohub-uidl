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
    # Handle input (dict or object)
    if isinstance(proj, dict):
        project = proj
    else:
        # Support for TeleportProject object via __json__
        if hasattr(proj, "__json__"):
            project = proj.__json__()
        elif hasattr(proj, "to_dict"):
            project = proj.to_dict()
        else:
            # Fallback: try to serialize
            try:
                project = json.loads(json.dumps(proj, default=lambda o: o.__dict__))
            except:
                project = proj.__dict__ if hasattr(proj, "__dict__") else proj

    component_name = project.get("name", "MyWidget")
    # Sanitize component name
    component_name = re.sub("[^a-zA-Z0-9]+", "", component_name)
    
    root = project.get("root", {})
    state_defs = root.get("stateDefinitions", {})
    prop_defs = root.get("propDefinitions", {})
    node = root.get("node", {})
    
    # 1. Python Traits Generation
    attrs = {}
    trait_types = {
        "string": Unicode,
        "boolean": Bool,
        "number": Float,
        "integer": Integer,
        "array": List,
        "object": Dict,
    }
    
    # Define default values and traits
    defaults = {}
    
    for name, defn in state_defs.items():
        t = defn.get("type", "string")
        default_val = defn.get("defaultValue")
        
        # Handle type conversion for default values
        if t == "boolean":
            if isinstance(default_val, str):
                default_val = default_val.lower() in ["true", "on", "yes", "1"]
            defaults[name] = bool(default_val) if default_val is not None else False
            attrs[name] = Bool(defaults[name]).tag(sync=True)
            
        elif t == "number":
            defaults[name] = float(default_val) if default_val is not None else 0.0
            attrs[name] = Float(defaults[name]).tag(sync=True)
            
        elif t == "integer":
            defaults[name] = int(default_val) if default_val is not None else 0
            attrs[name] = Integer(defaults[name]).tag(sync=True)
            
        elif t == "array":
            defaults[name] = list(default_val) if default_val is not None else []
            attrs[name] = List(defaults[name]).tag(sync=True)
            
        elif t == "object":
            defaults[name] = dict(default_val) if default_val is not None else {}
            attrs[name] = Dict(defaults[name]).tag(sync=True)
            
        else: # string
            defaults[name] = str(default_val) if default_val is not None else ""
            attrs[name] = Unicode(defaults[name]).tag(sync=True)

    # 2. JavaScript Generation
    
    # Collect dependencies
    dependencies = {} # path -> { version, imports: set(), default: bool }
    
    def collect_deps(n):
        # Check for dependency in the node itself (rare) or in its content (common for TeleportElement)
        content = n.get("content", {})
        
        # Check content for dependency
        if isinstance(content, dict) and "dependency" in content:
            dep = content["dependency"]
            if dep.get("type") == "package":
                path = dep["path"]
                version = dep.get("version", "latest")
                meta = dep.get("meta", {})
                
                if path not in dependencies:
                    dependencies[path] = {"version": version, "imports": set(), "default": False}
                
                if meta.get("namedImport"):
                    original_name = meta.get("originalName", content.get("elementType"))
                    dependencies[path]["imports"].add(original_name)
                else:
                    dependencies[path]["default"] = True
        
        # Also check node level (just in case)
        if "dependency" in n:
            dep = n["dependency"]
            if dep.get("type") == "package":
                path = dep["path"]
                version = dep.get("version", "latest")
                meta = dep.get("meta", {})
                
                if path not in dependencies:
                    dependencies[path] = {"version": version, "imports": set(), "default": False}
                
                if meta.get("namedImport"):
                    original_name = meta.get("originalName", content.get("elementType"))
                    dependencies[path]["imports"].add(original_name)
                else:
                    dependencies[path]["default"] = True
        
        if isinstance(content, dict) and "children" in content:
            for child in content["children"]:
                collect_deps(child)
                
    collect_deps(node)
    
    # Build Imports
    js_imports = []
    js_imports.append('import * as React from "https://esm.sh/react@18.2.0";')
    js_imports.append('import * as ReactDOM from "https://esm.sh/react-dom@18.2.0/client?deps=react@18.2.0";')
    
    for path, info in dependencies.items():
        url = f"https://esm.sh/{path}"
        if info["version"] and info["version"] != "latest":
            url += f"@{info['version']}"
            
        # Force shared React dependency to avoid "Invalid Hook Call" (Error #321)
        url += "?deps=react@18.2.0"
            
        # Handle imports
        import_clauses = []
        if info["default"]:
            # Generate a safe name for default import
            safe_name = re.sub("[^a-zA-Z0-9]+", "", path) + "Default"
            import_clauses.append(f"default as {safe_name}")
            # We might need to map this back to the component usage
            
        named = sorted(list(info["imports"]))
        if named:
            import_clauses.extend(named)
            
        if import_clauses:
            js_imports.append(f'import {{ {", ".join(import_clauses)} }} from "{url}";')

    # Build Component Tree
    def build_react_element(n, indent=8):
        spaces = " " * indent
        content = n.get("content", {})
        element_type = content.get("elementType", "div") if isinstance(content, dict) else "div"
        semantic_type = content.get("semanticType") if isinstance(content, dict) else None
        
        # Determine the component name to use
        tag_name = element_type
        
        # Check for dependency in content
        if isinstance(content, dict) and "dependency" in content:
            meta = content["dependency"].get("meta", {})
            if meta.get("namedImport"):
                tag_name = meta.get("originalName", element_type)
        
        # Map container to div
        if tag_name == "container":
            tag_name = "'div'"
        elif tag_name == "text":
            tag_name = "'span'"
        elif tag_name and tag_name[0].islower():
            # HTML tags should be quoted
            tag_name = f"'{tag_name}'"
        
        # Props
        props = {}
        attrs_dict = content.get("attrs", {}) if isinstance(content, dict) else {}
        for k, v in attrs_dict.items():
            props[k] = v
            
        # Handle dynamic props (state references)
        # The UIDL structure for children often contains dynamic content
        # But attributes can also be dynamic? The example shows 'children' having dynamic types.
        
        # Children
        children_code = []
        if isinstance(content, dict) and "children" in content:
            for child in content["children"]:
                child_type = child.get("type")
                child_content = child.get("content", {})
                
                if child_type == "static":
                    # Text content
                    if isinstance(child_content, str):
                        val = child_content
                    else:
                        val = child_content.get("content", "")
                    children_code.append(f'{spaces}  "{val}"')
                    
                elif child_type == "dynamic":
                    # State reference
                    ref_id = child_content.get("id")
                    if child_content.get("referenceType") == "state":
                        children_code.append(f'{spaces}  {ref_id}')
                    elif child_content.get("referenceType") == "prop":
                        # Prop passed to component (not fully supported in top-level widget yet)
                        children_code.append(f'{spaces}  props.{ref_id}')
                        
                elif child_type == "element":
                    children_code.append(build_react_element(child, indent + 2))
        
        props_str = json.dumps(props)
        # We might need to merge dynamic props here if they exist in a different structure
        
        children_str = ""
        if children_code:
            children_str = ",\n" + ",\n".join(children_code)
            
        return f"{spaces}React.createElement({tag_name}, {props_str}{children_str})"

    # Generate Component Body
    component_body = f"function {component_name}({{ model }}) {{\n"
    
    # State Hooks
    for name in state_defs.keys():
        component_body += f"  const [{name}, set_{name}] = React.useState(model.get('{name}'));\n"
        
    # Effect Hook for State Sync
    component_body += "\n  React.useEffect(() => {\n"
    component_body += "    const update = () => {\n"
    for name in state_defs.keys():
        component_body += f"      set_{name}(model.get('{name}'));\n"
    component_body += "    };\n"
    
    for name in state_defs.keys():
        component_body += f"    model.on('change:{name}', update);\n"
        
    component_body += "    return () => {\n"
    for name in state_defs.keys():
        component_body += f"      model.off('change:{name}', update);\n"
    component_body += "    };\n"
    component_body += "  }, [model]);\n\n"
    
    # Render
    component_body += "  return (\n"
    component_body += build_react_element(node, 4)
    component_body += "\n  );\n"
    component_body += "}\n"

    # Assemble ESM
    esm = "\n".join(js_imports) + "\n\n"
    esm += component_body + "\n\n"
    esm += "export default {\n"
    esm += "  render({ model, el }) {\n"
    esm += f"    const root = ReactDOM.createRoot(el);\n"
    esm += f"    root.render(React.createElement({component_name}, {{ model }}));\n"
    esm += "    return () => root.unmount();\n"
    esm += "  }\n"
    esm += "};\n"

    # 3. Final Widget Class
    attrs["_esm"] = Unicode(esm).tag(sync=True)
    
    # Initialize method
    def do_init(self, **kwargs):
        anywidget.AnyWidget.__init__(self, **kwargs)
        # Set default values
        for k, v in defaults.items():
            setattr(self, k, v)
            
    attrs["__init__"] = do_init
    
    return type(component_name + "Widget", (anywidget.AnyWidget,), attrs)


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
