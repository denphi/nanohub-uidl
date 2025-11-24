from .dom import getText
from .science_basics import getColor, getAtomName, getAtomLabel
import json

def extractVectors(tp, component, *args, **kwargs):
    eol = "\n"
    getColor(tp, component)
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
    js += (
        "          var nums = line.split(/[^\d-\.]+/).filter((e)=>{return !isNaN(parseFloat(e))});"
        + eol
    )
    js += "          vectors.push(nums.slice(1));" + eol
    js += "        }" + eol
    js += "      }" + eol
    js += "      if (line.startsWith('Reciprocal lattice vectors')){" + eol
    js += "        for (var ii=0; ii<3;ii++){" + eol
    js += "          i = i+1;" + eol
    js += "          var line = lines[i];" + eol
    js += (
        "          var nums = line.split(/[^\d-\.]+/).filter((e)=>{return !isNaN(parseFloat(e))});"
        + eol
    )
    js += "          ivectors.push(nums.slice(1));" + eol
    js += "        }" + eol
    js += "      }" + eol
    js += "      if (line.startsWith('Conventional cell Bravais vectors')){" + eol
    js += "        for (var ii=0; ii<3;ii++){" + eol
    js += "          i = i+1;" + eol
    js += "          var line = lines[i];" + eol
    js += (
        "          var nums = line.split(/[^\d-\.]+/).filter((e)=>{return !isNaN(parseFloat(e))});"
        + eol
    )
    js += "          box.push(nums.slice(1));" + eol
    js += "        }" + eol
    js += "      }" + eol
    js += "      if (line.startsWith('Primitive cell basis atoms')){" + eol
    js += "        i = i+1;" + eol
    js += "        while (i < lines.length &&  lines[i] != ''){" + eol
    js += "          var line = lines[i];" + eol
    js += (
        "          var nums = line.split(/[^\d-\.]+/).filter((e)=>{return !isNaN(parseFloat(e))});"
        + eol
    )
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
    # js += "  console.log(atoms);" + eol
    # js += "  console.log(vectors);" + eol
    js += (
        "  return {'vectors':vectors,'ivectors':ivectors,'atoms':atoms,'box':box};"
        + eol
    )
    js += "}" + eol
    component.addPropVariable(
        "extractVectors", {"type": "func", "defaultValue": js}
    )

    return {"type": "propCall2", "calls": "extractVectors", "args": ["self", "[]"]}

def loadVectors(tp, component, *args, **kwargs):
    eol = "\n"
    extractVectors(tp, component)
    cache_store = kwargs.get("cache_store", "CacheStore")
    # NanohubUtils.storageFactory(tp, store_name=cache_store) # Assuming imported or handled elsewhere? 
    # Wait, NanohubUtils is needed here.
    # I should import it if I use it.
    # But storageFactory is usually called in onSimulate or similar.
    # Here it is called to ensure cache store exists.
    from ..teleport.utils import NanohubUtils
    NanohubUtils.storageFactory(tp, store_name=cache_store)

    js = ""
    js += "async (component, seq, layout) => {" + eol
    js += (
        "  var output_xml = await " + cache_store + ".getItem('output_xml');" + eol
    )
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
    js += "    sequences = output[0].querySelectorAll('output > string');" + eol
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
    js += "  let vectors = component.props.extractVectors(component, lseq);" + eol
    js += "  if (component.props.onLoadVectors){" + eol
    js += "    component.props.onLoadVectors(component,vectors);" + eol
    js += "  }" + eol
    js += "  return vectors;" + eol
    js += "}" + eol
    component.addPropVariable("loadVectors", {"type": "func", "defaultValue": js})

    return {"type": "propCall2", "calls": "loadVectors", "args": ["self", "[]"]}

