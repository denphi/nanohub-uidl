import weakref
import os
import json
import re
from IPython.display import HTML, Javascript, display

class InstanceTracker(object):
    __instances__ = weakref.WeakValueDictionary()

    def __init__(self, *args, **kwargs):
        self.__instances__[id(self)] = self

    @classmethod
    def find_instance(cls, obj_id):
        return cls.__instances__.get(obj_id, None)


class JupyterCache(InstanceTracker):
    def __init__(self):
        InstanceTracker.__init__(self)
        self.ref = id(self)
        self.cache = {}

    def _initStorage(self, options={}):
        return True

    def _support(self, options={}):
        return True

    def clear(self, callback=None):
        self.cache = {}
        return True

    def getItem(self, key, callback=None):
        if callback is not None:
            callback()
        if key in self.cache:
            return self.cache[key]
        else:
            if os.path.isfile(key):
                with open(key, "rt") as f:
                    xml = f.read()
                    self.cache[key] = xml
                    return self.cache[key]
        return None

    def iterate(self, iteratorCallback={}, successCallback={}):
        raise "Not supported"
        return False

    def key(self, n, callback=None):
        if callback is not None:
            callback()
        if self.length() <= n:
            return self.cache.keys()[n]
        return None

    def keys(self, callback=None):
        if callback is not None:
            callback()
        return self.cache.keys()

    def length(self, callback=None):
        if callback is not None:
            callback()
        return len(self.cache.keys())

    def removeItem(self, key, callback=None):
        if callback is not None:
            callback()
        if key in self.cache:
            del self.cache[key]
            os.remove(key)
        return True

    def setItem(self, key, value, callback=None):
        if callback is not None:
            callback()
        with open(key, "wt") as f:
            f.write(value)
        self.cache[key] = value
        return True


