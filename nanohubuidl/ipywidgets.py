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
    # JavaScript reserved keywords and built-in identifiers
    JS_RESERVED_KEYWORDS = {
        'abstract', 'arguments', 'await', 'boolean', 'break', 'byte', 'case', 'catch',
        'char', 'class', 'const', 'continue', 'debugger', 'default', 'delete', 'do',
        'double', 'else', 'enum', 'eval', 'export', 'extends', 'false', 'final',
        'finally', 'float', 'for', 'function', 'goto', 'if', 'implements', 'import',
        'in', 'instanceof', 'int', 'interface', 'let', 'long', 'native', 'new',
        'null', 'package', 'private', 'protected', 'public', 'return', 'short', 'static',
        'super', 'switch', 'synchronized', 'this', 'throw', 'throws', 'transient',
        'true', 'try', 'typeof', 'var', 'void', 'volatile', 'while', 'with', 'yield'
    }

    def sanitize_js_identifier(name):
        """Sanitize JavaScript identifier by prefixing reserved keywords with underscore"""
        if name.lower() in JS_RESERVED_KEYWORDS:
            return f"_{name}"
        return name

    def clean_self_references(expr, state_vars=None, prop_defs=None, is_custom_component=False):
        """Clean up self.props and self.state references in expressions

        Args:
            expr: The expression string to clean
            state_vars: Set of state variable names (optional)
            prop_defs: Set of prop definition names (optional)
            is_custom_component: Whether this is in a custom component context

        Returns:
            Cleaned expression string
        """
        if not isinstance(expr, str):
            return expr

        # Replace self.props with props
        expr = expr.replace("self.props", "props")

        # Replace self.state.variableName with variableName (and sanitize if needed)
        if "self.state." in expr:
            if state_vars:
                # Replace each state variable reference
                for state_var in state_vars:
                    js_var = sanitize_js_identifier(state_var)
                    expr = expr.replace(f"self.state.{state_var}", js_var)
            # Fallback: just remove self.state. prefix
            expr = expr.replace("self.state.", "")

        # In custom components, replace props.propName with just propName for prop definitions
        # that have been extracted as local consts
        if is_custom_component and prop_defs:
            for prop_name in prop_defs:
                # Use word boundaries to avoid partial matches
                import re
                # Replace props.propName with just propName
                expr = re.sub(rf'\bprops\.{prop_name}\b', prop_name, expr)

        return expr

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

    # Extract custom code from globals if present
    globals_section = project.get("globals", {})
    custom_code = globals_section.get("customCode", {}).get("body", "")

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

        # Convert dictionary-format options to array format
        # This handles cases like {"Au-Gold": "Au-Gold", "Ag-Silver": "Ag-Silver"}
        # and converts them to [{"key": "Au-Gold", "name": "Au-Gold"}, ...]
        if isinstance(default_val, dict) and (name.endswith("_options") or t in ["array", "list"]):
            converted_array = []
            for key, value in default_val.items():
                if isinstance(value, dict):
                    # If value is already a dict with icon/name, use it
                    item = {"key": key, **value}
                else:
                    # Simple key-value pair
                    item = {"key": key, "name": value}
                converted_array.append(item)
            default_val = converted_array

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

        # Check for expandIcon usage - need Icon component
        if isinstance(content, dict) and "attrs" in content:
            attrs = content.get("attrs", {})
            if "expandIcon" in attrs and isinstance(attrs["expandIcon"], str):
                # Add Icon to Material-UI core dependencies
                if "@material-ui/core" not in dependencies:
                    dependencies["@material-ui/core"] = {"version": "latest", "imports": set(), "default": False}
                dependencies["@material-ui/core"]["imports"].add("Icon")

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

    # Collect dependencies from custom components
    custom_components = project.get("components", {})
    for comp_name, comp_def in custom_components.items():
        comp_node = comp_def.get("node", {})
        collect_deps(comp_node)

    # Check if we need to add Format dependency for FormatCustomNumber
    if "FormatCustomNumber" in custom_components:
        if "react-number-format" not in dependencies:
            dependencies["react-number-format"] = {
                "version": "4.3.1",
                "imports": set(),
                "default": True  # v4.3.1 uses default export
            }
        else:
            dependencies["react-number-format"]["default"] = True

    # Check if Plot elementType is used anywhere (for Plotly charts)
    def check_for_plot(n):
        """Recursively check if Plot elementType is used"""
        content = n.get("content", {})
        if isinstance(content, dict):
            if content.get("elementType") == "Plot":
                return True
            if "children" in content:
                for child in content["children"]:
                    if check_for_plot(child):
                        return True
        return False

    uses_plot = check_for_plot(node)
    # Also check custom components
    for comp_name, comp_def in custom_components.items():
        comp_node = comp_def.get("node", {})
        if check_for_plot(comp_node):
            uses_plot = True
            break

    # Move Material-UI Lab components from core to lab
    # These components are in @material-ui/lab, not @material-ui/core
    LAB_COMPONENTS = {
        'ToggleButton', 'ToggleButtonGroup', 'Alert', 'AlertTitle',
        'Autocomplete', 'AvatarGroup', 'Pagination', 'PaginationItem',
        'Rating', 'Skeleton', 'SpeedDial', 'SpeedDialAction', 'SpeedDialIcon',
        'Timeline', 'TimelineItem', 'TimelineSeparator', 'TimelineConnector',
        'TimelineContent', 'TimelineDot', 'TimelineOppositeContent',
        'TreeView', 'TreeItem'
    }

    if "@material-ui/core" in dependencies:
        core_imports = dependencies["@material-ui/core"]["imports"]
        lab_imports = set()

        # Find components that should be in lab
        for component in list(core_imports):
            if component in LAB_COMPONENTS:
                lab_imports.add(component)
                core_imports.remove(component)

        # Add lab dependency if we found lab components
        if lab_imports:
            if "@material-ui/lab" not in dependencies:
                dependencies["@material-ui/lab"] = {
                    "version": "latest",
                    "imports": set(),
                    "default": False
                }
            dependencies["@material-ui/lab"]["imports"].update(lab_imports)

    # Build Imports - use React 17 which Material-UI v4 was designed for
    js_imports = []
    # Use React 17 for compatibility with Material-UI v4
    js_imports.append('import * as React from "https://esm.sh/react@17.0.2";')
    js_imports.append('import * as ReactDOM from "https://esm.sh/react-dom@17.0.2";')

    # Check for common libraries in custom code, prop definitions, and custom components
    all_code_to_check = custom_code
    # Check root prop definitions
    for prop_name, prop_def in prop_defs.items():
        if prop_def.get("type") == "func":
            default_val = prop_def.get("defaultValue", "")
            if isinstance(default_val, str):
                all_code_to_check += default_val
    # Check custom component prop definitions
    for comp_name, comp_def in custom_components.items():
        comp_prop_defs = comp_def.get("propDefinitions", {})
        for prop_name, prop_def in comp_prop_defs.items():
            if prop_def.get("type") == "func":
                default_val = prop_def.get("defaultValue", "")
                if isinstance(default_val, str):
                    all_code_to_check += default_val

    if all_code_to_check:
        if "LocalForage" in all_code_to_check:
            js_imports.append('import * as LocalForage from "https://esm.sh/localforage@1.10.0";')
        if "Axios" in all_code_to_check:
            js_imports.append('import Axios from "https://esm.sh/axios@1.6.0";')

    # Add Plotly imports if Plot elementType is used
    if uses_plot:
        # plotly.js-dist is standalone and doesn't need React deps
        js_imports.append('import Plotly from "https://esm.sh/plotly.js-dist@2.26.0";')
        # react-plotly.js/factory needs React deps
        js_imports.append('import createPlotlyComponent from "https://esm.sh/react-plotly.js@2.6.0/factory?deps=react@17.0.2,react-dom@17.0.2";')

    # Check if Material-UI is used and needs theme provider
    has_material_ui = "@material-ui/core" in dependencies

    for path, info in dependencies.items():
        # Use esm.sh with React 17 as peer dependency
        url = f"https://esm.sh/{path}"
        if info["version"] and info["version"] != "latest":
            url += f"@{info['version']}"

        # Force all packages to use React 17
        url += "?deps=react@17.0.2,react-dom@17.0.2"

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

    # Add alias for Format (backward compatibility with FormatCustomNumber)
    if "FormatCustomNumber" in custom_components:
        # v4.3.1 uses default export, so we imported as reactnumberformatDefault
        js_imports.append('const Format = reactnumberformatDefault;')

    # Add Material-UI theme support
    if has_material_ui:
        js_imports.append('import { ThemeProvider as MuiThemeProvider, createMuiTheme } from "https://esm.sh/@material-ui/core/styles?deps=react@17.0.2,react-dom@17.0.2";')
        js_imports.append('')
        js_imports.append('// Create Material-UI theme')
        js_imports.append('const muiTheme = createMuiTheme();')
        js_imports.append('')
        js_imports.append('// Load Material Icons font')
        js_imports.append('const materialIconsLink = document.createElement("link");')
        js_imports.append('materialIconsLink.href = "https://fonts.googleapis.com/icon?family=Material+Icons";')
        js_imports.append('materialIconsLink.rel = "stylesheet";')
        js_imports.append('if (!document.querySelector(\'link[href*="Material+Icons"]\')) {')
        js_imports.append('  document.head.appendChild(materialIconsLink);')
        js_imports.append('}')

    # Parse Events for Functional Component
    def parse_events(events_dict, is_root_component=True, component_state_defs=None):
        """
        Parse event definitions and generate event handlers.

        Args:
            events_dict: Dictionary of event definitions
            is_root_component: Whether this is the root component (has access to model)
            component_state_defs: State definitions for the current component
        """
        event_handlers = {}
        valid_events = {
            "click": "onClick",
            "focus": "onFocus",
            "blur": "onBlur",
            "change": "onChange",
            "submit": "onSubmit",
            "keydown": "onKeyDown",
            "keyup": "onKeyUp",
            "keypress": "onKeyPress",
            "mouseenter": "onMouseEnter",
            "mouseleave": "onMouseLeave",
            "mouseover": "onMouseOver",
            "select": "onSelect",
            "touchstart": "onTouchStart",
            "touchend": "onTouchEnd",
            "scroll": "onScroll",
            "load": "onLoad",
        }

        # Use provided state defs or fall back to root state defs
        current_state_defs = component_state_defs if component_state_defs is not None else state_defs

        for ev, actions in events_dict.items():
            handler_name = valid_events.get(ev, ev)

            # Build function body
            body = ""
            if isinstance(actions, list):
                action_list = actions
            else:
                action_list = [actions]

            for action in action_list:
                if not isinstance(action, dict):
                    continue

                action_type = action.get("type")

                if action_type == "stateChange":
                    modifies = action.get("modifies")
                    js_modifies = sanitize_js_identifier(modifies)
                    new_state = action.get("newState")

                    # Handle $toggle and $ references
                    val_expr = ""
                    if isinstance(new_state, str):
                        if new_state == "$toggle":
                            val_expr = f"!{js_modifies}"
                        elif new_state.startswith("$"):
                            val_expr = new_state[1:]
                            # Clean up self references in expressions
                            val_expr = clean_self_references(val_expr, current_state_defs.keys())
                            # Handle Object.assign with e.id and e.value - convert to direct object spread
                            # Child components pass {'prop': value} instead of {id: 'prop', value: value}
                            if "Object.assign" in val_expr and "[e.id]" in val_expr and "e.value" in val_expr:
                                # Replace {[e.id]:e.value} with e (direct object spread)
                                # From: Object.assign({},parameters, {[e.id]:e.value})
                                # To:   Object.assign({},parameters, e)
                                val_expr = val_expr.replace("{[e.id]:e.value}", "e")
                        else:
                            val_expr = json.dumps(new_state)
                    else:
                        val_expr = json.dumps(new_state)

                    # Generate update code
                    # For root component: set_variable(val); model.set('variable', val);
                    # For custom components: just set_variable(val);
                    # Note: model.set() automatically syncs in anywidget, no need for save_changes()
                    body += f"set_{js_modifies}({val_expr});\n"
                    if is_root_component:
                        body += f"model.set('{modifies}', {val_expr});\n"

                elif action_type == "propCall" or action_type == "propCall2":
                    calls = action.get("calls")
                    args = action.get("args", [])
                    # In root component, these are local functions defined from propDefinitions
                    # or passed props if not root (but we are building root mostly)
                    # Clean up self references in arguments
                    cleaned_args = [clean_self_references(a, state_defs.keys()) if isinstance(a, str) and not a.startswith("'") else a for a in args]
                    args_str = ", ".join(cleaned_args)
                    body += f"{calls}({args_str});\n"
                    
                elif action_type == "logging":
                    modifies = action.get("modifies")
                    new_state = action.get("newState")
                    body += f"console.log('{modifies}', {json.dumps(new_state)});\n"

            if body:
                event_handlers[handler_name] = f"(e) => {{ {body} }}"
        
        return event_handlers

    # Build Component Tree
    def build_react_element(n, indent=8, context="root", comp_prop_defs=None, comp_state_defs=None):
        spaces = " " * indent
        content = n.get("content", {})
        element_type = content.get("elementType", "div") if isinstance(content, dict) else "div"
        semantic_type = content.get("semanticType") if isinstance(content, dict) else None

        # Determine the component name to use
        tag_name = element_type

        # Check if this is a custom component
        if semantic_type in custom_components or element_type in custom_components:
            # Custom component - use it directly without quotes
            tag_name = semantic_type if semantic_type in custom_components else element_type
        # Check for dependency in content
        elif isinstance(content, dict) and "dependency" in content:
            meta = content["dependency"].get("meta", {})
            if meta.get("namedImport"):
                tag_name = meta.get("originalName", element_type)
        # Map container to div
        elif tag_name == "container":
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

        # Add style if present
        if isinstance(content, dict) and "style" in content:
            props["style"] = content["style"]

        # Events
        events_dict = content.get("events", {}) if isinstance(content, dict) else {}
        is_root = (context == "root")
        current_comp_state_defs = comp_state_defs if comp_state_defs else state_defs
        event_handlers = parse_events(events_dict, is_root_component=is_root, component_state_defs=current_comp_state_defs)
        for k, v in event_handlers.items():
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
                        js_ref_id = sanitize_js_identifier(ref_id)
                        children_code.append(f'{spaces}  {js_ref_id}')
                    elif child_content.get("referenceType") == "prop":
                        # Clean up self.props and self.state references in prop expressions
                        # Use component-specific defs if available, otherwise root defs
                        state_vars = comp_state_defs.keys() if comp_state_defs else state_defs.keys()
                        prop_defs_keys = comp_prop_defs.keys() if comp_prop_defs else None
                        is_custom = context == "custom"
                        ref_id = clean_self_references(ref_id, state_vars, prop_defs_keys, is_custom)
                        children_code.append(f'{spaces}  {ref_id}')
                        
                elif child_type == "element":
                    children_code.append(build_react_element(child, indent + 2, context, comp_prop_defs, comp_state_defs))
        
        # Serialize props, but handle event handlers (which are raw strings)
        # We can't use json.dumps for functions.
        props_items = []
        for k, v in props.items():
            if k in event_handlers:
                props_items.append(f'"{k}": {v}')
            else:
                # Handle dynamic props in attributes
                val = v
                if isinstance(v, dict) and v.get("type") == "dynamic":
                    c = v.get("content", {})
                    if c.get("referenceType") == "state":
                        val = c.get("id")
                        js_val = sanitize_js_identifier(val)
                        props_items.append(f'"{k}": {js_val}')
                        continue
                    elif c.get("referenceType") == "prop":
                         # In custom components, props are local consts or props.name
                         # In root component with model, some are local functions
                         val = c.get("id")
                         # Clean up references like "property(this.props)" -> "property(props)"
                         val = val.replace("this.props", "props")
                         # Clean up self.props and self.state references
                         state_vars = comp_state_defs.keys() if comp_state_defs else state_defs.keys()
                         prop_defs_keys = comp_prop_defs.keys() if comp_prop_defs else None
                         is_custom = context == "custom"
                         val = clean_self_references(val, state_vars, prop_defs_keys, is_custom)
                         # For simple prop names in custom components that aren't function defs, add props. prefix
                         if context == "custom" and "(" not in val and "props." not in val:
                             # Check if this is a prop definition (function) or a simple prop reference
                             val = f"props.{val}"
                         props_items.append(f'"{k}": {val}')
                         continue

                # Special handling for expandIcon - convert string to Icon element
                if k == "expandIcon" and isinstance(val, str):
                    # Make sure Icon is imported
                    if "@material-ui/core" in dependencies:
                        dependencies["@material-ui/core"]["imports"].add("Icon")
                    props_items.append(f'"{k}": React.createElement(Icon, {{}}, "{val}")')
                else:
                    props_items.append(f'"{k}": {json.dumps(val)}')
        
        # For custom components, inject model so they can use jupyter_axios
        if semantic_type in custom_components or element_type in custom_components:
            if context == "root":
                # In root component, model is available directly
                props_items.append('"model": model')
            elif context == "custom":
                # In custom components, model was passed as a prop
                props_items.append('"model": model')

        props_str = "{" + ", ".join(props_items) + "}"

        # Add debugging for Dialog 'open' prop
        debug_code = ""
        if "Dialog" in tag_name and any('"open"' in item for item in props_items):
            open_prop = next((item.split(": ")[1] for item in props_items if item.startswith('"open"')), None)
            if open_prop:
                debug_code = f"(console.log('[DIALOG DEBUG] Creating Dialog with open:', {open_prop}), "
                props_str = debug_code + props_str + ")"

        children_str = ""
        if children_code:
            children_str = ",\n" + ",\n".join(children_code)

        return f"{spaces}React.createElement({tag_name}, {props_str}{children_str})"

    # Generate Prop Definitions (Local Functions)
    prop_defs_code = ""
    prop_definitions = project.get("root", {}).get("propDefinitions", {})
    
    # Python methods to be added to the class
    python_methods = {}
    
    # Helper for handling messages
    def _handle_custom_msg(self, content, buffers):
        if "event" in content:
            event_name = content["event"]
            data = content.get("data", [])

            # Handle special _inject_url event for Jupyter Notebook 7/JupyterLab
            if event_name == "_inject_url":
                try:
                    from IPython import get_ipython
                    import __main__

                    ipython = get_ipython()
                    if ipython is not None and isinstance(data, str):
                        # Update the jupyter_notebook_url variable
                        ipython.user_ns['jupyter_notebook_url'] = data
                        __main__.jupyter_notebook_url = data
                except:
                    pass
                return

            # Handle HTTP proxy requests for jupyter_axios
            if event_name == "_http_request":
                try:
                    import requests

                    request_id = data.get("id")
                    url = data.get("url")
                    method = data.get("method", "GET").upper()
                    headers = data.get("headers", {})
                    request_data = data.get("data")
                    params = data.get("params", {})

                    # Debug logging
                    print(f"[PROXY DEBUG] HTTP Request:")
                    print(f"  URL: {url}")
                    print(f"  Method: {method}")
                    print(f"  Headers: {headers}")
                    print(f"  Data type: {type(request_data)}")
                    print(f"  Data: {request_data}")

                    # Determine if data should be sent as form-encoded or JSON
                    content_type = headers.get("Content-Type", headers.get("content-type", ""))

                    # Make the HTTP request server-side
                    response = None
                    if method == "GET":
                        response = requests.get(url, params=params, headers=headers)
                    elif method == "POST":
                        # If content-type is form-encoded and data is a string, send as data
                        if "application/x-www-form-urlencoded" in content_type and isinstance(request_data, str):
                            print(f"[PROXY DEBUG] Sending as form-encoded data")
                            response = requests.post(url, data=request_data, params=params, headers=headers)
                        else:
                            print(f"[PROXY DEBUG] Sending as JSON")
                            response = requests.post(url, json=request_data, params=params, headers=headers)
                    elif method == "PUT":
                        if "application/x-www-form-urlencoded" in content_type and isinstance(request_data, str):
                            response = requests.put(url, data=request_data, params=params, headers=headers)
                        else:
                            response = requests.put(url, json=request_data, params=params, headers=headers)
                    elif method == "DELETE":
                        response = requests.delete(url, params=params, headers=headers)

                    if response is not None:
                        print(f"[PROXY DEBUG] Response:")
                        print(f"  Status: {response.status_code}")
                        print(f"  Reason: {response.reason}")
                        print(f"  Text: {response.text[:500]}")  # First 500 chars

                        # Send response back to JavaScript
                        self.send({
                            "event": "_http_response",
                            "data": {
                                "id": request_id,
                                "status": response.status_code,
                                "statusText": response.reason,
                                "data": response.text,
                                "headers": dict(response.headers)
                            }
                        })
                    else:
                        # Unsupported method
                        self.send({
                            "event": "_http_response",
                            "data": {
                                "id": request_id,
                                "error": f"Unsupported HTTP method: {method}"
                            }
                        })
                except Exception as e:
                    # Send error back to JavaScript
                    self.send({
                        "event": "_http_response",
                        "data": {
                            "id": request_id,
                            "error": str(e)
                        }
                    })
                return

            # Handle regular callbacks
            if event_name in self._callbacks:
                for callback in self._callbacks[event_name]:
                    # Call with unpacked arguments if list, or single arg
                    if isinstance(data, list):
                        callback(*data)
                    else:
                        callback(data)

    python_methods["_handle_custom_msg"] = _handle_custom_msg
    
    # Init method to setup callbacks
    def __init__(self, **kwargs):
        anywidget.AnyWidget.__init__(self, **kwargs)
        self._callbacks = {}
        self.on_msg(self._handle_custom_msg)
        
    python_methods["__init__"] = __init__

    for prop_name, prop_def in prop_definitions.items():
        if prop_def.get("type") == "func":
            default_val = prop_def.get("defaultValue", "()=>{}")

            # Fix self references in prop functions: self -> _self, self.props -> _self._props
            if "self" in default_val:
                # For functions with (self, ...) parameter, rename both parameter and references
                if re.search(r'\(self,', default_val):
                    default_val = re.sub(r'\(self,', r'(_self,', default_val)
                    default_val = re.sub(r'\bself\.props\b', r'_self._props', default_val)
                    default_val = re.sub(r'\bself\.state\b', r'_self.state', default_val)
                    # Also handle bare self references (like in callbacks)
                    default_val = re.sub(r'\bself\b(?!\.)', r'_self', default_val)

            # Convert Axios calls to use jupyter_axios proxy
            # Pattern: Axios.request(url, options) -> jupyter_axios.request(model, url, options)
            # Pattern: Axios.get(url, ...) -> jupyter_axios.get(model, url, ...)
            if "Axios." in default_val:
                # Convert Axios.request to jupyter_axios.request with model as first arg
                default_val = re.sub(
                    r'\bAxios\.request\s*\(',
                    r'jupyter_axios.request(model, ',
                    default_val
                )
                # Convert Axios.get to jupyter_axios.get with model as first arg
                default_val = re.sub(
                    r'\bAxios\.get\s*\(',
                    r'jupyter_axios.get(model, ',
                    default_val
                )
                # Convert Axios.post to jupyter_axios.post with model as first arg
                default_val = re.sub(
                    r'\bAxios\.post\s*\(',
                    r'jupyter_axios.post(model, ',
                    default_val
                )
                # Convert Axios.put to jupyter_axios.put with model as first arg
                default_val = re.sub(
                    r'\bAxios\.put\s*\(',
                    r'jupyter_axios.put(model, ',
                    default_val
                )
                # Convert Axios.delete to jupyter_axios.delete with model as first arg
                default_val = re.sub(
                    r'\bAxios\.delete\s*\(',
                    r'jupyter_axios.delete(model, ',
                    default_val
                )

            # Convert old setState syntax to functional component model.set() calls
            # Pattern: e.setState({"state_name": value}) or _self.setState({"state_name": value})
            if "setState" in default_val:
                # This converts class component setState to functional component model.set
                # We need to extract the state updates and convert them to model.set calls
                def convert_setState(match):
                    state_obj = match.group(2)  # The state object like {"loader_open":false}

                    # Parse the state object to extract key-value pairs
                    # Match patterns like "key":value or 'key':value
                    updates = []
                    state_obj_clean = state_obj.strip()
                    if state_obj_clean.startswith('{') and state_obj_clean.endswith('}'):
                        # Extract key-value pairs using regex
                        pairs = re.findall(r'["\']([^"\']+)["\']:\s*([^,}]+)', state_obj_clean)
                        for key, value in pairs:
                            updates.append(f'model.set("{key}", {value.strip()})')

                    if updates:
                        return '; '.join(updates)
                    else:
                        # Fallback: just remove setState call
                        return '/* setState removed - use model.set() instead */'

                # Replace patterns like: e.setState({"key": value}) or _self.setState(...)
                default_val = re.sub(
                    r'(\w+)\.setState\s*\(\s*(\{[^}]+\})\s*\)',
                    convert_setState,
                    default_val
                )

            # JS: Wrap the function to send message to Python
            # We execute the original logic AND send the event
            prop_defs_code += f"  const {prop_name} = (...args) => {{\n"
            prop_defs_code += f"    model.send({{ event: '{prop_name}', data: args }});\n"
            prop_defs_code += f"    return ({default_val})(...args);\n"
            prop_defs_code += f"  }};\n"
            
            # Python: Add method to register callback
            # We need a closure to capture prop_name
            def make_registrar(name):
                def registrar(self, callback):
                    if name not in self._callbacks:
                        self._callbacks[name] = []
                    self._callbacks[name].append(callback)
                return registrar
            
            python_methods[prop_name] = make_registrar(prop_name)

    # Generate State Hooks
    hooks_code = ""
    for name in state_defs.keys():
        js_name = sanitize_js_identifier(name)
        hooks_code += f"  const [{js_name}, set_{js_name}] = React.useState(model.get('{name}'));\n"

    component_body = f"function {component_name}({{ model }}) {{\n"
    component_body += "  console.log('[COMPONENT DEBUG] Component rendering...');\n"
    component_body += "  console.log('[COMPONENT DEBUG] Model object:', model);\n"
    component_body += "  console.log('[COMPONENT DEBUG] Model.get function:', typeof model.get);\n"

    # Add prop definitions
    component_body += "  console.log('[COMPONENT DEBUG] Defining prop functions...');\n"
    component_body += prop_defs_code + "\n"

    # Add hooks
    component_body += "  console.log('[COMPONENT DEBUG] Creating state hooks...');\n"
    component_body += hooks_code + "\n"
    component_body += "  console.log('[COMPONENT DEBUG] State hooks created');\n"
    if "loader_open" in state_defs:
        component_body += "  console.log('[LOADER STATE DEBUG] loader_open value:', loader_open);\n"

    # Create a self-like object for compatibility with class-component-style prop functions
    if state_defs or prop_definitions:
        component_body += "  // Create self object for compatibility with class-style functions\n"
        component_body += "  const self = {\n"
        if state_defs:
            component_body += "    state: {\n"
            state_items = [f"      {name}: {sanitize_js_identifier(name)}" for name in state_defs.keys()]
            component_body += ",\n".join(state_items)
            component_body += "\n    },\n"
        # Add props object containing all prop functions for inter-prop-function calls
        if prop_definitions:
            component_body += "    props: {\n"
            prop_items = [f"      {name}: {name}" for name in prop_definitions.keys()]
            component_body += ",\n".join(prop_items)
            component_body += "\n    }\n"
        else:
            component_body += "    props: {}\n"  # Empty object if no prop definitions
        component_body += "  };\n\n"

    # Effect Hook for State Sync
    component_body += "\n  React.useEffect(() => {\n"
    component_body += "    console.log('[STATE SYNC DEBUG] Setting up state synchronization...');\n"

    # Create separate listeners for each state to get the actual changed value
    for name in state_defs.keys():
        js_name = sanitize_js_identifier(name)
        component_body += f"    const update_{js_name} = () => {{\n"
        component_body += f"      // Use requestAnimationFrame to ensure model is fully updated\n"
        component_body += f"      requestAnimationFrame(() => {{\n"
        component_body += f"        const newValue = model.get('{name}');\n"
        component_body += f"        console.log('[STATE SYNC DEBUG] Change event for {name}, new value:', newValue);\n"
        component_body += f"        set_{js_name}(newValue);\n"
        component_body += f"      }});\n"
        component_body += f"    }};\n"

    for name in state_defs.keys():
        js_name = sanitize_js_identifier(name)
        component_body += f"    model.on('change:{name}', update_{js_name});\n"
        component_body += f"    console.log('[STATE SYNC DEBUG] Listening for change:{name}');\n"

    component_body += "    return () => {\n"
    for name in state_defs.keys():
        js_name = sanitize_js_identifier(name)
        component_body += f"      model.off('change:{name}', update_{js_name});\n"
    component_body += "    };\n"
    component_body += "  }, [model]);\n\n"

    # Add URL injection effect for Jupyter Notebook 7/JupyterLab compatibility
    component_body += "  // Inject notebook URL for compatibility (runs once on mount)\n"
    component_body += "  React.useEffect(() => {\n"
    component_body += "    // Send the current URL to Python for jupyter_notebook_url variable\n"
    component_body += "    if (typeof window !== 'undefined' && window.location) {\n"
    component_body += "      model.send({ event: '_inject_url', data: window.location.href });\n"
    component_body += "    }\n"

    # Call buildSchema on mount if it exists
    if "buildSchema" in prop_definitions:
        component_body += "    // Call buildSchema on component mount to load tool schema\n"
        component_body += "    console.log('[BUILD SCHEMA] Calling buildSchema on mount...');\n"
        component_body += "    console.log('[BUILD SCHEMA] self object:', self);\n"
        component_body += "    console.log('[BUILD SCHEMA] self.props:', self ? self.props : 'self is undefined');\n"
        component_body += "    console.log('[BUILD SCHEMA] buildSchema type:', typeof buildSchema);\n"
        component_body += "    if (typeof buildSchema === 'function') {\n"
        component_body += "      buildSchema(self).catch(err => {\n"
        component_body += "        console.error('[BUILD SCHEMA] Error loading schema:', err);\n"
        component_body += "        console.error('[BUILD SCHEMA] Error stack:', err.stack);\n"
        component_body += "        // Call onSchemaError if it exists\n"
        component_body += "        if (typeof onSchemaError === 'function') {\n"
        component_body += "          onSchemaError(self);\n"
        component_body += "        }\n"
        component_body += "      });\n"
        component_body += "    }\n"

    component_body += "  }, []);\n\n"

    # Render
    if has_material_ui:
        # Wrap with Material-UI ThemeProvider
        component_body += "  return (\n"
        component_body += "    React.createElement(MuiThemeProvider, {theme: muiTheme},\n"
        component_body += build_react_element(node, 6)
        component_body += ")\n"
        component_body += "  );\n"
    else:
        component_body += "  return (\n"
        component_body += build_react_element(node, 4)
        component_body += "\n  );\n"
    component_body += "}\n"

    # Generate custom component functions
    # First, determine dependency order (topological sort)
    # If component A uses component B, B must be defined before A
    def get_component_dependencies(comp_def):
        """Find which custom components this component uses"""
        deps = set()
        def find_deps(n):
            content = n.get("content", {})
            element_type = content.get("elementType") if isinstance(content, dict) else None
            semantic_type = content.get("semanticType") if isinstance(content, dict) else None

            # Check if this references a custom component
            if semantic_type in custom_components:
                deps.add(semantic_type)
            elif element_type in custom_components:
                deps.add(element_type)

            # Recurse into children
            if isinstance(content, dict) and "children" in content:
                for child in content["children"]:
                    find_deps(child)

        find_deps(comp_def.get("node", {}))
        return deps

    # Build dependency graph
    comp_deps = {name: get_component_dependencies(comp_def)
                 for name, comp_def in custom_components.items()}

    # Topological sort
    sorted_components = []
    visited = set()

    def visit(name):
        if name in visited:
            return
        visited.add(name)
        # Visit dependencies first
        for dep in comp_deps.get(name, set()):
            if dep in custom_components:  # Only visit if it's a custom component
                visit(dep)
        sorted_components.append(name)

    for comp_name in custom_components.keys():
        visit(comp_name)

    # Generate components in dependency order
    custom_component_code = ""

    # Create Plot component from Plotly if needed
    if uses_plot:
        custom_component_code += "// Create Plot component from Plotly\n"
        custom_component_code += "const Plot = createPlotlyComponent(Plotly);\n\n"

    for comp_name in sorted_components:
        comp_def = custom_components[comp_name]
        comp_prop_defs = comp_def.get("propDefinitions", {})
        comp_state_defs = comp_def.get("stateDefinitions", {})
        comp_node = comp_def.get("node", {})

        # Start component function
        # Accept both props and model so custom components can use jupyter_axios
        custom_component_code += f"function {comp_name}({{ model, ...props }}) {{\n"

        # Add prop definitions as local variables
        for prop_name, prop_def in comp_prop_defs.items():
            prop_type = prop_def.get("type")

            if prop_type == "func":
                default_val = prop_def.get("defaultValue", "()=>{}")
                # Fix naming conflicts: rename parameters and their references
                # Strategy: For functions with (props) or (self, ...) parameters, rename both
                # the parameter AND its usages within that function scope

                # Check if this function has (props)=> parameter
                if re.search(r'\(props\)\s*=>', default_val):
                    # This function uses (props) as parameter, so we need to be careful:
                    # - props.xxx where xxx is ALSO a prop definition should become just xxx (access outer const)
                    # - props.xxx where xxx is NOT a prop definition should become _props.xxx (access param)

                    # First, replace props.propName( with just propName( for prop definitions (before renaming props)
                    for other_prop_name in comp_prop_defs.keys():
                        # Replace props.propName( with propName( (function calls to outer consts)
                        default_val = re.sub(rf'\bprops\.{other_prop_name}\(', f'{other_prop_name}(', default_val)

                    # Then rename the parameter and bare 'props' references
                    default_val = re.sub(r'\(props\)\s*=>', r'(_props)=>', default_val)
                    # Replace standalone 'props' identifier (like in function calls) with _props
                    default_val = re.sub(r'\b(props)(?=\s*[,\)])', r'_props', default_val)

                    # Then rename remaining props. references to _props. (these are actual component props)
                    default_val = re.sub(r'\bprops\.', r'_props.', default_val)

                # For functions with (self, ...) parameter, rename both parameter and references
                if re.search(r'\(self,', default_val):
                    default_val = re.sub(r'\(self,', r'(_self,', default_val)
                    default_val = re.sub(r'\bself\.props\b', r'_self._props', default_val)
                    default_val = re.sub(r'\bself\.state\b', r'_self.state', default_val)
                    # Also handle bare self references (like in callbacks)
                    default_val = re.sub(r'\bself\b(?!\.)', r'_self', default_val)

                # Convert Axios calls to use jupyter_axios proxy for custom components
                # In custom components, model is available directly via destructured parameter
                if "Axios." in default_val:
                    # Convert Axios.request to jupyter_axios.request with model as first arg
                    default_val = re.sub(
                        r'\bAxios\.request\s*\(',
                        r'jupyter_axios.request(model, ',
                        default_val
                    )
                    # Convert Axios.get to jupyter_axios.get with model as first arg
                    default_val = re.sub(
                        r'\bAxios\.get\s*\(',
                        r'jupyter_axios.get(model, ',
                        default_val
                    )
                    # Convert Axios.post to jupyter_axios.post with model as first arg
                    default_val = re.sub(
                        r'\bAxios\.post\s*\(',
                        r'jupyter_axios.post(model, ',
                        default_val
                    )
                    # Convert Axios.put to jupyter_axios.put with model as first arg
                    default_val = re.sub(
                        r'\bAxios\.put\s*\(',
                        r'jupyter_axios.put(model, ',
                        default_val
                    )
                    # Convert Axios.delete to jupyter_axios.delete with model as first arg
                    default_val = re.sub(
                        r'\bAxios\.delete\s*\(',
                        r'jupyter_axios.delete(model, ',
                        default_val
                    )

                # Convert setState calls to use state setters for custom components
                if "setState" in default_val:
                    def convert_setState(match):
                        var_name = match.group(1)  # The variable name (self, selfr, e, etc.)
                        state_obj = match.group(2)  # The state object like {"open":false}
                        updates = []
                        state_obj_clean = state_obj.strip()
                        if state_obj_clean.startswith('{') and state_obj_clean.endswith('}'):
                            # Updated regex to handle spaces around colons and commas
                            # Matches: 'key' : value or "key" : value or 'key': value
                            # Also handles string values like '' or ""
                            pairs = re.findall(r'["\']([^"\']+)["\']\s*:\s*([^,}]+?)(?=\s*[,}])', state_obj_clean)
                            for key, value in pairs:
                                # For custom components, use set_stateName
                                js_key = sanitize_js_identifier(key)
                                updates.append(f'set_{js_key}({value.strip()})')
                        if updates:
                            return '; '.join(updates)
                        else:
                            return '/* setState removed - use state setters instead */'

                    default_val = re.sub(
                        r'(\w+)\.setState\s*\(\s*(\{[^}]+\})\s*\)',
                        convert_setState,
                        default_val
                    )
                    # Debug: print conversion result
                    if comp_name == "AuthSession" and prop_name == "onLoad":
                        print(f"[CUSTOM COMPONENT DEBUG] setState conversion for AuthSession.onLoad")
                        print(f"  Converted code (first 500 chars): {default_val[:500]}")

                # Wrap the default function in parentheses to avoid ambiguity with ||
                custom_component_code += f"  const {prop_name} = props.{prop_name} || ({default_val});\n"

            else:
                # Handle non-function props (objects, strings, numbers, etc.)
                default_val = prop_def.get("defaultValue")
                if default_val is not None:
                    # For non-function props, just create a const with the default value
                    custom_component_code += f"  const {prop_name} = props.{prop_name} !== undefined ? props.{prop_name} : {json.dumps(default_val)};\n"
                else:
                    # No default value, just use the prop directly
                    custom_component_code += f"  const {prop_name} = props.{prop_name};\n"

        # Add state hooks for component state
        # Track which state variables depend on which props for effect hooks
        state_prop_dependencies = {}  # {state_name: prop_expression}

        for state_name, state_def in comp_state_defs.items():
            js_state_name = sanitize_js_identifier(state_name)
            default_val = state_def.get("defaultValue")

            # Handle dynamic default values
            if isinstance(default_val, dict) and default_val.get("type") == "dynamic":
                ref_content = default_val.get("content", {})
                if ref_content.get("referenceType") == "prop":
                    ref_id = ref_content.get("id")
                    # Clean up self.props and self.state references
                    ref_id = clean_self_references(ref_id, comp_state_defs.keys())
                    custom_component_code += f"  const [{js_state_name}, set_{js_state_name}] = React.useState({ref_id});\n"
                    # Track this dependency for useEffect
                    state_prop_dependencies[state_name] = ref_id
                else:
                    # Fallback to undefined
                    custom_component_code += f"  const [{js_state_name}, set_{js_state_name}] = React.useState(undefined);\n"
            else:
                # Static default value
                custom_component_code += f"  const [{js_state_name}, set_{js_state_name}] = React.useState({json.dumps(default_val)});\n"

        # Add useEffect to sync state with prop changes
        if state_prop_dependencies:
            custom_component_code += "\n"
            custom_component_code += "  // Sync state variables when props change\n"
            custom_component_code += "  React.useEffect(() => {\n"
            for state_name, prop_expr in state_prop_dependencies.items():
                js_state_name = sanitize_js_identifier(state_name)
                custom_component_code += f"    set_{js_state_name}({prop_expr});\n"
            # Add all referenced props as dependencies
            # Extract base prop names from expressions like "parameters.mat"
            prop_deps = set()
            for prop_expr in state_prop_dependencies.values():
                # Extract the base prop name (before any dots)
                base_prop = prop_expr.split('.')[0].split('[')[0]
                prop_deps.add(base_prop)
            deps_list = ", ".join(sorted(prop_deps))
            custom_component_code += f"  }}, [{deps_list}]);\n"

        # Create self object for custom component prop functions
        if comp_state_defs or comp_prop_defs:
            custom_component_code += "\n"
            custom_component_code += "  // Create self object for compatibility with class-style functions\n"
            custom_component_code += "  const self = {\n"
            if comp_state_defs:
                custom_component_code += "    state: {\n"
                state_items = [f"      {name}: {sanitize_js_identifier(name)}" for name in comp_state_defs.keys()]
                custom_component_code += ",\n".join(state_items)
                custom_component_code += "\n    },\n"
            # Add props object containing all prop functions for inter-prop-function calls
            # Get only func-type props
            func_props = [name for name, defn in comp_prop_defs.items() if defn.get("type") == "func"] if comp_prop_defs else []
            if func_props:
                custom_component_code += "    props: {\n"
                prop_items = [f"      {name}: {name}" for name in func_props]
                custom_component_code += ",\n".join(prop_items)
                custom_component_code += "\n    }\n"
            else:
                custom_component_code += "    props: {}\n"
            custom_component_code += "  };\n"

        # Call onLoad on mount if it exists
        if "onLoad" in comp_prop_defs:
            custom_component_code += "\n"
            custom_component_code += "  // Call onLoad on component mount\n"
            custom_component_code += "  React.useEffect(() => {\n"
            custom_component_code += f"    console.log('[{comp_name}] Calling onLoad on mount...');\n"
            custom_component_code += "    if (typeof onLoad === 'function') {\n"
            custom_component_code += "      try {\n"
            custom_component_code += "        const result = onLoad(self);\n"
            custom_component_code += "        // If onLoad returns a promise, handle errors\n"
            custom_component_code += "        if (result && typeof result.then === 'function') {\n"
            custom_component_code += "          result.catch(err => {\n"
            custom_component_code += f"            console.error('[{comp_name}] onLoad promise rejected:', err);\n"
            custom_component_code += "            if (typeof onError === 'function') {\n"
            custom_component_code += "              onError(self);\n"
            custom_component_code += "            }\n"
            custom_component_code += "          });\n"
            custom_component_code += "        }\n"
            custom_component_code += "      } catch (err) {\n"
            custom_component_code += f"        console.error('[{comp_name}] onLoad error:', err);\n"
            custom_component_code += "        if (typeof onError === 'function') {\n"
            custom_component_code += "          onError(self);\n"
            custom_component_code += "        }\n"
            custom_component_code += "      }\n"
            custom_component_code += "    }\n"
            custom_component_code += "  }, []);\n"

        # Add render return
        custom_component_code += "  return (\n"
        custom_component_code += build_react_element(comp_node, 4, "custom", comp_prop_defs, comp_state_defs)
        custom_component_code += "\n  );\n"
        custom_component_code += "}\n\n"

    # Assemble ESM
    esm = "\n".join(js_imports) + "\n\n"

    # Add jupyter_axios proxy for server-side HTTP requests
    esm += "// jupyter_axios: Custom Axios implementation using Python kernel for HTTP requests\n"
    esm += "// This bypasses CORS by making requests server-side through the Jupyter kernel\n"
    esm += "const jupyter_axios = (() => {\n"
    esm += "  let requestCounter = 0;\n"
    esm += "  const pendingRequests = new Map();\n"
    esm += "\n"
    esm += "  // Setup response listener (will be called once when model is available)\n"
    esm += "  const setupListener = (model) => {\n"
    esm += "    if (setupListener.initialized) return;\n"
    esm += "    setupListener.initialized = true;\n"
    esm += "\n"
    esm += "    model.on('msg:custom', (msg) => {\n"
    esm += "      console.log('[jupyter_axios] Received message:', msg);\n"
    esm += "      if (msg.event === '_http_response') {\n"
    esm += "        const { id, status, statusText, data, headers, error } = msg.data;\n"
    esm += "        console.log('[jupyter_axios] Response received:', { id, status, statusText, error, dataLength: data ? data.length : 0 });\n"
    esm += "        const pending = pendingRequests.get(id);\n"
    esm += "        if (pending) {\n"
    esm += "          pendingRequests.delete(id);\n"
    esm += "          if (error) {\n"
    esm += "            console.error('[jupyter_axios] Request failed with error:', error);\n"
    esm += "            pending.reject(new Error(error));\n"
    esm += "          } else {\n"
    esm += "            // Parse JSON if content-type indicates it\n"
    esm += "            let parsedData = data;\n"
    esm += "            const contentType = headers && headers['content-type'] || headers && headers['Content-Type'] || '';\n"
    esm += "            console.log('[jupyter_axios] Content-Type:', contentType);\n"
    esm += "            if (contentType.includes('application/json')) {\n"
    esm += "              try {\n"
    esm += "                parsedData = JSON.parse(data);\n"
    esm += "                console.log('[jupyter_axios] Parsed JSON:', parsedData);\n"
    esm += "              } catch (e) {\n"
    esm += "                console.warn('[jupyter_axios] Failed to parse JSON response:', e);\n"
    esm += "              }\n"
    esm += "            }\n"
    esm += "            console.log('[jupyter_axios] Resolving promise with:', { status, statusText, data: parsedData });\n"
    esm += "            pending.resolve({\n"
    esm += "              status,\n"
    esm += "              statusText,\n"
    esm += "              data: parsedData,\n"
    esm += "              headers\n"
    esm += "            });\n"
    esm += "          }\n"
    esm += "        } else {\n"
    esm += "          console.warn('[jupyter_axios] No pending request found for id:', id);\n"
    esm += "        }\n"
    esm += "      }\n"
    esm += "    });\n"
    esm += "  };\n"
    esm += "\n"
    esm += "  const request = (model, url, options = {}) => {\n"
    esm += "    console.log('[jupyter_axios] Making request:', url, options);\n"
    esm += "    setupListener(model);\n"
    esm += "\n"
    esm += "    const requestId = ++requestCounter;\n"
    esm += "    const method = options.method || 'GET';\n"
    esm += "    const headers = options.headers || {};\n"
    esm += "    const data = options.data;\n"
    esm += "    const params = options.params || {};\n"
    esm += "\n"
    esm += "    return new Promise((resolve, reject) => {\n"
    esm += "      pendingRequests.set(requestId, { resolve, reject });\n"
    esm += "\n"
    esm += "      // Send request to Python\n"
    esm += "      model.send({\n"
    esm += "        event: '_http_request',\n"
    esm += "        data: {\n"
    esm += "          id: requestId,\n"
    esm += "          url,\n"
    esm += "          method,\n"
    esm += "          headers,\n"
    esm += "          data,\n"
    esm += "          params\n"
    esm += "        }\n"
    esm += "      });\n"
    esm += "    });\n"
    esm += "  };\n"
    esm += "\n"
    esm += "  // Return axios-compatible API\n"
    esm += "  return {\n"
    esm += "    request: (model, url, options) => request(model, url, options),\n"
    esm += "    get: (model, url, options = {}) => request(model, url, { ...options, method: 'GET' }),\n"
    esm += "    post: (model, url, data, options = {}) => request(model, url, { ...options, method: 'POST', data }),\n"
    esm += "    put: (model, url, data, options = {}) => request(model, url, { ...options, method: 'PUT', data }),\n"
    esm += "    delete: (model, url, options = {}) => request(model, url, { ...options, method: 'DELETE' })\n"
    esm += "  };\n"
    esm += "})();\n"
    esm += "\n"

    # Add custom code if present
    if custom_code:
        esm += "// Custom code from globals\n"
        esm += custom_code + "\n\n"

    esm += custom_component_code
    esm += component_body + "\n\n"
    esm += "export default {\n"
    esm += "  render({ model, el }) {\n"
    esm += "    console.log('[RENDER DEBUG] render() called');\n"
    esm += "    console.log('[RENDER DEBUG] model:', model);\n"
    esm += "    console.log('[RENDER DEBUG] el:', el);\n"
    esm += "    debugger;\n"
    esm += "    try {\n"
    esm += f"      console.log('[RENDER DEBUG] Creating React element for {component_name}...');\n"
    esm += f"      const element = React.createElement({component_name}, {{ model }});\n"
    esm += "      console.log('[RENDER DEBUG] React element created:', element);\n"
    esm += "      console.log('[RENDER DEBUG] Rendering to DOM...');\n"
    esm += "      debugger;\n"
    esm += "      ReactDOM.render(element, el);\n"
    esm += "      console.log('[RENDER DEBUG] Render complete');\n"
    esm += "      return () => {\n"
    esm += "        console.log('[RENDER DEBUG] Unmounting component...');\n"
    esm += "        ReactDOM.unmountComponentAtNode(el);\n"
    esm += "      };\n"
    esm += "    } catch (error) {\n"
    esm += "      console.error('[RENDER DEBUG] ERROR during render:', error);\n"
    esm += "      console.error('[RENDER DEBUG] Error stack:', error.stack);\n"
    esm += "      debugger; // Pause on error\n"
    esm += "      throw error;\n"
    esm += "    }\n"
    esm += "  }\n"
    esm += "};\n"

    # 3. Final Widget Class
    attrs["_esm"] = Unicode(esm).tag(sync=True)
    attrs.update(python_methods)

    # Prevent ipywidgets from trying to manage layout as a child widget
    # anywidget doesn't use layout/tooltip/tabbable traits from ipywidgets
    # Setting them to None prevents ipywidgets manager from trying to create child views
    attrs["layout"] = None
    attrs["tooltip"] = None
    attrs["tabbable"] = None

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
