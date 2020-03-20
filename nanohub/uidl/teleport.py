import json 
import requests
import jsonschema
import uuid, weakref, os
from IPython.display import HTML, Javascript, display

class TeleportGlobals():
    def __init__(self, *args, **kwargs):
        self.settings = {'language' : 'en', 'title' : ''}
        self.assets = []
        self.meta = []
        self.manifest = {}
        self.ids = {}
        
    def __json__(self):
        return {
            "settings" : self.settings,
            "assets" : self.assets,
            "meta" : self.meta,
            "manifest" : self.manifest
        }
    
    def __str__(self):
        return json.dumps(self.__json__())
        
    def buildReact(self, *args , **kwargs):
      react = ""
      for asset in self.assets:
        if asset["type"] == "script":          
          react += asset["content"] + "\n";
        if asset["type"] == "style":
          react += "var tstyle = document.createElement('style')\n";
          react += "document.head.appendChild(tstyle);\n";
          react += "tstyle.sheet.insertRule('" + asset["content"] + "');\n";
      return react
      
    def addAsset(self, id, asset):
      if id in self.ids:
        pass;
      else:
        self.ids[id] = len(self.ids)
        self.assets.append(asset)
      
        
class TeleportNode():
  def __init__(self, *args, **kwargs):
    self.type = ""
    self.content = None
    
  def __json__(self):
    return {
      "type": self.type,
      "content" : self.contentToJson(),
    }
    
  def contentToJson(self):
    if self.content is None:
      return {}
    else:
      return self.content.__json__()      
  
  def __str__(self):
      return json.dumps(self.__json__())

  def buildReact(self, *args , **kwargs):   
    react = ""
    if self.content == None:
      react += "''\n"
    else:
      if self.type == "static":
        react += " '" + str(self.content).replace("'", "\"") + "' "
      elif self.type == "dynamic":
        if ("referenceType" in self.content and self.content["referenceType"] == "state"):
          reference = "self.state." + self.content["id"] + "";
        elif ("referenceType" in self.content and self.content["referenceType"] == "prop"):
          reference = "self.props." + self.content["id"] + "";
        elif ("referenceType" in self.content and self.content["referenceType"] == "local"):
          reference = "" + self.content["id"] + "";
        #elif ("referenceType" in self.content and self.content["referenceType"] == "attr"):
        #  reference = "" + content["id"] + "";
        else:
          reference = "";
        react += " " + str(reference) + " "
      else:
        react += self.content.buildReact( nativeRef=kwargs.get("nativeRef","") )
    return react
        

class TeleportElement(TeleportNode):
  def __init__(self, content, *args, **kwargs):
    TeleportNode.__init__(self)
    self.type = "element"      
    self.content = content
    
  def addContent(self, child):
    self.content.children.append(child)
    
class TeleportConditional(TeleportNode):
  def __init__(self, content, *args, **kwargs):
    TeleportNode.__init__(self)
    self.type = "conditional"      
    self.node = TeleportElement(content)
    self.reference = kwargs.get("reference", {"type": "static","content":0})
    self.value = kwargs.get("value", None)
    self.conditions = kwargs.get("conditions", [])
    self.matchingCriteria = "all"

  def addContent(self, child):
    self.node.addContent(child)

  def buildReact(self, *args , **kwargs):  
    value = self.reference
    content = value["content"]
    try:
      if (value["type"] == "dynamic"):
        if ("referenceType" in content and content["referenceType"] == "state"):
          reference = "self.state." + content["id"] + "";
        elif ("referenceType" in content and content["referenceType"] == "prop"):
          reference = "self.props." + content["id"] + "";
        elif ("referenceType" in content and content["referenceType"] == "local"):
          reference = "" + content["id"] + "";
      elif (value["type"] == "static"):
        reference = content
    except:
      reference = self.reference

    value = self.value
    if isinstance(value, str) and value.startswith("$"):
        value = value.replace("$", "")
    else:
        value = json.dumps(value)

    react = ""
    react += "(("
    if (len(self.conditions) ==0):
        react += "( " + str(reference) + " == " + value +")"
    else:
        for i, condition in enumerate(self.conditions):  
            if i > 0:
                if self.matchingCriteria == "one":
                     react += " || "
                else:
                     react += " && "
            if ("operand" in condition):
                react += "( " + str(reference) + " " + str(condition["operation"]) + " " + json.dumps(condition["operand"]) +")"
            elif self.value is not None:
                react += "( " + str(reference) + " " + str(condition["operation"]) + " " + json.dumps(self.value) +")"
    react += ") ?"
    react += self.node.buildReact(nativeRef=kwargs.get("nativeRef",""))
    react += " : null)"
    return react

  def __json__(self):
    return {
      "type": self.type,
      "content" : { 
        "node" : self.node.__json__(),
        "reference" : self.reference, 
        "value" : self.value, 
        "condition": {
            "conditions" : self.conditions,
            "matchingCriteria": self.matchingCriteria
        },
      }
    }

