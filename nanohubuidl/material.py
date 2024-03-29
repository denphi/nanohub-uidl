from .teleport import *


class MaterialContent(TeleportContent):
    def __init__(self, *args, **kwargs):
        self.dependency = {
            "type": "package",
            "path": "@material-ui/core",
            "version": "latest",
            "meta": {"namedImport": True},
        }
        #'material-ui': 'https://unpkg.com/@material-ui/core@latest/umd/material-ui.production.min',
        super().__init__(self, *args, **kwargs)

    def buildElementType(self):
        elementType = self.semanticType
        if elementType is None:
            elementType = self.elementType
        return "Material." + elementType

    def __json__(self):
        tjson = super().__json__()
        tjson["dependency"] = self.dependency
        if self.elementType != None:
            tjson["semanticType"] = "Material." + self.elementType
            tjson["dependency"]["meta"]["originalName"] = self.elementType
        return tjson



class MaterialBuilder:
    def AppBar(*args, **kwargs):
        AppBar = TeleportElement(MaterialContent(elementType="AppBar"))
        AppBar.content.attrs["position"] = "static"
        AppBar.content.attrs["color"] = kwargs.get("color", "primary")

        if kwargs.get("style_state", None) is not None:
            AppBar.content.attrs["className"] = {
                "type": "dynamic",
                "content": {"referenceType": "state", "id": kwargs.get("style_state")},
            }
        AppBar.content.style = {"width": "inherit"}

        ToolBar = TeleportElement(MaterialContent(elementType="Toolbar"))
        ToolBar.content.attrs["variant"] = kwargs.get("variant", "regular")

        Typography = TeleportElement(MaterialContent(elementType="Typography"))
        Typography.content.attrs["variant"] = "h6"
        Typography.content.style = {"flex": 1, "textAlign": "center"}
        TypographyText = TeleportStatic(content=kwargs.get("title", ""))
        Typography.addContent(TypographyText)

        if kwargs.get("state", None) is not None:
            states = {0: "arrow_forward_ios", 1: "arrow_back_ios"}
            for k, v in states.items():
                IconButton = TeleportElement(MaterialContent(elementType="IconButton"))
                IconButton.content.attrs["edge"] = "start"
                IconButton.content.attrs["color"] = "inherit"
                IconButton.content.attrs["aria-label"] = "menu"
                IconButton.content.style = {
                    "border": "2px solid #F2F1F1",
                    "width": "50px",
                    "height": "50px",
                    "borderRadius": "50%",
                }

                IconButton.content.events["click"] = [
                    {
                        "type": "stateChange",
                        "modifies": kwargs.get("state", None),
                        "newState": (k == 0),
                    },
                ]
                if kwargs.get("styles", None) is not None:
                    styles = kwargs.get("styles", None)
                    IconButton.content.events["click"].append(
                        {
                            "type": "stateChange",
                            "modifies": styles[0],
                            "newState": styles[1][k],
                            "callbacks": kwargs.get("callbacks", []),
                        }
                    )

                Icon = TeleportElement(MaterialContent(elementType="Icon"))
                IconText = TeleportStatic(content=v)
                Icon.addContent(IconText)
                IconButton.addContent(Icon)
                IconButtonCondition = TeleportConditional(
                    TeleportContent(elementType="container")
                )
                IconButtonCondition.reference = {
                    "type": "dynamic",
                    "content": {
                        "referenceType": "state",
                        "id": kwargs.get("state", None),
                    },
                }
                IconButtonCondition.value = k
                IconButtonCondition.addContent(IconButton)
                ToolBar.addContent(IconButtonCondition)
        else:
            IconButton = TeleportElement(MaterialContent(elementType="IconButton"))
            IconButton.content.attrs["edge"] = "start"
            IconButton.content.attrs["color"] = "inherit"
            IconButton.content.attrs["aria-label"] = "menu"
            IconButton.content.style = {
                "border": "2px solid #F2F1F1",
                "width": "50px",
                "height": "50px",
                "borderRadius": "50%",
            }

            if kwargs.get("onClickMenu", None) is not None:
                IconButton.content.events["click"] = kwargs.get("onClickMenu", [])
            Icon = TeleportElement(MaterialContent(elementType="Icon"))
            IconText = TeleportStatic(content="arrow_forward_ios")
            Icon.addContent(IconText)
            IconButton.addContent(Icon)
            ToolBar.addContent(IconButton)

        ToolBar.addContent(Typography)
        AppBar.addContent(ToolBar)
        return AppBar

    def Drawer(*args, **kwargs):
        """This function creates a Material Element of type drawer.
        Kwargs:
        variant (string): variant type of Drawer ['permanent' | 'persistent' | 'temporary'].
        anchor (string) : Side from which the drawer will appear.  'left' | 'top' | 'right' | 'bottom'
        open (bool/string): If true, the drawer is open. If string, the drawer reacts to the state variable
        onClickClose(dict) : Callback fired when the drawer requests to be closed.

        Returns:
          TeleportElement

        Raises:
           AttributeError

        >>> Drawer(state="DrawerIsVisible", position="static", "variant":"dense" )

        """

        Drawer = TeleportElement(MaterialContent(elementType="Drawer"))
        Drawer.content.attrs["variant"] = kwargs.get("variant", "persistent")
        Drawer.content.attrs["anchor"] = kwargs.get("anchor", "left")
        state = kwargs.get("state", True)
        if isinstance(state, str):
            Drawer.content.attrs["open"] = {
                "type": "dynamic",
                "content": {"referenceType": "state", "id": state},
            }
        elif isinstance(state, bool):
            Drawer.content.attrs["open"] = state

        List = TeleportElement(MaterialContent(elementType="List"))
        if "onClickClose" in kwargs:
            ListItem = TeleportElement(MaterialContent(elementType="ListItem"))
            ListItem.content.attrs["button"] = True
            ListItem.content.events["click"] = kwargs.get("onClickClose", [])
            ListItemIcon = TeleportElement(MaterialContent(elementType="ListItemIcon"))
            InboxIcon = TeleportElement(MaterialContent(elementType="Icon"))
            InboxIconText = TeleportStatic(
                content="chevron_" + kwargs.get("anchor", "left")
            )
            InboxIcon.addContent(InboxIconText)
            ListItemText = TeleportElement(MaterialContent(elementType="ListItemText"))
            ListItemText.content.attrs["primary"] = ""
            Divider = TeleportElement(MaterialContent(elementType="Divider"))
            ListItemIcon.addContent(InboxIcon)
            ListItem.addContent(ListItemIcon)
            # ListItem.addContent(ListItemText)
            List.addContent(ListItem)
            Drawer.addContent(List)
            Drawer.addContent(Divider)

        return Drawer

    def ExpansionPanel(*args, **kwargs):
        """This function creates a Material Element of type ExpansionPanel.
        Kwargs:


        Returns:
          TeleportElement

        Raises:
           AttributeError

        >>> ExpansionPanel(state="DrawerIsVisible", position="static", "variant":"dense" )

        """
        ExpansionPanel = TeleportElement(MaterialContent(elementType="Accordion"))
        if kwargs.get("disabled", False) is True:
            ExpansionPanel.content.attrs["disabled"] = True
        if kwargs.get("expanded", None) is not None:
            ExpansionPanel.content.attrs["expanded"] = kwargs.get("expanded", False)
        if kwargs.get("defaultExpanded", None) is not None:
            ExpansionPanel.content.attrs["defaultExpanded"] = kwargs.get(
                "defaultExpanded", True
            )
        ExpansionPanelSummary = TeleportElement(
            MaterialContent(elementType="AccordionSummary")
        )
        ExpansionPanelSummary.content.attrs["expandIcon"] = "expand_more"
        ExpansionPanelSummary.content.attrs["aria-controls"] = kwargs.get(
            "aria-controls", "panel1a-content"
        )
        ExpansionPanelSummary.content.attrs["id"] = kwargs.get(
            "id", kwargs.get("title", "")
        )
        ExpansionPanelSummary.content.style = {
            "backgroundColor": "#dbeaf0",
            "display": "flex",
            "padding": "5px",
        }

        ExpansionPanelDetails = TeleportElement(
            MaterialContent(elementType="AccordionDetails")
        )
        ExpansionPanelDetails.content.style = {"padding": "0px"}
        if kwargs.get("content", None) is not None:
            for content in kwargs.get("content", []):
                ExpansionPanelDetails.addContent(content)
        if kwargs.get("title", None) is not None:
            Typography = TeleportElement(MaterialContent(elementType="Typography"))
            TypographyText = TeleportStatic(content=kwargs.get("title", ""))
            Typography.addContent(TypographyText)
            ExpansionPanelSummary.addContent(Typography)

        ExpansionPanel.addContent(ExpansionPanelSummary)
        ExpansionPanel.addContent(ExpansionPanelDetails)
        return ExpansionPanel

    def GridItem(*args, **kwargs):
        Grid = TeleportElement(MaterialContent(elementType="Grid"))
        Grid.content.attrs["item"] = True
        # Grid.content.attrs["alignContent"] = "center"
        if "content" in kwargs:
            Grid.addContent(kwargs.get("content"))
        if "style" in kwargs:
            Grid.content.style = kwargs.get("style")
        return Grid

    def Button(*args, **kwargs):
        """This function creates a Material Element of type button.
        Kwargs:
        title (string): title of the button
        size (string) :
        variant (string):

        Returns:
          TeleportElement

        Raises:
           AttributeError

        >>>

        """

        Button = TeleportElement(MaterialContent(elementType="Button"))
        Button.content.attrs["size"] = kwargs.get("size", "medium")
        Button.content.attrs["variant"] = kwargs.get("variant", "contained")
        Button.content.attrs["color"] = kwargs.get("color", "primary")
        Button.content.attrs["disableRipple"] = kwargs.get("disableRipple", False)
        if "className" in kwargs:
            Button.content.attrs["className"] = kwargs.get("className")
        if "style" in kwargs:
            Button.content.style = kwargs.get("style")

        if kwargs.get("onClickButton", None) is not None:
            Button.content.events["click"] = kwargs.get("onClickButton")
        Typography = TeleportElement(MaterialContent(elementType="Typography"))

        Typography.addContent(TeleportStatic(content=kwargs.get("title", "")))
        Button.addContent(Typography)
        return Button

    """def ThemeProvider(theme_var):      
    ThemeProvider = TeleportElement(MaterialContent(elementType="ThemeProvider"))
    ThemeProvider.content.attrs["theme"] = {
      "type": "dynamic",
      "content": {
        "referenceType": "local",
        "id": theme_var
      }
    }
    return ThemeProvider"""

    def DefaultTheme(*args, **kwargs):
        primary_color = kwargs.get("primary_color", "#3f51b5")
        secondary_color = kwargs.get("secondary_color", "#f50057")
        primary_bg = kwargs.get("primary_bg", "#9e9e9e")
        secondary_bg = kwargs.get("secondary_bg", "rgba(255, 255, 255, 0.87)")
        default_button = kwargs.get("default_button", "#rgba(0, 0, 0, 0.87)")
        primary_button = kwargs.get("primary_button", "rgba(255, 255, 255, 0.87)")
        secondary_button = kwargs.get("secondary_button", "rgba(255, 255, 255, 0.87)")
        default_button_bg = kwargs.get("default_button_bg", "#d5d5d5")
        primary_button_bg = kwargs.get("primary_button_bg", "#3f51b5")
        secondary_button_bg = kwargs.get("secondary_button_bg", "#f50057")
        drawer_position = kwargs.get("drawer_position", "fixed")
        
        return {
            
            "shadows": ["none" for i in range(25)],
            "palette": {
                "primary": {
                    "main": primary_color,
                },
                "secondary": {
                    "main": secondary_color,
                },
            },
            "components": {
                "MuiPaper": {
                    "styleOverrides": {
                        "root": {"color": "rgba(0, 0, 0, 0.54)"},
                    }
                },
                "MuiGrid": {
                    "styleOverrides": {
                        "item": {
                            "display": "flex",
                            "flexDirection": "column",
                            "padding": "4px",
                        }
                    }
                },
                "MuiDrawer": {
                    "styleOverrides": {
                        "paper": {
                            "width": "350px",
                            "marginTop": "56px",
                            "height": "calc(100% - 56px)",
                            "position": drawer_position,
                        }
                    }
                },
                "MuiAppBar": {
                    "styleOverrides": {
                        "colorPrimary": {"backgroundColor": primary_bg},
                        "colorSecondary": {"backgroundColor": secondary_bg},
                    }
                },
                "MuiButton": {
                    "styleOverrides": {

                        "root": {
                            "textTransform": "none",
                        },
                        "contained": {
                            "color": default_button,
                            "backgroundColor": default_button_bg,
                        },
                        "containedPrimary": {
                            "color": primary_button,
                            "backgroundColor": primary_button_bg,
                        },
                        "containedSecondary": {
                            "color": secondary_button,
                            "backgroundColor": secondary_button_bg,
                        },
                    }
                },
                "MuiGrid": {
                    "styleOverrides": {
                        "item": {
                            "padding": "4px 25px",
                            "margin": "0",
                            "display": "flex",
                            "boxSizing": "border-box",
                            "flexDirection": "column",
                        },
                        "container": {"width": "none"},
                    }
                },
                "MuiAccordionSummary": {
                    "styleOverrides": {
                        "expandIconWrapper": {"fontFamily": "Material Icons"},
                    },
                },
                "MuiExpansionPanel": {
                    "styleOverrides": {
                        "root": {
                            "&$expanded": {"margin": "0px"},
                        },
                    }
                },
                "MuiFormHelperText": {
                    "styleOverrides": {
                        "root": {
                            "WebkitTouchCallout": "none",
                            "WebkitUserSelect": "none",
                            "KhtmlUserSelect": "none",
                            "MozUserSelect": "none",
                            "msUserSelect": "none",
                            "userSelect": "none",
                        },
                    }
                },
                "MuiFormLabel": {
                    "styleOverrides": {
                        "root": {
                            "WebkitTouchCallout": "none",
                            "WebkitUserSelect": "none",
                            "KhtmlUserSelect": "none",
                            "MozUserSelect": "none",
                            "msUserSelect": "none",
                            "userSelect": "none",
                        },
                    }
                },
                "MuiTypography": {
                    "styleOverrides": {
                        "root": {
                            "WebkitTouchCallout": "none",
                            "WebkitUserSelect": "none",
                            "KhtmlUserSelect": "none",
                            "MozUserSelect": "none",
                            "msUserSelect": "none",
                            "userSelect": "none",
                        },
                        "body1": {"fontSize": "0.9rem"},
                    }
                },
                "MuiInputBase": {
                    "styleOverrides": {
                        "root": {"fontSize": "0.9rem"}
                    }
                },
                "MuiIconButton": {
                    "styleOverrides": {
                        "root": {"padding": "10px"},
                        "colorPrimary": {
                            "color": primary_button,
                            "backgroundColor": primary_button_bg,
                        },
                        "colorSecondary": {
                            "color": secondary_button,
                            "backgroundColor": secondary_button_bg,
                        },
                        "label": {
                            "fontFamily": "Material Icons",
                        },
                    }
                },
                "MuiOutlinedInput": {
                    "styleOverrides": {
                        "input": {"padding": "10px 10px"},
                        "inputMarginDense": {
                            "paddingTop": "0px",
                            "paddingBottom": "0px",
                        },
                    }
                },
                "MuiTab": {
                    "styleOverrides": {
                        "root": {
                            "minWidth": "90px",
                            "padding": "2px",
                            "textTransform": "none",
                            "@media (minWidth:600px)": {
                                "minWidth": "90px",
                                "padding": "2px",
                            },
                        }
                    }
                },
            },
        }

    def ThemeProvider(Component, theme):
        # Component.addPropVariable("createMuiTheme", {
        #    "type":"func",
        #    "defaultValue": "() => {return Material.createTheme(" + json.dumps(theme) + ");}"
        # })
        ThemeProvider = TeleportElement(MaterialContent(elementType="ThemeProvider"))
        # ThemeProvider.content.attrs["theme"] = {
        #  "type": "dynamic",
        #  "content": {
        #    "referenceType": "prop",
        #    "id": 'createMuiTheme()'
        #  }
        # }
        ThemeProvider.content.attrs["theme"] = (
            "$Material.createTheme(" + json.dumps(theme) + ")"
        )
        return ThemeProvider


