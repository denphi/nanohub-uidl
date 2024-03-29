from .teleport import *
from .rappture import *
from .material import *
import numpy as np
import json


class FormHelper:
    def Number(
        component, label, description, state, value=0, suffix="", *args, **kwargs
    ):
        if isinstance(state, str) and state not in component.stateDefinitions:
            component.addStateVariable(state, {"type": "number", "defaultValue": value})

        number = TeleportElement(TeleportContent(elementType="FormatCustomNumber"))
        variant = kwargs.get("variant", "outlined")
        number.content.attrs["variant"] = variant
        number.content.attrs["label"] = label
        number.content.attrs["fullWidth"] = True
        number.content.attrs["helperText"] = description
        number.content.attrs["suffix"] = suffix
        if kwargs.get("decimalScale", None) is not None:
            number.content.attrs["decimalscale"] = kwargs.get("decimalScale", 0)
        number.content.style = {"margin": "10px 0px 10px 0px"}
        number.content.events["blur"] = []

        number.content.events["blur"].append(
            {"type": "stateChange", "modifies": state, "newState": "$e.target.value"}
        )
        if kwargs.get("onChange", None) is not None:
            number.content.events["blur"].append(kwargs.get("onChange", None))
        number.content.attrs["value"] = {
            "type": "dynamic",
            "content": {"referenceType": "state", "id": state},
        }
        return number

    def NumberAsString(
        component, label, description, state, value=0, suffix="", *args, **kwargs
    ):
        if state not in component.stateDefinitions:
            component.addStateVariable(state, {"type": "string", "defaultValue": value})
        number = TeleportElement(TeleportContent(elementType="FormatCustomNumber"))
        variant = kwargs.get("variant", "outlined")
        number.content.attrs["variant"] = variant
        number.content.attrs["label"] = label
        number.content.attrs["fullWidth"] = True
        number.content.attrs["helperText"] = description
        number.content.attrs["suffix"] = suffix
        if kwargs.get("decimalScale", None) is not None:
            number.content.attrs["decimalscale"] = kwargs.get("decimalScale", 0)
        number.content.style = {"margin": "10px 0px 10px 0px"}
        number.content.events["blur"] = []
        number.content.events["blur"].append(
            {
                "type": "stateChange",
                "modifies": state,
                "newState": "$e.target.value + '" + suffix + "'",
            }
        )
        if kwargs.get("onChange", None) is not None:
            number.content.events["blur"].append(kwargs.get("onChange", None))

        number.content.attrs["value"] = {
            "type": "dynamic",
            "content": {"referenceType": "state", "id": state},
        }
        return number

    def StringListAsString(
        component, label, description, state, value, *args, **kwargs
    ):
        if isinstance(value, list):
            value = [str(v) for v in value]
        if state not in component.stateDefinitions:
            component.addStateVariable(state, {"type": "array", "defaultValue": value})
        string = TeleportElement(MaterialContent(elementType="TextField"))
        variant = kwargs.get("variant", "outlined")
        string.content.attrs["variant"] = variant
        string.content.attrs["label"] = label
        string.content.attrs["fullWidth"] = True
        string.content.attrs["helperText"] = description
        string.content.style = {"margin": "10px 0px 10px 0px"}
        string.content.events["change"] = []
        string.content.events["change"].append(
            {
                "type": "stateChange",
                "modifies": state,
                "newState": "$e.target.value.split(',')",
            }
        )
        if kwargs.get("onChange", None) is not None:
            string.content.events["change"].append(kwargs.get("onChange", None))

        string.content.attrs["value"] = {
            "type": "dynamic",
            "content": {"referenceType": "state", "id": state},
        }
        return string

    def NumberListAsString(
        component, label, description, state, value, *args, **kwargs
    ):
        if isinstance(value, list):
            value = [float(v) for v in value]
        if state not in component.stateDefinitions:
            component.addStateVariable(state, {"type": "array", "defaultValue": value})
        string = TeleportElement(MaterialContent(elementType="TextField"))
        variant = kwargs.get("variant", "outlined")
        string.content.attrs["variant"] = variant
        string.content.attrs["label"] = label
        string.content.attrs["fullWidth"] = True
        string.content.attrs["helperText"] = description
        string.content.style = {"margin": "10px 0px 10px 0px"}
        string.content.events["change"] = []
        string.content.events["change"].append(
            {
                "type": "stateChange",
                "modifies": state,
                "newState": "$e.target.value.split(',').map(x => Number.isInteger(Number(x)) ? Number(x).toFixed(1) : Number(x))",
            }
        )
        if kwargs.get("onChange", None) is not None:
            string.content.events["change"].append(kwargs.get("onChange", None))

        string.content.attrs["value"] = {
            "type": "dynamic",
            "content": {"referenceType": "state", "id": state},
        }
        return string

    def IntListAsString(component, label, description, state, value, *args, **kwargs):
        if isinstance(value, list):
            value = [int(v) for v in value]
        if state not in component.stateDefinitions:
            component.addStateVariable(state, {"type": "array", "defaultValue": value})
        string = TeleportElement(MaterialContent(elementType="TextField"))
        variant = kwargs.get("variant", "outlined")
        string.content.attrs["variant"] = variant
        string.content.attrs["label"] = label
        string.content.attrs["fullWidth"] = True
        string.content.attrs["helperText"] = description
        string.content.style = {"margin": "10px 0px 10px 0px"}
        string.content.events["change"] = []
        string.content.events["change"].append(
            {
                "type": "stateChange",
                "modifies": state,
                "newState": "$e.target.value.split(',').map(x => parseInt(Number(x)))",
            }
        )
        if kwargs.get("onChange", None) is not None:
            string.content.events["change"].append(kwargs.get("onChange", None))

        string.content.attrs["value"] = {
            "type": "dynamic",
            "content": {"referenceType": "state", "id": state},
        }
        return string

    def DictionaryAsString(
        component, label, description, state, value, *args, **kwargs
    ):
        if state not in component.stateDefinitions:
            component.addStateVariable(state, {"type": "object", "defaultValue": value})
        if "_" + state not in component.stateDefinitions:
            if (
                isinstance(value, dict)
                and "type" in value
                and value["type"] == "dynamic"
            ):
                if "content" in value:
                    content = value["content"]
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
                    component.addStateVariable(
                        "_" + state,
                        {
                            "type": "string",
                            "defaultValue": "$JSON.stringify(" + v + ")",
                        },
                    )
                else:
                    component.addStateVariable(
                        "_" + state, {"type": "string", "defaultValue": "{}"}
                    )
            else:
                component.addStateVariable(
                    "_" + state, {"type": "string", "defaultValue": json.dumps(value)}
                )
        if "_e_" + state not in component.stateDefinitions:
            component.addStateVariable(
                "_e_" + state, {"type": "boolean", "defaultValue": False}
            )
        string = TeleportElement(MaterialContent(elementType="TextField"))
        variant = kwargs.get("variant", "outlined")
        string.content.attrs["variant"] = variant
        string.content.attrs["label"] = label
        string.content.attrs["fullWidth"] = True
        string.content.attrs["helperText"] = description
        string.content.style = {"margin": "10px 0px 10px 0px"}
        string.content.events["change"] = []

        string.content.events["change"].append(
            {
                "type": "stateChange",
                "modifies": "_" + state,
                "newState": "$(e.target.value)",
            }
        )
        if kwargs.get("onChange", None) is not None:
            string.content.events["change"].append(kwargs.get("onChange", None))

        string.content.events["change"].append(
            {
                "type": "stateChange",
                "modifies": state,
                "newState": "$((o)=>{try {return JSON.parse(o);}catch(e){return {};}})(e.target.value)",
            }
        )

        string.content.events["change"].append(
            {
                "type": "stateChange",
                "modifies": "_e_" + state,
                "newState": "$((o)=>{try {JSON.parse(o); return false;}catch(e){return true;}})(e.target.value)",
            }
        )

        string.content.attrs["error"] = {
            "type": "dynamic",
            "content": {"referenceType": "state", "id": "_e_" + state},
        }
        string.content.attrs["value"] = {
            "type": "dynamic",
            "content": {"referenceType": "state", "id": "_" + state},
        }
        return string

    def IntSlider(
        component, label, description, state, value=0, suffix="", *args, **kwargs
    ):
        if state not in component.stateDefinitions:
            component.addStateVariable(
                state, {"type": "integer", "defaultValue": value}
            )

        FormControl = TeleportElement(MaterialContent(elementType="FormControl"))
        variant = kwargs.get("variant", "outlined")
        FormControl.content.attrs["variant"] = variant
        FormControl.content.style = {
            "border": "1px solid rgba(0, 0, 0, 0.23)",
            "borderRadius": "4px",
            "flexDirection": "row",
            "paddingLeft": "30px",
        }
        slider = TeleportElement(MaterialContent(elementType="Slider"))
        InputLabel = TeleportElement(MaterialContent(elementType="InputLabel"))
        InputLabel.content.attrs["htmlFor"] = "component-filled"
        InputLabel.content.attrs["shrink"] = True

        InputLabel.content.style = {"background": "white", "padding": "0px 2px"}
        InputLabelText = TeleportStatic(content=label)
        FormHelperText = TeleportElement(MaterialContent(elementType="FormHelperText"))
        FormHelperText.addContent(TeleportStatic(content=description))

        slider.content.events["change"] = []
        slider.content.events["change"].append(
            {"type": "stateChange", "modifies": state, "newState": "$arguments[1]"}
        )
        if kwargs.get("onChange", None) is not None:
            slider.content.events["change"].append(kwargs.get("onChange", None))

        slider.content.attrs["value"] = {
            "type": "dynamic",
            "content": {"referenceType": "state", "id": state},
        }
        slider.content.attrs["defaultValue"] = value
        # slider.content.attrs["valueLabelDisplay"] = kwargs.get("valueLabelDisplay", "on")
        slider.content.attrs["step"] = kwargs.get("step", 1)
        slider.content.attrs["min"] = kwargs.get("min", 0)
        slider.content.attrs["max"] = kwargs.get("max", 100)
        if kwargs.get("marks", True):
            min_v = slider.content.attrs["min"]
            max_v = slider.content.attrs["max"]
            step_v = slider.content.attrs["step"]
            slider.content.attrs["marks"] = [
                {
                    "value": int(i),
                    "label": str(int(i)),
                }
                for i in range(min_v, max_v + 1, step_v)
            ]
        InputLabel.addContent(InputLabelText)
        FormControl.addContent(InputLabel)
        FormControl.addContent(slider)
        FormControl.addContent(FormHelperText)
        return FormControl

    def NumberSlider(
        component, label, description, state, value=0, suffix="", *args, **kwargs
    ):
        if state not in component.stateDefinitions:
            component.addStateVariable(state, {"type": "number", "defaultValue": value})

        FormControl = TeleportElement(MaterialContent(elementType="FormControl"))
        variant = kwargs.get("variant", "outlined")
        FormControl.content.attrs["variant"] = variant
        FormControl.content.style = {
            "border": "1px solid rgba(0, 0, 0, 0.23)",
            "borderRadius": "4px",
            "flexDirection": "row",
            "paddingLeft": "30px",
        }
        slider = TeleportElement(MaterialContent(elementType="Slider"))
        InputLabel = TeleportElement(MaterialContent(elementType="InputLabel"))
        InputLabel.content.attrs["htmlFor"] = "component-filled"
        InputLabel.content.attrs["shrink"] = True

        InputLabel.content.style = {"background": "white", "padding": "0px 2px"}
        InputLabelText = TeleportStatic(content=label)
        FormHelperText = TeleportElement(MaterialContent(elementType="FormHelperText"))
        FormHelperText.addContent(TeleportStatic(content=description))

        slider.content.events["change"] = []
        slider.content.events["change"].append(
            {"type": "stateChange", "modifies": state, "newState": "$arguments[1]"}
        )
        if kwargs.get("onChange", None) is not None:
            slider.content.events["change"].append(kwargs.get("onChange", None))

        slider.content.attrs["value"] = {
            "type": "dynamic",
            "content": {"referenceType": "state", "id": state},
        }
        slider.content.attrs["defaultValue"] = value
        slider.content.attrs["valueLabelDisplay"] = kwargs.get(
            "valueLabelDisplay", "auto"
        )
        slider.content.attrs["step"] = kwargs.get("step", 0.1)
        slider.content.attrs["min"] = kwargs.get("min", 0)
        slider.content.attrs["max"] = kwargs.get("max", 100)
        if kwargs.get("marks", True):
            min_v = slider.content.attrs["min"]
            max_v = slider.content.attrs["max"]
            step_v = 0.5  # slider.content.attrs["step"]
            slider.content.attrs["marks"] = [
                {
                    "value": float(i),
                    "label": "%.1f" % i,
                }
                for i in np.arange(min_v, max_v + step_v, step_v)
            ]

        InputLabel.addContent(InputLabelText)
        FormControl.addContent(InputLabel)
        FormControl.addContent(slider)
        FormControl.addContent(FormHelperText)
        return FormControl

    def Switch(component, label, description, state, value=False, *args, **kwargs):
        if state not in component.stateDefinitions:
            component.addStateVariable(
                state, {"type": "boolean", "defaultValue": value}
            )
        FormControl = TeleportElement(MaterialContent(elementType="FormControl"))
        variant = kwargs.get("variant", "outlined")
        FormControl.content.attrs["variant"] = variant
        FormControl.content.style = {
            "border": "1px solid rgba(0, 0, 0, 0.23)",
            "borderRadius": "4px",
            "flexDirection": "row",
            "width": "100%",
        }
        switch = TeleportElement(MaterialContent(elementType="Switch"))
        InputLabel = TeleportElement(MaterialContent(elementType="InputLabel"))
        InputLabel.content.attrs["htmlFor"] = "component-filled"
        InputLabel.content.attrs["shrink"] = True

        InputLabel.content.style = {"background": "white", "padding": "0px 2px"}
        InputLabelText = TeleportStatic(content=label)
        FormHelperText = TeleportElement(MaterialContent(elementType="FormHelperText"))
        FormHelperText.addContent(TeleportStatic(content=description))

        switch.content.events["change"] = []
        switch.content.events["change"].append(
            {"type": "stateChange", "modifies": state, "newState": "$e.target.checked"}
        )
        if kwargs.get("onChange", None) is not None:
            switch.content.events["change"].append(kwargs.get("onChange", None))

        switch.content.attrs["checked"] = {
            "type": "dynamic",
            "content": {"referenceType": "state", "id": state},
        }
        InputLabel.addContent(InputLabelText)
        FormControl.addContent(InputLabel)
        FormControl.addContent(switch)
        FormControl.addContent(FormHelperText)
        return FormControl

    def IntSwitch(
        component, label, description, state, value, options, *args, **kwargs
    ):
        if state not in component.stateDefinitions:
            component.addStateVariable(state, {"type": "number", "defaultValue": value})
        if len(options) != 2:
            raise Exception("exactly 2 options are required")
        k = [int(vv) for vv in options.keys()]
        v = [str(vv) for vv in options.values()]
        IntSwitch = TeleportElement(TeleportContent(elementType="IntSwitch"))
        IntSwitch.content.attrs["options"] = v
        IntSwitch.content.attrs["ids"] = k
        IntSwitch.content.attrs["label"] = label
        IntSwitch.content.attrs["description"] = description
        IntSwitch.content.attrs["default_value"] = value
        IntSwitch.content.events["change"] = []
        IntSwitch.content.events["change"].append(
            {"type": "stateChange", "modifies": state, "newState": "$e.target.value"}
        )
        if kwargs.get("onChange", None) is not None:
            IntSwitch.content.events["change"].append(kwargs.get("onChange", None))
        return IntSwitch

    def Header(label, *args, **kwargs):
        Typography = TeleportElement(MaterialContent(elementType="Typography"))
        variant = kwargs.get("variant", "h6")
        Typography.content.attrs["variant"] = variant
        TypographyText = TeleportStatic(content=label)
        Divider = TeleportElement(MaterialContent(elementType="Divider"))
        Typography.addContent(TypographyText)
        Typography.addContent(Divider)
        return Typography

    def Select(component, label, description, state, value, options, *args, **kwargs):
        if state not in component.stateDefinitions:
            component.addStateVariable(state, {"type": "string", "defaultValue": value})
        select = TeleportElement(MaterialContent(elementType="Select"))
        variant = kwargs.get("variant", "outlined")
        select.content.attrs["variant"] = variant
        select.content.attrs["label"] = label
        #select.content.attrs["select"] = True
        select.content.attrs["fullWidth"] = True
        #select.content.attrs["helperText"] = description
        select.content.style = {"margin": "10px 0px 10px 0px"}
        select.content.events["change"] = []

        select.content.events["change"].append(
            {"type": "stateChange", "modifies": state, "newState": "$e.target.value"}
        )
        if kwargs.get("onChange", None) is not None:
            select.content.events["change"].append(kwargs.get("onChange", None))

        select.content.attrs["value"] = {
            "type": "dynamic",
            "content": {"referenceType": "state", "id": state},
        }

        for key, value in options.items():
            option = TeleportElement(MaterialContent(elementType="MenuItem"))
            option.content.attrs["key"] = key
            option.content.attrs["value"] = key
            option.addContent(TeleportStatic(content=value))
            select.addContent(option)

        return select

    def ButtonList(
        component, label, description, state, value, options, *args, **kwargs
    ):
        if state not in component.stateDefinitions:
            component.addStateVariable(state, {"type": "string", "defaultValue": value})
        component.addStateVariable(
            state + "_options",
            {
                "type": "list",
                "defaultValue": [
                    {"key": k, "name": v["name"]} for k, v in options.items()
                ],
            },
        )

        FormControl = TeleportElement(MaterialContent(elementType="FormControl"))
        variant = kwargs.get("variant", "outlined")
        FormControl.content.attrs["variant"] = variant
        FormControl.content.style = {
            "border": "1px solid rgba(0, 0, 0, 0.23)",
            "borderRadius": "4px",
            "width": "100%",
        }

        InputLabel = TeleportElement(MaterialContent(elementType="InputLabel"))
        InputLabel.content.attrs["htmlFor"] = "component-filled"
        InputLabel.content.attrs["shrink"] = True

        InputLabel.content.style = {"background": "white", "padding": "0px 2px"}
        InputLabelText = TeleportStatic(content=label)
        FormHelperText = TeleportElement(MaterialContent(elementType="FormHelperText"))
        FormHelperText.addContent(TeleportStatic(content=description))
        InputLabel.addContent(InputLabelText)

        ButtonListMaterial = TeleportElement(
            TeleportContent(elementType="ButtonListMaterial")
        )
        ButtonListMaterial.content.attrs["value"] = {
            "type": "dynamic",
            "content": {"referenceType": "state", "id": state},
        }
        ButtonListMaterial.content.attrs["description"] = description
        ButtonListMaterial.content.attrs["options"] = {
            "type": "dynamic",
            "content": {"referenceType": "state", "id": state + "_options"},
        }
        ButtonListMaterial.content.events["change"] = []
        ButtonListMaterial.content.events["change"].append(
            {"type": "stateChange", "modifies": state, "newState": "$e.target.value"}
        )
        if kwargs.get("onChange", None) is not None:
            ButtonListMaterial.content.events["change"].append(
                kwargs.get("onChange", None)
            )

        Paper = TeleportElement(MaterialContent(elementType="Paper"))
        Paper.content.style = {"width": "100%", "margin": "10px 0px 10px 0px"}

        FormControl.addContent(InputLabel)
        FormControl.addContent(ButtonListMaterial)
        Paper.addContent(FormControl)
        Paper.addContent(FormHelperText)
        return Paper

    def IconList(component, label, description, state, value, options, *args, **kwargs):
        if state not in component.stateDefinitions:
            component.addStateVariable(state, {"type": "string", "defaultValue": value})
        component.addStateVariable(
            state + "_options",
            {
                "type": "list",
                "defaultValue": [
                    {"key": k, "icon": v["icon"], "name": v["name"]}
                    for k, v in options.items()
                ],
            },
        )

        FormControl = TeleportElement(MaterialContent(elementType="FormControl"))
        variant = kwargs.get("variant", "outlined")
        FormControl.content.attrs["variant"] = variant
        FormControl.content.style = {
            "border": "1px solid rgba(0, 0, 0, 0.23)",
            "borderRadius": "4px",
            "width": "100%",
        }

        InputLabel = TeleportElement(MaterialContent(elementType="InputLabel"))
        InputLabel.content.attrs["htmlFor"] = "component-filled"
        InputLabel.content.attrs["shrink"] = True

        InputLabel.content.style = {"background": "white", "padding": "0px 2px"}
        InputLabelText = TeleportStatic(content=label)
        FormHelperText = TeleportElement(MaterialContent(elementType="FormHelperText"))
        FormHelperText.addContent(TeleportStatic(content=description))
        InputLabel.addContent(InputLabelText)

        IconListMaterial = TeleportElement(
            TeleportContent(elementType="IconListMaterial")
        )
        IconListMaterial.content.attrs["value"] = {
            "type": "dynamic",
            "content": {"referenceType": "state", "id": state},
        }
        IconListMaterial.content.attrs["description"] = description
        IconListMaterial.content.attrs["options"] = {
            "type": "dynamic",
            "content": {"referenceType": "state", "id": state + "_options"},
        }
        IconListMaterial.content.events["change"] = []
        IconListMaterial.content.events["change"].append(
            {"type": "stateChange", "modifies": state, "newState": "$e.target.value"}
        )

        if kwargs.get("onChange", None) is not None:
            IconListMaterial.content.events["change"].append(
                kwargs.get("onChange", None)
            )

        Paper = TeleportElement(MaterialContent(elementType="Paper"))
        Paper.content.style = {"width": "100%", "margin": "10px 0px 10px 0px"}

        FormControl.addContent(InputLabel)
        FormControl.addContent(IconListMaterial)
        Paper.addContent(FormControl)
        Paper.addContent(FormHelperText)
        return Paper

    def String(component, label, description, state, value, *args, **kwargs):
        if state not in component.stateDefinitions:
            component.addStateVariable(state, {"type": "string", "defaultValue": value})
        string = TeleportElement(MaterialContent(elementType="TextField"))
        variant = kwargs.get("variant", "outlined")
        string.content.attrs["variant"] = variant
        string.content.attrs["label"] = label
        # string.content.attrs["select"] = True
        string.content.attrs["fullWidth"] = True
        string.content.attrs["helperText"] = description
        string.content.style = {"margin": "10px 0px 10px 0px"}
        string.content.events["change"] = []
        string.content.events["change"].append(
            {"type": "stateChange", "modifies": state, "newState": "$e.target.value"}
        )
        if kwargs.get("onChange", None) is not None:
            string.content.events["change"].append(kwargs.get("onChange", None))

        string.content.attrs["value"] = {
            "type": "dynamic",
            "content": {"referenceType": "state", "id": state},
        }
        return string

    def Group(elements, *args, **kwargs):
        group = TeleportElement(MaterialContent(elementType="Grid"))
        group.content.attrs["container"] = True
        group.content.attrs["direction"] = kwargs.get("layout", "row")
        if kwargs.get("label", None) != None:
            Typography = TeleportElement(MaterialContent(elementType="Typography"))
            Typography.content.attrs["variant"] = "body1"
            Typography.content.attrs["gutterBottom"] = True
            Typography.content.style = {
                "flex": 1,
                "textAlign": "center",
                "padding": "10px",
            }
            TypographyText = TeleportStatic(content=kwargs.get("label", None))
            Typography.addContent(TypographyText)
            group.addContent(Typography)

        style = kwargs.get("style", {"margin": "5px", "width": "auto"})
        group.content.style = style
        for element in elements:
            group.addContent(element)
        return group

    def Container(elements, *args, **kwargs):

        FormControl = TeleportElement(MaterialContent(elementType="FormControl"))
        variant = kwargs.get("variant", "outlined")
        label = kwargs.get("label", "")
        description = kwargs.get("description", "")
        FormControl.content.attrs["variant"] = variant
        FormControl.content.style = {
            "border": "1px solid rgba(0, 0, 0, 0.23)",
            "borderRadius": "4px",
            "width": "100%",
        }
        InputLabel = TeleportElement(MaterialContent(elementType="InputLabel"))
        InputLabel.content.attrs["htmlFor"] = "component-filled"
        InputLabel.content.attrs["shrink"] = True

        InputLabel.content.style = {"background": "white", "padding": "0px 2px"}
        InputLabelText = TeleportStatic(content=label)
        FormHelperText = TeleportElement(MaterialContent(elementType="FormHelperText"))
        FormHelperText.addContent(TeleportStatic(content=description))
        InputLabel.addContent(InputLabelText)

        group = TeleportElement(MaterialContent(elementType="Grid"))
        group.content.attrs["container"] = True
        group.content.attrs["direction"] = kwargs.get("layout", "row")
        group.content.attrs["wrap"] = kwargs.get("wrap", "nowrap")

        style = kwargs.get("style", {"margin": "5px"})
        group.content.style = style
        for element in elements:
            group.addContent(element)
        FormControl.addContent(InputLabel)
        FormControl.addContent(group)

        Paper = TeleportElement(MaterialContent(elementType="Paper"))
        Paper.content.style = {"width": "100%", "margin": "10px 0px 10px 0px"}
        Paper.addContent(FormControl)
        Paper.addContent(FormHelperText)
        return Paper

    def Tabs(component, children, state, *args, **kwargs):
        if state not in component.stateDefinitions:
            component.addStateVariable(
                state,
                {"type": "integer", "defaultValue": kwargs.get("default_value", 0)},
            )

        main_container = TeleportElement(MaterialContent(elementType="Paper"))
        bar = TeleportElement(MaterialContent(elementType="AppBar"))
        bar.content.attrs["position"] = "static"
        bar.content.attrs["color"] = kwargs.get("barColor", "primary")

        tabs = TeleportElement(MaterialContent(elementType="Tabs"))
        tabs.content.attrs["indicatorColor"] = kwargs.get("indicatorColor", "primary")
        tabs.content.attrs["textColor"] = kwargs.get("textColor", "primary")
        tabs.content.attrs["variant"] = "scrollable"
        tabs.content.attrs["scrollButtons"] = "auto"
        tabs.content.attrs["value"] = {
            "type": "dynamic",
            "content": {"referenceType": "state", "id": state},
        }

        i = 0
        bar.addContent(tabs)
        main_container.addContent(bar)
        for key, value in children.items():
            container = TeleportConditional(MaterialContent(elementType="Paper"))

            container.reference = {
                "type": "dynamic",
                "content": {"referenceType": "state", "id": state},
            }
            container.value = i
            if isinstance(value, list):
                container.addContent(FormHelper.Group(value))
            elif isinstance(value, TeleportNode):
                container.addContent(value)
            else:
                raise Exception("invalid type of component")

            tab = TeleportElement(MaterialContent(elementType="Tab"))
            tab.content.attrs["label"] = key
            tab.content.events["click"] = [
                {"type": "stateChange", "modifies": state, "newState": i},
            ]
            i = i + 1
            main_container.addContent(container)
            tabs.addContent(tab)

        return main_container

    def ConditionalGroup(component, elements, state, conditions, *args, **kwargs):
        lstate = state.split(".")
        ltype = "state"
        if component.stateDefinitions.get(lstate[0], None) is None:
            ltype = "prop"
            if component.propDefinitions.get(lstate[0], None) is None:
                raise Exception("Not existing reference ('" + state + "')")

        Paper = MaterialContent(elementType="Paper")
        Paper.style = {"width": "100%"}
        container = TeleportConditional(Paper)
        container.reference = {
            "type": "dynamic",
            "content": {"referenceType": ltype, "id": state},
        }
        container.conditions = conditions
        for element in elements:
            if isinstance(element, list):
                container.addContent(FormHelper.Group(element))
            elif isinstance(element, TeleportNode):
                container.addContent(element)
        return container