class TeleportRepeat(TeleportNode):
  def __init__(self, content, *args, **kwargs):
    TeleportNode.__init__(self)
    self.type = "repeat"      
    self.node = TeleportElement(content)
    self.dataSource = kwargs.get("dataSource", {"type": "static","content":[]})
    self.iteratorName = kwargs.get("iteratorName", "it")
    self.useIndex = kwargs.get("iteratorName", True)

  def addContent(self, child):
    self.node.addContent(child)

  def buildReact(self, *args , **kwargs):  
    reference = self.dataSource
    content = reference["content"]
    try:
      if (reference["type"] == "dynamic"):
        if ("referenceType" in content and content["referenceType"] == "state"):
          reference = "self.state." + content["id"] + "";
        elif ("referenceType" in content and content["referenceType"] == "prop"):
          reference = "self.props." + content["id"] + "";
        elif ("referenceType" in content and content["referenceType"] == "local"):
          reference = "" + content["id"] + "";
      elif (value["dataSource"] == "static"):
        reference = json.dumps(content)
    except:
      reference = self.dataSource
    react = reference + ".map((" + self.iteratorName
    if  self.useIndex :
        react += ", index"
    react += ") => { try {return React.cloneElement("
    react += self.node.buildReact( nativeRef = str("index") + "+" )
    react += ")} catch { } })"
    return react

  def __json__(self):
    return {
      "type": self.type,
      "content" : { 
        "node" : self.node.__json__(),
        "dataSource" : self.dataSource, 
        "meta" :  {
            "iteratorName" : self.iteratorName,
            "useIndex": self.useIndex
        },
      }
    }
    
class TeleportDynamic(TeleportNode):
  def __init__(self, *args, **kwargs):
    TeleportNode.__init__(self)
    self.type = "dynamic"      
    self.content = kwargs.get("content", {})

  def __json__(self):
    return {
      "type": self.type,
      "content" : self.content,
    }    


class TeleportStatic(TeleportNode):
  def __init__(self, *args, **kwargs):
    TeleportNode.__init__(self)
    self.type = "static"      
    self.content = kwargs.get("content", "")

  def __json__(self):
    return {
      "type": self.type,
      "content" : self.content,
    }    

        
