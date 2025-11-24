from .plot_basics import plotXY, plotSequence, buildXYPlotly
from .dom import getText
from .science_advanced import getMolecule, FindPlaneIntersect
from .science_basics import getColor
from ..teleport.utils import NanohubUtils
import json
from numpy import linspace as nplinspace
from numpy import pi as nppi
from numpy import sin as npsin
from numpy import cos as npcos
from numpy import outer as npouter
from numpy import ones as npones

def loadXY(tp, component, *args, **kwargs):
    eol = "\n"
    plotXY(tp, component)
    cache_store = kwargs.get("cache_store", "CacheStore")
    NanohubUtils.storageFactory(tp, store_name=cache_store)
    js = ""
    js += "async (component, seq, layout) => {" + eol
    js += "  var output_xml = await " + cache_store + ".getItem('output_xml');" + eol
    js += "  if (!output_xml || output_xml == '')" + eol
    js += "    return;" + eol
    # js += "  console.log(output_xml);" + eol
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
    js += (
        "    if (sequence.hasAttribute('id') && seq.filter( (v) => new RegExp(v).test(sequence.getAttribute('id'))).length >0){"
        + eol
    )
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
    js += (
        "  window.dispatchEvent(new Event('resize'));" + eol
    )  # trying to trigger windows rescale does not work on IE
    js += "}" + eol
    component.addPropVariable("loadXY", {"type": "func", "defaultValue": js})

    return {"type": "propCall2", "calls": "loadXY", "args": ["self", "[]"]}

def loadXYDual(tp, component, *args, **kwargs):
    eol = "\n"
    plotXY(tp, component)
    cache_store = kwargs.get("cache_store", "CacheStore")
    NanohubUtils.storageFactory(tp, store_name=cache_store)
    js = ""
    js += "async (component, base, seq, layout) => {" + eol
    js += "  var output_xml = await " + cache_store + ".getItem('output_xml');" + eol
    js += "  if (!output_xml || output_xml == '')" + eol
    js += "    return;" + eol
    # js += "  console.log(output_xml);" + eol
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
    js += (
        "    if (sequence.hasAttribute('id') && seq.filter( (v) => new RegExp(v).test(sequence.getAttribute('id'))).length >0){"
        + eol
    )
    js += "      lseq.push(sequence);" + eol
    js += "    }" + eol
    js += (
        "    if (sequence.hasAttribute('id') && base.filter( (v) => new RegExp(v).test(sequence.getAttribute('id'))).length >0){"
        + eol
    )
    js += "      lbase.push(sequence);" + eol
    js += "    }" + eol
    js += "  }" + eol
    js += "  let pltb = component.props.plotXY(component, lbase);" + eol
    js += "  let plt = component.props.plotXY(component, lseq);" + eol
    js += (
        "  pltb['data'].forEach((v, i, a) => { a[i]['xaxis'] ='x'; if(a[i]['line']['color']=='yellow'){a[i]['line']['color'] = '#984ea3';} });"
        + eol
    )
    js += (
        "  plt['data'].forEach((v, i, a) => { a[i]['xaxis'] ='x2'; if(a[i]['line']['color']=='yellow'){a[i]['line']['color'] = '#984ea3';}});"
        + eol
    )
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
    js += (
        "  window.dispatchEvent(new Event('resize'));" + eol
    )  # trying to trigger windows rescale does not work on IE
    js += "}" + eol
    component.addPropVariable("loadXYDual", {"type": "func", "defaultValue": js})

    return {
        "type": "propCall2",
        "calls": "loadXYDual",
        "args": ["self", "[]", "[]"],
    }

def loadSequence(tp, component, *args, **kwargs):
    eol = "\n"
    plotSequence(tp, component)
    cache_store = kwargs.get("cache_store", "CacheStore")
    NanohubUtils.storageFactory(tp, store_name=cache_store)
    js = ""
    js += "async (component, seq) => {" + eol
    js += "  var output_xml = await " + cache_store + ".getItem('output_xml');" + eol
    js += "  if (!output_xml || output_xml == '')" + eol
    js += "    return;" + eol
    # js += "  console.log(output_xml);" + eol
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
    js += (
        "    if (sequence.hasAttribute('id') && seq.filter( (v) => new RegExp(v).test(sequence.getAttribute('id'))).length >0){"
        + eol
    )
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
    js += (
        "    window.dispatchEvent(new Event('resize'));" + eol
    )  # trying to trigger windows rescale does not work on IE
    js += "  }" + eol
    js += "}" + eol
    component.addPropVariable("loadSequence", {"type": "func", "defaultValue": js})

    return {"type": "propCall2", "calls": "loadSequence", "args": ["self", "[]"]}

