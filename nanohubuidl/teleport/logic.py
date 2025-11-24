import json
from .core import TeleportNode
from .elements import TeleportElement

class TeleportConditional(TeleportNode):
    def __init__(self, content, *args, **kwargs):
        TeleportNode.__init__(self)
        self.type = "conditional"
        self.node = TeleportElement(content)
        self.reference = kwargs.get("reference", {"type": "static", "content": 0})
        self.value = kwargs.get("value", None)
        self.conditions = kwargs.get("conditions", [])
        self.matchingCriteria = "all"

    def addContent(self, child):
        self.node.addContent(child)
        
    def insertContent(self, index, child):
        self.node.insertContent(index, child)
        
    def buildReact(self, *args, **kwargs):
        value = self.reference
        content = value["content"]
        try:
            if value["type"] == "dynamic":
                if "referenceType" in content and content["referenceType"] == "state":
                    reference = "self.state." + content["id"] + ""
                elif "referenceType" in content and content["referenceType"] == "prop":
                    reference = "self.props." + content["id"] + ""
                elif "referenceType" in content and content["referenceType"] == "local":
                    reference = "" + content["id"] + ""
            elif value["type"] == "static":
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
        if len(self.conditions) == 0:
            react += "( " + str(reference) + " == " + value + ")"
        else:
            for i, condition in enumerate(self.conditions):
                if i > 0:
                    if self.matchingCriteria == "one":
                        react += " || "
                    else:
                        react += " && "
                if "operand" in condition:
                    react += (
                        "( "
                        + str(reference)
                        + " "
                        + str(condition["operation"])
                        + " "
                        + json.dumps(condition["operand"])
                        + ")"
                    )
                elif self.value is not None:
                    react += (
                        "( "
                        + str(reference)
                        + " "
                        + str(condition["operation"])
                        + " "
                        + json.dumps(self.value)
                        + ")"
                    )
        react += ") ?"
        react += self.node.buildReact(nativeRef=kwargs.get("nativeRef", ""))
        react += " : null)"
        return react

    def __json__(self):
        return {
            "type": self.type,
            "content": {
                "node": self.node.__json__(),
                "reference": self.reference,
                "value": self.value,
                "condition": {
                    "conditions": self.conditions,
                    "matchingCriteria": self.matchingCriteria,
                },
            },
        }


class TeleportRepeat(TeleportNode):
    def __init__(self, content, *args, **kwargs):
        TeleportNode.__init__(self)
        self.type = "repeat"
        self.node = TeleportElement(content)
        self.dataSource = kwargs.get("dataSource", {"type": "static", "content": []})
        self.iteratorName = kwargs.get("iteratorName", "it")
        self.useIndex = kwargs.get("iteratorName", True)

    def addContent(self, child):
        self.node.addContent(child)

    def insertContent(self, index, child):
        self.node.insertContent(index, child)
        
    def buildReact(self, *args, **kwargs):
        reference = self.dataSource
        content = reference["content"]
        try:
            if reference["type"] == "dynamic":
                if "referenceType" in content and content["referenceType"] == "state":
                    reference = "self.state." + content["id"] + ""
                elif "referenceType" in content and content["referenceType"] == "prop":
                    reference = "self.props." + content["id"] + ""
                elif "referenceType" in content and content["referenceType"] == "local":
                    reference = "" + content["id"] + ""
            elif value["dataSource"] == "static":
                reference = json.dumps(content)
        except:
            reference = self.dataSource
        react = reference + ".map((" + self.iteratorName
        if self.useIndex:
            react += ", index"
        react += ") => { try {return React.cloneElement("
        react += self.node.buildReact(nativeRef=str("index") + "+")
        react += ")} catch { } })"
        return react

    def __json__(self):
        return {
            "type": self.type,
            "content": {
                "node": self.node.__json__(),
                "dataSource": self.dataSource,
                "meta": {"iteratorName": self.iteratorName, "useIndex": self.useIndex},
            },
        }


class TeleportDynamic(TeleportNode):
    def __init__(self, *args, **kwargs):
        TeleportNode.__init__(self)
        self.type = "dynamic"
        self.content = kwargs.get("content", {})

    def __json__(self):
        return {
            "type": self.type,
            "content": self.content,
        }


class TeleportStatic(TeleportNode):
    def __init__(self, *args, **kwargs):
        TeleportNode.__init__(self)
        self.type = "static"
        self.content = kwargs.get("content", "")

    def __json__(self):
        return {
            "type": self.type,
            "content": self.content,
        }