class TeleportComponent():
  def __init__(self, name_component, node, *args, **kwargs):
      self.name_component = name_component;
      self.propDefinitions = {}
      self.stateDefinitions = {}
      self.node = node
      
  def __json__(self):
      return {
        "name":self.name_component,
        "propDefinitions" : self.propDefinitions,
        "stateDefinitions" : self.stateDefinitions,
        "node" : self.node.__json__()
      }
  
  def __str__(self):
      return json.dumps(self.__json__())

  def addNode(self, child):
    if (isinstance(child, TeleportNode) ):
      self.node.addContent(child)
    else:
      raise AttributeError("children have to be TeleportNode types")

  def addStateVariable(self, state, definition={type:"string", "defaultValue":""}):
    if isinstance(definition, dict):
      if ("type" in definition and "defaultValue" in definition):
        self.stateDefinitions[state] =  {"type": definition["type"], "defaultValue": definition["defaultValue"] }
      else:
        raise AttributeError("type and/or defaultValue are missing on the definition")
        
    else:
      raise AttributeError("definition should be a dict")

  def addPropVariable(self, state, definition={type:"string", "defaultValue":""}):
    if isinstance(definition, dict):
      if ("type" in definition and definition["type"] == "func"):
        if "defaultValue" not in definition:
            definition["defaultValue"] = "() => {}"
        self.propDefinitions[state] =  { "type": definition["type"], "defaultValue": definition["defaultValue"] }
      elif ("type" in definition and "defaultValue" in definition):
        self.propDefinitions[state] =  {"type": definition["type"], "defaultValue": definition["defaultValue"] }
      else:
        raise AttributeError("type and/or defaultValue are missing on the definition")
        
    else:
      raise AttributeError("definition should be a dict")

  
  def buildReact(self, componentName):   
    react = ""
    react += "class " + componentName + " extends React.Component {\n"
    react += "constructor(props) {\n"
    react += "super(props);\n"
    react += "let self=this;\n"
    react += "this.state = {\n"
    for k,s in self.stateDefinitions.items():
      v = s['defaultValue']
      if isinstance(v,dict) and "type" in v and v["type"] == "dynamic":
        if ("content" in v):
          content = v["content"]
          if ("referenceType" in content and content["referenceType"] == "state"):
            raise Exception("state circular references")
          elif ("referenceType" in content and content["referenceType"] == "prop"):
            v = "self.props." + content["id"] + "";
          elif ("referenceType" in content and content["referenceType"] == "local"):
            v = "" + content["id"] + "";
      elif "type" in s:         
        if (s["type"] == "object"):
          v = str(json.dumps(v))    
        elif (s["type"] == "string"):
          v = str(json.dumps(str(v))) 
        elif (s["type"] == "boolean"):
          v = str(json.dumps(bool(v)))    
        elif (s["type"] == "number"):
          v = str(float(v))   
        elif (s["type"] == "func"):
          v = str(v)    
        elif (s["type"] == "array"):
          v = str(json.dumps(list(v)))    
        elif (s["type"] == "router"):
          v = None   
        else:
          v = str(json.dumps(v)) 
      else:
          v = str(json.dumps(v)) 
      react += "'" + str(k) + "' : " + v + ", \n"
    react += "};\n"
    react += "}; \n"
    react += "render(){\n"
    react += "let self=this;\n"
    react += "return " + self.node.buildReact() + ";\n"
    react += "}\n"
    react += "}\n"
    react += componentName + ".defaultProps = {\n"
    for k,s in self.propDefinitions.items():
      if ("type" in s and s["type"] == "func"):
          if ("defaultValue" in s):
              react += "'" + str(k) + "' : " + (s['defaultValue']) + ", \n"
          else:
              react += "'" + str(k) + "' : ()=>{}, \n"
      else:
          if ("defaultValue" in s):
              react += "'" + str(k) + "' : " + json.dumps(s['defaultValue']) + ",\n"
    react += "}\n"
    return react