def plotDrawingPlotly(tp, component, *args, **kwargs):
    buildXYPlotly(tp, component)
    getText(tp, component)
    getMolecule(tp, component)
    getColor(tp, component)
    samples = kwargs.get("samples", 20)
    resize = kwargs.get("resize", 0.15)
    phi = nplinspace(0, 2 * nppi, samples)
    theta = nplinspace(-nppi / 2, nppi / 2, samples)
    thetat = nplinspace(0, 2 * nppi, samples)
    linspace = nplinspace(0, 1, int(samples / 2))
    phit = nplinspace(0, nppi, samples)
    xt = npouter(npcos(thetat), npsin(phit)) * 4 * resize
    yt = npouter(npsin(thetat), npsin(phit)) * 4 * resize
    zt = npouter(npones(samples), npcos(phit)) * 4 * resize
    cosphi = npcos(phi) * resize
    cosphi[abs(cosphi) < 0.000000000001] = 0.0
    sinphi = npsin(phi) * resize
    sinphi[abs(sinphi) < 0.000000000001] = 0.0

    eol = "\n"
    js = ""
    js += "(component, sequence, method) => {" + eol
    js += "  var xt_base = " + json.dumps(xt.tolist()) + ";" + eol
    js += "  var yt_base = " + json.dumps(yt.tolist()) + ";" + eol
    js += "  var zt_base = " + json.dumps(zt.tolist()) + ";" + eol
    js += "  var cosphi = " + json.dumps(cosphi.tolist()) + ";" + eol
    js += "  var sinphi = " + json.dumps(sinphi.tolist()) + ";" + eol
    js += "  var linspace = " + json.dumps(linspace.tolist()) + ";" + eol
    js += "  var traces = [];" + eol
    js += "  var layout = {" + eol
    js += "    'scene':{'aspectmode':'data'}, " + eol
    js += "    'margin' : {'l':0,'r':0,'t':0,'b':0}," + eol
    # js += "    'template' : self.theme," + eol
    js += "  };" + eol
    js += "  var min_p = undefined;" + eol
    js += "  var max_p = undefined;" + eol
    js += "  for (var i=0;i<sequence.length;i++){" + eol
    js += "    var draw = sequence[i];" + eol
    js += (
        "    var label = component.props.getText(component, draw, ['index', 'label'])"
        + eol
    )
    js += "    var molecules = draw.querySelectorAll('molecule');" + eol
    js += "    for (var j=0;j<molecules.length;j++){" + eol
    js += (
        "      var molecule = component.props.getMolecule(component, molecules[i]);"
        + eol
    )
    js += "      if (method){" + eol
    js += "        molecule = method(component, molecule)" + eol
    js += "      }" + eol

    js += "      var colorset = new Set();" + eol
    js += (
        "      Object.values(molecule.atoms).forEach((e)=>{colorset.add(e[3])});"
        + eol
    )
    js += "      colorset = [...colorset];" + eol
    js += "      let xt = {};" + eol
    js += "      let yt = {};" + eol
    js += "      let zt = {};" + eol
    js += "      let st = {};" + eol
    js += "      let color = {};" + eol
    js += "      Object.keys(molecule.atoms).forEach((id)=>{" + eol
    js += "        var atom = molecule.atoms[id];" + eol
    js += (
        "        if (atom[5] == 'enabled' && !['Helium','Ytterbium','Xenon','Zinc'].includes(atom[3])){"
        + eol
    )
    js += (
        "          var xv = xt_base.map((e1)=>{return e1.map((e2)=>{return e2 + atom[0]})});"
        + eol
    )
    js += (
        "          var yv = yt_base.map((e1)=>{return e1.map((e2)=>{return e2 + atom[1]})});"
        + eol
    )
    js += (
        "          var zv = zt_base.map((e1)=>{return e1.map((e2)=>{return e2 + atom[2]})});"
        + eol
    )
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
    js += (
        "          xv.push(xv[0].map((ii)=>{return ii}),xv[1].map((ii)=>{return ii}),[]);"
        + eol
    )
    js += (
        "          yv.push(yv[0].map((ii)=>{return ii}),yv[1].map((ii)=>{return ii}),[]);"
        + eol
    )
    js += (
        "          zv.push(zv[0].map((ii)=>{return ii}),zv[1].map((ii)=>{return ii}),[]);"
        + eol
    )
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
    js += "      min_p = min_p.map((m)=>{return m-" + str(resize * 4) + ";});" + eol
    js += "      max_p = max_p.map((m)=>{return m+" + str(resize * 4) + ";});" + eol
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
    js += (
        "        colorscalea.push([(i+1)/(total_atms),component.props.getColor(component, atom)]);"
        + eol
    )
    js += (
        "        xt[atom].forEach((x)=>{cv.push(x.map((p)=>{ return (i+1); }));});"
        + eol
    )
    js += (
        "        xt[atom].forEach((x)=>{texts.push(x.map((p)=>{ return ''+atom; }));});"
        + eol
    )
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
    js += (
        "          var u = [0,1,2].map( (i) => { return atoms[at2][i]-atoms[at1][i]; });"
        + eol
    )
    js += "          var nu = math.norm(u);" + eol
    js += "          u = u.map((e)=>{return e/nu;});" + eol
    js += "          var v1 = math.random([3]);" + eol
    js += "          var dotv1 = math.dot(v1,u);" + eol
    js += "          var du = u.map((e)=>{return e*dotv1;});" + eol
    js += "          v1 = v1.map((e,i)=> {return (e-du[i])});" + eol
    js += "          v1 = v1.map((e,i)=> {return (e/math.norm(v1));});" + eol
    js += "          var v2 = math.cross(v1, u);" + eol
    js += "          v2 = v2.map((e,i)=> {return (e/math.norm(v2));});" + eol
    js += (
        "          var xd = linspace.map((p)=>{return p*(atoms[at1][0]-atoms[at2][0])+atoms[at2][0]});"
        + eol
    )
    js += (
        "          var yd = linspace.map((p)=>{return p*(atoms[at1][1]-atoms[at2][1])+atoms[at2][1]});"
        + eol
    )
    js += (
        "          var zd = linspace.map((p)=>{return p*(atoms[at1][2]-atoms[at2][2])+atoms[at2][2]});"
        + eol
    )
    js += "          var atm1 = atoms[at1][3];" + eol
    js += "          if (atm1 == 'Helium'){" + eol
    js += "            atm1 = atoms[at2][3];" + eol
    js += "          }" + eol
    js += "          var atm2 = atoms[at2][3];" + eol
    js += "          if (atm1 != atm2){" + eol
    js += "            for (var i = 0; i<(xd.length/2)+2; i++){" + eol
    js += (
        "              xt[atm2].push(cosphi.map((e,j)=>{return cosphi[j]*v1[0] + sinphi[j]*v2[0] + xd[i];}));"
        + eol
    )
    js += (
        "              yt[atm2].push(cosphi.map((e,j)=>{return cosphi[j]*v1[1] + sinphi[j]*v2[1] + yd[i];}));"
        + eol
    )
    js += (
        "              zt[atm2].push(cosphi.map((e,j)=>{return cosphi[j]*v1[2] + sinphi[j]*v2[2] + zd[i];}));"
        + eol
    )
    js += "            }" + eol
    js += "            xt[atm2].push([]);" + eol
    js += "            zt[atm2].push([]);" + eol
    js += "            yt[atm2].push([]);" + eol
    js += "            for (var i = (xd.length/2)-1; i<(xd.length); i++){" + eol
    js += (
        "              xt[atm1].push(cosphi.map((e,j)=>{return cosphi[j]*v1[0] + sinphi[j]*v2[0] + xd[i];}));"
        + eol
    )
    js += (
        "              yt[atm1].push(cosphi.map((e,j)=>{return cosphi[j]*v1[1] + sinphi[j]*v2[1] + yd[i];}));"
        + eol
    )
    js += (
        "              zt[atm1].push(cosphi.map((e,j)=>{return cosphi[j]*v1[2] + sinphi[j]*v2[2] + zd[i];}));"
        + eol
    )
    js += "            }" + eol
    js += "            xt[atm1].push([]);" + eol
    js += "            zt[atm1].push([]);" + eol
    js += "            yt[atm1].push([]);" + eol
    js += "          } else {" + eol
    js += "            for (var i = 0; i<(xd.length); i++){" + eol
    js += (
        "              xt[atm1].push(cosphi.map((e,j)=>{return cosphi[j]*v1[0] + sinphi[j]*v2[0] + xd[i];}));"
        + eol
    )
    js += (
        "              yt[atm1].push(cosphi.map((e,j)=>{return cosphi[j]*v1[1] + sinphi[j]*v2[1] + yd[i];}));"
        + eol
    )
    js += (
        "              zt[atm1].push(cosphi.map((e,j)=>{return cosphi[j]*v1[2] + sinphi[j]*v2[2] + zd[i];}));"
        + eol
    )
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
    js += (
        "        var cv = xt[c].map((x)=>{ return x.map((p) => {return 1;});});"
        + eol
    )
    js += (
        "        var colorscalea = [[0,'rgba(200,0,0,1.0)'], [1,component.props.getColor(component, c)]];"
        + eol
    )
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

    component.addPropVariable(
        "plotDrawingPlotly", {"type": "func", "defaultValue": js}
    )
    return {"type": "propCall2", "calls": "plotDrawingPlotly", "args": ["self", ""]}

