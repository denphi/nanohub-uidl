import json
import uuid
import weakref
import os
from IPython.display import HTML, Javascript, display
import re
import warnings
import psutil

class TeleportCustomCode:
    def __init__(self, *args, **kwargs):
        self.ids = {}
        self.code = []

    def buildReact(self, *args, **kwargs):
        return self.__json__()

    def addCustomCode(self, id, asset):
        if id in self.ids:
            pass
        else:
            self.ids[id] = len(self.ids)
            self.code.append(asset)

    def __json__(self):
        js = ""
        for code in self.code:
            js += code + "\n"
        return js


class TeleportGlobals:
    def __init__(self, *args, **kwargs):
        self.settings = {"language": "en", "title": ""}
        self.customCode = {"head": TeleportCustomCode(), "body": TeleportCustomCode()}
        self.assets = []
        self.meta = []
        self.manifest = {}
        self.ids = {}

    def __json__(self):
        jsn = {
            "settings": self.settings,
            "customCode": {},
            "assets": self.assets,
            "meta": self.meta,
            "manifest": self.manifest,
        }
        if len(self.customCode["head"].code) > 0:
            jsn["customCode"]["head"] = self.customCode["head"].__json__()
        if len(self.customCode["body"].code) > 0:
            jsn["customCode"]["body"] = self.customCode["body"].__json__()
        return jsn

    def __str__(self):
        return json.dumps(self.__json__())

    def buildReact(self, *args, **kwargs):
        react = ""
        for asset in self.assets:
            if asset["type"] == "script":
                react += asset["content"] + "\n"
            if asset["type"] == "style":
                react += "var tstyle = document.createElement('style')\n"
                react += "document.head.appendChild(tstyle);\n"
                react += "tstyle.sheet.insertRule('" + asset["content"] + "');\n"
        return react

    def addAsset(self, id, asset):
        if id in self.ids:
            pass
        else:
            self.ids[id] = len(self.ids)
            self.assets.append(asset)

    def addCustomCode(self, id, code, position="body"):
        if position in ["body", "head"]:
            self.customCode[position].addCustomCode(id, code)


class TeleportNode:
    def __init__(self, *args, **kwargs):
        self.type = ""
        self.content = None

    def __json__(self):
        return {
            "type": self.type,
            "content": self.contentToJson(),
        }

    def contentToJson(self):
        if self.content is None:
            return {}
        else:
            return self.content.__json__()

    def __str__(self):
        return json.dumps(self.__json__())

    def buildReact(self, *args, **kwargs):
        react = ""
        if self.content == None:
            react += "''\n"
        else:
            if self.type == "static":
                value = self.content
                if isinstance(value, str) and value.startswith("$"):
                    value = value.replace("$", "")
                else:
                    value = json.dumps(value)
                react += " " + str(value).replace("'", '"') + " "
            elif self.type == "dynamic":
                if (
                    "referenceType" in self.content
                    and self.content["referenceType"] == "state"
                ):
                    reference = "self.state." + self.content["id"] + ""
                elif (
                    "referenceType" in self.content
                    and self.content["referenceType"] == "prop"
                ):
                    reference = "self.props." + self.content["id"] + ""
                elif (
                    "referenceType" in self.content
                    and self.content["referenceType"] == "local"
                ):
                    reference = "" + self.content["id"] + ""
                else:
                    reference = ""
                react += " " + str(reference) + " "
            else:
                react += self.content.buildReact(nativeRef=kwargs.get("nativeRef", ""))
        return react

    def getNodeTypes(self):
        return set()