class NanohubUtils:
    def jupyterCache(tp, cache, *args, **kwargs):
        method_name = kwargs.get("method_name", "JUPYTERSTORAGE")
        driver_name = kwargs.get("driver_name", "jupyterStorage")

        eol = "\n"
        js = ""
        js += "function " + method_name + "(){" + eol
        js += "  function exec_j (command, p){" + eol
        js += "    var command_j = 'from uidl.material import JupyterCache;'" + eol
        js += "    command_j     += 'import json;'" + eol
        js += (
            "    command_j     += 'tmp = JupyterCache.find_instance("
            + str(cache.ref)
            + ");'"
            + eol
        )
        js += "    command_j     += 'print(json.dumps(tmp.' + command + '));'" + eol
        js += "    var kernel = IPython.notebook.kernel;" + eol
        # js += "    console.log(command_j);"+ eol;
        js += "    if(p!=undefined){" + eol
        js += "      let wp = p;" + eol
        js += "      var t = kernel.execute(command_j, {" + eol
        js += "        iopub: {" + eol
        js += "          output: (m)=>{ " + eol
        js += "            console.log(command, m);" + eol
        js += "            if(m.content != undefined){" + eol
        js += "              if(m.content.text != undefined){" + eol
        js += "                wp.resolve(JSON.parse(m.content.text)); " + eol
        js += "              } else if(m.content.traceback != undefined){" + eol
        js += "                wp.reject(); " + eol
        js += "              } else {" + eol
        js += "                wp.resolve(); " + eol
        js += "              }" + eol
        js += "            } else {" + eol
        js += "              wp.resolve(); " + eol
        js += "            }" + eol
        js += "          }" + eol
        js += "        }" + eol
        js += "      });" + eol
        js += "    } else {" + eol
        js += "      var t = kernel.execute(command_j, {" + eol
        js += "        iopub: {" + eol
        js += "          'output': (m)=>{ " + eol
        # js += "            console.log(command, m);"+ eol;
        js += "            if(m.content != undefined){" + eol
        js += "              if(m.content.text != undefined){" + eol
        js += "                return (JSON.parse(m.content.text));" + eol
        js += "              } else if( m.content.traceback != undefined){" + eol
        js += "                wp.reject(); " + eol
        js += "              } else {" + eol
        js += "                wp.resolve(); " + eol
        js += "              }" + eol
        js += "            }" + eol
        js += "          }" + eol
        js += "        }" + eol
        js += "      });" + eol
        js += "    }" + eol
        js += "  }" + eol
        js += "  function defer() {" + eol
        js += "    var res, rej;" + eol
        js += "    var promise = new Promise((resolve, reject) => {" + eol
        js += "      res = resolve;" + eol
        js += "      rej = reject;" + eol
        js += "    });" + eol
        js += "    promise.resolve = res;" + eol
        js += "    promise.reject = rej;" + eol
        js += "    return promise;" + eol
        js += "  }" + eol
        js += "  return {" + eol
        js += "    _driver: '" + driver_name + "'," + eol
        js += "    _initStorage: function(options) {" + eol
        js += "      var p = defer();" + eol
        js += "      exec_j('_initStorage()', p);" + eol
        js += "      return p;" + eol
        js += "    }," + eol
        js += "    _support: async function(options) {" + eol
        js += "      if (typeof IPython === 'undefined'){" + eol
        js += "        return false; " + eol
        js += "      } else { " + eol
        js += "        var p = defer();" + eol
        js += "        exec_j('_support()', p);" + eol
        js += "        return p;" + eol
        js += "      }" + eol
        js += "    }," + eol
        js += "    clear: async function(callback) {" + eol
        js += "      var p = defer();" + eol
        js += "      exec_j('clear()', p);" + eol
        js += "      return p;" + eol
        js += "    }," + eol
        js += "    getItem: async function(key, callback) {" + eol
        js += "      var p = defer();" + eol
        js += "      exec_j('getItem(\\'\\'\\''+key+'\\'\\'\\')', p);" + eol
        js += "      return p;" + eol
        js += "    }," + eol
        js += "    iterate: async function(iteratorCallback, successCallback) {" + eol
        js += "      var p = defer();" + eol
        js += "      exec_j('iterate(None,None)', p);" + eol
        js += "      return p;" + eol
        js += "    },    " + eol
        js += "    key: async function(n, callback) {" + eol
        js += "      var p = defer();" + eol
        js += "      exec_j('key(\\'\\'\\''+n+'\\'\\'\\')', p);" + eol
        js += "      return p;" + eol
        js += "    }," + eol
        js += "    keys: async function(callback) {" + eol
        js += "      var p = defer();" + eol
        js += "      exec_j('keys()', p);" + eol
        js += "      return p;" + eol
        js += "    }," + eol
        js += "    length: async function(callback) {" + eol
        js += "      var p = defer();" + eol
        js += "      exec_j('length()', p);" + eol
        js += "      return p;" + eol
        js += "    }," + eol
        js += "    removeItem: async function(key, callback) {" + eol
        js += "      var p = defer();" + eol
        js += "      exec_j('removeItem(\\'\\'\\''+key+'\\'\\'\\')', p);" + eol
        js += "      return p;" + eol
        js += "    }," + eol
        js += "    setItem: async function(key, value, callback) {" + eol
        js += "      var p = defer();" + eol
        js += (
            "      exec_j('setItem(\\'\\'\\''+key+'\\'\\'\\', \\'\\'\\''+value+'\\'\\'\\')', p);"
            + eol
        )
        js += "      return p;" + eol
        js += "    }" + eol
        js += "  }" + eol
        js += "}" + eol

        # tp.globals.addAsset(method_name, {
        #  "type": "script",
        #  "content": js
        # })
        tp.globals.addCustomCode(method_name, js)

        js = ""
        js += " LocalForage." + method_name + " = '" + driver_name + "'; " + eol
        js += " LocalForage.defineDriver(" + method_name + "()).then(()=>{" + eol
        js += "   LocalForage.setDriver(['" + driver_name + "']);" + eol
        js += " }).then(function() {" + eol
        js += "   LocalForage.ready();" + eol
        js += " }).then(function() {" + eol
        js += " });" + eol

        # tp.globals.addAsset("_" + method_name, {
        #  "type": "script",
        #  "content": js
        # })
        tp.globals.addCustomCode("_" + method_name, js)

        return [{"type": "propCall", "calls": method_name, "args": []}]

    def storageFactory(tp, *args, **kwargs):

        method_name = kwargs.get("method_name", "storageFactory")
        storage_name = kwargs.get("storage_name", "window.sessionStorage")
        store_name = kwargs.get("store_name", "sessionStore")

        component = tp.project_name
        component = "_" + re.sub("[^a-zA-Z0-9]+", "", component) + "_"

        if kwargs.get("jupyter_cache", None) is not None:
            NanohubUtils.jupyterCache(tp, kwargs.get("jupyter_cache", None))
        eol = "\n"
        js = ""
        js += "function cacheFactory(name, type){" + eol
        js += (
            "  if (type=='INDEXEDDB' && LocalForage.supports(LocalForage.INDEXEDDB)){"
            + eol
        )
        js += (
            "    return LocalForage.createInstance({'name': name, 'driver': [LocalForage.INDEXEDDB]})"
            + eol
        )
        js += (
            "  } else if (type=='LOCALSTORAGE' && LocalForage.supports(LocalForage.LOCALSTORAGE)){"
            + eol
        )
        js += (
            "    return LocalForage.createInstance({'name': name, 'driver': [LocalForage.LOCALSTORAGE]})"
            + eol
        )
        if kwargs.get("jupyter_cache", None) is not None:
            js += (
                "  } else if (type=='JUPYTERSTORAGE' && LocalForage.supports(LocalForage.JUPYTERSTORAGE)){"
                + eol
            )
            js += (
                "    return LocalForage.createInstance({'name': name, 'driver': [LocalForage.JUPYTERSTORAGE]})"
                + eol
            )
        js += "  }" + eol
        js += "  return undefined;" + eol
        js += "}" + eol

        js += "function getCookie(cname) {" + eol
        js += "  let name = cname + '=';" + eol
        js += "  let decodedCookie = decodeURIComponent(document.cookie);" + eol
        js += "  let ca = decodedCookie.split(';');" + eol
        js += "  for(let i = 0; i <ca.length; i++) {" + eol
        js += "    let c = ca[i];" + eol
        js += "    while (c.charAt(0) == ' ') {" + eol
        js += "      c = c.substring(1);" + eol
        js += "    }" + eol
        js += "    if (c.indexOf(name) == 0) {" + eol
        js += "      return c.substring(name.length, c.length);" + eol
        js += "   }" + eol
        js += " }" + eol
        js += " return '';" + eol
        js += "}" + eol

        js += "function " + method_name + " (getStorage){" + eol
        js += "  /* ISC License (ISC). Copyright 2017 Michal Zalecki */" + eol
        js += "  let inMemoryStorage = {};" + eol
        js += "  function isSupported() {" + eol
        js += "    try {" + eol
        js += (
            "      const testKey = '__some_random_key_you_are_not_going_to_use__';"
            + eol
        )
        js += "      var test = getStorage().setItem(testKey, testKey);" + eol
        js += "      if (test)" + eol
        js += "        getStorage();" + eol
        js += "      getStorage().removeItem(testKey);" + eol
        js += "      return true;" + eol
        js += "    } catch (e) {" + eol
        js += "      console.log('Accessing InMemory');" + eol
        js += "      return false;" + eol
        js += "    }" + eol
        js += "  }" + eol
        js += "  function clear(){" + eol
        js += "    if (isSupported()) {" + eol
        js += "      getStorage().clear();" + eol
        js += "    } else {" + eol
        js += "      inMemoryStorage = {};" + eol
        js += "    }" + eol
        js += "  }" + eol
        js += "  function getItem(name){" + eol
        js += "    let n = '" + component + "' + name" + eol
        js += "    if (isSupported()) {" + eol
        js += "      return getStorage().getItem(n);" + eol
        js += "    }" + eol
        js += "    if (inMemoryStorage.hasOwnProperty(n)) {" + eol
        js += "      return inMemoryStorage[n];" + eol
        js += "    }" + eol
        js += "    return null;" + eol
        js += "  }" + eol

        js += "  function key(index){" + eol
        js += "    if (isSupported()) {" + eol
        js += "      return getStorage().key(index);" + eol
        js += "    } else {" + eol
        js += "      return Object.keys(inMemoryStorage)[index] || null;" + eol
        js += "    }" + eol
        js += "  }" + eol

        js += "  function keys(){" + eol
        js += "    if (isSupported()) {" + eol
        js += "      return getStorage().keys();" + eol
        js += "    } else {" + eol
        js += "      return Object.keys(inMemoryStorage) || [];" + eol
        js += "    }" + eol
        js += "  }" + eol

        js += "  function removeItem(name){" + eol
        js += "    let n = '" + component + "' + name" + eol
        js += "    if (isSupported()) {" + eol
        js += "      getStorage().removeItem(n);" + eol
        js += "    } else {" + eol
        js += "      delete inMemoryStorage[n];" + eol
        js += "    }" + eol
        js += "  }" + eol

        js += "  function setItem(name, value){" + eol
        js += "    let n = '" + component + "' + name" + eol
        js += "    if (isSupported()) {" + eol
        js += "      getStorage().setItem(n, value);" + eol
        js += "    } else {" + eol
        js += "      inMemoryStorage[n] = String(value);" + eol
        js += "    }" + eol
        js += "  }" + eol

        js += "  function length(){" + eol
        js += "    if (isSupported()) {" + eol
        js += "      return getStorage().length;" + eol
        js += "    } else {" + eol
        js += "      return Object.keys(inMemoryStorage).length;" + eol
        js += "    }" + eol
        js += "  }" + eol

        js += "  return {" + eol
        js += "    getItem," + eol
        js += "    setItem," + eol
        js += "    removeItem," + eol
        js += "    clear," + eol
        js += "    key," + eol
        js += "    keys," + eol
        js += "    get length() {" + eol
        js += "      return length();" + eol
        js += "    }," + eol
        js += "  };" + eol
        js += "};" + eol

        # tp.globals.addAsset(method_name, {
        #  "type": "script",
        #  "content": js
        # })
        tp.globals.addCustomCode(method_name, js)

        # tp.globals.addAsset(store_name, {
        #  "type": "script",
        #  "content": "const " + store_name + " = " + method_name + "(() => " + storage_name + ");" + eol
        # })

        tp.globals.addCustomCode(
            store_name,
            "const "
            + store_name
            + " = "
            + method_name
            + "(() => "
            + storage_name
            + ");"
            + eol,
        )

        return [{"type": "propCall", "calls": method_name, "args": []}]
