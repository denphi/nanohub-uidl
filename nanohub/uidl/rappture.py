from .teleport import *
from .material import *
from numpy import linspace as nplinspace
from numpy import pi as nppi
from numpy import sin as npsin
from numpy import cos as npcos
from numpy import outer as npouter
from numpy import ones as npones
from numpy import array as nparray
from numpy import meshgrid as npmeshgrid
from numpy import fromstring as npfromstring
from numpy import concatenate as npconcatenate
from numpy import mgrid as npmgrid
from numpy import random as nprandom
from numpy import linalg as nplinalg
from numpy import cross as npcross
from numpy import ceil as npceil
from numpy import around as nparound

class RapptureBuilder():
    
  def Loader(Component, *args, **kwargs):
    Component.addStateVariable(kwargs.get("loader_status", "loader_status"), {"type":"string", "defaultValue": ""})
    Component.addStateVariable(kwargs.get("loader_open", "loader_open"), {"type":"boolean", "defaultValue": kwargs.get("is_open", True)})  
    
    Loader = TeleportElement(MaterialContent(elementType="Dialog"))
    Loader.content.attrs["open"] = {
      "type": "dynamic",
      "content": {
        "referenceType": "state",
        "id": kwargs.get("open", "loader_open")
      }    
    }
    Loader.content.attrs["disableBackdropClick"] = True
    Loader.content.attrs["disableEscapeKeyDown"] = True
    Loader.content.attrs["fullWidth"] = True
    Loader.content.attrs["maxWidth"] = 'xs'
    loadercnt = TeleportElement(MaterialContent(elementType="DialogContent"))
    loadercnt.content.style = { "textAlign": "center", "overflow" : "hidden"}

    LinearProgress = TeleportElement(MaterialContent(elementType="LinearProgress"))
    LinearProgress.content.attrs["color"] = 'secondary'

    #loadercir = TeleportElement(MaterialContent(elementType="CircularProgress"))
    #loadercir.content.style = {"width": "100px", "height": "100px", "overflow": "none"}

    loadertext = TeleportElement(MaterialContent(elementType="DialogTitle"))
    loadertext.addContent(TeleportDynamic(
        content = {
            "referenceType": "state",
            "id": kwargs.get("open", "loader_status")
        }
    ))
    loadertext.content.style = {"textAlign": "center"}

    #loadercnt.addContent(loadercir)
    loadercnt.addContent(LinearProgress)
    Loader.addContent(loadercnt)
    Loader.addContent(loadertext)


    

    return Loader

  def Error(Component, *args, **kwargs):
    Component.addStateVariable(kwargs.get("error_status", "error_status"), {"type":"string", "defaultValue": ""})
    Component.addStateVariable(kwargs.get("error_open", "error_open"), {"type":"boolean", "defaultValue": False})  
    Error = TeleportElement(MaterialContent(elementType="Dialog"))
    Error.content.attrs["open"] = {
      "type": "dynamic",
      "content": {
        "referenceType": "state",
        "id": kwargs.get("error_open", "error_open")
      }    
    }
    Error.content.attrs["fullWidth"] = True
    Error.content.attrs["maxWidth"] = 'xs'
    DialogContent = TeleportElement(MaterialContent(elementType="DialogContent"))
    DialogContent.content.style = { "textAlign": "center", "overflow" : "hidden"}
    


    Typography = TeleportElement(MaterialContent(elementType="Typography"))
    Typography.content.attrs["variant"] = "h6"
    TypographyText = TeleportStatic(content=kwargs.get("title", "Error Message"))
    Typography.addContent(TypographyText)    

    Icon0 = TeleportElement(MaterialContent(elementType="Icon"))
    Icon0.content.style={'position':'absolute', 'top' : '10px', 'left' : '10px'}
    IconText0 = TeleportStatic(content="error")
    Icon0.addContent(IconText0)   

    
    IconButton = TeleportElement(MaterialContent(elementType="IconButton"))
    IconButton.content.style={'position':'absolute', 'top' : '10px', 'right' : '10px'}
    
    Icon = TeleportElement(MaterialContent(elementType="Icon"))
    IconText = TeleportStatic(content="close")
    Icon.addContent(IconText)   
    IconButton.addContent(Icon)
    IconButton.content.events["click"] = [{ 
        "type": "stateChange", 
        "modifies": kwargs.get("error_open", "error_open"),
        "newState": False
    }]

    
    DialogTitle = TeleportElement(MaterialContent(elementType="DialogTitle"))
    DialogTitle.content.attrs["disableTypography"] = True
    DialogTitle.content.style={'textAlign':'center', 'backgroundColor' : '#d95c5c'}
    DialogTitle.addContent(IconButton)
    DialogTitle.addContent(Typography)
    DialogTitle.addContent(Icon0)

    DialogContent.addContent(TeleportDynamic(
        content = {
            "referenceType": "state",
            "id": kwargs.get("error_status", "error_status")
        }
    ))
    DialogContent.content.style = {"textAlign": "center"}


    
    Error.addContent(DialogTitle)
    Error.addContent(DialogContent)

    return Error

  def onSimulate(tp, Component, *args, **kwargs):
    store_name="sessionStore";
    NanohubUtils.storageFactory(tp, store_name=store_name, storage_name="window.sessionStorage") 
    local_storage = "LocalStore"
    NanohubUtils.storageFactory(tp, store_name=local_storage, storage_name="NativeStorage")
    use_cache = kwargs.get("use_cache", True) #TODO False by default 
    if (use_cache):
      cache_store = kwargs.get("cache_store", "CacheStore");
      if kwargs.get('jupyter_cache', None) is not None:
        cache_storage = kwargs.get("cache_storage", "cacheFactory('"+cache_store+"', 'JUPYTERSTORAGE')") 
        NanohubUtils.storageFactory(tp, method_name='storageJupyterFactory', jupyter_cache=kwargs.get('jupyter_cache', None), store_name=cache_store, storage_name=cache_storage)
      else :
        cache_storage = kwargs.get("cache_storage", "cacheFactory('"+cache_store+"', 'INDEXEDDB')")
        NanohubUtils.storageFactory(tp, store_name=cache_store, storage_name=cache_storage)        
    eol = "\n"
    toolname = kwargs.get("toolname", "")
    url = kwargs.get("url", "")


    js = "async (self, ostate)=>{" + eol
    js += "  var state = self.state;" + eol
    js += "  " + local_storage + ".removeItem('output_xml');" + eol
    
    if (use_cache):
      js += "  self.props.onStatusChange({'target':{ 'value' : 'Checking Cache' } } );" + eol
      js += "  var str_key = JSON.stringify(state);" + eol
      js += "  var buffer_key = new TextEncoder('utf-8').encode(str_key);" + eol
      js += "  var hashBuffer = await window.crypto.subtle.digest('SHA-256', buffer_key);" + eol
      js += "  var hashArray = Array.from(new Uint8Array(hashBuffer));" + eol
      js += "  var hash_key = hashArray.map(b => b.toString(16).padStart(2, '0')).join('');" + eol
      #js += "  console.log(hash_key)" + eol
      js += "  var hash_q = await " + cache_store + ".getItem(hash_key)" + eol
      #js += "  console.log(hash_q)" + eol
      js += "  if( hash_q == null ){" + eol    
    js += "  self.props.onStatusChange({'target':{ 'value' : 'Parsing Tool Schema' } } );" + eol
    js += "  var params = JSON.parse(" + store_name + ".getItem('nanohub_tool_schema'));" + eol
    js += "  var xmlDoc = JSON.parse(" + store_name + ".getItem('nanohub_tool_xml'));" + eol
    js += "  self.props.onStatusChange({'target':{ 'value' : 'Parsing XML' } });" + eol
    js += "  if (window.DOMParser){" + eol
    js += "    let parser = new DOMParser();" + eol
    js += "    xmlDoc = parser.parseFromString(xmlDoc, 'text/xml');" + eol
    js += "  } else {" + eol
    js += "    xmlDoc = new ActiveXObject('Microsoft.XMLDOM');" + eol
    js += "    xmlDoc.async = false;" + eol
    js += "    xmlDoc.loadXML(xmlDoc);" + eol
    js += "  }" + eol
    js += "  self.props.onStatusChange({'target':{ 'value' : 'Loading Default Structures' } } );" + eol
    js += "  var elems = xmlDoc.getElementsByTagName('*');" + eol
    js += "  var discardtags = ['phase', 'group', 'option'];" + eol
    js += "  for (var i=0;i<elems.length;i++){" + eol
    js += "    var elem = elems[i];" + eol
    js += "    if (elem.tagName == 'structure'){" + eol
    js += "      var edefault = elem.querySelectorAll('default');" + eol
    js += "      if (edefault.length > 0){" + eol
    js += "        var params = edefault[0].querySelectorAll('parameters');" + eol
    js += "        if (params.length > 0){" + eol
    js += "          var current = xmlDoc.createElement('current');" + eol
    js += "          current.appendChild(params[0].cloneNode(true));" + eol
    js += "          elem.appendChild(current);" + eol
    js += "        }" + eol
    js += "      }" + eol
    js += "    }" + eol
    js += "  }" + eol;
    js += "  self.props.onStatusChange({'target':{ 'value' : 'Loading Default Parameters' } } );" + eol
    js += "  var elems = xmlDoc.getElementsByTagName('*');" + eol
    js += "  for (var i=0;i<elems.length;i++){" + eol
    js += "    var elem = elems[i];" + eol
    js += "    if (elem.hasAttribute('id')){" + eol
    js += "      var id = elem.getAttribute('id');" + eol
    js += "      if ((discardtags.findIndex((e)=> e == elem.tagName))<0){" + eol
    js += "        var current = elem.querySelectorAll('current');" + eol
    js += "        if (current.length > 0){" + eol
    js += "          var units='';" + eol
    js += "          var units_node = elem.querySelectorAll('units');" + eol
    js += "          if (units_node.length > 0){" + eol
    js += "            units=units_node[0].textContent;" + eol
    js += "          }" + eol
    js += "          var default_node = elem.querySelectorAll('default');" + eol
    js += "          if (default_node.length > 0){" + eol
    js += "            var defaultv = default_node[0].textContent;" + eol
    js += "            var current = elem.querySelectorAll('current');" + eol
    js += "            if (current.length > 0){" + eol
    js += "              elem.removeChild(current[0]);" + eol;
    js += "            }" + eol
    js += "            current = xmlDoc.createElement('current');" + eol
    js += "            if (units != '' && !defaultv.includes(units)){" + eol
    js += "              current.textContent = defaultv+units;" + eol
    js += "            } else {" + eol
    js += "              current.textContent = defaultv;" + eol
    js += "            }" + eol
    js += "            elem.appendChild(current);" + eol    
    js += "          }" + eol
    js += "        }" + eol
    js += "      }" + eol
    js += "    }" + eol
    js += "  }" + eol
    js += "  self.props.onStatusChange({'target':{ 'value' : 'Setting Parameters' } } );" + eol
    js += "  for (const id in state) {" + eol;
    js += "    let value = String(state[id]);" + eol;
    js += "    var elems = xmlDoc.getElementsByTagName('*');" + eol
    js += "    for (var i=0;i<elems.length;i++){" + eol;
    js += "      var elem = elems[i];" + eol
    js += "      if (elem.hasAttribute('id')){" + eol
    js += "        if ((discardtags.findIndex((e)=> e == elem.tagName))<0){" + eol
    js += "          var id_xml = elem.getAttribute('id');" + eol
    js += "          if (id == id_xml || id == '_'+id_xml){" + eol
    js += "            var current = elem.querySelectorAll('current');" + eol
    js += "            if (current.length > 0){" + eol
    js += "              elem.removeChild(current[0]);" + eol
    js += "            }" + eol
    js += "            current = xmlDoc.createElement('current');" + eol
    js += "            var units='';" + eol
    js += "            var units_node = elem.querySelectorAll('units');" + eol
    js += "            if (units_node.length > 0){" + eol
    js += "              units=units_node[0].textContent;" + eol
    js += "            }" + eol
    js += "            if (units != '' && !value.includes(units)){" + eol
    js += "              current.textContent = String(value)+units;" + eol
    js += "            } else {" + eol
    js += "              current.textContent = String(value);" + eol
    js += "            } " + eol    
    js += "            elem.appendChild(current);" + eol    
    js += "          }" + eol
    js += "        }" + eol
    js += "      }" + eol
    js += "    }" + eol
    js += "  }" + eol
    js += "  self.props.onStatusChange({'target':{ 'value' : 'Building Rappture Invoke' } } );" + eol
    js += "  var driver_str  = '<?xml version=\"1.0\"?>\\n' + new XMLSerializer().serializeToString(xmlDoc.documentElement);" + eol
    js += "  var driver_json = {'app': '" + toolname + "', 'xml': driver_str}" + eol;
    js += "  var nanohub_token = " + store_name + ".getItem('nanohub_token');" + eol
    js += "  var header_token = {'Authorization': 'Bearer ' + nanohub_token, 'Content-Type': 'application/x-www-form-urlencoded'}" + eol;
    js += "  var url = '" + url + "/run';";
    js += "  var str = [];" + eol
    js += "  for(var p in driver_json){" + eol
    js += "    str.push(encodeURIComponent(p) + '=' + encodeURIComponent(driver_json[p]));" + eol
    js += "  }" + eol
    js += "  let data =  str.join('&');" + eol
    js += "  var options = { 'handleAs' : 'json' , 'headers' : header_token, 'method' : 'POST', 'data' : data };" + eol
    js += "  self.props.onStatusChange({'target':{ 'value' : 'Submitting Simulation' } } );" + eol
    
    js += "  Axios.request(url, options)" + eol
    js += "  .then(function(response){" + eol
    js += "    var data = response.data;" + eol
    js += "    if(data.code){" + eol    
    js += "      if(data.message){" + eol    
    js += "        self.props.onError( '(' + data.code + ') ' +data.message );" + eol
    js += "      } else {" + eol    
    js += "        self.props.onError( '(' + data.code + ') Error sending the simulation' );" + eol
    js += "      } " + eol    
    js += "    }else{" + eol    
    js += "      if(data.session){" + eol    
    js += "        setTimeout(function(){ self.props.onCheckSession(self, data.session, 10) }, 4000);" + eol
    js += "      } else {" + eol    
    js += "        self.props.onError( 'Error submiting the simulation, session not found' );" + eol
    js += "      }" + eol    
    js += "    }" + eol    
    js += "  }).catch(function(error){" + eol
    js += "    self.props.onError(String(error));" + eol      
    js += "  })"
    if (use_cache):    
      js += "  } else { " + eol
      js += "    self.props.onStatusChange({'target':{ 'value' : 'Loading from local Cache' } } );" + eol
      js += "    " + local_storage + ".setItem('output_xml', JSON.stringify(hash_q));" + eol
      js += "    self.props.onSuccess(self)" + eol        
      js += "  }" + eol
    js += "}"
    
    Component.addPropVariable("onSimulate", {"type":"func", 'defaultValue' :js})    
    
    js = "(self, session_id, reload)=>{" + eol
    js += "  if (session_id == ''){" + eol;
    js += "     self.props.onError('invalid Session ID');" + eol              
    js += "  }" + eol;
    js += "  var session_json = {'session_num': session_id};" + eol;
    js += "  var nanohub_token = " + store_name + ".getItem('nanohub_token');" + eol
    js += "  var header_token = {'Authorization': 'Bearer ' + nanohub_token, 'Content-Type': 'application/x-www-form-urlencoded'}" + eol;
    js += "  var url = '" + url + "/status';" + eol
    js += "  var str = [];" + eol
    js += "  for(var p in session_json){" + eol
    js += "    str.push(encodeURIComponent(p) + '=' + encodeURIComponent(session_json[p]));" + eol
    js += "  }" + eol
    js += "  let data =  str.join('&');" + eol
    js += "  var options = { 'handleAs' : 'json' , 'headers' : header_token, 'method' : 'POST', 'data' : data };" + eol  
    js += "  Axios.request(url, options)" + eol
    js += "  .then(function(response){" + eol
    js += "    var status = response.data;" + eol
    js += "    if (status['success']){" + eol
    js += "      if (status['status']){" + eol
    js += "        if (status['status'].length > 0 && status['status'][0] != ''){" + eol
    js += "          self.props.onStatusChange({'target':{ 'value' : status['status'][0] } } );" + eol
    js += "        } else {" + eol
    js += "          self.props.onStatusChange({'target':{ 'value' : 'Checking status of session ' + String(session_id) } } );" + eol
    js += "        }" + eol
    js += "        if(status['finished']){" + eol
    js += "          if(status['run_file'] != ''){" + eol
    js += "            self.props.onLoad(self);" + eol      
    js += "            self.props.onLoadResults(self, session_id, status['run_file']);" + eol
    js += "          } else {" + eol
    js += "            if (reload > 0){" + eol
    js += "              setTimeout(function(){self.props.onCheckSession(self, session_id, 0)},2000);" + eol
    js += "            }" + eol
    js += "          }" + eol
    js += "        } else {" + eol
    js += "          if (reload > 0){" + eol
    js += "            setTimeout(function(){self.props.onCheckSession(self, session_id, reload)},2000);" + eol
    js += "          }" + eol
    js += "        }" + eol
    js += "      }"
    js += "    } else if (status['code']){" + eol
    js += "      if (status['code'] == 404){" + eol
    js += "        setTimeout(function(){self.props.onCheckSession(self, session_id, reload-1)},8000);" + eol          
    js += "      }"
    js += "      else if (status['code'] != 200){" + eol
    js += "        self.props.onError(status['message']);" + eol
    js += "      }"
    js += "    }"
    js += "  }).catch(function(error){" + eol
    js += "    if (reload > 0 && String(error).includes('404')){" + eol    
    js += "      setTimeout(function(){self.props.onCheckSession(self, session_id, reload-1)},8000);" + eol
    js += "    } else {" + eol
    js += "      self.props.onError(String(error));" + eol
    js += "    }" + eol
    js += "  })" + eol
    js += "}" + eol

    Component.addPropVariable("onCheckSession", {"type":"func", 'defaultValue' :js})    

    js = "(self, session_id, run_file)=> {" + eol
    js += "  var results_json = {'session_num': session_id, 'run_file': run_file};" + eol;
    js += "  var nanohub_token = " + store_name + ".getItem('nanohub_token');" + eol
    js += "  var header_token = {'Authorization': 'Bearer ' + nanohub_token, 'Content-Type': 'application/x-www-form-urlencoded'}" + eol;
    js += "  self.props.onStatusChange({'target':{ 'value' : 'Loading results data' } } );" + eol
    js += "  var url = '" + url + "/output';" + eol
    js += "  var str = [];" + eol
    js += "  for(var p in results_json){" + eol
    js += "    str.push(encodeURIComponent(p) + '=' + encodeURIComponent(results_json[p]));" + eol
    js += "  }" + eol
    js += "  let data =  str.join('&');" + eol
    js += "  var options = { 'handleAs' : 'json' , 'headers' : header_token, 'method' : 'POST', 'data' : data };" + eol
    js += "  Axios.request(url, options)" + eol
    js += "  .then(async (response)=>{" + eol
    js += "    var data = response.data;" + eol    
    js += "    if(data.success){" + eol    
    js += "      var output = data.output;" + eol   
    js += "      self.props.onStatusChange({'target':{ 'value' : 'Loading' } } );" + eol
    if (use_cache):
      js += "      var str_key = JSON.stringify(self.state);" + eol
      js += "      var buffer_key = new TextEncoder('utf-8').encode(str_key);" + eol
      js += "      var hashBuffer = await window.crypto.subtle.digest('SHA-256', buffer_key);" + eol
      js += "      var hashArray = Array.from(new Uint8Array(hashBuffer));" + eol
      js += "      var hash_key = hashArray.map(b => b.toString(16).padStart(2, '0')).join('');" + eol
      js += "      var hash_q = await " + cache_store + ".setItem(hash_key, output, (e)=>{self.props.onError(e.toString())});" + eol    
    js += "      " + local_storage + ".setItem('output_xml', JSON.stringify(output));" + eol
    js += "      self.props.onSuccess(self)" + eol
    js += "    }" + eol    
    js += "  }).catch(function(error){" + eol
    js += "    self.props.onError(error);" + eol
    js += "  })" + eol
    js += "}" + eol
    Component.addPropVariable("onLoadResults", {"type":"func", 'defaultValue' :js})    

    callbacklist = []
    states_def = "{ 'target' : { 'value' : {"
    for k, state in Component.stateDefinitions.items():
        states_def+= "'" + k + "': self.state." + k + " ,"
    states_def += "} } }"
    callbacklist.append({
        "type": "propCall2",
        "calls": "onSimulate",
        "args": ['self', states_def]
    })
    
    return callbacklist 


  def getText(tp, component, *args, **kwargs):    
    eol = "\n";
    js = ""
    js += "( component, obj, fields ) => {" + eol
    js += "  var text = '';" + eol
    js += "  if(obj){" + eol
    js += "    var objf = obj;" + eol
    js += "    try{" + eol
    js += "      for (var i=0;i<fields.length;i++){" + eol
    js += "        var field = fields[i];" + eol
    js += "        objf = objf.querySelectorAll(field);" + eol
    js += "        if (objf.length <= 0){" + eol
    js += "          return '';" + eol
    js += "        } else {" + eol
    js += "          objf = objf[0];" + eol
    js += "        }" + eol
    js += "      }" + eol
    js += "      text = objf.innerHTML" + eol
    js += "    } catch(error) {" + eol
    js += "      text = '';" + eol
    js += "    }" + eol
    js += "  }" + eol
    js += "  return text;" + eol
    js += "}" + eol
    component.addPropVariable("getText", {"type":"func", "defaultValue": js})
    return {
      "type": "propCall2",
      "calls": "getText",
      "args": ['self', 'undefined', []]
    }  
    
  def getXY(tp, component, *args, **kwargs):  
    eol = "\n";
    js = ""
    js += "( component, field, container )=>{" + eol
    js += "  var list_v = Array()" + eol
    js += "  component = field.querySelectorAll(container);" + eol
    js += "  for (var i=0; i<component.length; i++){" + eol
    js += "    var obj = component[i].querySelectorAll('xy');" + eol
    js += "    if (obj.length>0){" + eol
    js += "      var xy = obj[0].innerHTML;" + eol
    js += "    }" + eol
    js += "    list_v.push(xy);" + eol
    js += "  }" + eol
    js += "  return list_v;" + eol
    js += "}" + eol 
    component.addPropVariable("getXY", {"type":"func", "defaultValue": js})
    return {
      "type": "propCall2",
      "calls": "getXY",
      "args": ['self','undefined','undefined']
    }  

  def buildXYPlotly(tp, component, *args, **kwargs):    
    eol = "\n";  
    RapptureBuilder.getText(tp, component)
    RapptureBuilder.getXY(tp, component)
    js = ""
    js += "(component, fields, labels) => {" + eol
    js += "  var traces = Array();" + eol
    js += "  var layout = {};" + eol
    js += "  var xrange = [undefined,undefined];" + eol
    js += "  var xrange = [undefined,undefined];" + eol
    js += "  var yrange = [undefined,undefined];" + eol
    js += "  var xunits = '';" + eol
    js += "  var yunits = '';" + eol    
    js += "  var xaxis = '';" + eol
    js += "  var yaxis = '';" + eol    
    js += "  var xscale = 'linear';" + eol
    js += "  var yscale = 'linear';" + eol    
    js += "  var title = '';" + eol
    js += "  for (var i=0;i<fields.length;i++){" + eol
    js += "    var field= fields[i];" + eol
    js += "    var rapp_component = component.props.getXY(component, field, 'component');" + eol
    js += "    var label = component.props.getText(component, field, ['about','label']);" + eol
    js += "    var style = component.props.getText(component,field, ['about','style']);" + eol
    js += "    var line = {'color' : 'blue'};" + eol
    js += "    if (style && style != ''){" + eol
    js += "      var options = style.trim().split('-');" + eol
    js += "      for (var j=0;j<options.length;j++){" + eol
    js += "        var option = options[j]" + eol
    js += "        var val = option.trim().split(/[\s]+/);" + eol
    js += "        if (val.length == 2 ){" + eol
    js += "          if (val[0]=='color')" + eol
    js += "            line['color'] = val[1];" + eol
    js += "          else if (val[0]=='linestyle')" + eol
    js += "            if (val[1]=='dashed')" + eol
    js += "              line['dash'] = 'dash';" + eol
    js += "            else if (val[1]=='dotted')" + eol
    js += "              line['dash'] = 'dot';" + eol
    js += "        }" + eol
    js += "      }" + eol
    js += "    }" + eol
    js += "    if (labels != undefined){" + eol
    js += "      label = label + " " + labels[i];" + eol
    js += "    }" + eol
    js += "    title = component.props.getText(component,field, ['about','group']);" + eol
    js += "    var xaxis = component.props.getText(component,field, ['xaxis','label']);" + eol
    js += "    var xunits = component.props.getText(component,field, ['xaxis','units']);" + eol
    js += "    var xscale = component.props.getText(component,field, ['xaxis','scale']);" + eol
    js += "    try{" + eol
    js += "      var tempval;" + eol
    js += "      if (xrange[0] == undefined){" + eol
    js += "        tempval = parseFloat(component.props.getText(component,field, ['xaxis','min']));" + eol
    js += "      } else{" + eol
    js += "        tempval = min(xrange[0], parseFloat(component.props.getText(component,field, ['xaxis','min'])));" + eol
    js += "      }" + eol
    js += "      if ( !isNaN(tempval)){" + eol
    js += "        xrange[0] = tempval;" + eol
    js += "      }" + eol
    js += "    } catch(error){}" + eol
    js += "    try{" + eol
    js += "      var tempval;" + eol
    js += "      if (xrange[1] == undefined){" + eol
    js += "        tempval = parseFloat(component.props.getText(component,field, ['xaxis','max']));" + eol
    js += "      } else{" + eol
    js += "        tempval = min(xrange[1], parseFloat(component.props.getText(component,field, ['xaxis','max'])));" + eol
    js += "      }" + eol
    js += "      if ( !isNaN(tempval)){" + eol
    js += "        xrange[1] = tempval;" + eol
    js += "      }" + eol
    js += "    } catch(error){}" + eol
    js += "    try{" + eol
    js += "      var tempval;" + eol
    js += "      if (yrange[0] == undefined){" + eol
    js += "        tempval = parseFloat(component.props.getText(component,field, ['yaxis','min']));" + eol
    js += "      } else{" + eol
    js += "        tempval = min(yrange[0], parseFloat(component.props.getText(component,field, ['yaxis','min'])));" + eol
    js += "      }" + eol
    js += "      if ( !isNaN(tempval)){" + eol
    js += "        yrange[0] = tempval;" + eol
    js += "      }" + eol
    js += "    } catch(error){}" + eol
    js += "    try{" + eol
    js += "      var tempval;" + eol
    js += "      if (yrange[1] == undefined){" + eol
    js += "        tempval = parseFloat(component.props.getText(component,field, ['yaxis','max']));" + eol
    js += "      } else{" + eol
    js += "        tempval = min(yrange[1], parseFloat(component.props.getText(component,field, ['yaxis','max'])));" + eol
    js += "      }" + eol
    js += "      if ( !isNaN(tempval)){" + eol
    js += "        yrange[1] = tempval;" + eol
    js += "      }" + eol
    js += "    } catch(error){}" + eol
    js += "    if (xscale == ''){" + eol
    js += "      xscale = 'linear';" + eol
    js += "      yaxis = component.props.getText(component,field, ['yaxis','label']);" + eol
    js += "      yunits = component.props.getText(component,field, ['yaxis','units']);" + eol
    js += "      yscale = component.props.getText(component,field, ['yaxis','scale']);" + eol
    js += "    }" + eol
    js += "    if (yscale == ''){" + eol
    js += "      yscale = 'linear';" + eol
    js += "    }" + eol
    js += "    for (var j=0;j<rapp_component.length;j++){" + eol
    js += "      var obj = rapp_component[j];" + eol
    js += "      var xy = obj.trim().replace(/--/g, '').replace(/\\n|\\r/g,' ').split(/[\s]+/);" + eol
    js += "      xy = xy.filter(function(el){ return el != '' });" + eol    
    js += "      let xx = xy.filter(function(el, index){ return index%2 == 0 }).map(Number);" + eol    
    js += "      let yy = xy.filter(function(el, index){ return index%2 == 1 }).map(Number);" + eol        
    js += "      var trace1 = {" + eol
    js += "        'type' : 'scatter'," + eol
    js += "        'x' : xx," + eol
    js += "        'y' : yy," + eol
    js += "        'mode' : 'lines'," + eol
    js += "        'name' : label," + eol
    js += "        'line' : line," + eol
    js += "      };" + eol
    js += "      traces.push(trace1);" + eol
    js += "    }" + eol    
    js += "  }" + eol
    js += "  layout = {" + eol
    js += "    'title' : title," + eol
    js += "    'autosize' :  true," + eol
    js += "    'xaxis' : {" + eol
    js += "      'title' : xaxis + ' [' + xunits + ']'," + eol
    js += "      'type' : xscale," + eol
    js += "      'autorange' : true," + eol
    js += "      'range' : [-1,1]," + eol
    js += "      'exponentformat' :  'e'," + eol
    js += "    }," + eol
    js += "    'yaxis' : {" + eol
    js += "      'title' : yaxis + ' [' + yunits + ']'," + eol
    js += "      'type' : yscale," + eol
    js += "      'autorange' : true," + eol
    js += "      'range' : [-1,1]," + eol
    js += "      'exponentformat' : 'e'" + eol
    js += "    }," + eol
    js += "    'legend' : { 'orientation' : 'h', 'x':0.1, 'y':1.1 }," + eol
    js += "  };" + eol
    js += "  if (xrange[0] != undefined && xrange[1] != undefined){" + eol
    js += "    layout['xaxis']['autorange'] = false;" + eol
    js += "    layout['xaxis']['range'] = xrange;" + eol 
    js += "  }" + eol
    js += "  if (yrange[0] != undefined && yrange[1] != undefined){" + eol
    js += "    layout['yaxis']['autorange'] = false;" + eol
    js += "    layout['yaxis']['range'] = yrange;" + eol
    js += "  }" + eol
    js += "  return {'traces':traces, 'layout':layout}" + eol
    js += "}" + eol

    component.addPropVariable("buildXYPlotly", {"type":"func", "defaultValue": js})
    return {
      "type": "propCall2",
      "calls": "buildXYPlotly",
      "args": ['self',[], 'undefined']
    }    
    
  def plotXY(tp, component, *args, **kwargs): 
    RapptureBuilder.buildXYPlotly(tp, component)
    eol = "\n"
    js = ""
    js += "(component, sequence) => {" + eol
    js += "  var plt = component.props.buildXYPlotly(component, sequence);" + eol
    js += "  var tr = plt['traces'];" + eol
    js += "  var ly = plt['layout'];" + eol    
    js += "  var layout = {" + eol    
    js += "    'title' : ly['title']," + eol    
    js += "    'autosize' :  true," + eol    
    js += "    'xaxis' : {" + eol    
    js += "      'title' : ly['xaxis']['title']," + eol    
    js += "      'type' : ly['xaxis']['type']," + eol    
    js += "      'autorange' : ly['xaxis']['autorange']," + eol    
    js += "      'range' : ly['xaxis']['range']," + eol    
    js += "    }," + eol    
    js += "    'yaxis' : {" + eol    
    js += "      'title' : ly['yaxis']['title']," + eol    
    js += "      'type' : ly['yaxis']['type']," + eol    
    js += "      'autorange' : ly['yaxis']['autorange']," + eol    
    js += "      'range' : ly['yaxis']['range']," + eol   
    js += "    }" + eol    
    js += "  };" + eol
    js += "  return {'data':tr, 'frames':[], 'layout':layout}" + eol
    js += "}" + eol

    component.addPropVariable("plotXY", {"type":"func", "defaultValue": js})
    return {
      "type": "propCall2",
      "calls": "plotXY",
      "args": ['self', '']
    }
    
  def plotSequence(tp, component, *args, **kwargs): 
    RapptureBuilder.buildXYPlotly(tp, component)
    url = kwargs.get("url", "")    
    eol = "\n"
    js = ""
    js += "(component, sequence) => {" + eol
    js += "  var elements = sequence.getElementsByTagName('element');" + eol
    js += "  var label = 'TODO';" + eol
    js += "  var min_tr_x = undefined;" + eol
    js += "  var min_tr_y = undefined;" + eol
    js += "  var max_tr_x = undefined;" + eol
    js += "  var max_tr_y = undefined;" + eol
    js += "  var traces = [];" + eol
    js += "  var layout = {};" + eol
    js += "  var frames = {};" + eol    
    js += "  var options = [];" + eol        
    js += "  for (var i=0;i<elements.length;i++){" + eol
    js += "    var seq = elements[i];" + eol
    js += "    var index = seq.querySelectorAll('index');" + eol
    js += "    if (index.length>0 && index[0].innerHTML != ''){" + eol
    js += "      index = index[0].innerHTML;" + eol 
    js += "      var curves = seq.getElementsByTagName('curve');" + eol
    js += "      var plt = component.props.buildXYPlotly(component, curves);" + eol
    js += "      var tr = plt['traces'];" + eol
    js += "      var lay = plt['layout'];" + eol
    js += "      for (t=0; t<tr.length;t++){" + eol
    js += "        var minx, maxx;" + eol
    js += "        try {" + eol
    js += "          if (lay['xaxis']['type'] == 'log'){" + eol
    js += "            minx = Math.min.apply(null, tr[t].filter((function(el){ return el > 0 })));" + eol
    js += "            maxx = Math.max.apply(null, tr[t].filter((function(el){ return el > 0 })));" + eol
    js += "          } else {" + eol
    js += "            minx = Math.min.apply(null, tr[t]);" + eol
    js += "            maxx = Math.max.apply(null, tr[t]);" + eol
    js += "          }" + eol
    js += "          if (min_tr_x ==undefined || min_tr_x > minx){" + eol
    js += "            min_tr_x = minx;" + eol
    js += "          }" + eol
    js += "          if (max_tr_x ==undefined || max_tr_x < maxx){" + eol
    js += "            max_tr_x = maxx;" + eol
    js += "          }" + eol
    js += "        } catch(error){}" + eol
    js += "        var miny, maxy;" + eol
    js += "        try {" + eol
    js += "          if (lay['yaxis']['type'] == 'log'){" + eol
    js += "            miny = Math.min.apply(null, tr[t].filter((function(el){ return el > 0 })));" + eol
    js += "            maxy = Math.max.apply(null, tr[t].filter((function(el){ return el > 0 })));" + eol
    js += "          } else {" + eol
    js += "            miny = Math.min.apply(null, tr[t]);" + eol
    js += "            maxy = Math.max.apply(null, tr[t]);" + eol
    js += "          }" + eol
    js += "          if (min_tr_y ==undefined || min_tr_y > miny){" + eol
    js += "            min_tr_y = minx;" + eol
    js += "          }" + eol
    js += "          if (max_tr_y ==undefined || max_tr_y < maxy){" + eol
    js += "            max_tr_y = maxy;" + eol
    js += "          }" + eol
    js += "        } catch(error){}" + eol
    js += "      }" + eol
    js += "      if (traces.length == 0){" + eol
    js += "        layout = lay;" + eol
    js += "        traces = tr.slice(0);" + eol #clone
    js += "      }" + eol
    js += "      if (index in frames){" + eol
    js += "        frames[index].push(...tr.slice(0));" + eol
    js += "      } else {" + eol
    js += "        options.push(index);" + eol
    js += "        frames[index] = tr.slice(0);" + eol
    js += "      }" + eol
    js += "    }" + eol
    js += "  }" + eol
    js += "  var frms = [];" + eol
    
    js += "  layout['sliders'] = [{" + eol
    js += "    'pad': {t: 30}," + eol
    js += "    'x': 0.05," + eol
    js += "    'len': 0.95," + eol
    js += "    'currentvalue': {" + eol
    js += "      'xanchor': 'right'," + eol
    js += "      'prefix': ''," + eol
    js += "      'font': {" + eol
    js += "        'color': '#888'," + eol
    js += "        'size': 20" + eol
    js += "      }" + eol
    js += "    }," + eol
    js += "    'transition': {'duration': 100}," + eol
    js += "    'steps': []," + eol
    js += "  }];" + eol    

    js += "  Object.entries(frames).forEach(entry=>{" + eol
    js += "     var key = entry[0];" + eol
    js += "     var value = entry[1];" + eol
    js += "     frms.push({" + eol
    js += "       'name' : key," + eol
    js += "       'data' : value" + eol
    js += "     });" + eol
    js += "  });" + eol

    js += "  for(var f=0;f<frms.length;f++){" + eol
    js += "    layout['sliders'][0]['steps'].push({" + eol
    js += "      label : frms[f]['name']," + eol
    js += "      method : 'animate'," + eol
    js += "      args : [[frms[f]['name']], {" + eol
    js += "        mode: 'immediate'," + eol
    js += "        'frame' : 'transition'," + eol
    js += "        'transition' : {duration: 100}," + eol
    js += "      }]" + eol
    js += "    });" + eol
    js += "  }" + eol
    
    js += "  layout['updatemenus'] = [{" + eol
    js += "    type: 'buttons'," + eol
    js += "    showactive: false," + eol
    js += "    x: 0.05," + eol
    js += "    y: 0," + eol
    js += "    xanchor: 'right'," + eol
    js += "    yanchor: 'top'," + eol
    js += "    pad: {t: 60, r: 20}," + eol
    js += "    buttons: [{" + eol
    js += "      label: 'Play'," + eol
    js += "      method: 'animate'," + eol
    js += "      args: [null, {" + eol
    js += "        fromcurrent: true," + eol
    js += "        frame: {redraw: false, duration: 500}," + eol
    js += "        transition: {duration: 100}" + eol
    js += "      }]" + eol
    #js += "    },{" + eol
    #js += "      label: 'Pause'," + eol
    #js += "      method: 'animate'," + eol
    #js += "      args: [[null], {" + eol    
    #js += "        mode: 'immediate'," + eol
    #js += "        frame: {redraw: false, duration: 0}" + eol
    #js += "      }]" + eol
    js += "    }]" + eol
    js += "  }];" + eol    
    js += "  return {'data':traces, 'frames':frms, 'layout':layout}" + eol
    js += "}" + eol

    component.addPropVariable("plotSequence", {"type":"func", "defaultValue": js})
    return {
      "type": "propCall2",
      "calls": "plotSequence",
      "args": ['self', []]
    }  
    
  def loadXY(tp, component, *args, **kwargs):   
    eol = "\n";
    RapptureBuilder.plotXY(tp, component)
    store_name="LocalStore";
    NanohubUtils.storageFactory(tp, store_name=store_name)    
    js = ""
    js += "(component, seq, layout) => {" + eol
    js += "  var output_xml = " + store_name + ".getItem('output_xml');" + eol
    js += "  if (!output_xml || output_xml == '')" + eol
    js += "    return;" + eol
    #js += "  console.log(output_xml);" + eol
    js += "  var xmlDoc = JSON.parse(output_xml);" + eol
    js += "  var state = component.state;" + eol
    js += "  if (window.DOMParser){" + eol
    js += "    let parser = new DOMParser();" + eol
    js += "    xmlDoc = parser.parseFromString(xmlDoc, 'text/xml');" + eol
    js += "  } else {" + eol
    js += "    xmlDoc = new ActiveXObject('Microsoft.XMLDOM');" + eol
    js += "    xmlDoc.async = false;" + eol
    js += "    xmlDoc.loadXML(xmlDoc);" + eol
    js += "  }" + eol
    js += "  var output = xmlDoc.getElementsByTagName('output');" + eol
    js += "  var sequences = [];" + eol
    js += "  var lseq = Array();" + eol
    js += "  if (output.length > 0){" + eol
    js += "    sequences = output[0].querySelectorAll('output > curve');" + eol
    js += "  }" + eol    
    js += "  for (var i=0;i<sequences.length;i++){" + eol
    js += "    var sequence = sequences[i];" + eol
    js += "    if (sequence.hasAttribute('id') && seq.filter( (v) => new RegExp(v).test(sequence.getAttribute('id'))).length >0){" + eol
    js += "      lseq.push(sequence);" + eol
    js += "    }" + eol
    js += "  }" + eol
    js += "  var plt = component.props.plotXY(component, lseq);" + eol
    js += "  plt['layout']['showlegend'] = true" + eol        
    js += "  if (layout){" + eol    
    js += "    if (layout.showlegend !== undefined){" + eol
    js += "        plt['layout']['showlegend'] = layout.showlegend;" + eol
    js += "    }" + eol
    js += "    if (layout.xaxis){" + eol
    js += "      if (layout.xaxis.type){" + eol
    js += "        plt['layout']['xaxis']['type'] = layout.xaxis.type;" + eol
    js += "      }" + eol
    js += "    }" + eol
    js += "  }" + eol    
    js += "  component.setState({" + eol
    js += "    'data': plt['data']," + eol
    js += "    'layout': plt['layout']," + eol
    js += "    'frames': plt['frames']," + eol
    js += "    'config': {'displayModeBar': true, 'responsive': 'true'}" + eol    
    js += "  });" + eol
    js += "  window.dispatchEvent(new Event('resize'));" + eol #trying to trigger windows rescale does not work on IE
    js += "}" + eol
    component.addPropVariable("loadXY", {"type":"func", "defaultValue": js})    
    
    return {
      "type": "propCall2",
      "calls": "loadXY",
      "args": ['self', '[]']
    }

  def loadXYDual(tp, component, *args, **kwargs):   
    eol = "\n";
    RapptureBuilder.plotXY(tp, component)
    store_name="LocalStore";
    NanohubUtils.storageFactory(tp, store_name=store_name)    
    js = ""
    js += "(component, base, seq, layout) => {" + eol
    js += "  var output_xml = " + store_name + ".getItem('output_xml');" + eol
    js += "  if (!output_xml || output_xml == '')" + eol
    js += "    return;" + eol
    #js += "  console.log(output_xml);" + eol
    js += "  var xmlDoc = JSON.parse(output_xml);" + eol
    js += "  var state = component.state;" + eol
    js += "  if (window.DOMParser){" + eol
    js += "    let parser = new DOMParser();" + eol
    js += "    xmlDoc = parser.parseFromString(xmlDoc, 'text/xml');" + eol
    js += "  } else {" + eol
    js += "    xmlDoc = new ActiveXObject('Microsoft.XMLDOM');" + eol
    js += "    xmlDoc.async = false;" + eol
    js += "    xmlDoc.loadXML(xmlDoc);" + eol
    js += "  }" + eol
    js += "  var output = xmlDoc.getElementsByTagName('output');" + eol
    js += "  var sequences = [];" + eol
    js += "  var lbase = Array();" + eol
    js += "  var lseq = Array();" + eol
    js += "  if (output.length > 0){" + eol
    js += "    sequences = output[0].querySelectorAll('output > curve');" + eol
    js += "  }" + eol    
    js += "  for (var i=0;i<sequences.length;i++){" + eol
    js += "    var sequence = sequences[i];" + eol
    js += "    if (sequence.hasAttribute('id') && seq.filter( (v) => new RegExp(v).test(sequence.getAttribute('id'))).length >0){" + eol
    js += "      lseq.push(sequence);" + eol
    js += "    }" + eol
    js += "    if (sequence.hasAttribute('id') && base.filter( (v) => new RegExp(v).test(sequence.getAttribute('id'))).length >0){" + eol
    js += "      lbase.push(sequence);" + eol
    js += "    }" + eol
    js += "  }" + eol
    js += "  let pltb = component.props.plotXY(component, lbase);" + eol
    js += "  let plt = component.props.plotXY(component, lseq);" + eol
    js += "  pltb['data'].forEach((v, i, a) => { a[i]['xaxis'] ='x'; if(a[i]['line']['color']=='yellow'){a[i]['line']['color'] = '#984ea3';} });" + eol
    js += "  plt['data'].forEach((v, i, a) => { a[i]['xaxis'] ='x2'; if(a[i]['line']['color']=='yellow'){a[i]['line']['color'] = '#984ea3';}});" + eol
    js += "  plt['layout']['showlegend'] = true" + eol    
    js += "  if (layout){" + eol    
    js += "    if (layout.showlegend !== undefined){" + eol
    js += "        plt['layout']['showlegend'] = layout.showlegend;" + eol
    js += "    }" + eol
    js += "    if (layout.xaxis){" + eol
    js += "      if (layout.xaxis.type){" + eol
    js += "        plt['layout']['xaxis']['type'] = layout.xaxis.type;" + eol
    js += "      }" + eol
    js += "    }" + eol
    js += "  }" + eol
    js += "  component.setState({" + eol
    js += "    'data': pltb['data'].concat(plt['data'])," + eol
    js += "    'layout': {" + eol
    js += "      'title' : pltb['layout']['title']," + eol
    js += "      'xaxis' : {" + eol
    js += "        'domain': [0, 0.29]," + eol
    js += "        'title' : pltb['layout']['xaxis']['title']," + eol
    js += "        'autorange' : false," + eol
    js += "        'range' : [0,1]," + eol
    js += "        'type' : 'linear'," + eol
    js += "      }," + eol
    js += "      'xaxis2' : {" + eol
    js += "        'domain': [0.31, 1.0]," + eol
    js += "        'title' : plt['layout']['xaxis']['title']," + eol
    js += "        'autorange' : plt['layout']['xaxis']['autorange']," + eol
    js += "        'type' : plt['layout']['xaxis']['type']," + eol
    js += "      }," + eol
    js += "      'yaxis' : {" + eol
    js += "        'title' : plt['layout']['yaxis']['title']," + eol
    js += "        'autorange' : true," + eol
    js += "        'type' : 'linear'," + eol
    js += "      }," + eol
    js += "      'showlegend' :  plt['layout']['showlegend']," + eol
    js += "    }," + eol
    js += "    'frames': []," + eol
    js += "    'config': {'displayModeBar': true, 'responsive': 'true'}" + eol    
    js += "  });" + eol
    js += "  window.dispatchEvent(new Event('resize'));" + eol #trying to trigger windows rescale does not work on IE
    js += "}" + eol
    component.addPropVariable("loadXYDual", {"type":"func", "defaultValue": js})    
    
    return {
      "type": "propCall2",
      "calls": "loadXYDual",
      "args": ['self', '[]', '[]']
    }

  def loadSequence(tp, component, *args, **kwargs):   
    eol = "\n";
    RapptureBuilder.plotSequence(tp, component)
    store_name="LocalStore";
    NanohubUtils.storageFactory(tp, store_name=store_name)    
    js = ""
    js += "(component, seq) => {" + eol
    js += "  var output_xml = " + store_name + ".getItem('output_xml');" + eol
    js += "  if (!output_xml || output_xml == '')" + eol
    js += "    return;" + eol
    #js += "  console.log(output_xml);" + eol
    js += "  var xmlDoc = JSON.parse(output_xml);" + eol
    js += "  var state = component.state;" + eol
    js += "  if (window.DOMParser){" + eol
    js += "    let parser = new DOMParser();" + eol
    js += "    xmlDoc = parser.parseFromString(xmlDoc, 'text/xml');" + eol
    js += "  } else {" + eol
    js += "    xmlDoc = new ActiveXObject('Microsoft.XMLDOM');" + eol
    js += "    xmlDoc.async = false;" + eol
    js += "    xmlDoc.loadXML(xmlDoc);" + eol
    js += "  }" + eol
    js += "  var output = xmlDoc.getElementsByTagName('output');" + eol
    js += "  var sequences = [];" + eol
    js += "  var lseq = Array();" + eol
    js += "  if (output.length > 0){" + eol
    js += "    sequences = output[0].querySelectorAll('output > sequence');" + eol
    js += "  }" + eol    
    js += "  for (var i=0;i<sequences.length;i++){" + eol
    js += "    var sequence = sequences[i];" + eol
    js += "    if (sequence.hasAttribute('id') && seq.filter( (v) => new RegExp(v).test(sequence.getAttribute('id'))).length >0){" + eol
    js += "      lseq.push(sequence);" + eol
    js += "    }" + eol
    js += "  }" + eol
    js += "  if (lseq.length > 0){" + eol
    js += "    plt = component.props.plotSequence(component, lseq[0]);" + eol
    js += "    component.setState({" + eol
    js += "      'data': plt['data']," + eol
    js += "      'layout': plt['layout']," + eol
    js += "      'frames': plt['frames']," + eol
    js += "      'config': {'displayModeBar': true, 'responsive': 'true'}" + eol        
    js += "    });" + eol
    js += "    window.dispatchEvent(new Event('resize'));" + eol #trying to trigger windows rescale does not work on IE    
    js += "  }" + eol
    js += "}" + eol
    component.addPropVariable("loadSequence", {"type":"func", "defaultValue": js})    
    
    return {
      "type": "propCall2",
      "calls": "loadSequence",
      "args": ['self', '[]']
    }


  def buildSchema(tp, Component, *args, **kwargs):
    store_name="sessionStore";
    NanohubUtils.storageFactory(tp, store_name=store_name)
    toolname = kwargs.get("toolname", "")
    url = kwargs.get("url", "https://nanohub.org/api/tools")
    eol = "\n"
    js = ""
    js += "async (self) => {"
    js += "  var header_token = { 'Content-Type': 'application/x-www-form-urlencoded', 'Accept': '*/*' };" + eol
    js += "  var options = { 'handleAs' : 'xml' , 'headers' : header_token, 'method' : 'GET' };" + eol
    js += "  var url = '" + url + "/" + toolname + "/rappturexml';" + eol
    js += "  let params = {};"     + eol
    js += "  let selfr = self;"     + eol
    js += "  await Axios.request(url, options)" + eol
    js += "  .then(function(response){" + eol
    js += "    var data = response.data;"  + eol
    js += "    let parser = new DOMParser();   " + eol
    js += "    var periodicelement = [" + eol
    js += "        ['Hydrogen','H'], ['Helium','He'], ['Lithium','Li'], ['Beryllium','Be']," + eol
    js += "        ['Boron','B'], ['Carbon','C'], ['Nitrogen','N'], ['Oxygen','O']," + eol
    js += "        ['Fluorine','F'], ['Neon','Ne'], ['Sodium','Na'], ['Magnesium','Mg']," + eol
    js += "        ['Aluminium','Al'], ['Silicon','Si'], ['Phosphorus','P'], ['Sulfur','S']," + eol
    js += "        ['Chlorine','Cl'], ['Argon','Ar'], ['Potassium','K'], ['Calcium','Ca']," + eol
    js += "        ['Scandium','Sc'], ['Titanium','Ti'], ['Vanadium','V'], ['Chromium','Cr']," + eol
    js += "        ['Manganese','Mn'], ['Iron','Fe'], ['Cobalt','Co'], ['Nickel','Ni']," + eol
    js += "        ['Copper','Cu'], ['Zinc','Zn'], ['Gallium','Ga'], ['Germanium','Ge']," + eol
    js += "        ['Arsenic','As'], ['Selenium','Se'], ['Bromine','Br'], ['Krypton','Kr']," + eol
    js += "        ['Rubidium','Rb'], ['Strontium','Sr'], ['Yttrium','Y'], ['Zirconium','Zr']," + eol
    js += "        ['Niobium','Nb'], ['Molybdenum','Mo'], ['Technetium','Tc'], ['Ruthenium','Ru']," + eol
    js += "        ['Rhodium','Rh'], ['Palladium','Pd'], ['Silver','Ag'], ['Cadmium','Cd']," + eol
    js += "        ['Indium','In'], ['Tin','Sn'], ['Antimony','Sb'], ['Tellurium','Te']," + eol
    js += "        ['Iodine','I'], ['Xenon','Xe'], ['Caesium','Cs'], ['Barium','Ba']," + eol
    js += "        ['Lanthanum','La'], ['Cerium','Ce'], ['Praseodymium','Pr'], ['Neodymium','Nd']," + eol
    js += "        ['Promethium','Pm'], ['Samarium','Sm'], ['Europium','Eu'], ['Gadolinium','Gd']," + eol
    js += "        ['Terbium','Tb'], ['Dysprosium','Dy'], ['Holmium','Ho'], ['Erbium','Er']," + eol
    js += "        ['Thulium','Tm'], ['Ytterbium','Yb'], ['Lutetium','Lu'], ['Hafnium','Hf']," + eol
    js += "        ['Tantalum','Ta'], ['Tungsten','W'], ['Rhenium','Re'], ['Osmium','Os']," + eol
    js += "        ['Iridium','Ir'], ['Platinum','Pt'], ['Gold','Au'], ['Mercury','Hg']," + eol
    js += "        ['Thallium','Tl'], ['Lead','Pb'], ['Bismuth','Bi'], ['Polonium','Po']," + eol
    js += "        ['Astatine','At'], ['Radon','Rn'], ['Francium','Fr'], ['Radium','Ra']," + eol
    js += "        ['Actinium','Ac'], ['Thorium','Th'], ['Protactinium','Pa'], ['Uranium','U']," + eol
    js += "        ['Neptunium','Np'], ['Plutonium','Pu'], ['Americium','Am'], ['Curium','Cm']," + eol
    js += "        ['Berkelium','Bk'], ['Californium','Cf'], ['Einsteinium','Es'], ['Fermium','Fm']," + eol
    js += "        ['Mendelevium','Md'], ['Nobelium','No'], ['Lawrencium','Lr'], ['Rutherfordium','Rf']," + eol
    js += "        ['Dubnium','Db'], ['Seaborgium','Sg'], ['Bohrium','Bh'], ['Hassium','Hs']," + eol
    js += "        ['Meitnerium','Mt']        " + eol
    js += "    ];" + eol
    js += "    var xmlDoc = undefined;" + eol
    js += "    if (window.DOMParser){" + eol
    js += "        parser = new DOMParser();" + eol
    js += "        xmlDoc = parser.parseFromString(data, 'text/xml');" + eol
    js += "    } else {" + eol
    js += "        xmlDoc = new ActiveXObject('Microsoft.XMLDOM');" + eol
    js += "        xmlDoc.async = false;" + eol
    js += "        xmlDoc.loadXML(data);" + eol
    js += "    }" + eol
    js += "    var input = xmlDoc.getElementsByTagName('input');" + eol
    js += "    var inputs = input[0].getElementsByTagName('*');" + eol
    js += "    var parameters = [];" + eol
    js += "    var discardtags = ['phase', 'group', 'option', 'image', 'note'];" + eol
    js += "    for (var i=0;i<inputs.length;i++){" + eol
    js += "      var elem = inputs[i];" + eol
    js += "      if (elem.hasAttribute('id')){" + eol
    js += "        var id = elem.getAttribute('id');" + eol
    js += "        if (!(id in params)){" + eol
    js += "          var about = elem.getElementsByTagName('about');" + eol
    js += "          var description = '';" + eol
    js += "          var labelt = '';" + eol
    js += "          if (about.length > 0){" + eol
    js += "            var description = elem.getElementsByTagName('description');" + eol
    js += "            if (description.length > 0){" + eol
    js += "              description = description[0].innerHTML;" + eol
    js += "            }" + eol
    js += "            var label = about[0].getElementsByTagName('label');" + eol
    js += "            if (label.length > 0){" + eol
    js += "                labelt = label[0].innerHTML;" + eol
    js += "            }" + eol
    js += "          }" + eol
    js += "          if (parameters.length == 0 || id in parameters){" + eol
    js += "            if (!(discardtags.includes(elem.tagName))){" + eol
    js += "              var param = {'type': elem.tagName, 'description' : description};" + eol
    js += "              param['id'] = id;" + eol
    js += "              param['label'] = labelt;" + eol
    js += "              var units = elem.getElementsByTagName('units');" + eol
    js += "              if (units.length > 0){" + eol
    js += "                param['units'] = units[0].innerHTML;" + eol
    js += "              }" + eol
    js += "              var defaultv = elem.getElementsByTagName('default');" + eol
    js += "              if (defaultv.length > 0){" + eol
    js += "                param['default'] = defaultv[0].innerHTML;" + eol
    js += "              }" + eol
    js += "              var minv = elem.getElementsByTagName('min');" + eol
    js += "              if (minv.length > 0){" + eol
    js += "                param['min'] = minv[0].innerHTML;" + eol
    js += "              }" + eol
    js += "              var maxv = elem.getElementsByTagName('max');" + eol
    js += "              if (maxv.length > 0){" + eol
    js += "                param['max'] = maxv[0].innerHTML;" + eol
    js += "              }" + eol
    js += "              var currentv = elem.getElementsByTagName('current');" + eol
    js += "              if (currentv.length > 0){" + eol
    js += "                param['current'] = currentv[0].innerHTML;" + eol
    js += "              }" + eol
    js += "              var options = elem.getElementsByTagName('option');" + eol
    js += "              var opt_list = [];" + eol
    js += "              for (var j = 0;j<options.length;j++){" + eol
    js += "                var option = options[j];" + eol
    js += "                var lvalue = option.getElementsByTagName('value');" + eol
    js += "                var opt_val = ['', ''];" + eol
    js += "                if (lvalue.length>0){" + eol
    js += "                  if (lvalue[0].innerHTML != ''){" + eol
    js += "                    opt_val[0] = lvalue[0].innerHTML;" + eol
    js += "                    opt_val[1] = lvalue[0].innerHTML;" + eol
    js += "                  }" + eol
    js += "                }" + eol
    js += "                var labout = option.getElementsByTagName('about');" + eol
    js += "                if (labout.length>0){" + eol
    js += "                  let llabel = labout[0].getElementsByTagName('label');" + eol
    js += "                  if (llabel.length>0){" + eol
    js += "                    if (llabel[0].innerHTML != ''){" + eol
    js += "                      opt_val[0] = llabel[0].innerHTML;" + eol
    js += "                      if (opt_val[1] == ''){" + eol
    js += "                        opt_val[1] = llabel[0].innerHTML;" + eol
    js += "                      }" + eol
    js += "                    }" + eol
    js += "                  }" + eol
    js += "                }" + eol
    js += "                opt_list.push(opt_val);" + eol
    js += "              }" + eol
    js += "              param['options'] = opt_list;" + eol
    js += "              if (param['type'] == 'periodicelement'){" + eol
    js += "                  param['type'] = 'choice';" + eol
    js += "                  param['options'] = periodicelement;" + eol
    js += "              }" + eol
    js += "              if (param['options'].length > 0){" + eol
    js += "                var tmparray = param['options'].filter(p => p[1] == param['default']);" + eol
    js += "                if (tmparray.length == 0 ){" + eol
    js += "                  param['default'] = param['options'][0][1];" + eol
    js += "                }" + eol
    js += "              }" + eol
    js += "              if (param['type'] == 'string'){" + eol
    js += "                if (param['default'] && /\\r|\\n/.exec(param['default'].trim())){" + eol
    js += "                  param['type'] = 'text';" + eol
    js += "                }" + eol
    js += "              }" + eol
    js += "              if (about.length > 0 && label.length > 0)" + eol
    js += "                params [id] = param;" + eol
    js += "            }" + eol
    js += "          }" + eol
    js += "        }" + eol
    js += "      }" + eol
    js += "    }" + eol
    js += "    " + store_name + ".setItem('nanohub_tool_schema', JSON.stringify(params));" + eol
    js += "    " + store_name + ".setItem('nanohub_tool_xml', JSON.stringify(data));" + eol
    js += "    selfr.props.onLoadSchema(selfr)"
    js += "  }).catch(function(error){" + eol
    js += "    selfr.props.onSchemaError(selfr)"
    js += "  });" + eol
    js += "}" + eol
    
    Component.addPropVariable("buildSchema", {"type":"func", 'defaultValue' :js})   
    Component.addPropVariable("onLoadSchema", {"type":"func", 'defaultValue' :"(e)=>{}"})   
    Component.addPropVariable("onSchemaError", {"type":"func", 'defaultValue' :"(e)=>{}"})   
    callbacklist = []

    callbacklist.append({
        "type": "propCall2",
        "calls": "buildSchema",
        "args": ['self']
    })    
    return callbacklist   


  def loadMolecule(tp, component, *args, **kwargs,):   
    eol = "\n";
    RapptureBuilder.plotDrawingPlotly(tp, component)
    store_name="LocalStore";
    NanohubUtils.storageFactory(tp, store_name=store_name)    
    js = ""
    js += "(component, seq, method, layout) => {" + eol
    js += "  var output_xml = " + store_name + ".getItem('output_xml');" + eol
    js += "  if (!output_xml || output_xml == '')" + eol
    js += "    return;" + eol
    js += "  var xmlDoc = JSON.parse(output_xml);" + eol
    js += "  var state = component.state;" + eol
    js += "  if (window.DOMParser){" + eol
    js += "    let parser = new DOMParser();" + eol
    js += "    xmlDoc = parser.parseFromString(xmlDoc, 'text/xml');" + eol
    js += "  } else {" + eol
    js += "    xmlDoc = new ActiveXObject('Microsoft.XMLDOM');" + eol
    js += "    xmlDoc.async = false;" + eol
    js += "    xmlDoc.loadXML(xmlDoc);" + eol
    js += "  }" + eol
    js += "  var output = xmlDoc.getElementsByTagName('output');" + eol
    js += "  var sequences = [];" + eol
    js += "  var lseq = Array();" + eol
    js += "  if (output.length > 0){" + eol
    js += "    sequences = output[0].querySelectorAll('output > drawing');" + eol
    js += "  }" + eol    
    js += "  for (var i=0;i<sequences.length;i++){" + eol
    js += "    var sequence = sequences[i];" + eol
    js += "    if (sequence.hasAttribute('id') && seq.filter( (v) => new RegExp(v).test(sequence.getAttribute('id'))).length >0){" + eol
    js += "      lseq.push(sequence);" + eol
    js += "    }" + eol
    js += "  }" + eol
    js += "  let plt = component.props.plotDrawingPlotly(component, lseq, method);" + eol
    js += "  plt['layout']['showlegend'] = true" + eol        
    js += "  if (layout){" + eol    
    js += "    if (layout.showlegend !== undefined){" + eol
    js += "        plt['layout']['showlegend'] = layout.showlegend;" + eol
    js += "    }" + eol
    js += "    if (layout.xaxis){" + eol
    js += "      if (layout.xaxis.type){" + eol
    js += "        plt['layout']['xaxis']['type'] = layout.xaxis.type;" + eol
    js += "      }" + eol
    js += "    }" + eol
    js += "  }" + eol    
    js += "  component.setState({" + eol
    js += "    'data': plt['data']," + eol
    js += "    'layout': plt['layout']," + eol
    js += "    'frames': plt['frames']," + eol
    js += "    'config': {'displayModeBar': true, 'responsive': 'true'}" + eol    
    js += "  });" + eol
    js += "  window.dispatchEvent(new Event('resize'));" + eol #trying to trigger windows rescale does not work on IE
    js += "}" + eol
    component.addPropVariable("loadMolecule", {"type":"func", "defaultValue": js})    
    
    return {
      "type": "propCall2",
      "calls": "loadMolecule",
      "args": ['self', '[]']
    }


  def extractVectors(tp, component, *args, **kwargs):   
    eol = "\n";
    store_name="LocalStore";
    NanohubUtils.storageFactory(tp, store_name=store_name)    
    RapptureBuilder.getColor(tp, component)            
    js = ""
    js += "(component, seq, layout) => {" + eol
    js += "  var ivectors = [];" + eol
    js += "  var vectors = [];" + eol
    js += "  var atoms = [];" + eol
    js += "  var box = [];" + eol
    js += "  seq.forEach((s)=>{" + eol
    js += "    var latt = component.props.getText(component, s, ['current']);" + eol
    js += "    var lines = latt.split('\\n');" + eol
    js += "    let i=0;" + eol
    js += "    while (i < lines.length){" + eol
    js += "      var line = lines[i];" + eol
    js += "      if (line.startsWith('Primitive cell Bravais')){" + eol
    js += "        for (var ii=0; ii<3;ii++){" + eol
    js += "          i = i+1;" + eol
    js += "          var line = lines[i];" + eol
    js += "          var nums = line.split(/[^\d-\.]+/).filter((e)=>{return !isNaN(parseFloat(e))});" + eol
    js += "          vectors.push(nums.slice(1));" + eol
    js += "        }" + eol
    js += "      }" + eol
    js += "      if (line.startsWith('Reciprocal lattice vectors')){" + eol
    js += "        for (var ii=0; ii<3;ii++){" + eol
    js += "          i = i+1;" + eol
    js += "          var line = lines[i];" + eol
    js += "          var nums = line.split(/[^\d-\.]+/).filter((e)=>{return !isNaN(parseFloat(e))});" + eol
    js += "          ivectors.push(nums.slice(1));" + eol
    js += "        }" + eol
    js += "      }" + eol
    js += "      if (line.startsWith('Conventional cell Bravais vectors')){" + eol
    js += "        for (var ii=0; ii<3;ii++){" + eol
    js += "          i = i+1;" + eol
    js += "          var line = lines[i];" + eol
    js += "          var nums = line.split(/[^\d-\.]+/).filter((e)=>{return !isNaN(parseFloat(e))});" + eol
    js += "          box.push(nums.slice(1));" + eol
    js += "        }" + eol
    js += "      }" + eol
    js += "      if (line.startsWith('Primitive cell basis atoms')){" + eol
    js += "        i = i+1;" + eol
    js += "        while (i < lines.length &&  lines[i] != ''){" + eol
    js += "          var line = lines[i];" + eol
    js += "          var nums = line.split(/[^\d-\.]+/).filter((e)=>{return !isNaN(parseFloat(e))});" + eol
    js += "          var atom_name = line.match(/\(type: +([a-zA-Z]+)\)/);" + eol
    js += "          if (atom_name.length >1){" + eol
    
    js += "            nums.push(atom_name[1]);" + eol
    js += "          } else {" + eol
    js += "            nums.push('');" + eol
    js += "          }" + eol
    js += "          nums.push(component.props.getColor(component, nums[3]));" + eol  
    js += "          atoms.push(nums.slice(1));" + eol
    js += "          i = i+1;" + eol
    js += "        }" + eol
    js += "      }" + eol
    js += "      i = i+1;" + eol
    js += "    }" + eol
    js += "  });" + eol
    #js += "  console.log(atoms);" + eol
    #js += "  console.log(vectors);" + eol
    js += "  return {'vectors':vectors,'ivectors':ivectors,'atoms':atoms,'box':box};" + eol
    js += "}" + eol
    component.addPropVariable("extractVectors", {"type":"func", "defaultValue": js})    
    
    return {
      "type": "propCall2",
      "calls": "extractVectors",
      "args": ['self', '[]']
    }

  def loadVectors(tp, component, *args, **kwargs):   
    eol = "\n";
    RapptureBuilder.extractVectors(tp, component)
    store_name="LocalStore";
    NanohubUtils.storageFactory(tp, store_name=store_name)    
    js = ""
    js += "(component, seq, layout) => {" + eol
    js += "  var output_xml = " + store_name + ".getItem('output_xml');" + eol
    js += "  if (!output_xml || output_xml == '')" + eol
    js += "    return;" + eol
    #js += "  console.log(output_xml);" + eol
    js += "  var xmlDoc = JSON.parse(output_xml);" + eol
    js += "  var state = component.state;" + eol
    js += "  if (window.DOMParser){" + eol
    js += "    let parser = new DOMParser();" + eol
    js += "    xmlDoc = parser.parseFromString(xmlDoc, 'text/xml');" + eol
    js += "  } else {" + eol
    js += "    xmlDoc = new ActiveXObject('Microsoft.XMLDOM');" + eol
    js += "    xmlDoc.async = false;" + eol
    js += "    xmlDoc.loadXML(xmlDoc);" + eol
    js += "  }" + eol
    js += "  var output = xmlDoc.getElementsByTagName('output');" + eol
    js += "  var sequences = [];" + eol
    js += "  var lseq = Array();" + eol
    js += "  if (output.length > 0){" + eol
    js += "    sequences = output[0].querySelectorAll('output > string');" + eol
    js += "  }" + eol    
    js += "  for (var i=0;i<sequences.length;i++){" + eol
    js += "    var sequence = sequences[i];" + eol
    js += "    if (sequence.hasAttribute('id') && seq.filter( (v) => new RegExp(v).test(sequence.getAttribute('id'))).length >0){" + eol
    js += "      lseq.push(sequence);" + eol
    js += "    }" + eol
    js += "  }" + eol
    js += "  let vectors = component.props.extractVectors(component, lseq);" + eol 
    js += "  if (component.props.onLoadVectors){" + eol    
    js += "    component.props.onLoadVectors(component,vectors);" + eol
    js += "  }" + eol    
    js += "  return vectors;" + eol    
    js += "}" + eol
    component.addPropVariable("loadVectors", {"type":"func", "defaultValue": js})    
    
    return {
      "type": "propCall2",
      "calls": "loadVectors",
      "args": ['self', '[]']
    }

  def getColor(tp, component, *args, **kwargs):  
    RapptureBuilder.getAtomLabel(tp, component)
    eol = "\n"        
    js = ""
    js += "(component, molecule) => {" + eol
    js += "  var jcpk = {" + eol
    js += "    'H'  : 'rgba(255,255,255,1.0)'," + eol
    js += "    'He'  : 'rgba(20,20,20,1.0)'," + eol
    js += "    'Li' : 'rgba(188,190,187,1.0)'," + eol
    js += "    'Be' : 'rgba(134,134,134,1.0)'," + eol
    js += "    'B' : 'rgba(122,117,114,1.0)'," + eol
    js += "    'C' : 'rgba(31,120,180,1.0)'," + eol
    js += "    'N' : 'rgba(177,89,40,1.0)'," + eol
    js += "    'O' : 'rgba(238,32,16,1.0)'," + eol
    js += "    'F' : 'rgba(177,146,82,1.0)'," + eol
    js += "    'Ne' : 'rgba(255,0,0,1.0)'," + eol
    js += "    'Na' : 'rgba(218,220,217,1.0)'," + eol
    js += "    'Mg' : 'rgba(195,195,185,1.0)'," + eol
    js += "    'Al' : 'rgba(255,0,102,1.0)'," + eol
    js += "    'Si' : 'rgba(73,4,170,1.0)'," + eol
    js += "    'P' : 'rgba(255,0,9,1.0)'," + eol
    js += "    'S' : 'rgba(248,239,146,1.0)'," + eol
    js += "    'Cl' : 'rgba(251,154,153,1.0)'," + eol
    js += "    'Ar' : 'rgba(221,112,244,1.0)'," + eol
    js += "    'K' : 'rgba(165,171,171,1.0)'," + eol
    js += "    'Ca' : 'rgba(227,26,28,1.0)'," + eol
    js += "    'Sc' : 'rgba(176,173,166,1.0)'," + eol
    js += "    'Ti' : 'rgba(169,163,147,1.0)'," + eol
    js += "    'V' : 'rgba(191,189,202,1.0)'," + eol
    js += "    'Cr' : 'rgba(191,198,206,1.0)'," + eol
    js += "    'Mn' : 'rgba(206,205,200,1.0)'," + eol
    js += "    'Fe' : 'rgba(185,183,184,1.0)'," + eol
    js += "    'Co' : 'rgba(171,163,160,1.0)'," + eol
    js += "    'Ni' : 'rgba(181,165,150,1.0)'," + eol
    js += "    'Cu' : 'rgba(196,78,46,1.0)'," + eol
    js += "    'Zn' : 'rgba(255,0,0,1.0)'," + eol
    js += "    'Ga' : 'rgba(255,51,0,1.0)'," + eol
    js += "    'Ge' : 'rgba(0,255,0,1.0)'," + eol
    js += "    'As' : 'rgba(255,255,0,1.0)'," + eol
    js += "    'Se' : 'rgba(191,71,75,1.0)'," + eol
    js += "    'Br' : 'rgba(154,32,24,1.0)'," + eol
    js += "    'Kr' : 'rgba(164,162,175,1.0)'," + eol
    js += "    'Rb' : 'rgba(122,119,110,1.0)'," + eol
    js += "    'Sr' : 'rgba(217,206,160,1.0)'," + eol
    js += "    'Y' : 'rgba(153,155,154,1.0)'," + eol
    js += "    'Zr' : 'rgba(153,143,133,1.0)'," + eol
    js += "    'Nb' : 'rgba(98,91,138,1.0)'," + eol
    js += "    'Mo' : 'rgba(93,88,85,1.0)'," + eol
    js += "    'Tc' : 'rgba(131,120,116,1.0)'," + eol
    js += "    'Ru' : 'rgba(153,147,149,1.0)'," + eol
    js += "    'Rh' : 'rgba(156,143,135,1.0)'," + eol
    js += "    'Pd' : 'rgba(162,161,157,1.0)'," + eol
    js += "    'Ag' : 'rgba(202,178,214,1.0)'," + eol
    js += "    'Cd' : 'rgba(106,106,104,1.0)'," + eol
    js += "    'In' : 'rgba(106,61,154,1.0)'," + eol
    js += "    'Sn' : 'rgba(126,120,94,1.0)'," + eol
    js += "    'Sb' : 'rgba(0,0,191,1.0)'," + eol
    js += "    'Te' : 'rgba(150,155,158,1.0)'," + eol
    js += "    'I' : 'rgba(95,98,105,1.0)'," + eol
    js += "    'Xe' : 'rgba(0,0,255,1.0)'," + eol
    js += "    'Cs' : 'rgba(167,170,175,1.0)'," + eol
    js += "    'Ba' : 'rgba(62,71,86,1.0)'," + eol
    js += "    'La' : 'rgba(196,184,172,1.0)'," + eol
    js += "    'Ce' : 'rgba(110,101,94,1.0)'," + eol
    js += "    'Pr' : 'rgba(96,91,97,1.0)'," + eol
    js += "    'Nd' : 'rgba(156,154,155,1.0)'," + eol
    js += "    'Pm' : 'rgba(102,102,102,1.0)'," + eol
    js += "    'Sm' : 'rgba(136,117,100,1.0)'," + eol
    js += "    'Eu' : 'rgba(217,213,204,1.0)'," + eol
    js += "    'Gd' : 'rgba(119,129,105,1.0)'," + eol
    js += "    'Tb' : 'rgba(236,241,235,1.0)'," + eol
    js += "    'Dy' : 'rgba(134,121,102,1.0)'," + eol
    js += "    'Ho' : 'rgba(131,123,121,1.0)'," + eol
    js += "    'Er' : 'rgba(177,182,175,1.0)'," + eol
    js += "    'Tm' : 'rgba(168,163,160,1.0)'," + eol
    js += "    'Yb' : 'rgba(0,255,0,1.0)'," + eol
    js += "    'Lu' : 'rgba(160,161,153,1.0)'," + eol
    js += "    'Hf' : 'rgba(171,188,178,1.0)'," + eol
    js += "    'Ta' : 'rgba(154,155,160,1.0)'," + eol
    js += "    'W' : 'rgba(60,0,255,1.0)'," + eol
    js += "    'Re' : 'rgba(123,123,121,1.0)'," + eol
    js += "    'Os' : 'rgba(185,196,200,1.0)'," + eol
    js += "    'Ir' : 'rgba(137,130,112,1.0)'," + eol
    js += "    'Pt' : 'rgba(210,211,205,1.0)'," + eol
    js += "    'Au' : 'rgba(203,152,53,1.0)'," + eol
    js += "    'Hg' : 'rgba(80,46,48,1.0)'," + eol
    js += "    'Tl' : 'rgba(143,141,142,1.0)'," + eol
    js += "    'Pb' : 'rgba(81,81,81,1.0)'," + eol
    js += "    'Bi' : 'rgba(114,106,103,1.0)'," + eol
    js += "    'Po' : 'rgba(139,153,164,1.0)'," + eol
    js += "    'At' : 'rgba(102,102,102,1.0)'," + eol
    js += "    'Rn' : 'rgba(71,132,0,1.0)'," + eol
    js += "    'Fr' : 'rgba(102,102,102,1.0)'," + eol
    js += "    'Ra' : 'rgba(156,152,125,1.0)'," + eol
    js += "    'Ac' : 'rgba(66,73,224,1.0)'," + eol
    js += "    'Th' : 'rgba(80,73,65,1.0)'," + eol
    js += "    'Pa' : 'rgba(154,147,92,1.0)'," + eol
    js += "    'U' : 'rgba(120,122,119,1.0)'," + eol
    js += "    'Np' : 'rgba(90,73,53,1.0)'," + eol
    js += "    'Pu' : 'rgba(200,200,200,1.0)'," + eol
    js += "    'Am' : 'rgba(117,80,28,1.0)'," + eol
    js += "    'Cm' : 'rgba(62,65,58,1.0)'," + eol
    js += "    'Bk' : 'rgba(208,208,208,1.0)'," + eol
    js += "    'Cf' : 'rgba(231,231,231,1.0)'," + eol
    js += "    'Es' : 'rgba(59,163,200,1.0)'," + eol
    js += "    'Fm' : 'rgba(102,102,102,1.0)'," + eol
    js += "    'Md' : 'rgba(102,102,102,1.0)'," + eol
    js += "    'No' : 'rgba(102,102,102,1.0)'," + eol
    js += "    'Lr' : 'rgba(102,102,102,1.0)'," + eol
    js += "    'Rf' : 'rgba(102,102,102,1.0)'," + eol
    js += "    'Db' : 'rgba(102,102,102,1.0)'," + eol
    js += "    'Sg' : 'rgba(102,102,102,1.0)'," + eol
    js += "    'Bh' : 'rgba(102,102,102,1.0)'," + eol
    js += "    'Hs' : 'rgba(102,102,102,1.0)'," + eol
    js += "    'Mt' : 'rgba(102,102,102,1.0)'," + eol
    js += "  };" + eol
    js += "  if (molecule in jcpk) {" + eol
    js += "    return jcpk[molecule];" + eol
    js += "  } else if (Number.isInteger(molecule) && molecule < Object.keys(jcpk).length) {" + eol
    js += "    return jcpk[Object.keys(jcpk)[molecule]];" + eol
    js += "  } else {" + eol
    js += "    molecule = component.props.getAtomLabel(component, molecule);" + eol
    js += "    if (molecule in jcpk) {" + eol
    js += "      return jcpk[molecule];" + eol
    js += "    } else {" + eol
    js += "      return '#000';" + eol
    js += "    }" + eol
    js += "  }" + eol
    js += "}" + eol

    component.addPropVariable("getColor", {"type":"func", "defaultValue": js})    
    return {
      "type": "propCall2",
      "calls": "getColor",
      "args": ['self', '[]']
    }     

  def getAtomName(tp, component, *args, **kwargs):  
    eol = "\n"        
    js = ""
    js += "(component, molecule) => {" + eol
    js += "  var names = {" + eol
    js += "    'H' : 'Hydrogen'," + eol
    js += "    'He' : 'Helium'," + eol
    js += "    'Li' : 'Lithium'," + eol
    js += "    'Be' : 'Beryllium'," + eol
    js += "    'B' : 'Boron'," + eol
    js += "    'C' : 'Carbon'," + eol
    js += "    'N' : 'Nitrogen'," + eol
    js += "    'O' : 'Oxygen'," + eol
    js += "    'F' : 'Fluorine'," + eol
    js += "    'Ne' : 'Neon'," + eol
    js += "    'Na' : 'Sodium'," + eol
    js += "    'Mg' : 'Magnesium'," + eol
    js += "    'Al' : 'Aluminium'," + eol
    js += "    'Si' : 'Silicon'," + eol
    js += "    'P' : 'Phosphorus'," + eol
    js += "    'S' : 'Sulfur'," + eol
    js += "    'Cl' : 'Chlorine'," + eol
    js += "    'Ar' : 'Argon'," + eol
    js += "    'K' : 'Potassium'," + eol
    js += "    'Ca' : 'Calcium'," + eol
    js += "    'Sc' : 'Scandium'," + eol
    js += "    'Ti' : 'Titanium'," + eol
    js += "    'V' : 'Vanadium'," + eol
    js += "    'Cr' : 'Chromium'," + eol
    js += "    'Mn' : 'Manganese'," + eol
    js += "    'Fe' : 'Iron'," + eol
    js += "    'Co' : 'Cobalt'," + eol
    js += "    'Ni' : 'Nickel'," + eol
    js += "    'Cu' : 'Copper'," + eol
    js += "    'Zn' : 'Zinc'," + eol
    js += "    'Ga' : 'Gallium'," + eol
    js += "    'Ge' : 'Germanium'," + eol
    js += "    'As' : 'Arsenic'," + eol
    js += "    'Se' : 'Selenium'," + eol
    js += "    'Br' : 'Bromine'," + eol
    js += "    'Kr' : 'Krypton'," + eol
    js += "    'Rb' : 'Rubidium'," + eol
    js += "    'Sr' : 'Strontium'," + eol
    js += "    'Y' : 'Yttrium'," + eol
    js += "    'Zr' : 'Zirconium'," + eol
    js += "    'Nb' : 'Niobium'," + eol
    js += "    'Mo' : 'Molybdenum'," + eol
    js += "    'Tc' : 'Technetium'," + eol
    js += "    'Ru' : 'Ruthenium'," + eol
    js += "    'Rh' : 'Rhodium'," + eol
    js += "    'Pd' : 'Palladium'," + eol
    js += "    'Ag' : 'Silver'," + eol
    js += "    'Cd' : 'Cadmium'," + eol
    js += "    'In' : 'Indium'," + eol
    js += "    'Sn' : 'Tin'," + eol
    js += "    'Sb' : 'Antimony'," + eol
    js += "    'Te' : 'Tellurium'," + eol
    js += "    'I' : 'Iodine'," + eol
    js += "    'Xe' : 'Xenon'," + eol
    js += "    'Cs' : 'Caesium'," + eol
    js += "    'Ba' : 'Barium'," + eol
    js += "    'La' : 'Lanthanum'," + eol
    js += "    'Ce' : 'Cerium'," + eol
    js += "    'Pr' : 'Praseodymium'," + eol
    js += "    'Nd' : 'Neodymium'," + eol
    js += "    'Pm' : 'Promethium'," + eol
    js += "    'Sm' : 'Samarium'," + eol
    js += "    'Eu' : 'Europium'," + eol
    js += "    'Gd' : 'Gadolinium'," + eol
    js += "    'Tb' : 'Terbium'," + eol
    js += "    'Dy' : 'Dysprosium'," + eol
    js += "    'Ho' : 'Holmium'," + eol
    js += "    'Er' : 'Erbium'," + eol
    js += "    'Tm' : 'Thulium'," + eol
    js += "    'Yb' : 'Ytterbium'," + eol
    js += "    'Lu' : 'Lutetium'," + eol
    js += "    'Hf' : 'Hafnium'," + eol
    js += "    'Ta' : 'Tantalum'," + eol
    js += "    'W' : 'Tungsten'," + eol
    js += "    'Re' : 'Rhenium'," + eol
    js += "    'Os' : 'Osmium'," + eol
    js += "    'Ir' : 'Iridium'," + eol
    js += "    'Pt' : 'Platinum'," + eol
    js += "    'Au' : 'Gold'," + eol
    js += "    'Hg' : 'Mercury'," + eol
    js += "    'Tl' : 'Thallium'," + eol
    js += "    'Pb' : 'Lead'," + eol
    js += "    'Bi' : 'Bismuth'," + eol
    js += "    'Po' : 'Polonium'," + eol
    js += "    'At' : 'Astatine'," + eol
    js += "    'Rn' : 'Radon'," + eol
    js += "    'Fr' : 'Francium'," + eol
    js += "    'Ra' : 'Radium'," + eol
    js += "    'Ac' : 'Actinium'," + eol
    js += "    'Th' : 'Thorium'," + eol
    js += "    'Pa' : 'Protactinium'," + eol
    js += "    'U' : 'Uranium'," + eol
    js += "    'Np' : 'Neptunium'," + eol
    js += "    'Pu' : 'Plutonium'," + eol
    js += "    'Am' : 'Americium'," + eol
    js += "    'Cm' : 'Curium'," + eol
    js += "    'Bk' : 'Berkelium'," + eol
    js += "    'Cf' : 'Californium'," + eol
    js += "    'Es' : 'Einsteinium'," + eol
    js += "    'Fm' : 'Fermium'," + eol
    js += "    'Md' : 'Mendelevium'," + eol
    js += "    'No' : 'Nobelium'," + eol
    js += "    'Lr' : 'Lawrencium'," + eol
    js += "    'Rf' : 'Rutherfordium'," + eol
    js += "    'Db' : 'Dubnium'," + eol
    js += "    'Sg' : 'Seaborgium'," + eol
    js += "    'Bh' : 'Bohrium'," + eol
    js += "    'Hs' : 'Hassium'," + eol
    js += "    'Mt' : 'Meitnerium'" + eol
    js += "  };" + eol
    js += "  if (molecule in names) {" + eol
    js += "    return names[molecule];" + eol
    js += "  } else if (Number.isInteger(molecule) && molecule <= Object.keys(names).length) {" + eol
    js += "    return names[Object.keys(names)[molecule-1]];" + eol
    js += "  } else {" + eol
    js += "    return '';" + eol
    js += "  }" + eol
    js += "}" + eol

    component.addPropVariable("getAtomName", {"type":"func", "defaultValue": js})    
    return {
      "type": "propCall2",
      "calls": "getAtomName",
      "args": ['self', '[]']
    }     

  def getAtomLabel(tp, component, *args, **kwargs):  
    eol = "\n"        
    js = ""
    js += "(component, molecule) => {" + eol
    js += "  var labels = {" + eol
    js += "    'Hydrogen':'H'," + eol
    js += "    'Helium':'He'," + eol
    js += "    'Lithium':'Li'," + eol
    js += "    'Beryllium':'Be'," + eol
    js += "    'Boron':'B'," + eol
    js += "    'Carbon':'C'," + eol
    js += "    'Nitrogen':'N'," + eol
    js += "    'Oxygen':'O'," + eol
    js += "    'Fluorine':'F'," + eol
    js += "    'Neon':'Ne'," + eol
    js += "    'Sodium':'Na'," + eol
    js += "    'Magnesium':'Mg'," + eol
    js += "    'Aluminium':'Al'," + eol
    js += "    'Silicon':'Si'," + eol
    js += "    'Phosphorus':'P'," + eol
    js += "    'Sulfur':'S'," + eol
    js += "    'Chlorine':'Cl'," + eol
    js += "    'Argon':'Ar'," + eol
    js += "    'Potassium':'K'," + eol
    js += "    'Calcium':'Ca'," + eol
    js += "    'Scandium':'Sc'," + eol
    js += "    'Titanium':'Ti'," + eol
    js += "    'Vanadium':'V'," + eol
    js += "    'Chromium':'Cr'," + eol
    js += "    'Manganese':'Mn'," + eol
    js += "    'Iron':'Fe'," + eol
    js += "    'Cobalt':'Co'," + eol
    js += "    'Nickel':'Ni'," + eol
    js += "    'Copper':'Cu'," + eol
    js += "    'Zinc':'Zn'," + eol
    js += "    'Gallium':'Ga'," + eol
    js += "    'Germanium':'Ge'," + eol
    js += "    'Arsenic':'As'," + eol
    js += "    'Selenium':'Se'," + eol
    js += "    'Bromine':'Br'," + eol
    js += "    'Krypton':'Kr'," + eol
    js += "    'Rubidium':'Rb'," + eol
    js += "    'Strontium':'Sr'," + eol
    js += "    'Yttrium':'Y'," + eol
    js += "    'Zirconium':'Zr'," + eol
    js += "    'Niobium':'Nb'," + eol
    js += "    'Molybdenum':'Mo'," + eol
    js += "    'Technetium':'Tc'," + eol
    js += "    'Ruthenium':'Ru'," + eol
    js += "    'Rhodium':'Rh'," + eol
    js += "    'Palladium':'Pd'," + eol
    js += "    'Silver':'Ag'," + eol
    js += "    'Cadmium':'Cd'," + eol
    js += "    'Indium':'In'," + eol
    js += "    'Tin':'Sn'," + eol
    js += "    'Antimony':'Sb'," + eol
    js += "    'Tellurium':'Te'," + eol
    js += "    'Iodine':'I'," + eol
    js += "    'Xenon':'Xe'," + eol
    js += "    'Caesium':'Cs'," + eol
    js += "    'Barium':'Ba'," + eol
    js += "    'Lanthanum':'La'," + eol
    js += "    'Cerium':'Ce'," + eol
    js += "    'Praseodymium':'Pr'," + eol
    js += "    'Neodymium':'Nd'," + eol
    js += "    'Promethium':'Pm'," + eol
    js += "    'Samarium':'Sm'," + eol
    js += "    'Europium':'Eu'," + eol
    js += "    'Gadolinium':'Gd'," + eol
    js += "    'Terbium':'Tb'," + eol
    js += "    'Dysprosium':'Dy'," + eol
    js += "    'Holmium':'Ho'," + eol
    js += "    'Erbium':'Er'," + eol
    js += "    'Thulium':'Tm'," + eol
    js += "    'Ytterbium':'Yb'," + eol
    js += "    'Lutetium':'Lu'," + eol
    js += "    'Hafnium':'Hf'," + eol
    js += "    'Tantalum':'Ta'," + eol
    js += "    'Tungsten':'W'," + eol
    js += "    'Rhenium':'Re'," + eol
    js += "    'Osmium':'Os'," + eol
    js += "    'Iridium':'Ir'," + eol
    js += "    'Platinum':'Pt'," + eol
    js += "    'Gold':'Au'," + eol
    js += "    'Mercury':'Hg'," + eol
    js += "    'Thallium':'Tl'," + eol
    js += "    'Lead':'Pb'," + eol
    js += "    'Bismuth':'Bi'," + eol
    js += "    'Polonium':'Po'," + eol
    js += "    'Astatine':'At'," + eol
    js += "    'Radon':'Rn'," + eol
    js += "    'Francium':'Fr'," + eol
    js += "    'Radium':'Ra'," + eol
    js += "    'Actinium':'Ac'," + eol
    js += "    'Thorium':'Th'," + eol
    js += "    'Protactinium':'Pa'," + eol
    js += "    'Uranium':'U'," + eol
    js += "    'Neptunium':'Np'," + eol
    js += "    'Plutonium':'Pu'," + eol
    js += "    'Americium':'Am'," + eol
    js += "    'Curium':'Cm'," + eol
    js += "    'Berkelium':'Bk'," + eol
    js += "    'Californium':'Cf'," + eol
    js += "    'Einsteinium':'Es'," + eol
    js += "    'Fermium':'Fm'," + eol
    js += "    'Mendelevium':'Md'," + eol
    js += "    'Nobelium':'No'," + eol
    js += "    'Lawrencium':'Lr'," + eol
    js += "    'Rutherford:':'Rf'," + eol
    js += "    'Dubnium':'Db'," + eol
    js += "    'Seaborgium':'Sg'," + eol
    js += "    'Bohrium':'Bh'," + eol
    js += "    'Hassium':'Hs'," + eol
    js += "    'Meitnerium':'M'," + eol
    js += "  };" + eol
    js += "  if (molecule in labels) {" + eol
    js += "    return labels[molecule];" + eol
    js += "  } else if (Number.isInteger(molecule) && molecule <= Object.keys(labels).length) {" + eol
    js += "    return labels[Object.keys(labels)[molecule-1]];" + eol
    js += "  } else {" + eol
    js += "    return molecule;" + eol
    js += "  }" + eol
    js += "}" + eol

    component.addPropVariable("getAtomLabel", {"type":"func", "defaultValue": js})    
    return {
      "type": "propCall2",
      "calls": "getAtomLabel",
      "args": ['self', '[]']
    }     

  def getMolecule(tp, component, *args, **kwargs):  
    RapptureBuilder.getText(tp, component)        
    RapptureBuilder.getColor(tp, component)        
    RapptureBuilder.getAtomName(tp, component)        
    eol = "\n"        
    js = ""
    js += "(component, molecule) => {" + eol
    js += "  var atoms = {};" + eol
    js += "  var connections = {};" + eol
    js += "  var pdb = molecule.querySelectorAll('pdb');" + eol
    js += "  if (pdb.length>0){" + eol
    js += "    let pdbt = component.props.getText(component, pdb[0], []);" + eol
    js += "    lines = pdbt.split('\\n');" + eol
    js += "    lines.forEach((line)=>{" + eol
    js += "      if (line.startsWith('ATOM')){" + eol
    js += "        var cols = line.split(/[\s]+/);" + eol
    js += "        var x_atom = parseFloat(cols[5]);" + eol
    js += "        var y_atom = parseFloat(cols[6]);" + eol
    js += "        var z_atom = parseFloat(cols[7]);" + eol
    js += "        var c_atom = component.props.getColor(component, cols[2]);" + eol
    js += "        var n_atom = component.props.getAtomName(component, cols[2]);" + eol
    js += "        var id_atom = parseInt(cols[1]);" + eol
    js += "        atoms[id_atom] = [x_atom,y_atom,z_atom, n_atom,c_atom, 'enabled'];" + eol
    js += "      } else if (line.startsWith('CONECT')){" + eol
    js += "        cols = line.split(/[\s]+/);" + eol
    js += "        var id_atom = parseInt(cols[1]);" + eol
    js += "        connections[id_atom] = cols.slice(1).map((c)=>{ return parseInt(c)});" + eol
    js += "      }" + eol
    js += "    });" + eol
    js += "  } else { " + eol
    js += "    let vtk = molecule.querySelectorAll('vtk')" + eol
    js += "    if (vtk.length>0){" + eol
    js += "      let vtkt = component.props.getText(component, vtk[0], []);" + eol
    js += "      var lines = vtkt.split('\\n');" + eol
    js += "      var i=0;" + eol
    js += "      var points = [];" + eol
    js += "      var vertices = [];" + eol
    js += "      while (i < lines.length){" + eol
    js += "        var line = lines[i];" + eol
    js += "        if (line.startsWith('POINTS')){" + eol
    js += "          let tpoints = parseInt(line.split(/[\s]+/)[1]);" + eol
    js += "          for (var ii=0; ii<Math.ceil(tpoints/3);ii++){" + eol
    js += "            var i = i+1;" + eol
    js += "            line = lines[i];" + eol
    js += "            let pp = line.split(/[\s]+/);" + eol
    js += "            if (points.length < tpoints) {" + eol
    js += "              points.push([parseFloat(pp[0]),parseFloat(pp[1]),parseFloat(pp[2])])" + eol
    js += "            } if (points.length < tpoints) {" + eol
    js += "              points.push([parseFloat(pp[3]),parseFloat(pp[4]),parseFloat(pp[5])])" + eol
    js += "            } if (points.length < tpoints) {" + eol
    js += "              points.push([parseFloat(pp[6]),parseFloat(pp[7]),parseFloat(pp[8])])" + eol
    js += "            }" + eol
    js += "          }" + eol
    js += "        } else if (line.startsWith('VERTICES')){" + eol
    js += "          var tvert = parseInt(line.split(/[\s]+/)[1])" + eol
    js += "          for (var ii=0; ii<tvert; ii++){" + eol
    js += "            i = i+1;" + eol  
    js += "            line = lines[i];" + eol
    js += "            let pp = line.split(/[\s]+/);" + eol
    js += "            pp = pp.map((p)=>{return parseInt(p)});" + eol
    js += "            atoms[pp[1]] = [points[ii][0],points[ii][1],points[ii][2], 'Si', 'rgb(240,200,160)', 'enabled'];" + eol
    js += "          }" + eol
    js += "          for (var j=0; j < points.lenght; j++){" + eol
    js += "            var point =  points[j];" + eol
    js += "            if (!(j in atoms)){" + eol
    js += "              atoms[j] = [point[0],point[1],point[2], '', 'rgb(0,0,0)', 'disabled'];" + eol
    js += "            }" + eol
    js += "          }" + eol
    js += "        } else if (line.startsWith('LINES')){" + eol
    js += "          let tlines = parseInt(line.split(/[\s]+/)[1])" + eol
    js += "          for (var ii=0; ii<tlines; ii++){" + eol
    js += "            i = i+1" + eol             
    js += "            line = lines[i]" + eol
    js += "            let pp = line.split(/[\s]+/)" + eol
    js += "            pp = pp.map((p)=>{return parseInt(p)});" + eol
    js += "            if (pp[1] in connections){" + eol
    js += "              connections[pp[1]].push(pp[2]);" + eol
    js += "            }else{" + eol
    js += "              connections[pp[1]] = [pp[2]];" + eol
    js += "            }" + eol
    js += "          }" + eol
    js += "        } else if (line.startsWith('atom_type')){" + eol
    js += "          let ttype = parseInt(line.split(/[\s]+/)[2]);" + eol
    js += "          for (var ii=0; ii<Math.ceil(ttype/9);ii++) {" + eol
    js += "            i = i+1;" + eol 
    js += "            line = lines[i];" + eol
    js += "            let pp = line.split(/[\s]+/);" + eol
    js += "            pp = pp.map((p)=>{return parseInt(p)});" + eol
    js += "            for (var k=0; k<9; k++){" + eol
    js += "              let atom_id = (9*ii+k);" + eol
    js += "              if (atom_id in atoms && component.props.getColor(component, pp[k])){" + eol
    js += "                atoms[atom_id][3] = component.props.getAtomName(component, pp[k]);" + eol
    js += "                atoms[atom_id][4] = component.props.getColor(component, pp[k]);" + eol
    js += "              }" + eol
    js += "            }" + eol
    js += "          }" + eol
    js += "        }" + eol
    js += "        i = i+1;" + eol
    js += "      }" + eol
    js += "    }" + eol
    js += "  }" + eol
    js += "  return {'atoms' : atoms, 'connections' : connections};" + eol
    js += "}" + eol

    component.addPropVariable("getMolecule", {"type":"func", "defaultValue": js})    
    return {
      "type": "propCall2",
      "calls": "getMolecule",
      "args": ['self', '[]']
    }     


  def buildBasis(tp, component, *args, **kwargs):   

    eol = "\n"
    js = ""
    js += "(component, molecule, r_x, r_y,r_z) => {" + eol
    js += "  let atoms_basis = component.state.atoms;" + eol
    js += "  var atoms_set = {}" + eol
    js += "  atoms_basis.forEach((atom)=>{" + eol
    js += "    let key = ((parseFloat(atom[0]))*10).toFixed(3)+'_'+((parseFloat(atom[1]))*10).toFixed(3)+'_'+((parseFloat(atom[2]))*10).toFixed(3);" + eol
    js += "    if (!(key in atoms_set))" + eol
    js += "      atoms_set[key] = {'coord' : atom.slice(0,3).map((e,i)=>{return (e)*10}), 'connection': new Set(), 'type' : atom[3], 'color': atom[4]};" + eol
    js += "  });" + eol
    js += "  let atoms0 = molecule.atoms;" + eol    
    js += "  var maxr = 0;" + eol    
    js += "  Object.keys(molecule.connections).forEach((atom1)=>{" + eol
    js += "    let connection = molecule.connections[atom1];" + eol    
    js += "    connection.forEach((atom2)=>{" + eol    
    js += "      let at1 = atoms0[atom1];" + eol  
    js += "      let x1 = (parseFloat(at1[0]));" + eol    
    js += "      let y1 = (parseFloat(at1[1]));" + eol    
    js += "      let z1 = (parseFloat(at1[2]));" + eol    
    js += "      let k1 = x1.toFixed(3) +'_'+y1.toFixed(3)+'_'+z1.toFixed(3);" + eol        
    js += "      let at2 = atoms0[atom2];" + eol  
    js += "      let x2 = (parseFloat(at2[0]));" + eol    
    js += "      let y2 = (parseFloat(at2[1]));" + eol    
    js += "      let z2 = (parseFloat(at2[2]));" + eol    
    js += "      let k2 = x2.toFixed(3) +'_'+y2.toFixed(3)+'_'+z2.toFixed(3);" + eol        
    js += "      let dist = Math.hypot(x1-x2, y1-y2, z1-z2, );" + eol    
    js += "      if ( dist > maxr){" + eol    
    js += "        maxr = dist;" + eol
    js += "      }" + eol    
    js += "    });" + eol    
    js += "  });" + eol
    js += "  var maxr = maxr + 0.0001;" + eol
    js += "  var crystal_set = {}" + eol
    js += "  let vec = component.state.vectors;" + eol    
    js += "  for (var ii=0 ; ii<r_x; ii++){" + eol
    js += "    for (var jj=0 ; jj<r_y; jj++){" + eol
    js += "      for (var kk=0 ; kk<r_z; kk++){" + eol
    js += "        for (let ias in atoms_set){" + eol
    js += "          let value = atoms_set[ias];" + eol
    js += "          let x0 = value.coord[0] + (ii*vec[0][0] + jj*vec[1][0] + kk*vec[2][0])*10;" + eol
    js += "          let y0 = value.coord[1] + (ii*vec[0][1] + jj*vec[1][1] + kk*vec[2][1])*10;" + eol
    js += "          let z0 = value.coord[2] + (ii*vec[0][2] + jj*vec[1][2] + kk*vec[2][2])*10;" + eol
    js += "          let k0 = parseFloat(x0).toFixed(3)+'_'+parseFloat(y0).toFixed(3)+'_'+parseFloat(z0).toFixed(3);" + eol   
    js += "          if (!(k0 in crystal_set)){" + eol
    js += "            crystal_set[k0] = {'coord':[x0,y0,z0],'connection':[],'type':value.type,'color':value.color };" + eol 
    js += "          }" + eol
    js += "        }" + eol
    js += "      }" + eol
    js += "    }" + eol
    js += "  }" + eol    
    js += "  var crystal_ids = {}" + eol    
    js += "  var connection_ids = {}" + eol    
    js += "  Object.keys(crystal_set).forEach((c, i)=>{" + eol  
    js += "    crystal_ids[c] = i;" + eol  
    js += "  });" + eol    
    js += "  let ids_set = Object.keys(crystal_set);" + eol     
    js += "  ids_set.forEach((c, i)=>{" + eol    
    js += "    let atm1 = crystal_set[c];" + eol    
    js += "    crystal_set[c].connection = ids_set.map((c2, i2)=>{" + eol   
    js += "      let atm2 = crystal_set[c2];" + eol    
    js += "      if(i2<=i)" + eol    
    js += "        return undefined;" + eol 
    js += "      if(atm1.coord[0] - atm2.coord[0] > maxr|| atm1.coord[0]-atm2.coord[0] < -maxr)" + eol    
    js += "        return undefined;" + eol 
    js += "      if(atm1.coord[1] - atm2.coord[1] > maxr|| atm1.coord[1]-atm2.coord[1] < -maxr)" + eol    
    js += "        return undefined;" + eol 
    js += "      if(atm1.coord[2] - atm2.coord[2] > maxr|| atm1.coord[2]-atm2.coord[2] < -maxr)" + eol    
    js += "        return undefined;" + eol 
    js += "      let dist = Math.hypot(atm1.coord[0]-atm2.coord[0], atm1.coord[1]-atm2.coord[1], atm1.coord[2]-atm2.coord[2]);" + eol    
    js += "      if(dist < maxr && dist > 0){" + eol    
    js += "        return i2;" + eol 
    js += "      }" + eol    
    js += "    }).filter ((e)=>{return e!=undefined;});" + eol     
    js += "  });" + eol 
    js += "  molecule = { atoms: {}, connections:{} }" + eol
    js += "  Object.keys(crystal_set).forEach((c, i)=>{" + eol    
    js += "    let atm = crystal_set[c];" + eol    
    js += "    molecule.atoms[crystal_ids[c]] = [atm.coord[0],atm.coord[1],atm.coord[2],atm.type,atm.color,'enabled'];" + eol   
    js += "    molecule.connections[i] = atm.connection;" + eol    
    js += "  });" + eol
    js += "  return molecule;" + eol
    js += "}" + eol  
    
    component.addPropVariable("buildBasis", {"type":"func", "defaultValue": js})    
    return {
      "type": "propCall2",
      "calls": "buildBasis",
      "args": ['self', '[]']
    }    

  def buildCrystal(tp, component, *args, **kwargs):   

    eol = "\n"
    js = ""
    js += "(component, molecule, r_x, r_y,r_z) => {" + eol
    js += "  let atoms_basis = component.state.atoms;" + eol
    js += "  var atoms_set = {};" + eol
    js += "  atoms_basis.forEach((atom)=>{" + eol
    js += "    let key = ((parseFloat(atom[0]))*10).toFixed(3)+'_'+((parseFloat(atom[1]))*10).toFixed(3)+'_'+((parseFloat(atom[2]))*10).toFixed(3);" + eol
    js += "    if (!(key in atoms_set))" + eol
    js += "      atoms_set[key] = {'coord' : atom.slice(0,3).map((e,i)=>{return (e)*10}), 'connection': new Set(), 'type' : atom[3], 'color': atom[4]};" + eol
    js += "  });" + eol
    js += "  let atoms0 = molecule.atoms;" + eol    
    js += "  var maxr = 0;" + eol    
    js += "  Object.keys(molecule.connections).forEach((atom1)=>{" + eol
    js += "    let connection = molecule.connections[atom1];" + eol    
    js += "    connection.forEach((atom2)=>{" + eol    
    js += "      let at1 = atoms0[atom1];" + eol  
    js += "      let x1 = (parseFloat(at1[0]));" + eol    
    js += "      let y1 = (parseFloat(at1[1]));" + eol    
    js += "      let z1 = (parseFloat(at1[2]));" + eol    
    js += "      let k1 = x1.toFixed(3) +'_'+y1.toFixed(3)+'_'+z1.toFixed(3);" + eol        
    js += "      let at2 = atoms0[atom2];" + eol  
    js += "      let x2 = (parseFloat(at2[0]));" + eol    
    js += "      let y2 = (parseFloat(at2[1]));" + eol    
    js += "      let z2 = (parseFloat(at2[2]));" + eol    
    js += "      let k2 = x2.toFixed(3) +'_'+y2.toFixed(3)+'_'+z2.toFixed(3);" + eol        
    js += "      let dist = Math.hypot(x1-x2, y1-y2, z1-z2, );" + eol    
    js += "      if ( dist > maxr){" + eol    
    js += "        maxr = dist;" + eol
    js += "      }" + eol    
    js += "    });" + eol    
    js += "  });" + eol
    js += "  var maxr = maxr + 0.0001;" + eol
    js += "  var crystal_set = {}" + eol
    js += "  let ivec = component.state.ivectors.map((e)=>{return e.map((d)=>{return parseFloat(d);});});" + eol    
    js += "  let vec = component.state.vectors.map((e)=>{return e.map((d)=>{return parseFloat(d);});});" + eol  
    js += "  var a = [r_x,r_y,r_z];" + eol
    js += "  let x0 = a[0];//(a[0]*ivec[0][0] + a[1]*ivec[1][0] + a[2]*ivec[2][0]);" + eol
    js += "  let y0 = a[1];//(a[0]*ivec[0][1] + a[1]*ivec[1][1] + a[2]*ivec[2][1]);" + eol
    js += "  let z0 = a[2];//(a[0]*ivec[0][2] + a[1]*ivec[1][2] + a[2]*ivec[2][2]);" + eol
    js += "  let minv = [0,1,2].map((i)=>{return math.min(0, vec[0][i],vec[1][i],vec[2][i]);});" + eol
    js += "  let maxv = [0,1,2].map((i)=>{return math.max(0, vec[0][i],vec[1][i],vec[2][i]);});" + eol
    js += "  let dimv = [maxv[0]-minv[0],maxv[1]-minv[1],maxv[2]-minv[2]];" + eol
    
    #js += "  let x1 = dimv[0];" + eol
    #js += "  let y1 = dimv[1];" + eol
    #js += "  let z1 = dimv[2];" + eol
    
    js += "  let x1 = maxv[0];" + eol
    js += "  let y1 = maxv[1];" + eol
    js += "  let z1 = maxv[2];" + eol
    
    #js += "  let x1 = (vec[0][0] + vec[1][0] + vec[2][0]);" + eol
    #js += "  let y1 = (vec[0][1] + vec[1][1] + vec[2][1]);" + eol
    #js += "  let z1 = (vec[0][2] + vec[1][2] + vec[2][2]);" + eol

    
    js += "  if (x1==0) x1=1;" + eol
    js += "  if (y1==0) y1=1;" + eol
    js += "  if (z1==0) z1=1;" + eol
    js += "  let ncx = Math.abs(Math.ceil(x0/x1));" + eol
    js += "  if (ncx>100) ncx=100;" + eol
    js += "  let ncy = Math.abs(Math.ceil(y0/y1));" + eol
    js += "  if (ncy>100) ncy=100;" + eol
    js += "  let ncz = Math.abs(Math.ceil(z0/z1));" + eol
    js += "  if (ncz>100) ncz=100;" + eol
    js += "  ncz = ncz*5;" + eol #No IDEA why, but works #TODO
    js += "  for (var ii=-ncx ; ii<=ncx; ii++){" + eol
    js += "    for (var jj=-ncy ; jj<=ncy; jj++){" + eol
    js += "      for (var kk=-ncz ; kk<=ncz; kk++){" + eol
    js += "        for (let ias in atoms_set){" + eol
    js += "          let value = atoms_set[ias];" + eol
    js += "          let x0 = value.coord[0] + (ii*vec[0][0] + jj*vec[1][0] + kk*vec[2][0])*10;" + eol
    js += "          let y0 = value.coord[1] + (ii*vec[0][1] + jj*vec[1][1] + kk*vec[2][1])*10;" + eol
    js += "          let z0 = value.coord[2] + (ii*vec[0][2] + jj*vec[1][2] + kk*vec[2][2])*10;" + eol
    js += "          if (x0 >= -0.0001 && y0 >= -0.0001 && z0 >= -0.0001 && x0 < r_x*10 +0.0001 && y0 < r_y*10 +0.0001 && z0 < r_z*10+0.0001){" + eol
    js += "            let k0 = parseFloat(x0).toFixed(3)+'_'+parseFloat(y0).toFixed(3)+'_'+parseFloat(z0).toFixed(3);" + eol   
    js += "            if (!(k0 in crystal_set)){" + eol
    js += "              crystal_set[k0] = {'coord':[x0,y0,z0],'connection':[],'type':value.type,'color':value.color };" + eol 
    js += "            }" + eol
    js += "          }" + eol
    js += "        }" + eol
    js += "      }" + eol
    js += "    }" + eol
    js += "  }" + eol    
    js += "  var crystal_ids = {}" + eol    
    js += "  var connection_ids = {}" + eol    
    js += "  Object.keys(crystal_set).forEach((c, i)=>{" + eol  
    js += "    crystal_ids[c] = i;" + eol  
    js += "  });" + eol    
    js += "  let ids_set = Object.keys(crystal_set);" + eol     
    js += "  ids_set.forEach((c, i)=>{" + eol    
    js += "    let atm1 = crystal_set[c];" + eol    
    js += "    crystal_set[c].connection = ids_set.map((c2, i2)=>{" + eol   
    js += "      let atm2 = crystal_set[c2];" + eol    
    js += "      if(i2<=i)" + eol    
    js += "        return undefined;" + eol 
    js += "      if(atm1.coord[0] - atm2.coord[0] > maxr|| atm1.coord[0]-atm2.coord[0] < -maxr)" + eol    
    js += "        return undefined;" + eol 
    js += "      if(atm1.coord[1] - atm2.coord[1] > maxr|| atm1.coord[1]-atm2.coord[1] < -maxr)" + eol    
    js += "        return undefined;" + eol 
    js += "      if(atm1.coord[2] - atm2.coord[2] > maxr|| atm1.coord[2]-atm2.coord[2] < -maxr)" + eol    
    js += "        return undefined;" + eol 
    js += "      let dist = Math.hypot(atm1.coord[0]-atm2.coord[0], atm1.coord[1]-atm2.coord[1], atm1.coord[2]-atm2.coord[2]);" + eol    
    js += "      if(dist < maxr && dist > 0){" + eol    
    js += "        return i2;" + eol 
    js += "      }" + eol    
    js += "    }).filter ((e)=>{return e!=undefined;});" + eol     
    js += "  });" + eol 
    js += "  molecule = { atoms: {}, connections:{} }" + eol
    js += "  Object.keys(crystal_set).forEach((c, i)=>{" + eol    
    js += "    let atm = crystal_set[c];" + eol    
    js += "    molecule.atoms[crystal_ids[c]] = [atm.coord[0],atm.coord[1],atm.coord[2],atm.type,atm.color,'enabled'];" + eol   
    js += "    molecule.connections[i] = atm.connection;" + eol    
    js += "  });" + eol
    js += "  return molecule;" + eol
    js += "}" + eol  
    
    component.addPropVariable("buildCrystal", {"type":"func", "defaultValue": js})    
    return {
      "type": "propCall2",
      "calls": "buildCrystal",
      "args": ['self', '[]']
    }  

  def plotDrawingPlotly(tp, component, *args, **kwargs):   
    RapptureBuilder.buildXYPlotly(tp, component)
    RapptureBuilder.getText(tp, component)
    RapptureBuilder.getMolecule(tp, component)
    RapptureBuilder.getColor(tp, component)    
    samples = kwargs.get("samples", 20)
    resize = kwargs.get("resize", 0.15)
    phi = nplinspace(0, 2*nppi, samples)    
    theta = nplinspace(-nppi/2, nppi/2, samples)
    thetat = nplinspace(0,2*nppi,samples)
    linspace = nplinspace(0,1,int(samples/2))
    phit = nplinspace(0,nppi,samples)
    xt = npouter(npcos(thetat),npsin(phit)) * 4 * resize
    yt = npouter(npsin(thetat),npsin(phit)) * 4 * resize
    zt = npouter(npones(samples),npcos(phit)) * 4 * resize  
    cosphi = npcos(phi) * resize
    cosphi[abs(cosphi) < 0.000000000001] = 0.0
    sinphi = npsin(phi) * resize    
    sinphi[abs(sinphi) < 0.000000000001] = 0.0

    eol = "\n"
    js = ""
    js += "(component, sequence, method) => {" + eol
    js += "  var xt_base = "+json.dumps(xt.tolist())+";" + eol
    js += "  var yt_base = "+json.dumps(yt.tolist())+";" + eol
    js += "  var zt_base = "+json.dumps(zt.tolist())+";" + eol
    js += "  var cosphi = "+json.dumps(cosphi.tolist())+";" + eol
    js += "  var sinphi = "+json.dumps(sinphi.tolist())+";" + eol
    js += "  var linspace = "+json.dumps(linspace.tolist())+";" + eol
    js += "  var traces = [];" + eol
    js += "  var layout = {" + eol
    js += "    'scene':{'aspectmode':'data'}, " + eol
    js += "    'margin' : {'l':0,'r':0,'t':0,'b':0}," + eol
    #js += "    'template' : self.theme," + eol
    js += "  };" + eol
    js += "  var min_p = undefined;" + eol
    js += "  var max_p = undefined;" + eol
    js += "  for (var i=0;i<sequence.length;i++){" + eol    
    js += "    var draw = sequence[i];" + eol
    js += "    var label = component.props.getText(component, draw, ['index', 'label'])" + eol
    js += "    var molecules = draw.querySelectorAll('molecule');" + eol    
    js += "    for (var j=0;j<molecules.length;j++){" + eol    
    js += "      var molecule = component.props.getMolecule(component, molecules[i]);" + eol
    js += "      if (method){" + eol
    js += "        molecule = method(component, molecule)" + eol
    js += "      }" + eol
    
    js += "      var colorset = new Set();" + eol
    js += "      Object.values(molecule.atoms).forEach((e)=>{colorset.add(e[3])});" + eol    
    js += "      colorset = [...colorset];" + eol    
    js += "      let xt = {};" + eol
    js += "      let yt = {};" + eol
    js += "      let zt = {};" + eol
    js += "      let st = {};" + eol
    js += "      let color = {};" + eol
    js += "      Object.keys(molecule.atoms).forEach((id)=>{" + eol    
    js += "        var atom = molecule.atoms[id];" + eol
    js += "        if (atom[5] == 'enabled' && !['Helium','Ytterbium','Xenon','Zinc'].includes(atom[3])){" + eol
    js += "          var xv = xt_base.map((e1)=>{return e1.map((e2)=>{return e2 + atom[0]})});" + eol    
    js += "          var yv = yt_base.map((e1)=>{return e1.map((e2)=>{return e2 + atom[1]})});" + eol    
    js += "          var zv = zt_base.map((e1)=>{return e1.map((e2)=>{return e2 + atom[2]})});" + eol
    js += "          if (min_p == undefined || max_p==undefined){" + eol
    js += "            min_p = [atom[0], atom[1], atom[2]];" + eol
    js += "            max_p = [atom[0], atom[1], atom[2]];" + eol
    js += "          } else {" + eol
    js += "            min_p[0] = Math.min(min_p[0], atom[0]);" + eol
    js += "            min_p[1] = Math.min(min_p[1], atom[1]);" + eol
    js += "            min_p[2] = Math.min(min_p[2], atom[2]);" + eol
    js += "            max_p[0] = Math.max(max_p[0], atom[0]);" + eol
    js += "            max_p[1] = Math.max(max_p[1], atom[1]);" + eol
    js += "            max_p[2] = Math.max(max_p[2], atom[2]);" + eol
    js += "          }" + eol
    js += "          xv.push(xv[0].map((ii)=>{return ii}),xv[1].map((ii)=>{return ii}),[]);" + eol
    js += "          yv.push(yv[0].map((ii)=>{return ii}),yv[1].map((ii)=>{return ii}),[]);" + eol
    js += "          zv.push(zv[0].map((ii)=>{return ii}),zv[1].map((ii)=>{return ii}),[]);" + eol
    js += "          if (atom[3] in xt){" + eol
    js += "            xt[atom[3]].push(...xv);" + eol
    js += "            yt[atom[3]].push(...yv);" + eol
    js += "            zt[atom[3]].push(...zv);" + eol
    js += "          } else {" + eol
    js += "            xt[atom[3]] = xv;" + eol
    js += "            yt[atom[3]] = yv;" + eol
    js += "            zt[atom[3]] = zv;" + eol
    js += "          }" + eol
    js += "        }" + eol    
    js += "      });" + eol    
    js += "      min_p = min_p.map((m)=>{return m-"+str(resize*4)+";});" + eol    
    js += "      max_p = max_p.map((m)=>{return m+"+str(resize*4)+";});" + eol    
    js += "      if (component.props.onLoadBoundary){" + eol    
    js += "        component.props.onLoadBoundary(component,[min_p, max_p])" + eol
    js += "      }" + eol   
    
    js += "      var colorscalea = [[0,'rgba(200,0,0,1.0)']];" + eol
    js += "      var cv = [];" + eol
    js += "      var xts = [];" + eol
    js += "      var yts = [];" + eol
    js += "      var zts = [];" + eol
    js += "      var texts = [];" + eol
    js += "      var total_atms = Object.keys(xt).length;" + eol    
    js += "      Object.keys(xt).forEach((atom, i)=>{" + eol    
    js += "        colorscalea.push([(i+1)/(total_atms),component.props.getColor(component, atom)]);" + eol        
    js += "        xt[atom].forEach((x)=>{cv.push(x.map((p)=>{ return (i+1); }));});" + eol        
    js += "        xt[atom].forEach((x)=>{texts.push(x.map((p)=>{ return ''+atom; }));});" + eol        
    js += "        xt[atom].forEach((x)=>{xts.push(x);});" + eol        
    js += "        yt[atom].forEach((y)=>{yts.push(y);});" + eol        
    js += "        zt[atom].forEach((z)=>{zts.push(z);});" + eol        
    js += "      });" + eol    
    js += "      traces.push({" + eol    
    js += "        'type' : 'surface'," + eol    
    js += "        'x' : xts, " + eol    
    js += "        'y' : yts, " + eol    
    js += "        'z' : zts, " + eol    
    js += "        'cauto' : false," + eol    
    js += "        'cmin' : 0," + eol    
    js += "        'cmax' : total_atms," + eol    
    js += "        'hovertext' : texts," + eol    
    js += "        'showscale' : false," + eol    
    js += "        'hoverinfo' : 'text'," + eol    
    js += "        'colorscale' : colorscalea," + eol  
    js += "        'opacity' : 1.0," + eol
    js += "        'surfacecolor' : cv," + eol    
    js += "        'connectgaps' : false," + eol    
    js += "        'lighting' : { " + eol    
    js += "          'specular' : 2 ," + eol    
    js += "          'ambient' : 0.8," + eol    
    js += "          'diffuse' : 1, " + eol    
    js += "          'roughness' : 1, " + eol    
    js += "          'fresnel' : 2.0," + eol    
    js += "        }," + eol    
    js += "      });" + eol    
    
    js += "      xt = {};" + eol
    js += "      yt = {};" + eol
    js += "      zt = {};" + eol
    js += "      st = {};" + eol
    js += "      colorset.forEach((c)=>{" + eol
    js += "        xt[c]=[];" + eol
    js += "        yt[c]=[];" + eol
    js += "        zt[c]=[];" + eol
    js += "        st[c]=[];" + eol
    js += "      });" + eol
    js += "      let atoms = molecule.atoms;" + eol
    js += "      Object.keys(molecule.connections).forEach((atom1)=>{" + eol    
    js += "        let connection = molecule.connections[atom1];" + eol    
    js += "        connection.forEach((atom2)=>{" + eol    
    js += "          var at1 = atom1;" + eol    
    js += "          var at2 = atom2;" + eol    
    js += "          var u = [0,1,2].map( (i) => { return atoms[at2][i]-atoms[at1][i]; });" + eol    
    js += "          var nu = math.norm(u);" + eol    
    js += "          u = u.map((e)=>{return e/nu;});" + eol    
    js += "          var v1 = math.random([3]);" + eol    
    js += "          var dotv1 = math.dot(v1,u);" + eol   
    js += "          var du = u.map((e)=>{return e*dotv1;});" + eol    
    js += "          v1 = v1.map((e,i)=> {return (e-du[i])});" + eol      
    js += "          v1 = v1.map((e,i)=> {return (e/math.norm(v1));});" + eol    
    js += "          var v2 = math.cross(v1, u);" + eol    
    js += "          v2 = v2.map((e,i)=> {return (e/math.norm(v2));});" + eol    
    js += "          var xd = linspace.map((p)=>{return p*(atoms[at1][0]-atoms[at2][0])+atoms[at2][0]});" + eol    
    js += "          var yd = linspace.map((p)=>{return p*(atoms[at1][1]-atoms[at2][1])+atoms[at2][1]});" + eol    
    js += "          var zd = linspace.map((p)=>{return p*(atoms[at1][2]-atoms[at2][2])+atoms[at2][2]});" + eol
    js += "          var atm1 = atoms[at1][3];" + eol
    js += "          if (atm1 == 'Helium'){" + eol
    js += "            atm1 = atoms[at2][3];" + eol
    js += "          }" + eol
    js += "          var atm2 = atoms[at2][3];" + eol
    js += "          if (atm1 != atm2){" + eol
    js += "            for (var i = 0; i<(xd.length/2)+2; i++){" + eol
    js += "              xt[atm2].push(cosphi.map((e,j)=>{return cosphi[j]*v1[0] + sinphi[j]*v2[0] + xd[i];}));" + eol
    js += "              yt[atm2].push(cosphi.map((e,j)=>{return cosphi[j]*v1[1] + sinphi[j]*v2[1] + yd[i];}));" + eol
    js += "              zt[atm2].push(cosphi.map((e,j)=>{return cosphi[j]*v1[2] + sinphi[j]*v2[2] + zd[i];}));" + eol
    js += "            }" + eol
    js += "            xt[atm2].push([]);" + eol
    js += "            zt[atm2].push([]);" + eol
    js += "            yt[atm2].push([]);" + eol
    js += "            for (var i = (xd.length/2)-1; i<(xd.length); i++){" + eol
    js += "              xt[atm1].push(cosphi.map((e,j)=>{return cosphi[j]*v1[0] + sinphi[j]*v2[0] + xd[i];}));" + eol
    js += "              yt[atm1].push(cosphi.map((e,j)=>{return cosphi[j]*v1[1] + sinphi[j]*v2[1] + yd[i];}));" + eol
    js += "              zt[atm1].push(cosphi.map((e,j)=>{return cosphi[j]*v1[2] + sinphi[j]*v2[2] + zd[i];}));" + eol
    js += "            }" + eol
    js += "            xt[atm1].push([]);" + eol
    js += "            zt[atm1].push([]);" + eol
    js += "            yt[atm1].push([]);" + eol
    js += "          } else {" + eol
    js += "            for (var i = 0; i<(xd.length); i++){" + eol
    js += "              xt[atm1].push(cosphi.map((e,j)=>{return cosphi[j]*v1[0] + sinphi[j]*v2[0] + xd[i];}));" + eol
    js += "              yt[atm1].push(cosphi.map((e,j)=>{return cosphi[j]*v1[1] + sinphi[j]*v2[1] + yd[i];}));" + eol
    js += "              zt[atm1].push(cosphi.map((e,j)=>{return cosphi[j]*v1[2] + sinphi[j]*v2[2] + zd[i];}));" + eol
    js += "            }" + eol
    js += "            xt[atm1].push([]);" + eol
    js += "            zt[atm1].push([]);" + eol
    js += "            yt[atm1].push([]);" + eol
    js += "          }" + eol
    js += "        });" + eol
    js += "      });" + eol
    js += "      colorset.forEach((c) => {" + eol
    js += "        var opacity = 1.0;" + eol
    js += "        if (c == 'Helium'){" + eol
    js += "          opacity = 0.2;" + eol
    js += "        }" + eol
    js += "        var cv = xt[c].map((x)=>{ return x.map((p) => {return 1;});});" + eol
    js += "        var colorscalea = [[0,'rgba(200,0,0,1.0)'], [1,component.props.getColor(component, c)]];" + eol
    js += "        traces.push({" + eol
    js += "          'type' : 'surface'," + eol
    js += "          'x' : xt[c]," + eol
    js += "          'y' : yt[c]," + eol
    js += "          'z' : zt[c]," + eol
    js += "          'cauto' : false," + eol
    js += "          'cmin' : 0," + eol
    js += "          'cmax' : 1," + eol             
    js += "          'hovertext' : ''," + eol
    js += "          'showscale' : false," + eol
    js += "          'hoverinfo' : 'text'," + eol
    js += "          'colorscale' : colorscalea," + eol
    js += "          'surfacecolor' : cv," + eol      
    js += "          'connectgaps' : false," + eol
    js += "          'opacity' : opacity" + eol
    js += "        });" + eol
    js += "      });" + eol
    js += "    }" + eol
    js += "  }" + eol
    js += "  return {'data':traces, 'frames':[], 'layout':layout}" + eol
    js += "}" + eol

    component.addPropVariable("plotDrawingPlotly", {"type":"func", "defaultValue": js})
    return {
      "type": "propCall2",
      "calls": "plotDrawingPlotly",
      "args": ['self', '']
    }



  def FindPlaneIntersect(tp, component, *args, **kwargs):
    eol = "\n"
    js = ""
    js += "(component, boundary, normal, center) => {" + eol   
    js += "  var min_p = boundary[0];" + eol   
    js += "  var max_p = boundary[1];" + eol   
    js += "  var faces = [" + eol   
    js += "    [-1,0,0, min_p[0]]," + eol   
    js += "    [0,-1,0, min_p[1]]," + eol   
    js += "    [0,0,-1, min_p[2]]," + eol   
    js += "    [-1,0,0, max_p[0]]," + eol   
    js += "    [0,-1,0, max_p[1]]," + eol   
    js += "    [0,0,-1, max_p[2]]," + eol   
    js += "  ];" + eol   
    js += "  var epsilon = 1e-6;" + eol   
    js += "  var avg_p = [0,0,0];" + eol   
    js += "  avg_p[0] = min_p[0] + (max_p[0]-min_p[0])/2;" + eol   
    js += "  avg_p[1] = min_p[1] + (max_p[1]-min_p[1])/2;" + eol   
    js += "  avg_p[2] = min_p[2] + (max_p[2]-min_p[2])/2;" + eol   
    js += "  var min_point = undefined;" + eol   
    js += "  var max_point = undefined;" + eol   
    js += "  var line_points = new Set();" + eol   
    js += "  faces.map((f)=> {" + eol   
    js += "    var planeNormal = f.slice(0,3);" + eol   
    js += "    var rayDirection = normal;" + eol   
    js += "    var ndotu = math.dot(planeNormal,rayDirection);" + eol   
    js += "    if (math.abs(ndotu)>epsilon){" + eol   
    js += "      var planePoint = [0,1,2].map((i)=>{return -f[i]*f[3];});" + eol   
    js += "      let rayPoint = avg_p;" + eol   
    js += "      var w = [0,1,2].map((i)=>{return rayPoint[i] - planePoint[i];});" + eol   
    js += "      var si = -math.dot(planeNormal,w)/ndotu;" + eol   
    js += "      var wsi = [0,1,2].map((i)=>{return (w[i]+si*rayDirection[i]+planePoint[i]);});" + eol   
    js += "      var Psi = math.round(wsi, 8);" + eol   
    js += "      if (Psi[0] >= min_p[0]-epsilon && Psi[0] <= max_p[0]+epsilon){" + eol   
    js += "        if (Psi[1] >= min_p[1]-epsilon && Psi[1] <= max_p[1]+epsilon){" + eol   
    js += "          if (Psi[2] >= min_p[2]-epsilon && Psi[2] <= max_p[2]+epsilon){" + eol   
    js += "            line_points.add(JSON.stringify(Psi));" + eol   
    js += "          }" + eol   
    js += "        }" + eol   
    js += "      }" + eol   
    js += "    }" + eol   
    js += "  });" + eol   
    js += "  if (line_points.size != 2 )" + eol   
    js += "     return [[], []];" + eol   
    js += "  line_points = [...line_points].map((l)=>{return JSON.parse(l);});" + eol   
    js += "  var min_point = line_points[0];" + eol   
    js += "  var max_point = line_points[1];" + eol   
    js += "  avg_p[0] = min_point[0] + (max_point[0]-min_point[0])*center;" + eol   
    js += "  avg_p[1] = min_point[1] + (max_point[1]-min_point[1])*center;" + eol   
    js += "  avg_p[2] = min_point[2] + (max_point[2]-min_point[2])*center;" + eol   
    js += "  var normal_point = avg_p[0]*normal[0] + avg_p[1]*normal[1] + avg_p[2]*normal[2];" + eol   
    js += "  var mid_point = normal_point;" + eol   
    js += "  var points = [];" + eol   
        
    js += "  faces.map((b)=> {" + eol   
    js += "    var a_vec = normal;" + eol   
    js += "    var b_vec = b.slice(0,3);" + eol   
    js += "    var aXb_vec = math.cross(a_vec, b_vec);" + eol   
    js += "    let A = [a_vec, b_vec, aXb_vec];" + eol   
    js += "    if (math.det(A) != 0){" + eol   
    js += "      var d = [normal_point, -b[3], 0.];" + eol   
    js += "      var p_inter = math.lusolve(A, d);" + eol   
    js += "      points.push([p_inter, aXb_vec]);" + eol   
    js += "    }" + eol   
    js += "  });" + eol   
    js += "  var pts = new Set();" + eol   
    js += "  points.forEach((pt)=> {" + eol   
    js += "    var p = pt[0];" + eol   
    js += "    var v = pt[1];" + eol   
    js += "    faces.map((f)=> {" + eol   
    js += "      var planeNormal = f.slice(0,3);" + eol   
    js += "      var rayDirection = v;" + eol   
    js += "      var ndotu = math.dot(planeNormal,rayDirection);" + eol   
    js += "      if (math.abs(ndotu)>epsilon){" + eol
    js += "        var planePoint = [0,1,2].map((i)=>{return -f[i]*f[3];});" + eol
    js += "        var rayPoint = p;" + eol
    js += "        var w = [0,1,2].map((i)=>{return rayPoint[i] - planePoint[i];});" + eol
    js += "        var si = -math.dot(planeNormal,w)/ndotu;" + eol
    js += "        var wsi = [0,1,2].map((i)=>{return (w[i]+si*rayDirection[i]+planePoint[i]);});" + eol   
    js += "        var Psi = math.round(wsi, 8);" + eol   
    js += "        if (Psi[0] >= min_p[0]-epsilon && Psi[0] <= max_p[0]+epsilon){" + eol   
    js += "          if (Psi[1] >= min_p[1]-epsilon && Psi[1] <= max_p[1]+epsilon){" + eol   
    js += "            if (Psi[2] >= min_p[2]-epsilon && Psi[2] <= max_p[2]+epsilon){" + eol   
    js += "              pts.add(JSON.stringify(Psi));" + eol   
    js += "            }" + eol   
    js += "          }" + eol   
    js += "        }" + eol   
    js += "      }" + eol   
    js += "    });" + eol   
    js += "  });" + eol   
    js += "  return [...pts].map((l)=>{return JSON.parse(l);});" + eol   
    js += "}" + eol
    
    component.addPropVariable("FindPlaneIntersect", {"type":"func", "defaultValue": js})    
    return {
      "type": "propCall2",
      "calls": "FindPlaneIntersect",
      "args": ['self', '[]']
    }    


  def exposedShowPlanes(tp, component, *args, **kwargs):
    RapptureBuilder.FindPlaneIntersect(tp, component)
    eol = "\n"
    js = ""
    js += "(component, plane, unitvectors, center, boundary, color) => {" + eol   
    js += "  var traces = [];" + eol  
    js += "  var layout = {" + eol
    js += "    'scene':{'aspectmode':'data'}, " + eol
    js += "    'margin' : {'l':0,'r':0,'t':0,'b':0}," + eol
    #js += "    'template' : self.theme," + eol
    js += "  };" + eol    
    js += "  var normal = [ " + eol   
    js += "    plane[0]*unitvectors[0][0]+plane[0]*unitvectors[0][1]+plane[0]*unitvectors[0][2]," + eol   
    js += "    plane[1]*unitvectors[1][0]+plane[1]*unitvectors[1][1]+plane[1]*unitvectors[1][2]," + eol   
    js += "    plane[2]*unitvectors[2][0]+plane[2]*unitvectors[2][1]+plane[2]*unitvectors[2][2]" + eol   
    js += "  ];" + eol   
    js += "  var points = component.props.FindPlaneIntersect(component, boundary, normal, center);" + eol   
    js += "  var xt = points.map((point)=>{return point[0];});" + eol   
    js += "  var yt = points.map((point)=>{return point[1];});" + eol   
    js += "  var zt = points.map((point)=>{return point[2];});" + eol   
    js += "  var delaunayaxis = 'z';" + eol   
    js += "  if (new Set(xt).size == 1) " + eol  
    js += "    delaunayaxis = 'x'" + eol   
    js += "  else if (new Set(yt).size == 1) " + eol  
    js += "    delaunayaxis = 'y'" + eol  
    js += "  else if (new Set(zt).size == 1) " + eol  
    js += "    delaunayaxis = 'z'" + eol  
    js += "  else if (new Set(yt).size == new Set(xt).size) " + eol  
    js += "    delaunayaxis = 'y'" + eol  
    js += "  traces.push({" + eol  
    js += "    'type' : 'mesh3d'," + eol  
    js += "    'x' : xt, " + eol  
    js += "    'y' : yt, " + eol  
    js += "    'z' : zt, " + eol  
    js += "    'color' : color," + eol  
    js += "    'opacity' : 0.8," + eol  
    js += "    'hovertext' : ''," + eol  
    js += "    'hoverinfo' : 'text'," + eol  
    js += "    'delaunayaxis' : delaunayaxis" + eol  
    js += "  });" + eol  
    js += "  return({" + eol
    js += "    'data': traces," + eol
    js += "    'layout': layout," + eol
    js += "    'frames': []," + eol
    js += "    'config': {'displayModeBar': true, 'responsive': 'true'}" + eol    
    js += "  });" + eol
    js += "}" + eol
       
    component.addPropVariable("exposedShowPlanes", {"type":"func", "defaultValue": js})    
    return {
      "type": "propCall2",
      "calls": "exposedShowPlanes",
      "args": ['self', '[1,1,0]', '[[1,0,0],[0,1,0],[0,0,1]]','0.5','[[0,0,0],[5,5,5]]', '\'rgb(128,0,0)\'']
    }            
        
