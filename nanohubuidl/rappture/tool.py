from ..teleport.utils import NanohubUtils

def onSimulate(tp, Component, *args, **kwargs):
    store_name = "sessionStore"
    NanohubUtils.storageFactory(
        tp, store_name=store_name, storage_name="window.sessionStorage"
    )
    use_cache = kwargs.get("use_cache", True)  # TODO False by default
    cache_store = kwargs.get("cache_store", "CacheStore")
    if use_cache:
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
    url = kwargs.get("url", "")

    js = "async (self, ostate)=>{" + eol
    js += "  var state = self.state;" + eol
    js += "  " + cache_store + ".removeItem('output_xml');" + eol

    if use_cache:
        js += (
            "  self.props.onStatusChange({'target':{ 'value' : 'Checking Cache' } } );"
            + eol
        )
        js += "  var str_key = JSON.stringify(state);" + eol
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
        "  var params = JSON.parse("
        + store_name
        + ".getItem('nanohub_tool_schema'));"
        + eol
    )
    js += (
        "  var xmlDoc = JSON.parse("
        + store_name
        + ".getItem('nanohub_tool_xml'));"
        + eol
    )
    js += (
        "  self.props.onStatusChange({'target':{ 'value' : 'Parsing XML' } });"
        + eol
    )
    js += "  if (window.DOMParser){" + eol
    js += "    let parser = new DOMParser();" + eol
    js += "    xmlDoc = parser.parseFromString(xmlDoc, 'text/xml');" + eol
    js += "  } else {" + eol
    js += "    xmlDoc = new ActiveXObject('Microsoft.XMLDOM');" + eol
    js += "    xmlDoc.async = false;" + eol
    js += "    xmlDoc.loadXML(xmlDoc);" + eol
    js += "  }" + eol
    js += (
        "  self.props.onStatusChange({'target':{ 'value' : 'Loading Default Structures' } } );"
        + eol
    )
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
    js += "  }" + eol
    js += (
        "  self.props.onStatusChange({'target':{ 'value' : 'Loading Default Parameters' } } );"
        + eol
    )
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
    js += "              elem.removeChild(current[0]);" + eol
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
    js += (
        "  self.props.onStatusChange({'target':{ 'value' : 'Setting Parameters' } } );"
        + eol
    )
    js += "  for (const id in state) {" + eol
    js += "    let value = String(state[id]);" + eol
    js += "    var elems = xmlDoc.getElementsByTagName('*');" + eol
    js += "    for (var i=0;i<elems.length;i++){" + eol
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
    js += (
        "  self.props.onStatusChange({'target':{ 'value' : 'Building Rappture Invoke' } } );"
        + eol
    )
    js += (
        "  var driver_str  = '<?xml version=\"1.0\"?>\\n' + new XMLSerializer().serializeToString(xmlDoc.documentElement);"
        + eol
    )
    js += "  var driver_json = {'app': '" + toolname + "', 'xml': driver_str}" + eol
    js += "  var nanohub_token = " + store_name + ".getItem('nanohub_token');" + eol
    js += (
        "  var header_token = {'Authorization': 'Bearer ' + nanohub_token, 'Content-Type': 'application/x-www-form-urlencoded'}"
        + eol
    )
    js += "  var url = '" + url + "/run';"
    js += "  var str = [];" + eol
    js += "  for(var p in driver_json){" + eol
    js += (
        "    str.push(encodeURIComponent(p) + '=' + encodeURIComponent(driver_json[p]));"
        + eol
    )
    js += "  }" + eol
    js += "  let data =  str.join('&');" + eol
    js += (
        "  var options = { 'handleAs' : 'json' , 'headers' : header_token, 'method' : 'POST', 'data' : data };"
        + eol
    )
    js += (
        "  self.props.onStatusChange({'target':{ 'value' : 'Submitting Simulation' } } );"
        + eol
    )

    js += "  Axios.request(url, options)" + eol
    js += "  .then(function(response){" + eol
    js += "    var data = response.data;" + eol
    js += "    if(data.code){" + eol
    js += "      if(data.message){" + eol
    js += (
        "        self.props.onError( '(' + data.code + ') ' +data.message );" + eol
    )
    js += "      } else {" + eol
    js += (
        "        self.props.onError( '(' + data.code + ') Error sending the simulation' );"
        + eol
    )
    js += "      } " + eol
    js += "    }else{" + eol
    js += "      if(data.session){" + eol
    js += (
        "        setTimeout(function(){ self.props.onCheckSession(self, data.session, 10) }, 4000);"
        + eol
    )
    js += "      } else {" + eol
    js += (
        "        self.props.onError( 'Error submiting the simulation, session not found' );"
        + eol
    )
    js += "      }" + eol
    js += "    }" + eol
    js += "  }).catch(function(error){" + eol
    js += "    self.props.onError(String(error));" + eol
    js += "  })"
    if use_cache:
        js += "  } else { " + eol
        js += (
            "    self.props.onStatusChange({'target':{ 'value' : 'Loading from local Cache' } } );"
            + eol
        )
        js += (
            "    "
            + cache_store
            + ".setItem('output_xml', JSON.stringify(hash_q));"
            + eol
        )
        js += "    self.props.onSuccess(self)" + eol
        js += "  }" + eol
    js += "}"

    Component.addPropVariable("onSimulate", {"type": "func", "defaultValue": js})

    js = "(self, session_id, reload)=>{" + eol
    js += "  if (session_id == ''){" + eol
    js += "     self.props.onError('invalid Session ID');" + eol
    js += "  }" + eol
    js += "  var session_json = {'session_num': session_id};" + eol
    js += "  var nanohub_token = " + store_name + ".getItem('nanohub_token');" + eol
    js += (
        "  var header_token = {'Authorization': 'Bearer ' + nanohub_token, 'Content-Type': 'application/x-www-form-urlencoded'}"
        + eol
    )
    js += "  var url = '" + url + "/status';" + eol
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
    js += "  Axios.request(url, options)" + eol
    js += "  .then(function(response){" + eol
    js += "    var status = response.data;" + eol
    js += "    if (status['success']){" + eol
    js += "      if (status['status']){" + eol
    js += (
        "        if (status['status'].length > 0 && status['status'][0] != ''){"
        + eol
    )
    js += (
        "          self.props.onStatusChange({'target':{ 'value' : status['status'][0] } } );"
        + eol
    )
    js += "        } else {" + eol
    js += (
        "          self.props.onStatusChange({'target':{ 'value' : 'Checking status of session ' + String(session_id) } } );"
        + eol
    )
    js += "        }" + eol
    js += "        if(status['finished']){" + eol
    js += (
        "          let regex = /\[status\] output saved in [a-zA-Z0-9\/].*\/(run[0-9]*\.xml)/;"
        + eol
    )
    js += "          let m;" + eol
    js += "          if ((m = regex.exec(status['status'])) !== null) {" + eol
    js += "              self.props.onLoad(self);" + eol
    js += "              self.props.onLoadResults(self, session_id, m[1]);" + eol
    js += "          } else if(status['run_file'] != ''){" + eol
    js += "            self.props.onLoad(self);" + eol
    js += (
        "            self.props.onLoadResults(self, session_id, status['run_file']);"
        + eol
    )
    js += "          } else {" + eol
    js += "            if (reload > 0){" + eol
    js += (
        "              setTimeout(function(){self.props.onCheckSession(self, session_id, 0)},2000);"
        + eol
    )
    js += "            }" + eol
    js += "          }" + eol
    js += "        } else {" + eol
    js += "          if (reload > 0){" + eol
    js += (
        "            setTimeout(function(){self.props.onCheckSession(self, session_id, reload)},2000);"
        + eol
    )
    js += "          }" + eol
    js += "        }" + eol
    js += "      }"
    js += "    } else if (status['code']){" + eol
    js += "      if (status['code'] == 404){" + eol
    js += (
        "        setTimeout(function(){self.props.onCheckSession(self, session_id, reload-1)},8000);"
        + eol
    )
    js += "      }"
    js += "      else if (status['code'] != 200){" + eol
    js += "        self.props.onError(status['message']);" + eol
    js += "      }"
    js += "    }"
    js += "  }).catch(function(error){" + eol
    js += "    if (reload > 0 && String(error).includes('404')){" + eol
    js += (
        "      setTimeout(function(){self.props.onCheckSession(self, session_id, reload-1)},8000);"
        + eol
    )
    js += "    } else {" + eol
    js += "      self.props.onError(String(error));" + eol
    js += "    }" + eol
    js += "  })" + eol
    js += "}" + eol

    Component.addPropVariable(
        "onCheckSession", {"type": "func", "defaultValue": js}
    )

    js = "(self, session_id, run_file)=> {" + eol
    js += (
        "  var results_json = {'session_num': session_id, 'run_file': run_file};"
        + eol
    )
    js += "  var nanohub_token = " + store_name + ".getItem('nanohub_token');" + eol
    js += (
        "  var header_token = {'Authorization': 'Bearer ' + nanohub_token, 'Content-Type': 'application/x-www-form-urlencoded'}"
        + eol
    )
    js += (
        "  self.props.onStatusChange({'target':{ 'value' : 'Loading results data' } } );"
        + eol
    )
    js += "  var url = '" + url + "/output';" + eol
    js += "  var str = [];" + eol
    js += "  for(var p in results_json){" + eol
    js += (
        "    str.push(encodeURIComponent(p) + '=' + encodeURIComponent(results_json[p]));"
        + eol
    )
    js += "  }" + eol
    js += "  let data =  str.join('&');" + eol
    js += (
        "  var options = { 'handleAs' : 'json' , 'headers' : header_token, 'method' : 'POST', 'data' : data };"
        + eol
    )
    js += "  Axios.request(url, options)" + eol
    js += "  .then(async (response)=>{" + eol
    js += "    var data = response.data;" + eol
    js += "    if(data.success){" + eol
    js += "      var output = data.output;" + eol
    js += (
        "      self.props.onStatusChange({'target':{ 'value' : 'Loading' } } );"
        + eol
    )
    if use_cache:
        js += "      var str_key = JSON.stringify(self.state);" + eol
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
            + ".setItem(hash_key, output, (e)=>{self.props.onError(e.toString())});"
            + eol
        )
    js += (
        "      "
        + cache_store
        + ".setItem('output_xml', JSON.stringify(output));"
        + eol
    )
    js += "      self.props.onSuccess(self)" + eol
    js += "    }" + eol
    js += "  }).catch(function(error){" + eol
    js += "    self.props.onError(error);" + eol
    js += "  })" + eol
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