def getMolecule(tp, component, *args, **kwargs):
    getText(tp, component)
    getColor(tp, component)
    getAtomName(tp, component)
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
    js += (
        "        var n_atom = component.props.getAtomName(component, cols[2]);"
        + eol
    )
    js += "        var id_atom = parseInt(cols[1]);" + eol
    js += (
        "        atoms[id_atom] = [x_atom,y_atom,z_atom, n_atom,c_atom, 'enabled'];"
        + eol
    )
    js += "      } else if (line.startsWith('CONECT')){" + eol
    js += "        cols = line.split(/[\s]+/);" + eol
    js += "        var id_atom = parseInt(cols[1]);" + eol
    js += (
        "        connections[id_atom] = cols.slice(1).map((c)=>{ return parseInt(c)});"
        + eol
    )
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
    js += (
        "              points.push([parseFloat(pp[0]),parseFloat(pp[1]),parseFloat(pp[2])])"
        + eol
    )
    js += "            } if (points.length < tpoints) {" + eol
    js += (
        "              points.push([parseFloat(pp[3]),parseFloat(pp[4]),parseFloat(pp[5])])"
        + eol
    )
    js += "            } if (points.length < tpoints) {" + eol
    js += (
        "              points.push([parseFloat(pp[6]),parseFloat(pp[7]),parseFloat(pp[8])])"
        + eol
    )
    js += "            }" + eol
    js += "          }" + eol
    js += "        } else if (line.startsWith('VERTICES')){" + eol
    js += "          var tvert = parseInt(line.split(/[\s]+/)[1])" + eol
    js += "          for (var ii=0; ii<tvert; ii++){" + eol
    js += "            i = i+1;" + eol
    js += "            line = lines[i];" + eol
    js += "            let pp = line.split(/[\s]+/);" + eol
    js += "            pp = pp.map((p)=>{return parseInt(p)});" + eol
    js += (
        "            atoms[pp[1]] = [points[ii][0],points[ii][1],points[ii][2], 'Si', 'rgb(240,200,160)', 'enabled'];"
        + eol
    )
    js += "          }" + eol
    js += "          for (var j=0; j < points.lenght; j++){" + eol
    js += "            var point =  points[j];" + eol
    js += "            if (!(j in atoms)){" + eol
    js += (
        "              atoms[j] = [point[0],point[1],point[2], '', 'rgb(0,0,0)', 'disabled'];"
        + eol
    )
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
    js += (
        "              if (atom_id in atoms && component.props.getColor(component, pp[k])){"
        + eol
    )
    js += (
        "                atoms[atom_id][3] = component.props.getAtomName(component, pp[k]);"
        + eol
    )
    js += (
        "                atoms[atom_id][4] = component.props.getColor(component, pp[k]);"
        + eol
    )
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

    component.addPropVariable("getMolecule", {"type": "func", "defaultValue": js})
    return {"type": "propCall2", "calls": "getMolecule", "args": ["self", "[]"]}

