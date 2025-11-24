def getText(tp, component, *args, **kwargs):
    eol = "\n"
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
    component.addPropVariable("getText", {"type": "func", "defaultValue": js})
    return {
        "type": "propCall2",
        "calls": "getText",
        "args": ["self", "undefined", []],
    }

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