def buildSchema(tp, Component, *args, **kwargs):
    store_name = "sessionStore"
    NanohubUtils.storageFactory(tp, store_name=store_name)
    toolname = kwargs.get("toolname", "")
    url = kwargs.get("url", "https://nanohub.org/api/tools")
    eol = "\n"
    js = ""
    js += "async (self) => {"
    js += (
        "  var header_token = { 'Content-Type': 'application/x-www-form-urlencoded', 'Accept': '*/*' };"
        + eol
    )
    js += (
        "  var options = { 'handleAs' : 'xml' , 'headers' : header_token, 'method' : 'GET' };"
        + eol
    )
    js += "  var url = '" + url + "/" + toolname + "/rappturexml';" + eol
    js += "  let params = {};" + eol
    js += "  let selfr = self;" + eol
    js += "  await Axios.request(url, options)" + eol
    js += "  .then(function(response){" + eol
    js += "    var data = response.data;" + eol
    js += "    let parser = new DOMParser();   " + eol
    js += "    var periodicelement = [" + eol
    js += (
        "        ['Hydrogen','H'], ['Helium','He'], ['Lithium','Li'], ['Beryllium','Be'],"
        + eol
    )
    js += (
        "        ['Boron','B'], ['Carbon','C'], ['Nitrogen','N'], ['Oxygen','O'],"
        + eol
    )
    js += (
        "        ['Fluorine','F'], ['Neon','Ne'], ['Sodium','Na'], ['Magnesium','Mg'],"
        + eol
    )
    js += (
        "        ['Aluminium','Al'], ['Silicon','Si'], ['Phosphorus','P'], ['Sulfur','S'],"
        + eol
    )
    js += (
        "        ['Chlorine','Cl'], ['Argon','Ar'], ['Potassium','K'], ['Calcium','Ca'],"
        + eol
    )
    js += (
        "        ['Scandium','Sc'], ['Titanium','Ti'], ['Vanadium','V'], ['Chromium','Cr'],"
        + eol
    )
    js += (
        "        ['Manganese','Mn'], ['Iron','Fe'], ['Cobalt','Co'], ['Nickel','Ni'],"
        + eol
    )
    js += (
        "        ['Copper','Cu'], ['Zinc','Zn'], ['Gallium','Ga'], ['Germanium','Ge'],"
        + eol
    )
    js += (
        "        ['Arsenic','As'], ['Selenium','Se'], ['Bromine','Br'], ['Krypton','Kr'],"
        + eol
    )
    js += (
        "        ['Rubidium','Rb'], ['Strontium','Sr'], ['Yttrium','Y'], ['Zirconium','Zr'],"
        + eol
    )
    js += (
        "        ['Niobium','Nb'], ['Molybdenum','Mo'], ['Technetium','Tc'], ['Ruthenium','Ru'],"
        + eol
    )
    js += (
        "        ['Rhodium','Rh'], ['Palladium','Pd'], ['Silver','Ag'], ['Cadmium','Cd'],"
        + eol
    )
    js += (
        "        ['Indium','In'], ['Tin','Sn'], ['Antimony','Sb'], ['Tellurium','Te'],"
        + eol
    )
    js += (
        "        ['Iodine','I'], ['Xenon','Xe'], ['Caesium','Cs'], ['Barium','Ba'],"
        + eol
    )
    js += (
        "        ['Lanthanum','La'], ['Cerium','Ce'], ['Praseodymium','Pr'], ['Neodymium','Nd'],"
        + eol
    )
    js += (
        "        ['Promethium','Pm'], ['Samarium','Sm'], ['Europium','Eu'], ['Gadolinium','Gd'],"
        + eol
    )
    js += (
        "        ['Terbium','Tb'], ['Dysprosium','Dy'], ['Holmium','Ho'], ['Erbium','Er'],"
        + eol
    )
    js += (
        "        ['Thulium','Tm'], ['Ytterbium','Yb'], ['Lutetium','Lu'], ['Hafnium','Hf'],"
        + eol
    )
    js += (
        "        ['Tantalum','Ta'], ['Tungsten','W'], ['Rhenium','Re'], ['Osmium','Os'],"
        + eol
    )
    js += (
        "        ['Iridium','Ir'], ['Platinum','Pt'], ['Gold','Au'], ['Mercury','Hg'],"
        + eol
    )
    js += (
        "        ['Thallium','Tl'], ['Lead','Pb'], ['Bismuth','Bi'], ['Polonium','Po'],"
        + eol
    )
    js += (
        "        ['Astatine','At'], ['Radon','Rn'], ['Francium','Fr'], ['Radium','Ra'],"
        + eol
    )
    js += (
        "        ['Actinium','Ac'], ['Thorium','Th'], ['Protactinium','Pa'], ['Uranium','U'],"
        + eol
    )
    js += (
        "        ['Neptunium','Np'], ['Plutonium','Pu'], ['Americium','Am'], ['Curium','Cm'],"
        + eol
    )
    js += (
        "        ['Berkelium','Bk'], ['Californium','Cf'], ['Einsteinium','Es'], ['Fermium','Fm'],"
        + eol
    )
    js += (
        "        ['Mendelevium','Md'], ['Nobelium','No'], ['Lawrencium','Lr'], ['Rutherfordium','Rf'],"
        + eol
    )
    js += (
        "        ['Dubnium','Db'], ['Seaborgium','Sg'], ['Bohrium','Bh'], ['Hassium','Hs'],"
        + eol
    )
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
    js += (
        "    var discardtags = ['phase', 'group', 'option', 'image', 'note'];" + eol
    )
    js += "    for (var i=0;i<inputs.length;i++){" + eol
    js += "      var elem = inputs[i];" + eol
    js += "      if (elem.hasAttribute('id')){" + eol
    js += "        var id = elem.getAttribute('id');" + eol
    js += "        if (!(id in params)){" + eol
    js += "          var about = elem.getElementsByTagName('about');" + eol
    js += "          var description = '';" + eol
    js += "          var labelt = '';" + eol
    js += "          if (about.length > 0){" + eol
    js += (
        "            var description = elem.getElementsByTagName('description');"
        + eol
    )
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
    js += (
        "              var param = {'type': elem.tagName, 'description' : description};"
        + eol
    )
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
    js += (
        "                  let llabel = labout[0].getElementsByTagName('label');"
        + eol
    )
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
    js += (
        "                var tmparray = param['options'].filter(p => p[1] == param['default']);"
        + eol
    )
    js += "                if (tmparray.length == 0 ){" + eol
    js += "                  param['default'] = param['options'][0][1];" + eol
    js += "                }" + eol
    js += "              }" + eol
    js += "              if (param['type'] == 'string'){" + eol
    js += (
        "                if (param['default'] && /\\r|\\n/.exec(param['default'].trim())){"
        + eol
    )
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
    js += (
        "    "
        + store_name
        + ".setItem('nanohub_tool_schema', JSON.stringify(params));"
        + eol
    )
    js += (
        "    "
        + store_name
        + ".setItem('nanohub_tool_xml', JSON.stringify(data));"
        + eol
    )
    js += "    selfr.props.onLoadSchema(selfr)"
    js += "  }).catch(function(error){" + eol
    js += "    selfr.props.onSchemaError(selfr)"
    js += "  });" + eol
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
