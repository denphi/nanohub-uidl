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
import json


class SimtoolBuilder:
    def Loader(Component, *args, **kwargs):
        Component.addStateVariable(
            kwargs.get("loader_status", "loader_status"),
            {"type": "string", "defaultValue": ""},
        )
        Component.addStateVariable(
            kwargs.get("loader_open", "loader_open"),
            {"type": "boolean", "defaultValue": kwargs.get("is_open", True)},
        )

        Loader = TeleportElement(MaterialContent(elementType="Dialog"))
        Loader.content.attrs["open"] = {
            "type": "dynamic",
            "content": {
                "referenceType": "state",
                "id": kwargs.get("open", "loader_open"),
            },
        }
        Loader.content.attrs["disableBackdropClick"] = True
        Loader.content.attrs["disableEscapeKeyDown"] = True
        Loader.content.attrs["fullWidth"] = True
        Loader.content.attrs["maxWidth"] = "xs"
        loadercnt = TeleportElement(MaterialContent(elementType="DialogContent"))
        loadercnt.content.style = {"textAlign": "center", "overflow": "hidden"}

        LinearProgress = TeleportElement(MaterialContent(elementType="LinearProgress"))
        LinearProgress.content.attrs["color"] = "secondary"

        loadertext = TeleportElement(MaterialContent(elementType="DialogTitle"))
        loadertext.addContent(
            TeleportDynamic(
                content={
                    "referenceType": "state",
                    "id": kwargs.get("open", "loader_status"),
                }
            )
        )
        loadertext.content.style = {"textAlign": "center"}

        # loadercnt.addContent(loadercir)
        loadercnt.addContent(LinearProgress)
        Loader.addContent(loadercnt)
        Loader.addContent(loadertext)

        return Loader

    def Error(Component, *args, **kwargs):
        Component.addStateVariable(
            kwargs.get("error_status", "error_status"),
            {"type": "string", "defaultValue": ""},
        )
        Component.addStateVariable(
            kwargs.get("error_open", "error_open"),
            {"type": "boolean", "defaultValue": False},
        )
        Error = TeleportElement(MaterialContent(elementType="Dialog"))
        Error.content.attrs["open"] = {
            "type": "dynamic",
            "content": {
                "referenceType": "state",
                "id": kwargs.get("error_open", "error_open"),
            },
        }
        Error.content.attrs["fullWidth"] = True
        Error.content.attrs["maxWidth"] = "xs"
        DialogContent = TeleportElement(MaterialContent(elementType="DialogContent"))
        DialogContent.content.style = {"textAlign": "center", "overflow": "hidden"}

        Typography = TeleportElement(MaterialContent(elementType="Typography"))
        Typography.content.attrs["variant"] = "h6"
        TypographyText = TeleportStatic(content=kwargs.get("title", "Error Message"))
        Typography.addContent(TypographyText)

        Icon0 = TeleportElement(MaterialContent(elementType="Icon"))
        Icon0.content.style = {"position": "absolute", "top": "10px", "left": "10px"}
        IconText0 = TeleportStatic(content="error")
        Icon0.addContent(IconText0)

        IconButton = TeleportElement(MaterialContent(elementType="IconButton"))
        IconButton.content.style = {
            "position": "absolute",
            "top": "10px",
            "right": "10px",
        }

        Icon = TeleportElement(MaterialContent(elementType="Icon"))
        IconText = TeleportStatic(content="close")
        Icon.addContent(IconText)
        IconButton.addContent(Icon)
        IconButton.content.events["click"] = [
            {
                "type": "stateChange",
                "modifies": kwargs.get("error_open", "error_open"),
                "newState": False,
            }
        ]

        DialogTitle = TeleportElement(MaterialContent(elementType="DialogTitle"))
        DialogTitle.content.attrs["disableTypography"] = True
        DialogTitle.content.style = {
            "textAlign": "center",
            "backgroundColor": "#d95c5c",
        }
        DialogTitle.addContent(IconButton)
        DialogTitle.addContent(Typography)
        DialogTitle.addContent(Icon0)

        DialogContent.addContent(
            TeleportDynamic(
                content={
                    "referenceType": "state",
                    "id": kwargs.get("error_status", "error_status"),
                }
            )
        )
        DialogContent.content.style = {"textAlign": "center"}

        Error.addContent(DialogTitle)
        Error.addContent(DialogContent)

        return Error

    def onSimulate(tp, Component, *args, **kwargs):
        SimtoolBuilder.buildSchema(tp, Component, *args, **kwargs)
        store_name = "sessionStore"
        NanohubUtils.storageFactory(
            tp, store_name=store_name, storage_name="window.sessionStorage"
        )
        use_cache = kwargs.get("use_cache", True)
        outputs = kwargs.get("outputs", [])
        if use_cache:
            cache_store = kwargs.get("cache_store", "CacheStore")
            if kwargs.get("jupyter_cache", None) is not None:
                cache_storage = kwargs.get(
                    "cache_storage",
                    "cacheFactory('" + cache_store + "', 'JUPYTERSTORAGE')",
                )
                NanohubUtils.storageFactory(
                    tp,
                    method_name="storageJupyterFactory",
                    jupyter_cache=kwargs.get("jupyter_cache", None),
                    store_name=cache_store,
                    storage_name=cache_storage,
                )
            else:
                cache_storage = kwargs.get(
                    "cache_storage", "cacheFactory('" + cache_store + "', 'INDEXEDDB')"
                )
                NanohubUtils.storageFactory(
                    tp, store_name=cache_store, storage_name=cache_storage
                )
        eol = "\n"
        toolname = kwargs.get("toolname", "")
        revision = kwargs.get("revision", "")
        url = kwargs.get("url", "")

        js = "async (self, ostate)=>{" + eol
        js += "  var state = self.state;" + eol

        if use_cache:
            js += (
                "  self.props.onStatusChange({'target':{ 'value' : 'Checking Cache' } } );"
                + eol
            )
            js += "  var d_state = Object.assign({}, self.state);" + eol
            js += "  delete d_state['testing'];" + eol
            js += "  delete d_state['paletteColors'];" + eol
            js += "  var str_key = JSON.stringify(d_state);" + eol
            js += "  var buffer_key = new TextEncoder('utf-8').encode(str_key);" + eol
            js += (
                "  var hashBuffer = await window.crypto.subtle.digest('SHA-256', buffer_key);"
                + eol
            )
            js += "  var hashArray = Array.from(new Uint8Array(hashBuffer));" + eol
            js += (
                "  var hash_key = hashArray.map(b => b.toString(16).padStart(2, '0')).join('');"
                + eol
            )
            # js += "  console.log(hash_key)" + eol
            js += "  var hash_q = await " + cache_store + ".getItem(hash_key)" + eol
            # js += "  console.log(hash_q)" + eol
            js += "  if( hash_q == null ){" + eol
        js += (
            "  self.props.onStatusChange({'target':{ 'value' : 'Parsing Tool Schema' } } );"
            + eol
        )
        js += (
            "  var schema = JSON.parse("
            + store_name
            + ".getItem('nanohub_tool_schema'));"
            + eol
        )
        js += "  if(!schema){" + eol
        js += "    await self.props.buildSchema(self);" + eol
        js += (
            "    schema = JSON.parse("
            + store_name
            + ".getItem('nanohub_tool_schema'));"
            + eol
        )
        js += "    if(!schema){" + eol
        js += (
            "      self.props.onError( 'Error submiting the simulation, schema can not be loaded' );"
            + eol
        )
        js += "      return;" + eol
        js += "    }" + eol
        js += "  }" + eol
        js += "  var inputs = {};" + eol
        js += "  for (const id in schema.inputs) {" + eol
        js += "    if (id in state){" + eol
        js += "      inputs[id] = state[id];" + eol
        js += "    } else {" + eol
        js += "      inputs[id] = schema.inputs[id].value;" + eol
        js += "    }" + eol
        js += "  }" + eol
        # js += "  console.log(inputs);" + eol
        js += "  let data = {" + eol
        js += "    'name': '" + toolname + "', " + eol
        js += "    'revision': '" + str(revision) + "', " + eol
        js += "    'inputs': inputs, " + eol
        js += "    'outputs':" + json.dumps(outputs) + "," + eol
        js += "    'cores' : state['cores']," + eol
        js += "    'cutoff' : state['cutoff']," + eol
        js += "    'venue' : state['venue']" + eol
        js += "  }" + eol
        js += "  var nanohub_token = " + store_name + ".getItem('nanohub_token');" + eol
        js += "  var header_token = {'Authorization': 'Bearer ' + nanohub_token}" + eol
        js += "  var url = '" + url + "/run';" + eol
        js += (
            "  self.props.onStatusChange({'target':{ 'value' : 'Submitting Simulation' } } );"
            + eol
        )
        js += (
            "  var options = { 'handleAs' : 'json' , 'headers' : header_token, 'method' : 'POST', 'data' : data };"
            + eol
        )
        js += "  try{" + eol
        js += "    Axios.request(url, options)" + eol
        js += "    .then(function(response){" + eol
        js += "      var data = response.data;" + eol
        # js += "      console.log(data);" + eol
        js += "      if(data.code){" + eol
        js += "        if(data.message){" + eol
        js += (
            "          self.props.onError( '(' + data.code + ') ' +data.message );"
            + eol
        )
        js += "        } else {" + eol
        js += (
            "          self.props.onError( '(' + data.code + ') Error sending the simulation' );"
            + eol
        )
        js += "        } " + eol
        js += "      }else{" + eol
        js += "        if(data.id){" + eol
        js += "          if('outputs' in data){" + eol
        js += "            self.props.onLoad(self);" + eol
        js += (
            "            self.props.onLoadResults(self, data.id, data['outputs']);"
            + eol
        )
        js += "          } else {" + eol
        js += (
            "            setTimeout(function(){ self.props.onCheckSession(self, data.id, 10) }, 5000);"
            + eol
        )
        js += "          }" + eol
        js += "        } else {" + eol
        js += (
            "          self.props.onError( 'Error submiting the simulation, session not found' );"
            + eol
        )
        js += "        }" + eol
        js += "      }" + eol
        js += "    }).catch(function(error){" + eol
        js += "      if (error.response){" + eol
        js += "        if (error.response.data){" + eol
        js += "          if (error.response.data.message){" + eol
        js += (
            "            self.props.onError(String(error.response.data.message));" + eol
        )
        js += "          } else {" + eol
        js += "            self.props.onError(String(error.response.data));" + eol
        js += "          }" + eol
        js += "        } else {" + eol
        js += "          self.props.onError(String(error.response));" + eol
        js += "        }" + eol
        js += "      } else {" + eol
        js += "        self.props.onError(String(error));" + eol
        js += "      }" + eol
        js += "    });" + eol
        js += "  } catch (err) {" + eol
        js += "    self.props.onError(String(err));" + eol
        js += "  }" + eol
        if use_cache:
            js += "  } else { " + eol
            js += (
                "    self.props.onStatusChange({'target':{ 'value' : 'Loading from local Cache' } } );"
                + eol
            )
            js += "    self.props.onSuccess(self, hash_key)" + eol
            js += "  }" + eol
        js += "}"

        Component.addPropVariable("onSimulate", {"type": "func", "defaultValue": js})

        js = "(self, session_id, reload)=>{" + eol
        js += "  if (session_id == ''){" + eol
        js += "     self.props.onError('invalid Session ID');" + eol
        js += "  }" + eol
        js += "  var session_json = {'session_num': session_id};" + eol
        js += "  var nanohub_token = " + store_name + ".getItem('nanohub_token');" + eol
        js += "  var header_token = {'Authorization': 'Bearer ' + nanohub_token}" + eol
        js += "  var url = '" + url + "/run/' + session_id;" + eol
        js += "  var str = [];" + eol
        js += "  for(var p in session_json){" + eol
        js += (
            "    str.push(encodeURIComponent(p) + '=' + encodeURIComponent(session_json[p]));"
            + eol
        )
        js += "  }" + eol
        js += "  let data =  str.join('&');" + eol
        js += (
            "  var options = { 'handleAs' : 'json' , 'headers' : header_token, 'method' : 'POST', 'data' : data };"
            + eol
        )
        js += "  try{" + eol
        js += "    Axios.request(url, options)" + eol
        js += "    .then(function(response){" + eol
        js += "      var status = response.data;" + eol
        js += "      if (status['success']){" + eol
        js += "        if ('status' in status){" + eol
        js += "          if(status['status'] == 'error'){" + eol
        js += "            self.props.onError(status['status']);" + eol
        js += "          }" + eol
        js += "          else {" + eol
        js += (
            "            self.props.onStatusChange({'target':{ 'value' : status['status'] } } );"
            + eol
        )
        js += "            if('outputs' in status && status['outputs']){" + eol
        js += "              self.props.onLoad(self);" + eol
        js += (
            "              self.props.onLoadResults(self, session_id, status['outputs']);"
            + eol
        )
        js += "            } else {" + eol
        js += "              if (reload > 0){" + eol
        js += (
            "                setTimeout(function(){self.props.onCheckSession(self, session_id, reload)},10000);"
            + eol
        )
        js += "              }" + eol
        js += "            }" + eol
        js += "          }" + eol
        js += "        }"
        js += "      } else if (status['code']){" + eol
        # js += "        if (status['code'] == 404){" + eol
        # js += "          setTimeout(function(){self.props.onCheckSession(self, session_id, reload-1)},8000);" + eol
        # js += "        }"
        # js += "        else if (status['code'] != 200){" + eol
        js += "          self.props.onError(status['message']);" + eol
        # js += "        }"
        js += "      }"
        js += "    }).catch(function(error){" + eol
        js += "      if (error.response){" + eol
        js += "        if (error.response.data){" + eol
        js += "          if (error.response.data.message){" + eol
        js += (
            "            self.props.onError(String(error.response.data.message));" + eol
        )
        js += "          } else {" + eol
        js += "            self.props.onError(String(error.response.data));" + eol
        js += "          }" + eol
        js += "        } else {" + eol
        js += "          self.props.onError(String(error.response));" + eol
        js += "        }" + eol
        js += "      } else {" + eol
        js += "        self.props.onError(String(error));" + eol
        js += "      }" + eol
        js += "    })" + eol
        js += "  } catch (err) {" + eol
        js += "    self.props.onError(String(err));" + eol
        js += "  }" + eol
        js += "}" + eol

        Component.addPropVariable(
            "onCheckSession", {"type": "func", "defaultValue": js}
        )
        Component.addStateVariable(
            "paletteColors",
            {
                "type": "array",
                "defaultValue": [
                    "#636EFA",
                    "#EF553B",
                    "#00CC96",
                    "#AB63FA",
                    "#FFA15A",
                    "#19D3F3",
                    "#FF6692",
                    "#B6E880",
                    "#FF97FF",
                    "#FECB52",
                ],
            },
        )

        js = "async (self, session_id, output)=> {" + eol

        js += (
            "      self.props.onStatusChange({'target':{ 'value' : 'Loading Results' } } );"
            + eol
        )
        if use_cache:
            js += "      var d_state = Object.assign({}, self.state);" + eol
            js += "      delete d_state['testing'];" + eol
            js += "      delete d_state['paletteColors'];" + eol
            js += "      var str_key = JSON.stringify(d_state);" + eol
            js += (
                "      var buffer_key = new TextEncoder('utf-8').encode(str_key);" + eol
            )
            js += (
                "      var hashBuffer = await window.crypto.subtle.digest('SHA-256', buffer_key);"
                + eol
            )
            js += "      var hashArray = Array.from(new Uint8Array(hashBuffer));" + eol
            js += (
                "      var hash_key = hashArray.map(b => b.toString(16).padStart(2, '0')).join('');"
                + eol
            )
            js += (
                "      var hash_q = await "
                + cache_store
                + ".setItem(hash_key, JSON.stringify(output), (e)=>{self.props.onError(e.toString())});"
                + eol
            )
            js += (
                "      var olist_json = await "
                + cache_store
                + ".getItem('cache_list');"
                + eol
            )
            js += "      if (!olist_json || olist_json == '')" + eol
            js += "        olist_json = '{}';" + eol
            js += "      var cacheList = JSON.parse(olist_json);" + eol
            js += "      let paletteColorsc = [...self.state.paletteColors]" + eol
            js += "      d_state['.color'] = paletteColorsc.shift();" + eol
            js += "      paletteColorsc.push(d_state['.color']);" + eol
            js += "      self.setState({'paletteColors': paletteColorsc});" + eol
            js += "      cacheList[hash_key] = d_state;" + eol
            js += (
                "      var hash_q = await "
                + cache_store
                + ".setItem('cache_list', JSON.stringify(cacheList), (e)=>{self.props.onError(e.toString())});"
                + eol
            )
        js += "      self.props.onSuccess(self, hash_key)" + eol
        js += "}" + eol

        Component.addPropVariable("onLoadResults", {"type": "func", "defaultValue": js})

        callbacklist = []
        states_def = "{ 'target' : { 'value' : {"
        for k, state in Component.stateDefinitions.items():
            states_def += "'" + k + "': self.state." + k + " ,"
        states_def += "} } }"
        callbacklist.append(
            {"type": "propCall2", "calls": "onSimulate", "args": ["self", states_def]}
        )

        return callbacklist

    def getXY(tp, component, *args, **kwargs):
        eol = "\n"
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
        component.addPropVariable("getXY", {"type": "func", "defaultValue": js})
        return {
            "type": "propCall2",
            "calls": "getXY",
            "args": ["self", "undefined", "undefined"],
        }

    def buildXYPlotly(tp, component, *args, **kwargs):
        eol = "\n"
        SimtoolBuilder.getXY(tp, component)
        js = ""
        js += "(component, fields, labels) => {" + eol
        js += "  var traces = Array();" + eol
        js += "  var layout = {};" + eol
        js += "  var xrange = [undefined,undefined];" + eol
        js += "  var xrange = [undefined,undefined];" + eol
        js += "  var yrange = [undefined,undefined];" + eol
        js += "  for (const [i, field] of Object.entries(fields)){" + eol
        js += "    var label = i;" + eol
        js += "    var line = {'color' : 'blue'};" + eol
        js += "    if (labels != undefined){" + eol
        js += "      label = label + " " + labels[i];" + eol
        js += "    }" + eol
        js += "    var sortedfield = {};" + eol
        js += "    for( let ii=0,nn=field['position'].length; ii<nn; ii++){" + eol
        js += "      sortedfield[field['position'][ii]] = field['function'][ii];" + eol
        js += "    }" + eol
        js += "    let sortedkeys = Object.keys(sortedfield);" + eol
        js += "    sortedkeys.sort((a, b) => a - b);" + eol
        js += "    var sortedvalues = [];" + eol
        js += "    sortedkeys.forEach(i => sortedvalues.push(sortedfield[i]));" + eol
        js += "    var trace1 = {" + eol
        js += "      'type' : 'scatter'," + eol
        js += "      'x' : sortedkeys," + eol
        js += "      'y' : sortedvalues," + eol
        js += "      'mode' : 'lines'," + eol
        js += "      'name' : label," + eol
        js += "      'line' : line," + eol
        js += "    };" + eol
        js += "    traces.push(trace1);" + eol
        js += "  }" + eol
        js += "  layout = {};" + eol
        js += "  return {'traces':traces, 'layout':layout}" + eol
        js += "}" + eol

        component.addPropVariable("buildXYPlotly", {"type": "func", "defaultValue": js})
        return {
            "type": "propCall2",
            "calls": "buildXYPlotly",
            "args": ["self", [], "undefined"],
        }

    def plotXY(tp, component, *args, **kwargs):
        SimtoolBuilder.buildXYPlotly(tp, component)
        eol = "\n"
        js = ""
        js += "(component, sequence) => {" + eol
        js += "  var plt = component.props.buildXYPlotly(component, sequence);" + eol
        js += "  var tr = plt['traces'];" + eol
        js += "  var ly = plt['layout'];" + eol
        js += "  var layout = {};" + eol
        js += "  return {'data':tr, 'frames':[], 'layout':layout}" + eol
        js += "}" + eol

        component.addPropVariable("plotXY", {"type": "func", "defaultValue": js})
        return {"type": "propCall2", "calls": "plotXY", "args": ["self", ""]}

    def plotSequence(tp, component, *args, **kwargs):
        SimtoolBuilder.buildXYPlotly(tp, component)
        url = kwargs.get("url", "")
        eol = "\n"
        js = ""
        js += "(component, sequence, normalize=false, start_trace=0) => {" + eol
        js += "  var label = 'TODO';" + eol
        js += "  var min_tr_x = undefined;" + eol
        js += "  var min_tr_y = undefined;" + eol
        js += "  var max_tr_x = undefined;" + eol
        js += "  var max_tr_y = undefined;" + eol
        js += "  var traces = [];" + eol
        js += "  var layout = {};" + eol
        js += "  var frames = {};" + eol
        js += "  var options = [];" + eol
        js += "  for (const [i, curves] of Object.entries(sequence)){" + eol
        js += "    var plt = component.props.buildXYPlotly(component, curves);" + eol
        js += "    var tr = plt['traces'];" + eol
        js += "    var lay = plt['layout'];" + eol
        js += "    for (let t=0; t<tr.length;t++){" + eol
        js += "      var minx, maxx;" + eol
        js += "      try {" + eol
        js += "        minx = Math.min.apply(null, tr[t]['x']);" + eol
        js += "        maxx = Math.max.apply(null, tr[t]['x']);" + eol
        js += "        if (min_tr_x ==undefined || min_tr_x > minx){" + eol
        js += "          min_tr_x = minx;" + eol
        js += "        }" + eol
        js += "        if (max_tr_x ==undefined || max_tr_x < maxx){" + eol
        js += "          max_tr_x = maxx;" + eol
        js += "        }" + eol
        js += "      } catch(error){}" + eol
        js += "      var miny, maxy;" + eol
        js += "      try {" + eol
        js += "        miny = Math.min.apply(null, tr[t]['y']);" + eol
        js += "        maxy = Math.max.apply(null, tr[t]['y']);" + eol
        js += "        if (min_tr_y ==undefined || min_tr_y > miny){" + eol
        js += "          min_tr_y = miny;" + eol
        js += "        }" + eol
        js += "        if (max_tr_y ==undefined || max_tr_y < maxy){" + eol
        js += "          max_tr_y = maxy;" + eol
        js += "        }" + eol
        js += "      } catch(error){}" + eol
        js += "    }" + eol
        js += "    if (i in frames){" + eol
        js += "      frames[i].push(...tr.slice(0));" + eol
        js += "    } else {" + eol
        js += "      options.push(i);" + eol
        js += "      frames[i] = tr.slice(0);" + eol
        js += "    }" + eol
        js += "  }" + eol

        js += "    if (traces.length == 0){" + eol
        js += "      layout = lay;" + eol
        js += "      traces =frames[ Object.keys(frames)[start_trace]];" + eol  # clone
        js += "    }" + eol

        js += "  var frms = [];" + eol

        js += "  if (normalize && !isNaN(min_tr_x) && !isNaN(max_tr_x)){" + eol
        js += (
            "    layout['xaxis']= {'autorange':false, 'range':[min_tr_x, max_tr_x]};"
            + eol
        )
        js += "  } if (normalize && !isNaN(min_tr_y) && !isNaN(max_tr_y)) {" + eol
        js += (
            "    layout['yaxis']= {'autorange':false, 'range':[min_tr_y, max_tr_y]};"
            + eol
        )
        js += "  } " + eol

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
        js += "    }]" + eol
        js += "  }];" + eol
        js += "  return {'data':traces, 'frames':frms, 'layout':layout}" + eol
        js += "}" + eol

        component.addPropVariable("plotSequence", {"type": "func", "defaultValue": js})
        return {"type": "propCall2", "calls": "plotSequence", "args": ["self", []]}

    def loadXY(tp, component, *args, **kwargs):
        eol = "\n"
        SimtoolBuilder.plotXY(tp, component)

        cache_store = kwargs.get("cache_store", "CacheStore")
        if kwargs.get("jupyter_cache", None) is not None:
            cache_storage = kwargs.get(
                "cache_storage", "cacheFactory('" + cache_store + "', 'JUPYTERSTORAGE')"
            )
            NanohubUtils.storageFactory(
                tp,
                method_name="storageJupyterFactory",
                jupyter_cache=kwargs.get("jupyter_cache", None),
                store_name=cache_store,
                storage_name=cache_storage,
            )
        else:
            cache_storage = kwargs.get(
                "cache_storage", "cacheFactory('" + cache_store + "', 'INDEXEDDB')"
            )
            NanohubUtils.storageFactory(
                tp, store_name=cache_store, storage_name=cache_storage
            )

        js = ""
        js += "async (component, seq, layout, axis_ids) => {" + eol
        js += (
            "  var olist_json = await " + cache_store + ".getItem('cache_list');" + eol
        )
        js += "  if (!olist_json || olist_json == '')" + eol
        js += "    olist_json = '{}';" + eol
        js += "  let inputs = JSON.parse(olist_json);" + eol
        js += (
            "  let dash = ['solid', 'dot', 'dash', 'longdash', 'dashdot', 'longdashdot'];"
            + eol
        )
        js += "  var cacheList = component.state.active_cache;" + eol
        js += "  let cdata = [];" + eol
        js += "  let plt;" + eol
        js += "  for (const hash_ind in cacheList) {" + eol
        js += "    let hash_key = cacheList[hash_ind];" + eol
        js += "    var output_json = await " + cache_store + ".getItem(hash_key);" + eol
        # js += "    console.log(hash_q)" + eol
        js += "    if (!output_json || output_json == '')" + eol
        js += "      return;" + eol
        js += "    var jsonOutput = JSON.parse(output_json);" + eol
        js += "    var state = component.state;" + eol
        js += "    var lseq = Array();" + eol
        js += "    if (!axis_ids) {" + eol
        js += "      axis_ids = {'position':'position','function':'function'};" + eol
        js += "    }" + eol
        js += "    for (var i=0;i<seq.length;i++){" + eol
        js += "      var sequence = seq[i];" + eol
        js += "      if (sequence in jsonOutput){" + eol
        js += "        let curves = jsonOutput[sequence];" + eol
        js += "        lseq[sequence] = {" + eol
        js += "          'position':curves[axis_ids['position']]," + eol
        js += "          'function':curves[axis_ids['function']]" + eol
        js += "        };" + eol
        js += "      }" + eol
        js += "    }" + eol
        js += "    plt = component.props.plotXY(component, lseq);" + eol
        js += "    plt['data'].forEach((v, i, a) => { " + eol
        # js += "      a[i]['legendgroup'] = hash_key; " + eol
        js += "      a[i]['line']['color']=inputs[hash_key]['.color']; " + eol
        js += "      a[i]['line']['dash'] = dash[i % dash.length];" + eol
        js += "    });" + eol
        js += "    cdata = cdata.concat(plt['data']);" + eol
        js += "  }" + eol
        js += "  if (plt === undefined){" + eol
        js += "    plt = {'layout': {}};" + eol
        js += "  }" + eol
        js += "  if (layout){" + eol
        js += "    plt['layout'] = {" + eol
        js += "      ...plt['layout']," + eol
        js += "      ...layout" + eol
        js += "    };" + eol
        js += "  }" + eol
        js += "  component.setState({" + eol
        js += "    'data': cdata," + eol
        js += "    'layout': plt['layout']," + eol
        js += "    'frames': plt['frames']," + eol
        js += "    'config': {'displayModeBar': true, 'responsive': 'true'}" + eol
        js += "  });" + eol
        # js += "  window.dispatchEvent(new Event('resize'));" + eol #trying to trigger windows rescale does not work on IE
        js += (
            "  window.dispatchEvent(new Event('relayout'));" + eol
        )  # trying to trigger windows rescale does not work on IE
        js += "}" + eol
        component.addPropVariable("loadXY", {"type": "func", "defaultValue": js})

        return {"type": "propCall2", "calls": "loadXY", "args": ["self", "[]"]}

    def loadDefaultSimulation(tp, component, *args, **kwargs):
        store_name = "sessionStore"
        NanohubUtils.storageFactory(tp, store_name=store_name)
        eol = "\n"
        eol = "\n"
        js = ""
        js += "async (self) => {" + eol
        js += "  if (" + store_name + ".getItem('nanohub_token')){" + eol
        js += "    self.props.onSimulate(self);" + eol
        js += "  }" + eol
        js += "}" + eol
        component.addPropVariable(
            "loadDefaultSimulation", {"type": "func", "defaultValue": js}
        )
        return {
            "type": "propCall2",
            "calls": "loadDefaultSimulation",
            "args": ["e", "self"],
        }

    def downloadOutput(tp, component, *args, **kwargs):
        toolname = kwargs.get("toolname", "")
        revision = kwargs.get("revision", "")
        url = kwargs.get("url", "")
        store_name = "sessionStore"
        NanohubUtils.storageFactory(tp, store_name=store_name)
        cache_store = kwargs.get("cache_store", "CacheStore")
        if kwargs.get("jupyter_cache", None) is not None:
            cache_storage = kwargs.get(
                "cache_storage", "cacheFactory('" + cache_store + "', 'JUPYTERSTORAGE')"
            )
            NanohubUtils.storageFactory(
                tp,
                method_name="storageJupyterFactory",
                jupyter_cache=kwargs.get("jupyter_cache", None),
                store_name=cache_store,
                storage_name=cache_storage,
            )
        else:
            cache_storage = kwargs.get(
                "cache_storage", "cacheFactory('" + cache_store + "', 'INDEXEDDB')"
            )
            NanohubUtils.storageFactory(
                tp, store_name=cache_store, storage_name=cache_storage
            )

        eol = "\n"
        js = ""
        js += "async (self, component) => {" + eol
        js += (
            "  var olist_json = await " + cache_store + ".getItem('cache_list');" + eol
        )
        js += "  if (!olist_json || olist_json == '')" + eol
        js += "    olist_json = '{}';" + eol
        js += "  let inputs = JSON.parse(olist_json);" + eol
        js += "  for (const input in inputs) {" + eol
        js += "    let data = {" + eol
        js += "      'name': '" + toolname + "', " + eol
        js += "      'revision': '" + str(revision) + "', " + eol
        js += "      'inputs': inputs[input], " + eol
        js += "      'outputs' : [component]," + eol
        js += "      'cores' : inputs[input]['cores']," + eol
        js += "      'cutoff' : inputs[input]['cutoff']," + eol
        js += "      'venue' : inputs[input]['venue']" + eol
        js += "    }" + eol
        js += (
            "    var nanohub_token = " + store_name + ".getItem('nanohub_token');" + eol
        )
        js += (
            "    var header_token = {'Authorization': 'Bearer ' + nanohub_token}" + eol
        )
        js += "    var url = '" + url + "/run';" + eol
        js += (
            "    var options = { 'handleAs' : 'json' , 'headers' : header_token, 'method' : 'POST', 'data' : data };"
            + eol
        )
        js += "    try{" + eol
        js += "      Axios.request(url, options)" + eol
        js += "      .then(function(response){" + eol
        js += "        var data = response.data;" + eol
        # js += "        console.log(data);" + eol
        js += "        if(data.code){" + eol
        js += "          if(data.message){" + eol
        # js += "            self.props.onError( '(' + data.code + ') ' +data.message );" + eol
        js += "          } else {" + eol
        # js += "            self.props.onError( '(' + data.code + ') Error sending the simulation' );" + eol
        js += "          } " + eol
        js += "        }else{" + eol
        js += "          if(data.id){" + eol
        js += "            if('outputs' in data){" + eol
        # js += "              self.props.onLoad(self);" + eol #TODO create window + display Data
        js += "            } else {" + eol
        js += (
            "              setTimeout(function(){ self.props.downloadOutput(self, data.id, 10) }, 5000);"
            + eol
        )
        js += "            }" + eol
        js += "          } else {" + eol
        # js += "            self.props.onError( 'Error submiting the simulation, session not found' );" + eol
        js += "          }" + eol
        js += "        }" + eol
        js += "      }).catch(function(error){" + eol
        js += "        if (error.response){" + eol
        js += "          if (error.response.data){" + eol
        js += "            if (error.response.data.message){" + eol
        # js += "              self.props.onError(String(error.response.data.message));" + eol
        js += "            } else {" + eol
        # js += "              self.props.onError(String(error.response.data));" + eol
        js += "            }" + eol
        js += "          } else {" + eol
        # js += "            self.props.onError(String(error.response));" + eol
        js += "          }" + eol
        js += "        } else {" + eol
        # js += "          self.props.onError(String(error));" + eol
        js += "        }" + eol
        js += "      });" + eol
        js += "    } catch (err) {" + eol
        # js += "      self.props.onError(String(err));" + eol
        js += "    }" + eol
        js += "  }" + eol
        js += "}" + eol
        component.addPropVariable(
            "downloadOutput", {"type": "func", "defaultValue": js}
        )
        return {"type": "propCall2", "calls": "downloadOutput", "args": ["e", "self"]}

    def loadSequence(tp, component, *args, **kwargs):
        eol = "\n"
        SimtoolBuilder.plotSequence(tp, component)
        cache_store = kwargs.get("cache_store", "CacheStore")
        if kwargs.get("jupyter_cache", None) is not None:
            cache_storage = kwargs.get(
                "cache_storage", "cacheFactory('" + cache_store + "', 'JUPYTERSTORAGE')"
            )
            NanohubUtils.storageFactory(
                tp,
                method_name="storageJupyterFactory",
                jupyter_cache=kwargs.get("jupyter_cache", None),
                store_name=cache_store,
                storage_name=cache_storage,
            )
        else:
            cache_storage = kwargs.get(
                "cache_storage", "cacheFactory('" + cache_store + "', 'INDEXEDDB')"
            )
            NanohubUtils.storageFactory(
                tp, store_name=cache_store, storage_name=cache_storage
            )
        js = ""
        js += (
            "async (component, seq, layout, axis_ids, normalize=false, start_trace=0) => {"
            + eol
        )
        js += (
            "  var olist_json = await " + cache_store + ".getItem('cache_list');" + eol
        )
        js += "  if (!olist_json || olist_json == '')" + eol
        js += "    olist_json = '{}';" + eol
        js += "  let inputs = JSON.parse(olist_json);" + eol
        js += (
            "  let dash = ['solid', 'dot', 'dash', 'longdash', 'dashdot', 'longdashdot'];"
            + eol
        )
        js += "  var cacheList = component.state.active_cache;" + eol
        js += "  let cdata = [];" + eol
        js += "  let cframes = {};" + eol
        js += "  var state = component.state;" + eol
        js += "  var lseq = {};" + eol
        js += "  let plt;" + eol
        js += "  for (const hash_ind in cacheList) {" + eol
        js += "    let hash_key = cacheList[hash_ind];" + eol
        js += "    var output_json = await " + cache_store + ".getItem(hash_key);" + eol
        js += "    if (!output_json || output_json == '')" + eol
        js += "      return;" + eol
        js += "    var jsonOutput = JSON.parse(output_json);" + eol
        js += "    if (!axis_ids) {" + eol
        js += "      axis_ids = {'position':'position','function':'function'};" + eol
        js += "    }" + eol
        js += "    for (var i=0;i<seq.length;i++){" + eol
        js += "      var sequence = seq[i];" + eol
        js += "      if (sequence in jsonOutput){" + eol
        js += "        let curves = jsonOutput[sequence];" + eol
        js += "        for (const [key, value] of Object.entries(curves)){" + eol
        js += "          if (key == axis_ids['position']){" + eol
        js += "            for (let key2 in lseq){" + eol
        js += "              lseq[key2][sequence] = {" + eol
        js += "                'position':curves[axis_ids['position']]," + eol
        js += "                'function':curves[axis_ids['function']]" + eol
        js += "              };" + eol
        js += "            }" + eol
        js += "            break;" + eol
        js += "          }" + eol
        js += "          if (!(key in lseq)){" + eol
        js += "            lseq[key] = {};" + eol
        js += "          }" + eol
        js += "          lseq[key][sequence] = {" + eol
        js += "            'position':curves[key][axis_ids['position']]," + eol
        js += "            'function':curves[key][axis_ids['function']]" + eol
        js += "          };" + eol
        js += "        }" + eol
        js += "      }" + eol
        js += "    }" + eol
        js += (
            "    plt = component.props.plotSequence(component, lseq, normalize, start_trace);"
            + eol
        )
        js += "    cdata = cdata.concat(plt['data']);" + eol
        js += (
            "    plt['frames'].forEach((p) => { p['data'].forEach((v, i, a) => { " + eol
        )
        js += "      a[i]['line']['color']=inputs[hash_key]['.color']; " + eol
        js += "      a[i]['line']['dash'] = dash[i % dash.length];" + eol
        js += "    }); });" + eol
        js += (
            "    plt['frames'].forEach(e => { if (!(e['name'] in cframes )) cframes[e['name']]=[]; });"
            + eol
        )
        js += (
            "    plt['frames'].forEach(e => { cframes[e['name']] = cframes[e['name']].concat(e['data'])} ); ;"
            + eol
        )
        js += "  }" + eol
        js += "  if (plt === undefined){" + eol
        js += "    plt = {'layout': {}};" + eol
        js += "  }" + eol
        js += "  function mergeDeep(target, source) {" + eol
        js += "    const isObject = (obj) => obj && typeof obj === 'object';" + eol
        js += "    if (!isObject(target) || !isObject(source)) {" + eol
        js += "      return source;" + eol
        js += "    }" + eol
        js += "    Object.keys(source).forEach(key => {" + eol
        js += "      const targetValue = target[key];" + eol
        js += "      const sourceValue = source[key];" + eol
        js += (
            "      if (Array.isArray(targetValue) && Array.isArray(sourceValue)) {"
            + eol
        )
        js += "        target[key] = targetValue.concat(sourceValue);" + eol
        js += "      } else if (isObject(targetValue) && isObject(sourceValue)) {" + eol
        js += (
            "        target[key] = mergeDeep(Object.assign({}, targetValue), sourceValue);"
            + eol
        )
        js += "      } else {" + eol
        js += "        target[key] = sourceValue;" + eol
        js += "      }" + eol
        js += "    });" + eol
        js += "    return target;" + eol
        js += "  }" + eol
        js += "  if (layout){" + eol
        js += "    mergeDeep (plt['layout'], layout);" + eol
        js += (
            "    if (layout['xaxis'] && layout['xaxis']['type'] && layout['xaxis']['type'] == 'log'){"
            + eol
        )
        js += "      if (plt['layout']['xaxis']['range'][0] == 0){" + eol
        js += "        plt['layout']['xaxis']['range'][0] = 1e-20;" + eol
        js += "      }" + eol
        js += (
            "      plt['layout']['xaxis']['range'][0] = Math.log10(plt['layout']['xaxis']['range'][0]);"
            + eol
        )
        js += (
            "      plt['layout']['xaxis']['range'][1] = Math.log10(plt['layout']['xaxis']['range'][1]);"
            + eol
        )
        js += "    }" + eol
        js += (
            "    if (layout['yaxis'] && layout['yaxis']['type'] && layout['yaxis']['type'] == 'log'){"
            + eol
        )
        js += "      if (plt['layout']['yaxis']['range'][0] == 0){" + eol
        js += "        plt['layout']['yaxis']['range'][0] = 1e-20;" + eol
        js += "      }" + eol
        js += (
            "      plt['layout']['yaxis']['range'][0] = Math.log10(plt['layout']['yaxis']['range'][0]);"
            + eol
        )
        js += (
            "      plt['layout']['yaxis']['range'][1] = Math.log10(plt['layout']['yaxis']['range'][1]);"
            + eol
        )
        js += "    }    " + eol
        js += "  }" + eol
        js += "  cframes = Object.keys(cframes).map((key, index) => ({" + eol
        js += "    data: cframes[key]," + eol
        js += "    name: key" + eol
        js += "  }));" + eol
        js += "  component.setState({" + eol
        js += "    'data': cdata," + eol
        js += "    'layout': plt['layout']," + eol
        js += "    'frames': cframes," + eol
        js += "    'config': {'displayModeBar': true, 'responsive': 'true'}" + eol
        js += "  });" + eol
        # js += "  window.dispatchEvent(new Event('resize'));"
        js += "  window.dispatchEvent(new Event('relayout'));"

        js += "}" + eol
        component.addPropVariable("loadSequence", {"type": "func", "defaultValue": js})

        return {"type": "propCall2", "calls": "loadSequence", "args": ["self", "[]"]}

    def buildSchema(tp, Component, *args, **kwargs):
        store_name = "sessionStore"
        NanohubUtils.storageFactory(tp, store_name=store_name)
        toolname = kwargs.get("toolname", "")
        revision = kwargs.get("revision", "")
        url = kwargs.get("url", "https://nanohub.org/api/results/simtools")
        eol = "\n"
        js = ""
        js += "async (self) => {"
        js += "  var nanohub_token = " + store_name + ".getItem('nanohub_token');" + eol
        js += (
            "  var header_token = {'Authorization': 'Bearer ' + nanohub_token, 'Content-Type': 'application/x-www-form-urlencoded', 'Accept': '*/*' };"
            + eol
        )
        js += (
            "  var options = { 'handleAs' : 'json' , 'headers' : header_token, 'method' : 'GET' };"
            + eol
        )
        js += (
            "  var url = '"
            + url
            + "/get/"
            + toolname
            + "/"
            + str(revision)
            + "';"
            + eol
        )
        js += "  let params = {};" + eol
        js += "  let selfr = self;" + eol
        js += "  try{" + eol
        js += "    await Axios.request(url, options)" + eol
        js += "    .then(function(response){" + eol
        js += "      var data = response.data;" + eol
        js += "      var schema = data.tool;" + eol
        js += "      var schema_json = JSON.stringify(schema);" + eol
        js += "      if (schema_json){" + eol
        js += (
            "        "
            + store_name
            + ".setItem('nanohub_tool_schema', schema_json);"
            + eol
        )
        js += "        selfr.props.onLoadSchema(selfr)"
        js += "      } else {" + eol
        js += "        selfr.props.onSchemaError(selfr)"
        js += "      }" + eol
        js += "    }).catch(function(error){" + eol
        js += "      if (error.response){" + eol
        js += "        if (error.response.data){" + eol
        js += "          if (error.response.data.message){" + eol
        js += (
            "            selfr.props.onSchemaError(String(error.response.data.message));"
            + eol
        )
        js += "          } else {" + eol
        js += (
            "            selfr.props.onSchemaError(String(error.response.data));" + eol
        )
        js += "          }" + eol
        js += "        } else {" + eol
        js += "          selfr.props.onSchemaError(String(error.response));" + eol
        js += "        }" + eol
        js += "      } else {" + eol
        js += "        selfr.props.onSchemaError(String(error));" + eol
        js += "      }" + eol
        js += "    });" + eol
        js += "  } catch (err){" + eol
        js += "    selfr.props.onSchemaError(selfr)"
        js += "  }" + eol
        js += "}" + eol

        Component.addPropVariable("buildSchema", {"type": "func", "defaultValue": js})
        Component.addPropVariable(
            "onLoadSchema", {"type": "func", "defaultValue": "(e)=>{}"}
        )
        Component.addPropVariable(
            "onSchemaError", {"type": "func", "defaultValue": "(e)=>{}"}
        )
        callbacklist = []

        callbacklist.append(
            {"type": "propCall2", "calls": "buildSchema", "args": ["self"]}
        )
        return callbacklist

    def refreshViews(tp, Component, *args, **kwargs):

        cache_store = kwargs.get("cache_store", "CacheStore")
        if kwargs.get("jupyter_cache", None) is not None:
            cache_storage = kwargs.get(
                "cache_storage", "cacheFactory('" + cache_store + "', 'JUPYTERSTORAGE')"
            )
            NanohubUtils.storageFactory(
                tp,
                method_name="storageJupyterFactory",
                jupyter_cache=kwargs.get("jupyter_cache", None),
                store_name=cache_store,
                storage_name=cache_storage,
            )
        else:
            cache_storage = kwargs.get(
                "cache_storage", "cacheFactory('" + cache_store + "', 'INDEXEDDB')"
            )
            NanohubUtils.storageFactory(
                tp, store_name=cache_store, storage_name=cache_storage
            )

        eol = "\n"
        js = "async (self)=>{" + eol
        js += "  let selfr = self;" + eol
        js += (
            "  var olist_json = await " + cache_store + ".getItem('cache_list');" + eol
        )

        ####
        js += "  if (!olist_json || olist_json == ''){" + eol
        js += "    selfr.setState({'cached_results':[]});" + eol
        js += "    return;" + eol
        js += "  }" + eol
        js += "  var cacheList = JSON.parse(olist_json);" + eol
        js += "  var listState = [];" + eol
        js += "  for (const key in cacheList) {" + eol
        js += "    let inputs = cacheList[key];" + eol
        js += "    let c = '#F00';" + eol
        js += "    let d = '';" + eol
        js += "    for (const input in inputs) {" + eol
        js += (
            "      d += JSON.stringify(input) + ' : ' + JSON.stringify(inputs[input]) + '\\n';"
            + eol
        )
        js += "    }" + eol
        js += "    listState.push({" + eol
        js += "      'id':key," + eol
        js += "      'icon':'show_chart'," + eol
        js += "      'value':key," + eol
        js += "      'style':{'color':inputs['.color']}," + eol
        js += "      'description' : d" + eol
        js += "    });" + eol
        js += "  }" + eol
        # js += "  console.log(listState);" + eol
        js += "  selfr.setState({'cached_results':listState});" + eol

        js += "  let vis = selfr.state['visualization']; " + eol
        js += "  if (vis['function'] == 'loadSequence'){" + eol
        js += (
            "      selfr.props.loadSequence(selfr, vis['dataset'], vis['layout'], vis['parameters'], vis['normalize'], vis['start_trace']);"
            + eol
        )
        js += "  } else if (vis['function'] == 'loadXY'){" + eol
        js += (
            "      selfr.props.loadXY(selfr, vis['dataset'], vis['layout'], vis['parameters']);"
            + eol
        )
        js += "  }" + eol
        ###
        js += "}" + eol
        Component.addPropVariable("refreshViews", {"type": "func", "defaultValue": js})

        return [{"type": "propCall2", "calls": "refreshViews", "args": ["self", ""]}]

    def removeCacheRecord(tp, Component, *args, **kwargs):
        cache_store = kwargs.get("cache_store", "CacheStore")
        if kwargs.get("jupyter_cache", None) is not None:
            cache_storage = kwargs.get(
                "cache_storage", "cacheFactory('" + cache_store + "', 'JUPYTERSTORAGE')"
            )
            NanohubUtils.storageFactory(
                tp,
                method_name="storageJupyterFactory",
                jupyter_cache=kwargs.get("jupyter_cache", None),
                store_name=cache_store,
                storage_name=cache_storage,
            )
        else:
            cache_storage = kwargs.get(
                "cache_storage", "cacheFactory('" + cache_store + "', 'INDEXEDDB')"
            )
            NanohubUtils.storageFactory(
                tp, store_name=cache_store, storage_name=cache_storage
            )
        eol = "\n"
        js = "async (self)=>{" + eol
        js += "  let selfr = self;" + eol
        js += (
            "  var olist_json = await " + cache_store + ".getItem('cache_list');" + eol
        )
        js += "  if (!olist_json || olist_json == ''){" + eol
        js += "    return;" + eol
        js += "  }" + eol
        js += "  var cacheList = JSON.parse(olist_json);" + eol
        js += "  var listState = {};" + eol
        js += "  var nactive_cache = [];" + eol
        js += "  var nlastSelected = [];" + eol
        js += "  for (const key in cacheList) {" + eol
        js += "    if (!selfr.state.lastSelected.includes(key)){" + eol
        js += "      listState[key]=cacheList[key];" + eol
        js += "      if (self.state.active_cache.includes(key)){" + eol
        js += "        nactive_cache.push(key)" + eol
        js += "      }" + eol
        js += "      if (key in self.state.lastSelected){" + eol
        js += "        nlastSelected.push(key)" + eol
        js += "      }" + eol
        js += "    }" + eol
        js += "  }" + eol
        js += (
            "  var hash_q = await "
            + cache_store
            + ".setItem('cache_list', JSON.stringify(listState), (e)=>{self.props.onError(e.toString())});"
            + eol
        )
        js += (
            "  var hash_q = "
            + cache_store
            + ".removeItem(selfr.state.lastSelected);"
            + eol
        )
        js += (
            "  selfr.setState({'active_cache':nactive_cache, 'lastSelected':[]},() => selfr.props.refreshViews(selfr));"
            + eol
        )
        js += "}" + eol
        Component.addPropVariable(
            "removeCacheRecord", {"type": "func", "defaultValue": js}
        )

        return [
            {"type": "propCall2", "calls": "removeCacheRecord", "args": ["self", ""]}
        ]