class TeleportProject():
  def __init__(self, name, *args, **kwargs):
      self.project_name = name
      self.globals = TeleportGlobals();
      self.root = TeleportComponent("MainComponent", TeleportElement(TeleportContent(elementType="container")));
      self.components = {};
      self.ref = uuid.uuid4()

  def addComponent(self, name, comp, *args, **kwargs):
    if name not in self.components:
      self.components[name] = comp;

  def __json__(self):
      return {
          "$schema": "https://docs.teleporthq.io/uidl-schema/v1/project.json",
          "name": self.project_name,
          "globals" : self.globals.__json__(),
          "root" : self.root.__json__(),
          "components" : {k:v.__json__() for k,v in self.components.items()}
      }
  
  def __str__(self):
      return json.dumps(self.__json__())
      
  def validate (self):
    return True;
    response = requests.get("https://docs.teleporthq.io/uidl-schema/v1/project.json")    
    if (response.text != ""):      
      schema = response.json()
      schema = json.dumps(schema)
      #v = jsonschema.Draft6Validator(response.text).validate(self.__json__())
      v = jsonschema.Draft6Validator(schema, (), jsonschema.RefResolver("https://docs.teleporthq.io/uidl-schema/v1/", ""))
      v = v.validate(self.__json__())
      return v;

  def buildReact(self, filename="tempreact.html"):
    
    react = ""
    react += "<!DOCTYPE html>\n"
    react += "<html style='height:100%'>\n"
    react += "<head>\n"
    react += "<meta charset='UTF-8'/>\n"
    react += "<meta name='viewport' content='initial-scale=1, maximum-scale=1, user-scalable=no, width=device-width'/>\n"
    react += "<title>" + self.project_name + "</title>\n"
    react += "<script src='https://cdn.plot.ly/plotly-latest.min.js'></script>\n"    
    react += "<script src='https://cdnjs.cloudflare.com/ajax/libs/require.js/2.3.6/require.min.js'></script>\n"
    react += "<link rel='stylesheet' href='https://fonts.googleapis.com/icon?family=Material+Icons'/>\n"
    react += "</head>\n"
    react += "  <body style='padding:0;margin:0;height:100%'>\n"
    react += "    <div id='root' style='height:100%'></div>\n"
    react += "<script type='text/javascript'>\n"
    react += "requirejs.config({\n"
    react += "    paths: {\n"
    react += "        'react': 'https://unpkg.com/react@16.8.6/umd/react.development',\n"
    react += "        'react-dom': 'https://unpkg.com/react-dom@16.8.6/umd/react-dom.development',\n"
    react += "        'material-ui': 'https://unpkg.com/@material-ui/core@latest/umd/material-ui.development',\n"
    react += "        'plotlycomponent': 'https://unpkg.com/react-plotly.js@2.3/dist/create-plotly-component',\n"
    react += "        'plotly': 'https://cdn.plot.ly/plotly-latest.min',\n"
    react += "        'math': 'https://cdnjs.cloudflare.com/ajax/libs/mathjs/6.6.1/math.min',\n"
    react += "        'axios': 'https://unpkg.com/axios/dist/axios.min',\n"
    react += "        'localforage' : 'https://www.unpkg.com/localforage@1.7.3/dist/localforage.min',\n"    
    react += "        'number-format': 'https://unpkg.com/react-number-format@4.3.1/dist/react-number-format',\n"   
    react += "        'prop-types': 'https://unpkg.com/prop-types@15.6/prop-types.min',\n"
    react += "    }\n"
    react += "});\n"
    react += "requirejs(['react', 'react-dom'], function(React, ReactDOM) {\n"
    react += "  window.React = React\n"
    react += "  let _react = React\n"
    react += "  requirejs(['material-ui', 'axios', 'localforage', 'prop-types'], function(Material, Axios, LocalForage, PropTypes) {\n"    
    react += "    _react.PropTypes = PropTypes\n"
    react += "    requirejs(['plotlycomponent', 'plotly', 'math', 'number-format'], function(PlotlyComponent, Plotly, math, Format) {\n"
    react += "      window.React = React\n"
    react += "      const Plot = PlotlyComponent.default(Plotly);\n";
    react += self.globals.buildReact();
    react += self.root.buildReact(self.root.name_component)
    for k, v in self.components.items():
      react += v.buildReact(k)
    react += "      ReactDOM.render(\n"
    react += "          React.createElement(" + self.root.name_component + ", {key:'" + str(self.ref) + "'}),\n"
    react += "          document.getElementById('root')\n"
    react += "      );\n"
    react += "    });    \n"
    react += "  });    \n"
    react += "})    \n"
    react += "</script>\n"
    react += "  </body>\n"
    react += "</html>\n"
    f = open(filename, "w")
    f.write(react)
    f.close()
    return react

  def displayWidget(self, *args, **kwargs):
    filename = "__TMPReactBuld.dat"
    self.buildReact(filename)
    file1 = open(filename, 'r') 
    lines = file1.readlines() 
    component = ""
    append = False
    for line in lines: 
        if line.startswith("<script type='text/javascript'>"):
            append = True
            continue;
        if append:
            if line.startswith("</script>"):
                append = False
            else :
                component +=  line

    display(HTML("<link rel='stylesheet' href='https://fonts.googleapis.com/icon?family=Material+Icons'/>"))
    display(HTML("<style>div#root p {font-size:unset}</style>"))
    display(HTML("<style>div#root label {font-size:1.5rem}</style>"))
    display(HTML("<style>div#root div {font-size:unset}</style>"))
    display(HTML("<style>div#root svg {font-size:x-large}</style>"))
    display(HTML("<style>div#root h6 {margin-top:0px}</style>"))
    display(HTML("<style>div#root img {margin-top:0px}</style>"))
    display(HTML("<div id='root' style='height:" + str(kwargs.get("height","900px")) + ";width:" + str(kwargs.get("width","100%")) + ";padding:0px;position:relative'></div>"))
    display(Javascript(component))
  
        
