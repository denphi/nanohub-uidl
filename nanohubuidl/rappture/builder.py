from .loader import Loader, Error
from .tool import onSimulate, buildSchema
from .dom import getText, getXY
from .plot_basics import buildXYPlotly, plotXY, plotSequence
from .plot_advanced import loadXY, loadXYDual, loadSequence, plotDrawingPlotly, exposedShowPlanes, loadMolecule
from .science_basics import getColor, getAtomName, getAtomLabel
from .science_advanced import extractVectors, loadVectors, getMolecule, buildBasis, buildCrystal, FindPlaneIntersect

class RapptureBuilder:
    Loader = staticmethod(Loader)
    Error = staticmethod(Error)
    onSimulate = staticmethod(onSimulate)
    buildSchema = staticmethod(buildSchema)
    getText = staticmethod(getText)
    getXY = staticmethod(getXY)
    buildXYPlotly = staticmethod(buildXYPlotly)
    plotXY = staticmethod(plotXY)
    plotSequence = staticmethod(plotSequence)
    loadXY = staticmethod(loadXY)
    loadXYDual = staticmethod(loadXYDual)
    loadSequence = staticmethod(loadSequence)
    plotDrawingPlotly = staticmethod(plotDrawingPlotly)
    exposedShowPlanes = staticmethod(exposedShowPlanes)
    loadMolecule = staticmethod(loadMolecule)
    getColor = staticmethod(getColor)
    getAtomName = staticmethod(getAtomName)
    getAtomLabel = staticmethod(getAtomLabel)
    extractVectors = staticmethod(extractVectors)
    loadVectors = staticmethod(loadVectors)
    getMolecule = staticmethod(getMolecule)
    buildBasis = staticmethod(buildBasis)
    buildCrystal = staticmethod(buildCrystal)
    FindPlaneIntersect = staticmethod(FindPlaneIntersect)