def buildBasis(tp, component, *args, **kwargs):

    eol = "\n"
    js = ""
    js += "(component, molecule, r_x, r_y,r_z) => {" + eol
    js += "  let atoms_basis = component.state.atoms;" + eol
    js += "  var atoms_set = {}" + eol
    js += "  atoms_basis.forEach((atom)=>{" + eol
    js += (
        "    let key = ((parseFloat(atom[0]))*10).toFixed(3)+'_'+((parseFloat(atom[1]))*10).toFixed(3)+'_'+((parseFloat(atom[2]))*10).toFixed(3);"
        + eol
    )
    js += "    if (!(key in atoms_set))" + eol
    js += (
        "      atoms_set[key] = {'coord' : atom.slice(0,3).map((e,i)=>{return (e)*10}), 'connection': new Set(), 'type' : atom[3], 'color': atom[4]};"
        + eol
    )
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
    js += (
        "          let x0 = value.coord[0] + (ii*vec[0][0] + jj*vec[1][0] + kk*vec[2][0])*10;"
        + eol
    )
    js += (
        "          let y0 = value.coord[1] + (ii*vec[0][1] + jj*vec[1][1] + kk*vec[2][1])*10;"
        + eol
    )
    js += (
        "          let z0 = value.coord[2] + (ii*vec[0][2] + jj*vec[1][2] + kk*vec[2][2])*10;"
        + eol
    )
    js += (
        "          let k0 = parseFloat(x0).toFixed(3)+'_'+parseFloat(y0).toFixed(3)+'_'+parseFloat(z0).toFixed(3);"
        + eol
    )
    js += "          if (!(k0 in crystal_set)){" + eol
    js += (
        "            crystal_set[k0] = {'coord':[x0,y0,z0],'connection':[],'type':value.type,'color':value.color };"
        + eol
    )
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
    js += (
        "      if(atm1.coord[0] - atm2.coord[0] > maxr|| atm1.coord[0]-atm2.coord[0] < -maxr)"
        + eol
    )
    js += "        return undefined;" + eol
    js += (
        "      if(atm1.coord[1] - atm2.coord[1] > maxr|| atm1.coord[1]-atm2.coord[1] < -maxr)"
        + eol
    )
    js += "        return undefined;" + eol
    js += (
        "      if(atm1.coord[2] - atm2.coord[2] > maxr|| atm1.coord[2]-atm2.coord[2] < -maxr)"
        + eol
    )
    js += "        return undefined;" + eol
    js += (
        "      let dist = Math.hypot(atm1.coord[0]-atm2.coord[0], atm1.coord[1]-atm2.coord[1], atm1.coord[2]-atm2.coord[2]);"
        + eol
    )
    js += "      if(dist < maxr && dist > 0){" + eol
    js += "        return i2;" + eol
    js += "      }" + eol
    js += "    }).filter ((e)=>{return e!=undefined;});" + eol
    js += "  });" + eol
    js += "  molecule = { atoms: {}, connections:{} }" + eol
    js += "  Object.keys(crystal_set).forEach((c, i)=>{" + eol
    js += "    let atm = crystal_set[c];" + eol
    js += (
        "    molecule.atoms[crystal_ids[c]] = [atm.coord[0],atm.coord[1],atm.coord[2],atm.type,atm.color,'enabled'];"
        + eol
    )
    js += "    molecule.connections[i] = atm.connection;" + eol
    js += "  });" + eol
    js += "  return molecule;" + eol
    js += "}" + eol

    component.addPropVariable("buildBasis", {"type": "func", "defaultValue": js})
    return {"type": "propCall2", "calls": "buildBasis", "args": ["self", "[]"]}