class TeleportContent():
  def __init__(self, *args, **kwargs):
    self.elementType = kwargs.get("elementType", None)
    self.attrs = {}
    self.events = {}
    self.style = {}
    self.children = []
    self.ref = uuid.uuid4()
    self.name =  kwargs.get("name", None)
    
  def __json__(self):
    tjson = {}
    if self.name != None:
      tjson["name"] = self.name
    if self.elementType != None:
      tjson["elementType"] = self.elementType
    if len(self.style) > 0:
      tjson["style"] = self.style
    if len(self.attrs) > 0:
      tjson["attrs"] = self.attrs # False -> "false"
    if len(self.events) > 0:
      tjson["events"] = self.events
    if len(self.children) > 0:
      tjson["children"] = [component.__json__() for component in self.children]
    return tjson
  
  def __str__(self):
      return json.dumps(self.__json__())             

  def buildElementType(self):   
    elementType = self.elementType
    if elementType == "container":
      elementType = "'div'"
    elif elementType.islower():
      elementType = "'"+elementType+"'"
    return elementType
  
  def parseFunctionsList(list):
    v = ""
    for func in list:   
      if "type" in func and func["type"] == "stateChange":
        if (isinstance(func["newState"], str) and func["newState"] == "$toggle"):
          v += "self.setState({'" + str(func["modifies"]) + "': !self.state." + str(func["modifies"]) + "}); "
        elif (isinstance(func["newState"], str) and func["newState"].startswith("$")):
          v += "self.setState({'" + str(func["modifies"]) + "':" + func["newState"].replace("$","") + "}); "
        else:
          v += "self.setState({'" + str(func["modifies"]) + "':" + json.dumps(func["newState"]) + "}); "
      elif "type" in func and func["type"] == "logging":
        v += "console.log('" + str(func["modifies"]) + "', " + str(json.dumps(func["newState"])) + "); "
      elif "type" in func and func["type"] == "propCall":
        v += str(func["calls"]) + "(" + ", ".join(func["args"]) + ");"
      elif "type" in func and func["type"] == "propCall2":
        v += "self.props." + str(func["calls"]) + "(" + ", ".join(func["args"]) + ");"
    return v

    
  def buildReact(self, *args , **kwargs):   
    react = ""
    elementType = self.buildElementType()
    react += "React.createElement("+elementType+", {key:" + kwargs.get("nativeRef","") + "'" + str(self.ref) + "'"
    sep = " ,"
    for attr, value in self.attrs.items():
      v = value
      if isinstance(value,dict):
        if "type" in value and "content" in value:
          content = value["content"]
          if (value["type"] == "dynamic"):
            if ("referenceType" in content and content["referenceType"] == "state"):
              v = "self.state." + content["id"] + "";
            elif ("referenceType" in content and content["referenceType"] == "prop"):
              v = "self.props." + content["id"] + "";
            elif ("referenceType" in content and content["referenceType"] == "local"):
              v = "" + content["id"] + "";
      else: 
        if isinstance(v, str) and v.startswith("$"):
            v = v.replace("$", "")
        else:
            v = str(json.dumps(v))
      react += sep + "'"+ attr + "': " + v + ""

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
      "load": "onLoad"
    };
    for ev, list in self.events.items():
      event_rename = ev
      if ev in valid_events:
        event_rename = valid_events[ev]
      v = "function(e){"
      v += "  " + TeleportContent.parseFunctionsList(list) + "\n"
      v += "}"
      if v != "function(){}": 
        react += sep + "'"+ event_rename + "': " + v + ""
    if len(self.style) > 0:
      react += sep + "'style': " + json.dumps(self.style) + ""
    react += "}"

    if len(self.children) > 0:
      if len(self.children) == 1:
        react += ",\n"
        for child in self.children:
          react += child.buildReact(nativeRef=kwargs.get("nativeRef",""))
        react += ")\n"
      else:
        react += ",[\n"
        sep = ""
        for child in self.children:
          react += sep + child.buildReact(nativeRef=kwargs.get("nativeRef",""))
          sep = " ,"
        react += "])\n"
    else:
      react += ")\n"
    
    return react

class InstanceTracker(object):
    __instances__ = weakref.WeakValueDictionary()
    def __init__(self, *args, **kwargs):
        self.__instances__[id(self)]=self
    @classmethod
    def find_instance(cls, obj_id):
        return cls.__instances__.get(obj_id, None)

