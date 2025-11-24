import json
import uuid
from .core import TeleportNode

class TeleportElement(TeleportNode):
    def __init__(self, content, *args, **kwargs):
        TeleportNode.__init__(self)
        self.type = "element"
        self.content = content

    def addContent(self, child):
        self.content.children.append(child)

    def insertContent(self, index, child):
        self.content.children.insert(index, child)

    def getNodeTypes(self):
        return self.content.getNodeTypes()


class TeleportContent:
    def __init__(self, *args, **kwargs):
        self.elementType = kwargs.get("elementType", None)
        self.semanticType = kwargs.get("semanticType", self.elementType)
        self.attrs = {}
        self.events = {}
        self.style = {}
        self.children = []
        self.ref = uuid.uuid4()
        self.name = kwargs.get("name", None)

    def getNodeTypes(self):
        types = set()
        if self.elementType != None:
            types.add(self.elementType)
        for c in self.children:
            for v in c.getNodeTypes():
                types.add(v)
        return types

    def __json__(self):
        tjson = {}
        if self.name != None:
            tjson["name"] = self.name
        if self.elementType != None:
            tjson["elementType"] = self.elementType
        if self.semanticType != None:
            tjson["semanticType"] = self.semanticType
        if len(self.style) > 0:
            tjson["style"] = self.style
        if len(self.attrs) > 0:
            tjson["attrs"] = self.attrs  # False -> "false"
        if len(self.events) > 0:
            tjson["events"] = self.events
        if len(self.children) > 0:
            tjson["children"] = [component.__json__() for component in self.children]
        return tjson

    def __str__(self):
        return json.dumps(self.__json__())

    def buildElementType(self):
        elementType = self.semanticType
        if elementType is None:
            elementType = self.elementType
        if elementType == "container":
            elementType = "'div'"
        elif elementType == "text":
            elementType = "'span'"
        elif elementType.islower():
            elementType = "'" + elementType + "'"
        return elementType

    @staticmethod
    def parseFunctionsList(list):
        v = ""
        for func in list:
            if "type" in func and func["type"] == "stateChange":
                callback_d = "(e)=>{}"
                state_d = "{}"
                if "callbacks" in func:
                    callback_d = (
                        "(e)=>{"
                        + TeleportContent.parseFunctionsList(func["callbacks"])
                        + "}"
                    )
                if isinstance(func["newState"], str) and func["newState"] == "$toggle":
                    state_d = (
                        "{'"
                        + str(func["modifies"])
                        + "': !self.state."
                        + str(func["modifies"])
                        + "}"
                    )
                elif isinstance(func["newState"], str) and func["newState"].startswith(
                    "$"
                ):
                    state_d = (
                        "{'"
                        + str(func["modifies"])
                        + "':"
                        + func["newState"].replace("$", "")
                        + "}"
                    )
                else:
                    state_d = (
                        "{'"
                        + str(func["modifies"])
                        + "':"
                        + json.dumps(func["newState"])
                        + "}"
                    )
                v += "self.setState(" + state_d + "," + callback_d + " );"
            elif "type" in func and func["type"] == "logging":
                v += (
                    "console.log('"
                    + str(func["modifies"])
                    + "', "
                    + str(json.dumps(func["newState"]))
                    + "); "
                )
            elif "type" in func and func["type"] == "propCall":
                v += str(func["calls"]) + "(" + ", ".join(func["args"]) + ");"
            elif "type" in func and func["type"] == "propCall2":
                v += (
                    "self.props."
                    + str(func["calls"])
                    + "("
                    + ", ".join(func["args"])
                    + ");"
                )
        return v

    def buildReact(self, *args, **kwargs):
        try:
            react = ""
            elementType = self.buildElementType()
            react += (
                "React.createElement("
                + elementType
                + ", {key:"
                + kwargs.get("nativeRef", "")
                + "'"
                + str(self.ref)
                + "'"
            )
            sep = ","
            for attr, value in self.attrs.items():
                v = value
                if isinstance(value, dict):
                    if "type" in value and "content" in value:
                        content = value["content"]
                        if value["type"] == "dynamic":
                            if (
                                "referenceType" in content
                                and content["referenceType"] == "state"
                            ):
                                v = "self.state." + content["id"] + ""
                            elif (
                                "referenceType" in content
                                and content["referenceType"] == "prop"
                            ):
                                v = "self.props." + content["id"] + ""
                            elif (
                                "referenceType" in content
                                and content["referenceType"] == "local"
                            ):
                                v = "" + content["id"] + ""
                    else:
                        v = str(json.dumps(v))
                else:
                    if isinstance(v, str) and v.startswith("$"):
                        v = v.replace("$", "")
                    else:
                        v = str(json.dumps(v))
                react += sep + "'" + attr + "': " + v + ""

            valid_events = {
                "click": "onClick",
                "focus": "onFocus",
                "blur": "onBlur",
                "change": "onChange",
                "submit": "onSubmit",
                "keydown": "onKeyDown",
                "keyup": "onKeyUp",
                "keypress": "onKeyPress",
                "mouseenter": "onMouseEnter",
                "mouseleave": "onMouseLeave",
                "mouseover": "onMouseOver",
                "select": "onSelect",
                "touchstart": "onTouchStart",
                "touchend": "onTouchEnd",
                "scroll": "onScroll",
                "load": "onLoad",
            }
            for ev, list in self.events.items():
                event_rename = ev
                if ev in valid_events:
                    event_rename = valid_events[ev]
                v = "function(e){"
                v += "  " + TeleportContent.parseFunctionsList(list) + "\n"
                v += "}"
                if v != "function(){}":
                    react += sep + "'" + event_rename + "': " + v + ""
            if isinstance(self.style, str) and self.style.startswith("$"):
                react += sep + "'style': " + self.style.replace("$", "") + ""
            elif len(self.style) > 0:
                react += sep + "'style': " + json.dumps(self.style) + ""
            react += "}"

            if len(self.children) > 0:
                if len(self.children) == 1:
                    react += ",\n"
                    for child in self.children:
                        react += child.buildReact(nativeRef=kwargs.get("nativeRef", ""))
                    react += ")\n"
                else:
                    react += ",[\n"
                    sep = ""
                    for child in self.children:
                        react += sep + child.buildReact(
                            nativeRef=kwargs.get("nativeRef", "")
                        )
                        sep = " ,"
                    react += "])"
            else:
                react += ")"
        except Exception as e:
            print (self.elementType)
            raise e
        return react