def buildCrystal(tp, component, *args, **kwargs):

    eol = "\n"
    js = ""
    js += "(component, molecule, r_x, r_y,r_z) => {" + eol
    js += "  let atoms_basis = component.state.atoms;" + eol
    js += "  var atoms_set = {};" + eol
    js += "  atoms_basis.forEach((atom)=>{" + eol
    js += (
        "    let key = ((parseFloat(atom[0]))*10).toFixed(3)+'_'+((parseFloat(atom[1]))*10).toFixed(3)+'_'+((parseFloat(atom[2]))*10).toFixed(3);"
        + eol
    )
    js += "    if (!(key in atoms_set))" + eol
    js += (
        "      atoms_set[key] = {'coord' : atom.slice(0,3).map((e,i)=>{return (e)*10}), 'connection': new Set(), 'type' : atom[3], 'color': atom[4]};"
        + eol
    )
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
    js += (
        "  let ivec = component.state.ivectors.map((e)=>{return e.map((d)=>{return parseFloat(d);});});"
        + eol
    )
    js += (
        "  let vec = component.state.vectors.map((e)=>{return e.map((d)=>{return parseFloat(d);});});"
        + eol
    )
    js += "  var a = [r_x,r_y,r_z];" + eol
    js += (
        "  let x0 = a[0];//(a[0]*ivec[0][0] + a[1]*ivec[1][0] + a[2]*ivec[2][0]);"
        + eol
    )
    js += (
        "  let y0 = a[1];//(a[0]*ivec[0][1] + a[1]*ivec[1][1] + a[2]*ivec[2][1]);"
        + eol
    )
    js += (
        "  let z0 = a[2];//(a[0]*ivec[0][2] + a[1]*ivec[1][2] + a[2]*ivec[2][2]);"
        + eol
    )
    js += (
        "  let minv = [0,1,2].map((i)=>{return math.min(0, vec[0][i],vec[1][i],vec[2][i]);});"
        + eol
    )
    js += (
        "  let maxv = [0,1,2].map((i)=>{return math.max(0, vec[0][i],vec[1][i],vec[2][i]);});"
        + eol
    )
    js += "  let dimv = [maxv[0]-minv[0],maxv[1]-minv[1],maxv[2]-minv[2]];" + eol

    # js += "  let x1 = dimv[0];" + eol
    # js += "  let y1 = dimv[1];" + eol
    # js += "  let z1 = dimv[2];" + eol

    js += "  let x1 = maxv[0];" + eol
    js += "  let y1 = maxv[1];" + eol
    js += "  let z1 = maxv[2];" + eol

    # js += "  let x1 = (vec[0][0] + vec[1][0] + vec[2][0]);" + eol
    # js += "  let y1 = (vec[0][1] + vec[1][1] + vec[2][1]);" + eol
    # js += "  let z1 = (vec[0][2] + vec[1][2] + vec[2][2]);" + eol

    js += "  if (x1==0) x1=1;" + eol
    js += "  if (y1==0) y1=1;" + eol
    js += "  if (z1==0) z1=1;" + eol
    js += "  let ncx = Math.abs(Math.ceil(x0/x1));" + eol
    js += "  if (ncx>100) ncx=100;" + eol
    js += "  let ncy = Math.abs(Math.ceil(y0/y1));" + eol
    js += "  if (ncy>100) ncy=100;" + eol
    js += "  let ncz = Math.abs(Math.ceil(z0/z1));" + eol
    js += "  if (ncz>100) ncz=100;" + eol
    js += "  ncz = ncz*5;" + eol  # No IDEA why, but works #TODO
    js += "  for (var ii=-ncx ; ii<=ncx; ii++){" + eol
    js += "    for (var jj=-ncy ; jj<=ncy; jj++){" + eol
    js += "      for (var kk=-ncz ; kk<=ncz; kk++){" + eol
    js += "        for (let ias in atoms_set){" + eol
    js += "          let value = atoms_set[ias];" + eol
    js += (
        "          let x0 = value.coord[0] + (ii*vec[0][0] + jj*vec[1][0] + kk*vec[2][0])*10;"
        + eol
    )
    js += (
        "          let y0 = value.coord[1] + (ii*vec[0][1] + jj*vec[1][1] + kk*vec[2][1])*10;"
        + eol
    )
    js += (
        "          let z0 = value.coord[2] + (ii*vec[0][2] + jj*vec[1][2] + kk*vec[2][2])*10;"
        + eol
    )
    js += (
        "          if (x0 >= -0.0001 && y0 >= -0.0001 && z0 >= -0.0001 && x0 < r_x*10 +0.0001 && y0 < r_y*10 +0.0001 && z0 < r_z*10+0.0001){"
        + eol
    )
    js += (
        "            let k0 = parseFloat(x0).toFixed(3)+'_'+parseFloat(y0).toFixed(3)+'_'+parseFloat(z0).toFixed(3);"
        + eol
    )
    js += "            if (!(k0 in crystal_set)){" + eol
    js += (
        "              crystal_set[k0] = {'coord':[x0,y0,z0],'connection':[],'type':value.type,'color':value.color };"
        + eol
    )
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
    js += (
        "      if(atm1.coord[0] - atm2.coord[0] > maxr|| atm1.coord[0]-atm2.coord[0] < -maxr)"
        + eol
    )
    js += "        return undefined;" + eol
    js += (
        "      if(atm1.coord[1] - atm2.coord[1] > maxr|| atm1.coord[1]-atm2.coord[1] < -maxr)"
        + eol
    )
    js += "        return undefined;" + eol
    js += (
        "      if(atm1.coord[2] - atm2.coord[2] > maxr|| atm1.coord[2]-atm2.coord[2] < -maxr)"
        + eol
    )
    js += "        return undefined;" + eol
    js += (
        "      let dist = Math.hypot(atm1.coord[0]-atm2.coord[0], atm1.coord[1]-atm2.coord[1], atm1.coord[2]-atm2.coord[2]);"
        + eol
    )
    js += "      if(dist < maxr && dist > 0){" + eol
    js += "        return i2;" + eol
    js += "      }" + eol
    js += "    }).filter ((e)=>{return e!=undefined;});" + eol
    js += "  });" + eol
    js += "  molecule = { atoms: {}, connections:{} }" + eol
    js += "  Object.keys(crystal_set).forEach((c, i)=>{" + eol
    js += "    let atm = crystal_set[c];" + eol
    js += (
        "    molecule.atoms[crystal_ids[c]] = [atm.coord[0],atm.coord[1],atm.coord[2],atm.type,atm.color,'enabled'];"
        + eol
    )
    js += "    molecule.connections[i] = atm.connection;" + eol
    js += "  });" + eol
    js += "  return molecule;" + eol
    js += "}" + eol

    component.addPropVariable("buildCrystal", {"type": "func", "defaultValue": js})
    return {"type": "propCall2", "calls": "buildCrystal", "args": ["self", "[]"]}

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
    js += (
        "      var w = [0,1,2].map((i)=>{return rayPoint[i] - planePoint[i];});"
        + eol
    )
    js += "      var si = -math.dot(planeNormal,w)/ndotu;" + eol
    js += (
        "      var wsi = [0,1,2].map((i)=>{return (w[i]+si*rayDirection[i]+planePoint[i]);});"
        + eol
    )
    js += "      var Psi = math.round(wsi, 8);" + eol
    js += (
        "      if (Psi[0] >= min_p[0]-epsilon && Psi[0] <= max_p[0]+epsilon){" + eol
    )
    js += (
        "        if (Psi[1] >= min_p[1]-epsilon && Psi[1] <= max_p[1]+epsilon){"
        + eol
    )
    js += (
        "          if (Psi[2] >= min_p[2]-epsilon && Psi[2] <= max_p[2]+epsilon){"
        + eol
    )
    js += "            line_points.add(JSON.stringify(Psi));" + eol
    js += "          }" + eol
    js += "        }" + eol
    js += "      }" + eol
    js += "    }" + eol
    js += "  });" + eol
    js += "  if (line_points.size != 2 )" + eol
    js += "     return [[], []];" + eol
    js += (
        "  line_points = [...line_points].map((l)=>{return JSON.parse(l);});" + eol
    )
    js += "  var min_point = line_points[0];" + eol
    js += "  var max_point = line_points[1];" + eol
    js += "  avg_p[0] = min_point[0] + (max_point[0]-min_point[0])*center;" + eol
    js += "  avg_p[1] = min_point[1] + (max_point[1]-min_point[1])*center;" + eol
    js += "  avg_p[2] = min_point[2] + (max_point[2]-min_point[2])*center;" + eol
    js += (
        "  var normal_point = avg_p[0]*normal[0] + avg_p[1]*normal[1] + avg_p[2]*normal[2];"
        + eol
    )
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
    js += (
        "        var w = [0,1,2].map((i)=>{return rayPoint[i] - planePoint[i];});"
        + eol
    )
    js += "        var si = -math.dot(planeNormal,w)/ndotu;" + eol
    js += (
        "        var wsi = [0,1,2].map((i)=>{return (w[i]+si*rayDirection[i]+planePoint[i]);});"
        + eol
    )
    js += "        var Psi = math.round(wsi, 8);" + eol
    js += (
        "        if (Psi[0] >= min_p[0]-epsilon && Psi[0] <= max_p[0]+epsilon){"
        + eol
    )
    js += (
        "          if (Psi[1] >= min_p[1]-epsilon && Psi[1] <= max_p[1]+epsilon){"
        + eol
    )
    js += (
        "            if (Psi[2] >= min_p[2]-epsilon && Psi[2] <= max_p[2]+epsilon){"
        + eol
    )
    js += "              pts.add(JSON.stringify(Psi));" + eol
    js += "            }" + eol
    js += "          }" + eol
    js += "        }" + eol
    js += "      }" + eol
    js += "    });" + eol
    js += "  });" + eol
    js += "  return [...pts].map((l)=>{return JSON.parse(l);});" + eol
    js += "}" + eol

    component.addPropVariable(
        "FindPlaneIntersect", {"type": "func", "defaultValue": js}
    )
    return {
        "type": "propCall2",
        "calls": "FindPlaneIntersect",
        "args": ["self", "[]"],
    }