class JupyterCache(InstanceTracker):
    def __init__(self):
        InstanceTracker.__init__(self)
        self.ref = id(self);   
        self.cache = {};
        
    def _initStorage(self, options={}):
        return True;
        
    def _support(self, options={}):
        return True;
    
    def clear(self, callback=None):
        self.cache = {};
        return True;
    
    def getItem(self, key, callback=None):
        if callback is not None:
            callback();    
        if key in self.cache:
            return self.cache[key];
        else:
            if os.path.isfile(key ):
                with open(key,'rt' ) as f:
                    xml = f.read()
                    self.cache[key] = xml
                    return self.cache[key];
        return None;
            
    def iterate(self, iteratorCallback={}, successCallback={}):
        raise "Not supported";
        return False;
            
    def key(self, n, callback=None):
        if callback is not None:
            callback();        
        if self.length() <= n: 
            return self.cache.keys()[n]
        return None;
    
    def keys(self, callback=None):
        if callback is not None:
            callback();
        return self.cache.keys();
            
    def length(self, callback=None):
        if callback is not None:
            callback();  
        return len(self.cache.keys());
            
    def removeItem(self, key, callback=None):
        if callback is not None:
            callback();    
        if key in self.cache:
            del self.cache[key];
            os.remove(key)
        return True;
            
    def setItem(self, key, value, callback=None):
        if callback is not None:
            callback();
        with open(key,'wt' ) as f:
            f.write(value)        
        self.cache[key]=value;
        return True;