class MaterialComponents:
    def FormatCustomNumber(tp, *args, **kwargs):
        paper = TeleportElement(MaterialContent(elementType="Paper"))
        paper.content.attrs["elevation"] = kwargs.get("elevation", 0)
        paper.content.style = {"width": "100%"}
        FComponent = TeleportComponent("FormatCustomNumber", paper)
        FComponent.addPropVariable(
            "formatter",
            {
                "type": "func",
                "defaultValue": """(props)=>{
        return React.forwardRef((value, ref) => {
            let nprops = {
                'style':props.style,
                'className':value.className,
                'onValueChange': (v)=> {
                    value.onChange( {'target':{'value':Number.isInteger(props.decimalscale) ? parseInt(v.value) : parseFloat(v.value)} } );
                },
                'onBlur' : (v)=> {
                    props.onBlur( {'target':{'value':Number.isInteger(props.decimalscale) ? parseInt(v.target.value) : parseFloat(v.target.value) } } );
                },
                'value' : Number.isInteger(props.decimalscale) ? parseInt(value.value) : parseFloat(value.value),
                'isAllowed': (v)=> {
                    if (props.range && props.range.length == 2)
                        return v.value >= props.range[0] && v.value <= props.range[1];
                    return true;
                },
                'decimalScale':Number.isInteger(props.decimalscale) ? props.decimalscale : undefined,
                'suffix':"",
                'getInputRef':ref,
            };
            return React.createElement(Format,nprops);
        });
    }""",
            },
        )
        FComponent.addPropVariable(
            "property",
            {
                "type": "func",
                "defaultValue": """(props)=>{
        return {
            'inputComponent': props.formatter(props), 
            'endAdornment': props.suffix
        };
    }""",
            },
        )
        FComponent.addPropVariable(
            "shrink", {"type": "object", "defaultValue": {"shrink": True}}
        )
        FComponent.addPropVariable("range", {"type": "array", "defaultValue": []})
        FComponent.addPropVariable(
            "decimalscale", {"type": "number", "defaultValue": "none"}
        )

        TextField = TeleportElement(MaterialContent(elementType="TextField"))
        TextField.content.attrs["onBlur"] = {
            "type": "dynamic",
            "content": {"referenceType": "prop", "id": "onBlur"},
        }
        TextField.content.attrs["InputProps"] = {
            "type": "dynamic",
            "content": {"referenceType": "prop", "id": "property(this.props)"},
        }
        TextField.content.attrs["className"] = {
            "type": "dynamic",
            "content": {"referenceType": "prop", "id": "className"},
        }
        TextField.content.attrs["InputLabelProps"] = {
            "type": "dynamic",
            "content": {"referenceType": "prop", "id": "shrink"},
        }
        TextField.content.attrs["variant"] = {
            "type": "dynamic",
            "content": {"referenceType": "prop", "id": "variant"},
        }
        TextField.content.attrs["label"] = {
            "type": "dynamic",
            "content": {"referenceType": "prop", "id": "label"},
        }
        TextField.content.attrs["fullWidth"] = {
            "type": "dynamic",
            "content": {"referenceType": "prop", "id": "fullWidth"},
        }
        TextField.content.attrs["helperText"] = {
            "type": "dynamic",
            "content": {"referenceType": "prop", "id": "helperText"},
        }
        TextField.content.attrs["label"] = {
            "type": "dynamic",
            "content": {"referenceType": "prop", "id": "label"},
        }
        TextField.content.attrs["style"] = {
            "type": "dynamic",
            "content": {"referenceType": "prop", "id": "style"},
        }
        TextField.content.attrs["value"] = {
            "type": "dynamic",
            "content": {"referenceType": "prop", "id": "value"},
        }
        TextField.content.attrs["decimalscale"] = {
            "type": "dynamic",
            "content": {"referenceType": "prop", "id": "decimalscale"},
        }
        TextField.content.attrs["size"] = "small"
        TextField.content.attrs["type"] = "number"
        FComponent.node.addContent(TextField)

        tp.addComponent("FormatCustomNumber", FComponent)

    def IconList(tp, *args, **kwargs):

        Paper = TeleportElement(MaterialContent(elementType="Paper"))
        Paper.content.attrs["elevation"] = kwargs.get("elevation", 0)
        Paper.content.style = {"width": "100%"}
        IComponent = TeleportComponent("IconListMaterial", Paper)
        IComponent.addStateVariable(
            "open_expansion", {"type": "bool", "defaultValue": True}
        )
        IComponent.addStateVariable(
            "class_names", {"type": "object", "defaultValue": {}}
        )
        IComponent.addPropVariable("value", {"type": "string", "defaultValue": ""})
        IComponent.addPropVariable("options", {"type": "array", "defaultValue": []})
        IComponent.addPropVariable(
            "onChange", {"type": "func", "defaultValue": "(e)=>{}"}
        )
        IComponent.addPropVariable(
            "getName",
            {
                "type": "func",
                "defaultValue": "(l,v)=>{let j=l.find((e)=>{return e.key==v}); if (j){ return j.name;} else { return '';} }",
            },
        )
        IComponent.addPropVariable(
            "getPath",
            {
                "type": "func",
                "defaultValue": "(l,v)=>{let j=l.find((e)=>{return e.key==v}); if (j){ return j.icon;} else { return '';} }",
            },
        )
        bvalues = {True: "primary", False: "secondary"}
        ExpansionPanel = TeleportElement(MaterialContent(elementType="Accordion"))
        ExpansionPanel.content.attrs["expanded"] = {
            "type": "dynamic",
            "content": {"referenceType": "state", "id": "open_expansion"},
        }
        ExpansionPanel.content.attrs["defaultExpanded"] = True
        ExpansionPanelSummary = TeleportElement(
            MaterialContent(elementType="AccordionSummary")
        )
        ExpansionPanelSummary.content.attrs["expandIcon"] = "expand_more"
        ExpansionPanelSummary.content.attrs["aria-controls"] = kwargs.get(
            "aria-controls", "panel1a-content"
        )

        SvgIcon = TeleportElement(MaterialContent(elementType="SvgIcon"))

        Path = TeleportElement(TeleportContent(elementType="path"))
        Path.content.attrs["d"] = "$local.icon"
        Path.content.attrs["fill"] = "transparent"
        Path.content.attrs["stroke"] = "currentColor"
        SvgIcon.content.style = {"fontSize": "25px"}
        SvgIcon.addContent(Path)
        ConditionalIcon = TeleportConditional(SvgIcon)
        ConditionalIcon.reference = {
            "type": "dynamic",
            "content": {"referenceType": "prop", "id": "value"},
        }
        ConditionalIcon.value = "$local.key"
        RepeatIcons = TeleportRepeat(ConditionalIcon)
        RepeatIcons.iteratorName = "local"
        RepeatIcons.dataSource = {
            "type": "dynamic",
            "content": {"referenceType": "prop", "id": "options"},
        }
        ExpansionPanelSummary.addContent(RepeatIcons)

        Typography = TeleportElement(MaterialContent(elementType="Typography"))
        Typography.content.attrs["variant"] = "body1"
        TypographyText = TeleportDynamic(
            content={
                "referenceType": "prop",
                "id": "getName(self.props.options, self.props.value)",
            }
        )
        Typography.addContent(TypographyText)
        Typography.addContent(TeleportStatic(content="  "))
        ExpansionPanelSummary.addContent(Typography)

        ExpansionPanelDetails = TeleportElement(
            MaterialContent(elementType="AccordionDetails")
        )

        Grid = TeleportElement(MaterialContent(elementType="Grid"))
        Grid.content.attrs["container"] = True
        Grid.content.attrs["direction"] = kwargs.get("direction", "row")
        Grid.content.attrs["justify"] = kwargs.get("justify", "space-evenly")
        Grid.content.attrs["alignItems"] = kwargs.get("alignItems", "flex-start")

        GridItem = TeleportElement(MaterialContent(elementType="Grid"))
        GridItem.content.style = {"padding": "1px 12px"}
        GridItem.content.attrs["item"] = True
        IconButton = TeleportElement(MaterialContent(elementType="IconButton"))
        IconButton.content.attrs["edge"] = "start"
        IconButton.content.attrs["color"] = {
            "type": "dynamic",
            "content": {
                "referenceType": "local",
                "id": "(local.key == this.props.value)?'primary':'secondary'",
            },
        }

        IconButton.content.style = {
            "border": "2px solid #F2F1F1",
            "width": "50px",
            "height": "50px",
            "borderRadius": "50%",
            "fontSize": "25px",
        }
        IconButton.content.events["click"] = [
            # {
            #  "type": "stateChange",
            #  "modifies": "open_expansion",
            #  "newState": False
            # },
            {
                "type": "propCall2",
                "calls": "onChange",
                "args": ["{'target':{'value':local.key}}"],
            }
        ]
        SvgIcon2 = TeleportElement(MaterialContent(elementType="SvgIcon"))
        Path2 = TeleportElement(TeleportContent(elementType="path"))
        Path2.content.attrs["d"] = "$local.icon"
        Path2.content.attrs["fill"] = "transparent"
        Path2.content.attrs["stroke"] = "currentColor"
        SvgIcon2.addContent(Path)
        IconButton.addContent(SvgIcon2)
        GridItem.addContent(IconButton)
        FormHelperText = TeleportElement(MaterialContent(elementType="FormHelperText"))
        FormHelperText.content.style = {
            "margin": "0px -12px",
            "maxWidth": "80px",
            "minWidth": "80px",
            "overflow": "hidden",
        }
        FormHelperText.addContent(
            TeleportDynamic(content={"referenceType": "local", "id": "local.name"})
        )
        GridItem.addContent(FormHelperText)
        RepeatButtons = TeleportRepeat(GridItem)
        RepeatButtons.iteratorName = "local"
        RepeatButtons.dataSource = {
            "type": "dynamic",
            "content": {"referenceType": "prop", "id": "options"},
        }
        Grid.addContent(RepeatButtons)

        ExpansionPanelDetails.addContent(Grid)
        ExpansionPanel.addContent(ExpansionPanelSummary)
        ExpansionPanel.addContent(ExpansionPanelDetails)
        ExpansionPanel.content.events["change"] = [
            {"type": "stateChange", "modifies": "open_expansion", "newState": "$toggle"}
        ]
        Paper.addContent(ExpansionPanel)

        tp.addComponent("IconListMaterial", IComponent)

    def ButtonList(tp, *args, **kwargs):

        bvalues = {True: "primary", False: "secondary"}
        ExpansionPanel = TeleportElement(MaterialContent(elementType="Accordion"))
        ExpansionPanel.content.attrs["expanded"] = {
            "type": "dynamic",
            "content": {"referenceType": "state", "id": "open_expansion"},
        }
        ExpansionPanel.content.attrs["defaultExpanded"] = True
        ExpansionPanelSummary = TeleportElement(
            MaterialContent(elementType="AccordionSummary")
        )
        ExpansionPanelSummary.content.attrs["expandIcon"] = "expand_more"
        ExpansionPanelSummary.content.attrs["aria-controls"] = kwargs.get(
            "aria-controls", "panel1a-content"
        )

        Typography = TeleportElement(MaterialContent(elementType="Typography"))
        Typography.content.attrs["variant"] = "body1"
        TypographyText = TeleportDynamic(
            content={
                "referenceType": "prop",
                "id": "getName(self.props.options, self.props.value)",
            }
        )
        Typography.addContent(TypographyText)
        Typography.addContent(TeleportStatic(content="  "))
        ExpansionPanelSummary.addContent(Typography)

        ExpansionPanelDetails = TeleportElement(
            MaterialContent(elementType="AccordionDetails")
        )

        Grid = TeleportElement(MaterialContent(elementType="Grid"))
        Grid.content.attrs["container"] = True
        Grid.content.attrs["direction"] = kwargs.get("direction", "row")
        Grid.content.attrs["justify"] = kwargs.get("justify", "space-evenly")
        Grid.content.attrs["alignItems"] = kwargs.get("alignItems", "flex-start")

        GridItem = TeleportElement(MaterialContent(elementType="Grid"))
        GridItem.content.style = {"padding": "1px 12px"}
        GridItem.content.attrs["item"] = True
        FabButton2 = TeleportElement(MaterialContent(elementType="Fab"))
        FabButton2.addContent(
            TeleportDynamic(content={"referenceType": "local", "id": "local.key"})
        )
        FabButton2.content.attrs["size"] = "small"
        FabButton2.content.attrs["color"] = {
            "type": "dynamic",
            "content": {
                "referenceType": "local",
                "id": "(local.key == this.props.value)?'primary':'secondary'",
            },
        }
        FabButton2.content.attrs["variant"] = "extended"
        FabButton2.content.events["click"] = [
            {
                "type": "stateChange",
                "modifies": "open_expansion",
                "newState": "$self.props.always_open",
            },
            {
                "type": "propCall2",
                "calls": "onChange",
                "args": ["{'target':{'value':local.key}}"],
            },
        ]
        GridItem.addContent(FabButton2)
        RepeatButtons = TeleportRepeat(GridItem)
        RepeatButtons.iteratorName = "local"
        RepeatButtons.dataSource = {
            "type": "dynamic",
            "content": {"referenceType": "prop", "id": "options"},
        }
        Grid.addContent(RepeatButtons)

        ExpansionPanelDetails.addContent(Grid)
        ExpansionPanelSummaryCondition = TeleportConditional(
            TeleportContent(elementType="container")
        )
        ExpansionPanelSummaryCondition.reference = {
            "type": "dynamic",
            "content": {"referenceType": "prop", "id": "hide_header"},
        }
        ExpansionPanelSummaryCondition.value = False
        ExpansionPanelSummaryCondition.addContent(ExpansionPanelSummary)
        ExpansionPanel.addContent(ExpansionPanelSummaryCondition)
        ExpansionPanel.addContent(ExpansionPanelDetails)
        ExpansionPanel.content.events["change"] = [
            {"type": "stateChange", "modifies": "open_expansion", "newState": "$toggle"}
        ]

        Paper = TeleportElement(MaterialContent(elementType="Paper"))
        Paper.addContent(ExpansionPanel)
        Paper.content.style = {"width": "100%"}
        Paper.content.attrs["elevation"] = kwargs.get("elevation", 0)

        BLMComponent = TeleportComponent("ButtonListMaterial", Paper)

        BLMComponent.addPropVariable(
            "always_open", {"type": "bool", "defaultValue": False}
        )
        BLMComponent.addPropVariable(
            "hide_header", {"type": "bool", "defaultValue": False}
        )
        BLMComponent.addPropVariable("options", {"type": "array", "defaultValue": []})
        BLMComponent.addPropVariable(
            "onChange", {"type": "func", "defaultValue": "(e)=>{}"}
        )
        BLMComponent.addPropVariable(
            "getName",
            {
                "type": "func",
                "defaultValue": "(l,v)=>{let j=l.find((e)=>{return e.key==v}); if (j){ return j.name;} else { return '';} }",
            },
        )
        BLMComponent.addPropVariable("value", {"type": "string", "defaultValue": ""})

        BLMComponent.addStateVariable(
            "open_expansion", {"type": "bool", "defaultValue": True}
        )
        BLMComponent.addStateVariable(
            "class_names", {"type": "object", "defaultValue": {}}
        )

        tp.addComponent("ButtonListMaterial", BLMComponent)
        return "ButtonListMaterial"

    def IntSwitch(tp, *args, **kwargs):
        Paper = TeleportElement(MaterialContent(elementType="Paper"))
        Paper.content.style = {"width": "100%"}
        Paper.content.attrs["elevation"] = kwargs.get("elevation", 0)
        IComponent = TeleportComponent("IntSwitch", Paper)

        FormControl = TeleportElement(MaterialContent(elementType="FormControl"))
        variant = kwargs.get("variant", "outlined")
        FormControl.content.attrs["variant"] = variant
        FormControl.content.style = {
            "border": "1px solid rgba(0, 0, 0, 0.23)",
            "borderRadius": "4px",
            "flexDirection": "row",
            "width": "100%",
        }

        IComponent.addPropVariable(
            "default_value", {"type": "number", "defaultValue": "1"}
        )
        IComponent.addStateVariable(
            "checked",
            {
                "type": "boolean",
                "defaultValue": {
                    "type": "dynamic",
                    "content": {
                        "referenceType": "prop",
                        "id": "default_value==self.props.ids[1]",
                    },
                },
            },
        )
        IComponent.addStateVariable(
            "onColor",
            {
                "type": "string",
                "defaultValue": {
                    "type": "dynamic",
                    "content": {
                        "referenceType": "prop",
                        "id": "default_value==self.props.ids[0]? 'primary' : 'secondary'",
                    },
                },
            },
        )
        IComponent.addStateVariable(
            "offColor",
            {
                "type": "string",
                "defaultValue": {
                    "type": "dynamic",
                    "content": {
                        "referenceType": "prop",
                        "id": "default_value!=self.props.ids[0]? 'primary' : 'secondary'",
                    },
                },
            },
        )
        IComponent.addPropVariable("ids", {"type": "array", "defaultValue": [0, 1]})
        IComponent.addPropVariable(
            "options", {"type": "array", "defaultValue": ["Off", "On"]}
        )
        IComponent.addPropVariable("label", {"type": "string", "defaultValue": ""})
        IComponent.addPropVariable(
            "descripption", {"type": "string", "defaultValue": ""}
        )
        IComponent.addPropVariable(
            "onChange", {"type": "func", "defaultValue": "(e)=>{}"}
        )

        Switch = TeleportElement(MaterialContent(elementType="Switch"))
        Switch.content.attrs["htmlFor"] = "component-filled"
        Switch.content.attrs["color"] = "primary"
        InputLabel = TeleportElement(MaterialContent(elementType="InputLabel"))
        InputLabel.content.attrs["htmlFor"] = "component-filled"
        InputLabel.content.attrs["shrink"] = True
        FormHelperTextOn = TeleportElement(MaterialContent(elementType="Typography"))
        FormHelperTextOn.content.attrs["variant"] = "body1"
        FormHelperTextOn.content.style = {"maxWidth": "80px", "lineHeight": "1.2"}
        FormHelperTextOn.content.attrs["color"] = {
            "type": "dynamic",
            "content": {"referenceType": "state", "id": "onColor"},
        }
        FormHelperTextOn.addContent(
            TeleportDynamic(content={"referenceType": "prop", "id": "options[0]"})
        )
        FormHelperTextOff = TeleportElement(MaterialContent(elementType="Typography"))
        FormHelperTextOff.content.attrs["variant"] = "body1"
        FormHelperTextOff.content.style = {"maxWidth": "80px", "lineHeight": "1.2"}
        FormHelperTextOff.content.attrs["color"] = {
            "type": "dynamic",
            "content": {"referenceType": "state", "id": "offColor"},
        }
        FormHelperTextOff.addContent(
            TeleportDynamic(content={"referenceType": "prop", "id": "options[1]"})
        )

        InputLabel.content.style = {"background": "white", "padding": "0px 2px"}
        InputLabelText = TeleportDynamic(
            content={"referenceType": "prop", "id": "label"}
        )

        Switch.content.events["change"] = [
            {
                "type": "stateChange",
                "modifies": "checked",
                "newState": "$e.target.checked",
            },
            {
                "type": "stateChange",
                "modifies": "onColor",
                "newState": "$e.target.checked?'secondary':'primary'",
            },
            {
                "type": "stateChange",
                "modifies": "offColor",
                "newState": "$e.target.checked?'primary':'secondary'",
            },
            {
                "type": "propCall2",
                "calls": "onChange",
                "args": ["{'target':{'value':self.props.ids[e.target.checked?1:0]}}"],
            },
        ]
        Switch.content.attrs["checked"] = {
            "type": "dynamic",
            "content": {"referenceType": "state", "id": "checked"},
        }
        InputLabel.addContent(InputLabelText)
        Grid = TeleportElement(MaterialContent(elementType="Grid"))
        Grid.content.attrs["container"] = True
        Grid.content.style = {"width": "100%"}
        Grid.content.attrs["direction"] = kwargs.get("direction", "row")
        Grid.content.attrs["justify"] = kwargs.get("justify", "space-evenly")
        Grid.content.attrs["alignItems"] = kwargs.get("alignItems", "flex-start")

        Grid.addContent(
            MaterialBuilder.GridItem(
                content=FormHelperTextOn, style={"padding": "5px 5px 5px 0px"}
            )
        )
        Grid.addContent(MaterialBuilder.GridItem(content=Switch))
        Grid.addContent(
            MaterialBuilder.GridItem(
                content=FormHelperTextOff, style={"padding": "5px 5px 5px 0px"}
            )
        )

        FormControl.addContent(InputLabel)
        FormControl.addContent(Grid)
        FormHelperText = TeleportElement(MaterialContent(elementType="FormHelperText"))
        FormHelperText.addContent(
            TeleportDynamic(content={"referenceType": "prop", "id": "description"})
        )
        Paper.addContent(FormControl)
        Paper.addContent(FormHelperText)
        tp.addComponent("IntSwitch", IComponent)

        return FormControl

    def ColorSliders(tp, *args, **kwargs):

        Paper = TeleportElement(MaterialContent(elementType="Paper"))
        Paper.content.attrs["elevation"] = kwargs.get("elevation", 0)
        Paper.content.style = {"width": "100%"}
        CComponent = TeleportComponent("ColorSliders", Paper)

        CComponent.addPropVariable("colors", {"type": "object", "defaultValue": {}})

        eol = "\n"
        updateState = ""
        updateState += "(c,i,a,v)=>{ " + eol
        updateState += "  let change = false;" + eol
        updateState += "  let new_colors = c.props.colors.map((e, ii)=>{" + eol
        updateState += "    if(ii==i){" + eol
        updateState += "      if(e.visible){" + eol
        updateState += "        change = true;" + eol
        updateState += "      }" + eol
        updateState += "      let clone = JSON.parse(JSON.stringify(e));" + eol
        updateState += "      clone[a]=v;" + eol
        updateState += "      if(clone.visible){" + eol
        updateState += "        change = true;" + eol
        updateState += "      }" + eol
        updateState += "      return clone;" + eol
        updateState += "    }" + eol
        updateState += "    return e;" + eol
        updateState += "  })" + eol
        updateState += "  c.setState({'colors' : new_colors});" + eol
        updateState += "  if (c.timeout){" + eol
        updateState += "    clearTimeout(c.timeout)" + eol
        updateState += "  }" + eol
        updateState += "  c.timeout = setTimeout(()=>{ " + eol
        updateState += "    if(change){" + eol
        updateState += "      c.props.onChange( {'target':{'value':new_colors} } ); " + eol
        updateState += "    } " + eol
        updateState += "  }, 50);" + eol
        
        updateState += "}" + eol
        CComponent.addPropVariable(
            "updateState", {"type": "func", "defaultValue": updateState}
        )
        CComponent.addPropVariable(
            "colorlist",
            {
                "type": "array",
                "defaultValue": [
                    "#a6cee3",
                    "#1f78b4",
                    "#b2df8a",
                    "#33a02c",
                    "#fb9a99",
                    "#e31a1c",
                ],
            },
        )
        CComponent.addPropVariable(
            "nextColor",
            {
                "type": "func",
                "defaultValue": "(self, c)=>{ var colors = self.props.colorlist; var ind = colors.indexOf(c); return colors[((ind+1)>=colors.length)?0:ind+1] }",
            },
        )
        CComponent.addPropVariable(
            "onChange", {"type": "func", "defaultValue": "(e)=>{}"}
        )

        Grid = TeleportElement(MaterialContent(elementType="Grid"))
        Grid.content.attrs["container"] = True
        Grid.content.attrs["direction"] = kwargs.get("direction", "column")
        Grid.content.attrs["justify"] = kwargs.get("justify", "space-evenly")

        GridItem = TeleportElement(MaterialContent(elementType="Grid"))
        GridItem.content.attrs["container"] = True
        GridItem.content.attrs["direction"] = kwargs.get("direction", "row")
        GridItem.content.attrs["justify"] = kwargs.get("justify", "space-evenly")

        IconButton = TeleportElement(MaterialContent(elementType="IconButton"))
        IconButton.content.attrs["edge"] = "start"
        IconButton.content.attrs["size"] = "small"
        IconButton.content.style = {"font-size": "25px"}

        IconButton.content.events["click"] = [
            {
                "type": "propCall2",
                "calls": "updateState",
                "args": [
                    "self",
                    "index",
                    "'visible'",
                    "!self.props.colors[index].visible",
                ],
            }
        ]
        Icon = TeleportElement(MaterialContent(elementType="Icon"))
        Icon.addContent(
            TeleportDynamic(
                content={
                    "referenceType": "local",
                    "id": "local.visible?'visibility':'visibility_off'",
                }
            )
        )

        IconButton.addContent(Icon)

        GridItem0 = TeleportElement(MaterialContent(elementType="Grid"))
        GridItem0.content.style = {"padding": "5px 5px 0px 5px"}
        GridItem0.content.attrs["item"] = True
        GridItem0.addContent(IconButton)

        Slider = TeleportElement(MaterialContent(elementType="Slider"))
        Slider.content.attrs["value"] = {
            "type": "dynamic",
            "content": {"referenceType": "local", "id": "local.center"},
        }

        Slider.content.events["change"] = [
            {
                "type": "propCall2",
                "calls": "updateState",
                "args": ["self", "index", "'center'", "arguments[1]"],
            }
        ]

        GridItem1 = TeleportElement(MaterialContent(elementType="Grid"))
        GridItem1.content.style = {"padding": "5px 5px 0px 5px", "flex": "1"}
        GridItem1.content.attrs["item"] = True
        GridItem1.addContent(Slider)

        IconButton2 = TeleportElement(MaterialContent(elementType="IconButton"))
        IconButton2.content.attrs["edge"] = "start"
        IconButton2.content.attrs["size"] = "small"
        IconButton2.content.events["click"] = [
            {
                "type": "propCall2",
                "calls": "updateState",
                "args": [
                    "self",
                    "index",
                    "'color'",
                    "self.props.nextColor(self, self.props.colors[index].color)",
                ],
            }
        ]
        IconButton2.content.style = {"font-size": "25px"}

        SvgIcon = TeleportElement(MaterialContent(elementType="SvgIcon"))
        Path = TeleportElement(TeleportContent(elementType="path"))
        Path.content.attrs["d"] = "M 22 12 a 10 10 0 10 0 0.1"
        Path.content.attrs["fill"] = {
            "type": "dynamic",
            "content": {"referenceType": "local", "id": "local.color"},
        }
        SvgIcon.addContent(Path)
        IconButton2.addContent(SvgIcon)

        GridItem2 = TeleportElement(MaterialContent(elementType="Grid"))
        GridItem2.content.style = {"padding": "5px 5px 0px 5px"}
        GridItem2.content.attrs["item"] = True
        GridItem2.addContent(IconButton2)

        GridItem.addContent(GridItem0)
        GridItem.addContent(GridItem1)
        GridItem.addContent(GridItem2)

        FormHelperText = TeleportElement(MaterialContent(elementType="FormHelperText"))
        FormHelperText.content.style = {"marginTop": "-12px", "overflow": "hidden"}
        FormHelperText.addContent(
            TeleportDynamic(content={"referenceType": "local", "id": "local.label"})
        )
        GridItem0.addContent(FormHelperText)
        RepeatButtons = TeleportRepeat(GridItem)
        RepeatButtons.iteratorName = "local"
        RepeatButtons.dataSource = {
            "type": "dynamic",
            "content": {"referenceType": "prop", "id": "colors"},
        }
        Grid.addContent(RepeatButtons)

        Paper.addContent(Grid)

        tp.addComponent("ColorSliders", CComponent)
        return "ColorSliders"
