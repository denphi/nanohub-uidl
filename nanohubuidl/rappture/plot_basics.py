from .dom import getText, getXY

def buildXYPlotly(tp, component, *args, **kwargs):
    eol = "\n"
    getText(tp, component)
    getXY(tp, component)
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
    js += (
        "    var rapp_component = component.props.getXY(component, field, 'component');"
        + eol
    )
    js += (
        "    var label = component.props.getText(component, field, ['about','label']);"
        + eol
    )
    js += (
        "    var style = component.props.getText(component,field, ['about','style']);"
        + eol
    )
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
    js += (
        "    title = component.props.getText(component,field, ['about','group']);"
        + eol
    )
    js += (
        "    var xaxis = component.props.getText(component,field, ['xaxis','label']);"
        + eol
    )
    js += (
        "    var xunits = component.props.getText(component,field, ['xaxis','units']);"
        + eol
    )
    js += (
        "    var xscale = component.props.getText(component,field, ['xaxis','scale']);"
        + eol
    )
    js += "    try{" + eol
    js += "      var tempval;" + eol
    js += "      if (xrange[0] == undefined){" + eol
    js += (
        "        tempval = parseFloat(component.props.getText(component,field, ['xaxis','min']));"
        + eol
    )
    js += "      } else{" + eol
    js += (
        "        tempval = min(xrange[0], parseFloat(component.props.getText(component,field, ['xaxis','min'])));"
        + eol
    )
    js += "      }" + eol
    js += "      if ( !isNaN(tempval)){" + eol
    js += "        xrange[0] = tempval;" + eol
    js += "      }" + eol
    js += "    } catch(error){}" + eol
    js += "    try{" + eol
    js += "      var tempval;" + eol
    js += "      if (xrange[1] == undefined){" + eol
    js += (
        "        tempval = parseFloat(component.props.getText(component,field, ['xaxis','max']));"
        + eol
    )
    js += "      } else{" + eol
    js += (
        "        tempval = min(xrange[1], parseFloat(component.props.getText(component,field, ['xaxis','max'])));"
        + eol
    )
    js += "      }" + eol
    js += "      if ( !isNaN(tempval)){" + eol
    js += "        xrange[1] = tempval;" + eol
    js += "      }" + eol
    js += "    } catch(error){}" + eol
    js += "    try{" + eol
    js += "      var tempval;" + eol
    js += "      if (yrange[0] == undefined){" + eol
    js += (
        "        tempval = parseFloat(component.props.getText(component,field, ['yaxis','min']));"
        + eol
    )
    js += "      } else{" + eol
    js += (
        "        tempval = min(yrange[0], parseFloat(component.props.getText(component,field, ['yaxis','min'])));"
        + eol
    )
    js += "      }" + eol
    js += "      if ( !isNaN(tempval)){" + eol
    js += "        yrange[0] = tempval;" + eol
    js += "      }" + eol
    js += "    } catch(error){}" + eol
    js += "    try{" + eol
    js += "      var tempval;" + eol
    js += "      if (yrange[1] == undefined){" + eol
    js += (
        "        tempval = parseFloat(component.props.getText(component,field, ['yaxis','max']));"
        + eol
    )
    js += "      } else{" + eol
    js += (
        "        tempval = min(yrange[1], parseFloat(component.props.getText(component,field, ['yaxis','max'])));"
        + eol
    )
    js += "      }" + eol
    js += "      if ( !isNaN(tempval)){" + eol
    js += "        yrange[1] = tempval;" + eol
    js += "      }" + eol
    js += "    } catch(error){}" + eol
    js += "    if (xscale == ''){" + eol
    js += "      xscale = 'linear';" + eol
    js += (
        "      yaxis = component.props.getText(component,field, ['yaxis','label']);"
        + eol
    )
    js += (
        "      yunits = component.props.getText(component,field, ['yaxis','units']);"
        + eol
    )
    js += (
        "      yscale = component.props.getText(component,field, ['yaxis','scale']);"
        + eol
    )
    js += "    }" + eol
    js += "    if (yscale == ''){" + eol
    js += "      yscale = 'linear';" + eol
    js += "    }" + eol
    js += "    for (var j=0;j<rapp_component.length;j++){" + eol
    js += "      var obj = rapp_component[j];" + eol
    js += (
        "      var xy = obj.trim().replace(/--/g, '').replace(/\\n|\\r/g,' ').split(/[\s]+/);"
        + eol
    )
    js += "      xy = xy.filter(function(el){ return el != '' });" + eol
    js += (
        "      let xx = xy.filter(function(el, index){ return index%2 == 0 }).map(Number);"
        + eol
    )
    js += (
        "      let yy = xy.filter(function(el, index){ return index%2 == 1 }).map(Number);"
        + eol
    )
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

    component.addPropVariable("buildXYPlotly", {"type": "func", "defaultValue": js})
    return {
        "type": "propCall2",
        "calls": "buildXYPlotly",
        "args": ["self", [], "undefined"],
    }

def plotXY(tp, component, *args, **kwargs):
    buildXYPlotly(tp, component)
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

    component.addPropVariable("plotXY", {"type": "func", "defaultValue": js})
    return {"type": "propCall2", "calls": "plotXY", "args": ["self", ""]}

def plotSequence(tp, component, *args, **kwargs):
    buildXYPlotly(tp, component)
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
    js += (
        "            minx = Math.min.apply(null, tr[t].filter((function(el){ return el > 0 })));"
        + eol
    )
    js += (
        "            maxx = Math.max.apply(null, tr[t].filter((function(el){ return el > 0 })));"
        + eol
    )
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
    js += (
        "            miny = Math.min.apply(null, tr[t].filter((function(el){ return el > 0 })));"
        + eol
    )
    js += (
        "            maxy = Math.max.apply(null, tr[t].filter((function(el){ return el > 0 })));"
        + eol
    )
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
    js += "        traces = tr.slice(0);" + eol  # clone
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
    js += "    }]" + eol
    js += "  }];" + eol
    js += "  return {'data':traces, 'frames':frms, 'layout':layout}" + eol
    js += "}" + eol

    component.addPropVariable("plotSequence", {"type": "func", "defaultValue": js})
    return {"type": "propCall2", "calls": "plotSequence", "args": ["self", []]}