class NanohubUtils(): 
    
  def jupyterCache(tp, cache, *args, **kwargs):
    method_name = kwargs.get("method_name", "JUPYTERSTORAGE")
    driver_name = kwargs.get("driver_name", "jupyterStorage")
    
    eol = "\n";    
    js = ""    
    js += "function " + method_name + "(){" + eol;
    js += "  function exec_j (command, p){" + eol;
    js += "    var command_j = 'from uidl.material import JupyterCache;'" + eol;
    js += "    command_j     += 'import json;'" + eol;
    js += "    command_j     += 'tmp = JupyterCache.find_instance("+ str(cache.ref) + ");'" + eol;
    js += "    command_j     += 'print(json.dumps(tmp.' + command + '));'" + eol;
    js += "    var kernel = IPython.notebook.kernel;"+ eol;
    #js += "    console.log(command_j);"+ eol;
    js += "    if(p!=undefined){"+ eol;
    js += "      let wp = p;"+ eol;
    js += "      var t = kernel.execute(command_j, {"+ eol;
    js += "        iopub: {"+ eol;
    js += "          output: (m)=>{ "+ eol;
    js += "            console.log(command, m);"+ eol;
    js += "            if(m.content != undefined){"+ eol;
    js += "              if(m.content.text != undefined){"+ eol;
    js += "                wp.resolve(JSON.parse(m.content.text)); "+ eol;
    js += "              } else if(m.content.traceback != undefined){"+ eol;
    js += "                wp.reject(); "+ eol;
    js += "              } else {"+ eol;
    js += "                wp.resolve(); "+ eol;
    js += "              }"+ eol;
    js += "            } else {"+ eol;
    js += "              wp.resolve(); "+ eol;
    js += "            }"+ eol;
    js += "          }"+ eol;
    js += "        }"+ eol;
    js += "      });"+ eol;
    js += "    } else {" + eol; 
    js += "      var t = kernel.execute(command_j, {"+ eol;
    js += "        iopub: {"+ eol;
    js += "          'output': (m)=>{ "+ eol;
    #js += "            console.log(command, m);"+ eol;
    js += "            if(m.content != undefined){"+ eol;
    js += "              if(m.content.text != undefined){"+ eol;
    js += "                return (JSON.parse(m.content.text));"+ eol;
    js += "              } else if( m.content.traceback != undefined){"+ eol;
    js += "                wp.reject(); "+ eol;  
    js += "              } else {"+ eol;
    js += "                wp.resolve(); "+ eol;
    js += "              }"+ eol;    
    js += "            }"+ eol;
    js += "          }"+ eol;
    js += "        }"+ eol;
    js += "      });"+ eol;
    js += "    }" + eol; 
    js += "  }" + eol;     
    js += "  function defer() {" + eol;
    js += "    var res, rej;" + eol;
    js += "    var promise = new Promise((resolve, reject) => {" + eol;
    js += "      res = resolve;" + eol;
    js += "      rej = reject;" + eol;
    js += "    });" + eol;
    js += "    promise.resolve = res;" + eol;
    js += "    promise.reject = rej;" + eol;
    js += "    return promise;" + eol;
    js += "  }" + eol;
    js += "  return {" + eol;
    js += "    _driver: '"+driver_name+"'," + eol;
    js += "    _initStorage: function(options) {" + eol;
    js += "      var p = defer();"+ eol;
    js += "      exec_j('_initStorage()', p);" + eol;
    js += "      return p;"+ eol;
    js += "    }," + eol;
    js += "    _support: async function(options) {" + eol;
    js += "      if (typeof IPython === 'undefined'){"+ eol;
    js += "        return false; "+ eol;
    js += "      } else { "+ eol;
    js += "        var p = defer();"+ eol;
    js += "        exec_j('_support()', p);" + eol;
    js += "        return p;"+ eol;
    js += "      }"+ eol;
    js += "    }," + eol;
    js += "    clear: async function(callback) {" + eol;
    js += "      var p = defer();"+ eol;
    js += "      exec_j('clear()', p);" + eol;
    js += "      return p;"+ eol;
    js += "    }," + eol;
    js += "    getItem: async function(key, callback) {" + eol;
    js += "      var p = defer();"+ eol;
    js += "      exec_j('getItem(\\'\\'\\''+key+'\\'\\'\\')', p);" + eol;
    js += "      return p;"+ eol;
    js += "    }," + eol;
    js += "    iterate: async function(iteratorCallback, successCallback) {" + eol;
    js += "      var p = defer();"+ eol;
    js += "      exec_j('iterate(None,None)', p);" + eol;
    js += "      return p;"+ eol;
    js += "    },    " + eol;
    js += "    key: async function(n, callback) {" + eol;
    js += "      var p = defer();"+ eol;
    js += "      exec_j('key(\\'\\'\\''+n+'\\'\\'\\')', p);" + eol;
    js += "      return p;"+ eol;
    js += "    }," + eol;
    js += "    keys: async function(callback) {" + eol;
    js += "      var p = defer();"+ eol;
    js += "      exec_j('keys()', p);" + eol;
    js += "      return p;"+ eol;
    js += "    }," + eol;
    js += "    length: async function(callback) {" + eol;
    js += "      var p = defer();"+ eol;
    js += "      exec_j('length()', p);" + eol;
    js += "      return p;"+ eol;
    js += "    }," + eol;
    js += "    removeItem: async function(key, callback) {" + eol;
    js += "      var p = defer();"+ eol;
    js += "      exec_j('removeItem(\\'\\'\\''+key+'\\'\\'\\')', p);" + eol;
    js += "      return p;"+ eol;
    js += "    }," + eol;
    js += "    setItem: async function(key, value, callback) {" + eol;
    js += "      var p = defer();"+ eol;
    js += "      exec_j('setItem(\\'\\'\\''+key+'\\'\\'\\', \\'\\'\\''+value+'\\'\\'\\')', p);" + eol;
    js += "      return p;"+ eol;
    js += "    }" + eol;
    js += "  }" + eol;
    js += "}" + eol;

        
    tp.globals.addAsset(method_name, {
      "type": "script",
      "content": js
    })    

    js = ""
    js += " LocalForage."+method_name+" = '"+driver_name+"'; " + eol
    js += " LocalForage.defineDriver("+method_name+"()).then(()=>{" + eol
    js += "   LocalForage.setDriver(['"+driver_name+"']);" + eol
    js += " }).then(function() {" + eol
    js += "   LocalForage.ready();" + eol
    js += " }).then(function() {" + eol
    js += " });" + eol
    
    tp.globals.addAsset("_" + method_name, {
      "type": "script",
      "content": js
    })

    return [
      {
        "type": "propCall",
        "calls": method_name,
        "args": []
      }
    ]

  def storageFactory(tp, *args, **kwargs):
    method_name = kwargs.get("method_name", "storageFactory")
    storage_name = kwargs.get("storage_name", "window.sessionStorage")
    store_name = kwargs.get("store_name", "sessionStore")
    if (kwargs.get("jupyter_cache", None) is not None):
        NanohubUtils.jupyterCache(tp, kwargs.get("jupyter_cache", None))
    eol = "\n";    
    js = ""
    js += "function cacheFactory(name, type){" + eol;
    js += "  if (type=='INDEXEDDB' && LocalForage.supports(LocalForage.INDEXEDDB)){" + eol
    js += "    return LocalForage.createInstance({'name': name, 'driver': [LocalForage.INDEXEDDB]})" + eol
    js += "  } else if (type=='LOCALSTORAGE' && LocalForage.supports(LocalForage.LOCALSTORAGE)){" + eol
    js += "    return LocalForage.createInstance({'name': name, 'driver': [LocalForage.LOCALSTORAGE]})" + eol
    if (kwargs.get("jupyter_cache", None) is not None):
      js += "  } else if (type=='JUPYTERSTORAGE' && LocalForage.supports(LocalForage.JUPYTERSTORAGE)){" + eol
      js += "    return LocalForage.createInstance({'name': name, 'driver': [LocalForage.JUPYTERSTORAGE]})" + eol
    js += "  }" + eol;
    js += "  return undefined;" + eol;
    js += "}" + eol;
    js += "function " + method_name + " (getStorage){" + eol;
    js += "  /* ISC License (ISC). Copyright 2017 Michal Zalecki */" + eol;
    js += "  let inMemoryStorage = {};" + eol;
    js += "  function isSupported() {" + eol;
    js += "    try {" + eol;
    js += "      const testKey = '__some_random_key_you_are_not_going_to_use__';" + eol;
    js += "      var test = getStorage().setItem(testKey, testKey);" + eol;
    js += "      if (test)" + eol;
    js += "        getStorage();" + eol;
    js += "      getStorage().removeItem(testKey);" + eol;
    js += "      return true;" + eol;
    js += "    } catch (e) {" + eol;
    js += "      console.log('Accessing InMemory');" + eol;
    js += "      return false;" + eol;
    js += "    }" + eol;
    js += "  }" + eol;
    js += "  function clear(){" + eol;
    js += "    if (isSupported()) {" + eol;
    js += "      getStorage().clear();" + eol;
    js += "    } else {" + eol;
    js += "      inMemoryStorage = {};" + eol;
    js += "    }" + eol;
    js += "  }" + eol;
    js += "  function getItem(name){" + eol;
    js += "    if (isSupported()) {" + eol;
    js += "      return getStorage().getItem(name);" + eol;
    js += "    }" + eol;
    js += "    if (inMemoryStorage.hasOwnProperty(name)) {" + eol;
    js += "      return inMemoryStorage[name];" + eol;
    js += "    }" + eol;
    js += "    return null;" + eol;
    js += "  }" + eol;

    js += "  function key(index){" + eol;
    js += "    if (isSupported()) {" + eol;
    js += "      return getStorage().key(index);" + eol;
    js += "    } else {" + eol;
    js += "      return Object.keys(inMemoryStorage)[index] || null;" + eol;
    js += "    }" + eol;
    js += "  }" + eol;

    js += "  function removeItem(name){" + eol;
    js += "    if (isSupported()) {" + eol;
    js += "      getStorage().removeItem(name);" + eol;
    js += "    } else {" + eol;
    js += "      delete inMemoryStorage[name];" + eol;
    js += "    }" + eol;
    js += "  }" + eol;

    js += "  function setItem(name, value){" + eol;
    js += "    if (isSupported()) {" + eol;
    js += "      getStorage().setItem(name, value);" + eol;
    js += "    } else {" + eol;
    js += "      inMemoryStorage[name] = String(value);" + eol;
    js += "    }" + eol;
    js += "  }" + eol;

    js += "  function length(){" + eol;
    js += "    if (isSupported()) {" + eol;
    js += "      return getStorage().length;" + eol;
    js += "    } else {" + eol;
    js += "      return Object.keys(inMemoryStorage).length;" + eol;
    js += "    }" + eol;
    js += "  }" + eol;

    js += "  return {" + eol;
    js += "    getItem," + eol;
    js += "    setItem," + eol;
    js += "    removeItem," + eol;
    js += "    clear," + eol;
    js += "    key," + eol;
    js += "    get length() {" + eol;
    js += "      return length();" + eol;
    js += "    }," + eol;
    js += "  };" + eol;
    js += "};" + eol;

    tp.globals.addAsset(method_name, {
      "type": "script",
      "content": js
    })    

    tp.globals.addAsset(store_name, {
      "type": "script",
      "content": "const " + store_name + " = " + method_name + "(() => " + storage_name + ");" + eol
    })

    return [
      {
        "type": "propCall",
        "calls": method_name,
        "args": []
      }
    ]