class AppBuilder:

    """def Results(Component, *args, **kwargs):
    results = kwargs.get("results", {});
    onClick = kwargs.get("onClick", []);
    onLoad = kwargs.get("onLoad", []);
    open_plot = {k:'secondary' for  k,v in results.items()}
    Component.addStateVariable("open_plot", {"type":"object", "defaultValue": open_plot})
    Grid = TeleportElement(MaterialContent(elementType="Grid"))
    Grid.content.style = { 'width' : '100%' }
    Grid.content.attrs["container"] = True
    Grid.content.attrs["direction"] = "column"
    colors = {True:"primary",False:"secondary"}
    for k,v in results.items():
        open_elem = {k1:colors[k==k1] for k1,v1 in results.items()}
        v_action = []
        if isinstance(v["action"], dict):
            v_action.append(v["action"])
        elif isinstance(v["action"], list):
            for va in v["action"]:
                v_action.append(va)
        v_action.append({ "type": "stateChange", "modifies": "open_plot","newState":open_elem })
        Grid.addContent(MaterialBuilder.GridItem(content=MaterialBuilder.Button(
          title = v["title"],
          color={
            "type": "dynamic",
            "content": {
             "referenceType": "state",
             "id": "open_plot." + k
            }
          },
          onClickButton = onClick + v_action + onLoad
        )))
    return Grid"""

    def Results(Component, *args, **kwargs):
        results = kwargs.get("results", {})
        onClick = kwargs.get("onClick", [])
        onLoad = kwargs.get("onLoad", [])
        Component.addStateVariable(
            "open_plot", {"type": "string", "defaultValue": list(results.keys())[0]}
        )
        ToggleButtonGroup = TeleportElement(
            MaterialContent(elementType="ToggleButtonGroup")
        )
        ToggleButtonGroup.content.style = {
            "width": "100%",
            "flexDirection": "column",
            "display": "inline-flex",
        }
        ToggleButtonGroup.content.attrs["orientation"] = "vertical"
        ToggleButtonGroup.content.attrs["exclusive"] = True

        ToggleButtonGroup.content.attrs["value"] = {
            "type": "dynamic",
            "content": {"referenceType": "state", "id": "open_plot"},
        }

        for k, v in results.items():
            v_action = []
            if isinstance(v["action"], dict):
                v_action.append(v["action"])
            elif isinstance(v["action"], list):
                for va in v["action"]:
                    v_action.append(va)
            v_action.append(
                {"type": "stateChange", "modifies": "open_plot", "newState": k}
            )
            ToggleButton = TeleportElement(
                MaterialContent(elementType="ToggleButton")
            )
            ToggleButton.content.attrs["value"] = k
            ToggleButton.content.events["click"] = onClick + v_action + onLoad
            Typography = TeleportElement(MaterialContent(elementType="Typography"))
            Typography.addContent(TeleportStatic(content=v["title"]))
            ToggleButton.addContent(Typography)
            ToggleButtonGroup.addContent(ToggleButton)

        return ToggleButtonGroup

    def createGroups(Component, layout, fields, *args, **kwargs):
        Group = None

        if "type" in layout and layout["type"] == "tab":
            Group = TeleportElement(MaterialContent(elementType="Paper"))
            children = {}
            if "children" in layout:
                for i, child in enumerate(layout["children"]):
                    children[child["label"]] = AppBuilder.createGroups(
                        Component, child, fields
                    )
            Group.addContent(FormHelper.Tabs(Component, children, "testing"))
        elif "type" in layout and layout["type"] == "group":
            Group = TeleportElement(MaterialContent(elementType="Paper"))
            Group.content.style = {"border": "1px solid #f1f1f1", "width": "100%"}
            children = []
            if "children" in layout:
                for i, child in enumerate(layout["children"]):
                    children.append(AppBuilder.createGroups(Component, child, fields))
            direction = "row"
            if "layout" in layout and layout["layout"] == "horizontal":
                direction = "column"
            Group.addContent(
                FormHelper.Group(children, direction=direction, label=layout["label"])
            )
        elif "type" in layout and layout["type"] == "container":
            Group = TeleportElement(MaterialContent(elementType="Paper"))
            Group.content.style = {"border": "1px solid #f1f1f1", "width": "100%"}
            children = []
            if "children" in layout:
                for i, child in enumerate(layout["children"]):
                    children.append(AppBuilder.createGroups(Component, child, fields))
            direction = "row"
            label = ""
            description = ""
            if "layout" in layout and layout["layout"] == "horizontal":
                direction = "column"
            if "description" in layout:
                description = layout["description"]
            if "label" in layout:
                label = layout["label"]
            Group.addContent(
                FormHelper.Container(
                    children, direction=direction, label=label, description=description
                )
            )
        else:
            if layout["id"] in fields:
                Group = fields[layout["id"]]
            elif "_" + layout["id"] in fields:
                Group = fields["_" + layout["id"]]
            else:
                Group = TeleportElement(MaterialContent(elementType="Paper"))

        if "enable" in layout and layout["enable"] is not None:
            for r in layout["enable"]:
                operand = None
                operation = "=="
                value = None
                if "operand" in r:
                    operand = r["operand"]
                if "operator" in r:
                    operation = r["operator"]
                if "value" in r:
                    if isinstance(r["value"], str):
                        value = r["value"].strip('"')
                    else:
                        value = r["value"]
                if value is not None and operation is not None and operand is not None:
                    if operation == "in":
                        listv = [
                            {"operation": "==", "operand": v} for v in value.split(",")
                        ]
                        Group = FormHelper.ConditionalGroup(
                            Component, [Group], operand, listv
                        )
                        Group.matchingCriteria = "one"
                    else:
                        Group = FormHelper.ConditionalGroup(
                            Component,
                            [Group],
                            operand,
                            [{"operation": operation, "operand": value}],
                        )
        return Group

    def Settings(tp, Component, settings, *args, **kwargs):
        layout = kwargs.get(
            "layout",
            {
                "type": "group",
                "id": "",
                "label": "",
                "layout": "horizontal",
                "children": [{"id": id} for id, value in settings.items()],
            },
        )

        MaterialComponents.FormatCustomNumber(tp)
        MaterialComponents.IconList(tp)
        MaterialComponents.IntSwitch(tp)
        MaterialComponents.ButtonList(tp)

        NComponent = TeleportComponent(
            "NsopticsSettingsComponent",
            TeleportElement(MaterialContent(elementType="Paper")),
        )
        NComponent.node.content.style = {"width": "100%"}
        NComponent.addPropVariable(
            "onSubmit", {"type": "func", "defaultValue": "(e)=>{}"}
        )
        NComponent.addPropVariable(
            "onClick", {"type": "func", "defaultValue": "(e)=>{}"}
        )
        NComponent.addPropVariable(
            "onChange", {"type": "func", "defaultValue": "(e)=>{}"}
        )
        NComponent.addPropVariable(
            "onLoad", {"type": "func", "defaultValue": "(e)=>{}"}
        )
        NComponent.addPropVariable(
            "onSuccess", {"type": "func", "defaultValue": "(e)=>{}"}
        )
        NComponent.addPropVariable(
            "onError", {"type": "func", "defaultValue": "(e)=>{}"}
        )
        NComponent.addPropVariable(
            "onStatusChange",
            {"type": "func", "defaultValue": "(e)=>{ console.log (e.target.value)}"},
        )

        parameters = {}
        params = {}
        for k, v in settings.items():
            if isinstance(k, str) == False or k.isnumeric():
                k = "_" + k
            if "type" in v:
                param = None
                value = {
                    "type": "dynamic",
                    "content": {"referenceType": "prop", "id": "parameters." + k},
                }
                if v["type"] == "IconList":
                    param = FormHelper.IconList(
                        NComponent,
                        v["label"],
                        v["description"],
                        k,
                        value,
                        v["options"],
                        onChange={
                            "type": "propCall2",
                            "calls": "onChange",
                            "args": ["{'" + k + "':e.target.value}"],
                        },
                    )
                if v["type"] == "ButtonList":
                    param = FormHelper.ButtonList(
                        NComponent,
                        v["label"],
                        v["description"],
                        k,
                        value,
                        v["options"],
                        onChange={
                            "type": "propCall2",
                            "calls": "onChange",
                            "args": ["{'" + k + "':e.target.value}"],
                        },
                    )
                if v["type"] == "Select":
                    param = FormHelper.Select(
                        NComponent,
                        v["label"],
                        v["description"],
                        k,
                        value,
                        v["options"],
                        onChange={
                            "type": "propCall2",
                            "calls": "onChange",
                            "args": ["{'" + k + "':e.target.value}"],
                        },
                    )
                elif v["type"] == "IntegerAsString":
                    param = FormHelper.NumberAsString(
                        NComponent,
                        v["label"],
                        v["description"],
                        k,
                        value,
                        v["units"],
                        decimalScale=0,
                        onChange={
                            "type": "propCall2",
                            "calls": "onChange",
                            "args": [
                                "{'" + k + "':e.target.value + '" + v["units"] + "'}"
                            ],
                        },
                    )
                    if (
                        "min" in v
                        and "max" in v
                        and v["min"] is not None
                        and v["max"] is not None
                    ):
                        param.content.attrs["range"] = [v["min"], v["max"]]

                elif v["type"] == "Integer":
                    param = FormHelper.Number(
                        NComponent,
                        v["label"],
                        v["description"],
                        k,
                        value,
                        v["units"],
                        decimalScale=0,
                        onChange={
                            "type": "propCall2",
                            "calls": "onChange",
                            "args": ["{'" + k + "':e.target.value}"],
                        },
                    )
                    if (
                        "min" in v
                        and "max" in v
                        and v["min"] is not None
                        and v["max"] is not None
                    ):
                        param.content.attrs["range"] = [v["min"], v["max"]]

                elif v["type"] == "Number":
                    param = FormHelper.Number(
                        NComponent,
                        v["label"],
                        v["description"],
                        k,
                        value,
                        v["units"],
                        onChange={
                            "type": "propCall2",
                            "calls": "onChange",
                            "args": ["{'" + k + "':e.target.value}"],
                        },
                    )
                    if (
                        "min" in v
                        and "max" in v
                        and v["min"] is not None
                        and v["max"] is not None
                    ):
                        param.content.attrs["range"] = [v["min"], v["max"]]

                elif v["type"] == "NumberAsString":
                    param = FormHelper.NumberAsString(
                        NComponent,
                        v["label"],
                        v["description"],
                        k,
                        value,
                        v["units"],
                        onChange={
                            "type": "propCall2",
                            "calls": "onChange",
                            "args": [
                                "{'" + k + "':e.target.value + '" + v["units"] + "'}"
                            ],
                        },
                    )
                    if (
                        "min" in v
                        and "max" in v
                        and v["min"] is not None
                        and v["max"] is not None
                    ):
                        param.content.attrs["range"] = [v["min"], v["max"]]

                elif v["type"] == "String":
                    param = FormHelper.String(
                        NComponent,
                        v["label"],
                        v["description"],
                        k,
                        value,
                        onChange={
                            "type": "propCall2",
                            "calls": "onChange",
                            "args": ["{'" + k + "':e.target.value}"],
                        },
                    )
                elif v["type"] == "Boolean":
                    param = FormHelper.Switch(
                        NComponent,
                        v["label"],
                        v["description"],
                        k,
                        value,
                        onChange={
                            "type": "propCall2",
                            "calls": "onChange",
                            "args": ["{'" + k + "':e.target.checked}"],
                        },
                    )
                elif v["type"] == "IntSwitch":
                    param = FormHelper.IntSwitch(
                        NComponent,
                        v["label"],
                        v["description"],
                        k,
                        value,
                        v["options"],
                        onChange={
                            "type": "propCall2",
                            "calls": "onChange",
                            "args": ["{'" + k + "':e.target.value}"],
                        },
                    )
                elif v["type"] == "DictionaryAsString":
                    param = FormHelper.DictionaryAsString(
                        NComponent,
                        v["label"],
                        v["description"],
                        k,
                        value,
                        onChange={
                            "type": "propCall2",
                            "calls": "onChange",
                            "args": ["{'" + k + "':e.target.value}"],
                        },
                    )
                elif v["type"] == "StringListAsString":
                    param = FormHelper.StringListAsString(
                        NComponent,
                        v["label"],
                        v["description"],
                        k,
                        value,
                        onChange={
                            "type": "propCall2",
                            "calls": "onChange",
                            "args": ["{'" + k + "':e.target.value}"],
                        },
                    )
                elif v["type"] == "NumberListAsString":
                    param = FormHelper.NumberListAsString(
                        NComponent,
                        v["label"],
                        v["description"],
                        k,
                        value,
                        onChange={
                            "type": "propCall2",
                            "calls": "onChange",
                            "args": ["{'" + k + "':e.target.value}"],
                        },
                    )
                elif v["type"] == "IntListAsString":
                    param = FormHelper.IntListAsString(
                        NComponent,
                        v["label"],
                        v["description"],
                        k,
                        value,
                        onChange={
                            "type": "propCall2",
                            "calls": "onChange",
                            "args": ["{'" + k + "':e.target.value}"],
                        },
                    )

            if param is not None:
                params[k] = param
                parameters[k] = v["default_value"]
        Tabs = AppBuilder.createGroups(NComponent, layout, params)

        if kwargs.get("runSimulation", "rappture") == "rappture":
            runSimulation = RapptureBuilder.onSimulate(
                tp,
                NComponent,
                cache_store=kwargs.get("cache_store", "CacheStore"),
                toolname=kwargs.get("toolname", ""),
                url=kwargs.get("url", None),
                jupyter_cache=kwargs.get("jupyter_cache", None),
            )
        else:
            runSimulation = SimtoolBuilder.onSimulate(
                tp,
                NComponent,
                cache_store=kwargs.get("cache_store", "CacheStore"),
                toolname=kwargs.get("toolname", ""),
                revision=kwargs.get("revision", ""),
                url=kwargs.get("url", None),
                outputs=kwargs.get("outputs", []),
                jupyter_cache=kwargs.get("jupyter_cache", None),
            )

        runSimulation.append(
            {
                "type": "propCall2",
                "calls": "onClick",
                "args": [runSimulation[0]["args"][1]],
            }
        )
        runSimulation.append(
            {
                "type": "propCall2",
                "calls": "onSubmit",
                "args": [runSimulation[0]["args"][1]],
            }
        )
        Grid = TeleportElement(MaterialContent(elementType="Grid"))
        Grid.content.attrs["container"] = True
        Grid.content.attrs["direction"] = "column"
        Grid.addContent(
            MaterialBuilder.GridItem(
                content=MaterialBuilder.Button(
                    title="Simulate", onClickButton=runSimulation, color="inherit"
                )
            )
        )
        Tabs.addContent(Grid)
        NComponent.node.addContent(Tabs)
        NComponent.addPropVariable(
            "parameters", {"type": "object", "defaultValue": parameters}
        )
        Component.addStateVariable(
            "parameters", {"type": "object", "defaultValue": parameters}
        )
        AppSettings = TeleportElement(
            TeleportContent(elementType="AppSettingsComponent")
        )
        AppSettings.content.attrs["parameters"] = {
            "type": "dynamic",
            "content": {"referenceType": "state", "id": "parameters"},
        }
        tp.components["AppSettingsComponent"] = NComponent

        AppSettings.content.events["submit"] = [
            {
                "type": "stateChange",
                "modifies": "parameters",
                "newState": "$e.target.value",
            }
        ]

        AppSettings.content.events["onChange"] = [
            {
                "type": "stateChange",
                "modifies": "parameters",
                "newState": "${...self.state.parameters, ...e}",
            }
        ]

        return AppSettings

    def ColorSliders(tp, Component, *args, **kwargs):
        MaterialComponents.ColorSliders(tp)
        sliders = kwargs.get("sliders", {})
        skeys = list(sliders.keys())
        svalues = list(sliders.values())
        Grid = TeleportElement(MaterialContent(elementType="Grid"))
        Grid.content.attrs["container"] = True
        Grid.content.attrs["direction"] = "column"

        if len(skeys) > 0:
            Component.addStateVariable(
                "planes",
                {
                    "type": "array",
                    "defaultValue": [
                        {
                            "visible": False,
                            "center": 50,
                            "color": s["color"],
                            "label": s["label"],
                            "plane": s["plane"],
                            "use_miller": "options" in s,
                        }
                        for s in svalues
                    ],
                },
            )

            ColorSliders0 = TeleportElement(TeleportContent(elementType="ColorSliders"))
            ColorSliders0.content.attrs["colors"] = {
                "type": "dynamic",
                "content": {"referenceType": "state", "id": "planes"},
            }

            ColorSliders0.content.events["change"] = [
                {
                    "type": "stateChange",
                    "modifies": "planes",
                    "newState": "$e.target.value",
                }
            ]
            Grid.addContent(
                MaterialBuilder.GridItem(
                    content=ColorSliders0, style={"padding": "0px"}
                )
            )
            eol = "\n"
            updateState = ""
            updateState += "(c,i,a,v)=>{ " + eol
            updateState += "  let new_map = c.state.planes.map((e, ii)=>{" + eol
            updateState += "    if(ii==i){" + eol
            updateState += "      let clone = JSON.parse(JSON.stringify(e));" + eol
            updateState += "      clone[a] = v.split('').map((k)=>Number(k));" + eol
            updateState += "      return clone;" + eol
            updateState += "    }" + eol
            updateState += "    return e;" + eol
            updateState += "  })" + eol
            updateState += "  c.setState({'planes' : new_map});" + eol
            updateState += "  if (c.timeout){" + eol
            updateState += "    clearTimeout(c.timeout)" + eol
            updateState += "  }" + eol
            updateState += (
                "  c.timeout = setTimeout(()=>{ c.props.onChange( {'target':{'value':new_map}} ) }, 20);"
                + eol
            )
            updateState += "}" + eol
            Component.addPropVariable(
                "updateState", {"type": "func", "defaultValue": updateState}
            )
            for s, v in sliders.items():
                if "options" in v:
                    Component.addStateVariable(
                        s,
                        {
                            "type": "string",
                            "defaultValue": list(v["options"].keys())[0],
                        },
                    )
                    ButtonListMaterial = TeleportElement(
                        TeleportContent(elementType="ButtonListMaterial")
                    )
                    ButtonListMaterial.content.attrs["always_open"] = True
                    ButtonListMaterial.content.attrs["hide_header"] = True
                    ButtonListMaterial.content.attrs["value"] = {
                        "type": "dynamic",
                        "content": {"referenceType": "state", "id": s + ""},
                    }
                    ButtonListMaterial.content.attrs["description"] = ""
                    ButtonListMaterial.content.attrs["options"] = [
                        {"key": k, "name": k} for k, v in (v["options"].items())
                    ]
                    ButtonListMaterial.content.events["change"] = [
                        {
                            "type": "stateChange",
                            "modifies": s,
                            "newState": "$e.target.value",
                        },
                        {
                            "type": "propCall2",
                            "calls": "updateState",
                            "args": ["self", "3", "'plane'", "e.target.value"],
                        },
                    ]
                    Grid.addContent(
                        MaterialBuilder.GridItem(
                            content=ButtonListMaterial, style={"padding": "0px"}
                        )
                    )

        return Grid