def exposedShowPlanes(tp, component, *args, **kwargs):
    FindPlaneIntersect(tp, component)
    eol = "\n"
    js = ""
    js += "(component, plane, unitvectors, center, boundary, color) => {" + eol
    js += "  var traces = [];" + eol
    js += "  var layout = {" + eol
    js += "    'scene':{'aspectmode':'data'}, " + eol
    js += "    'margin' : {'l':0,'r':0,'t':0,'b':0}," + eol
    # js += "    'template' : self.theme," + eol
    js += "  };" + eol
    js += "  var normal = [ " + eol
    js += (
        "    plane[0]*unitvectors[0][0]+plane[0]*unitvectors[0][1]+plane[0]*unitvectors[0][2],"
        + eol
    )
    js += (
        "    plane[1]*unitvectors[1][0]+plane[1]*unitvectors[1][1]+plane[1]*unitvectors[1][2],"
        + eol
    )
    js += (
        "    plane[2]*unitvectors[2][0]+plane[2]*unitvectors[2][1]+plane[2]*unitvectors[2][2]"
        + eol
    )
    js += "  ];" + eol
    js += (
        "  var points = component.props.FindPlaneIntersect(component, boundary, normal, center);"
        + eol
    )
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

    component.addPropVariable(
        "exposedShowPlanes", {"type": "func", "defaultValue": js}
    )
    return {
        "type": "propCall2",
        "calls": "exposedShowPlanes",
        "args": [
            "self",
            "[1,1,0]",
            "[[1,0,0],[0,1,0],[0,0,1]]",
            "0.5",
            "[[0,0,0],[5,5,5]]",
            "'rgb(128,0,0)'",
        ],
    }

def loadMolecule(tp, component, *args, **kwargs):
    eol = "\n"
    plotDrawingPlotly(tp, component)
    cache_store = kwargs.get("cache_store", "CacheStore")
    NanohubUtils.storageFactory(tp, store_name=cache_store)
    js = ""
    js += "async (component, seq, method, layout) => {" + eol
    js += (
        "  var output_xml = await " + cache_store + ".getItem('output_xml');" + eol
    )
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
    js += (
        "    if (sequence.hasAttribute('id') && seq.filter( (v) => new RegExp(v).test(sequence.getAttribute('id'))).length >0){"
        + eol
    )
    js += "      lseq.push(sequence);" + eol
    js += "    }" + eol
    js += "  }" + eol
    js += (
        "  let plt = component.props.plotDrawingPlotly(component, lseq, method);"
        + eol
    )
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
    js += (
        "  window.dispatchEvent(new Event('resize'));" + eol
    )  # trying to trigger windows rescale does not work on IE
    js += "}" + eol
    component.addPropVariable("loadMolecule", {"type": "func", "defaultValue": js})

    return {"type": "propCall2", "calls": "loadMolecule", "args": ["self", "[]"]}
