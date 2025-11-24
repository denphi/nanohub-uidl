from ..teleport import TeleportElement, TeleportDynamic, TeleportStatic
from ..material import MaterialContent

def Loader(Component, *args, **kwargs):
    Component.addStateVariable(
        kwargs.get("loader_status", "loader_status"),
        {"type": "string", "defaultValue": ""},
    )
    Component.addStateVariable(
        kwargs.get("loader_open", "loader_open"),
        {"type": "boolean", "defaultValue": kwargs.get("is_open", True)},
    )

    Loader = TeleportElement(MaterialContent(elementType="Dialog"))
    Loader.content.attrs["open"] = {
        "type": "dynamic",
        "content": {
            "referenceType": "state",
            "id": kwargs.get("open", "loader_open"),
        },
    }
    #Loader.content.attrs["disableBackdropClick"] = True
    Loader.content.attrs["disableEscapeKeyDown"] = True
    Loader.content.attrs["fullWidth"] = True
    Loader.content.attrs["maxWidth"] = "xs"
    loadercnt = TeleportElement(MaterialContent(elementType="DialogContent"))
    loadercnt.content.style = {"textAlign": "center", "overflow": "hidden"}

    LinearProgress = TeleportElement(MaterialContent(elementType="LinearProgress"))
    LinearProgress.content.attrs["color"] = "secondary"

    # loadercir = TeleportElement(MaterialContent(elementType="CircularProgress"))
    # loadercir.content.style = {"width": "100px", "height": "100px", "overflow": "none"}

    loadertext = TeleportElement(MaterialContent(elementType="DialogTitle"))
    loadertext.addContent(
        TeleportDynamic(
            content={
                "referenceType": "state",
                "id": kwargs.get("open", "loader_status"),
            }
        )
    )
    loadertext.content.style = {"textAlign": "center"}

    # loadercnt.addContent(loadercir)
    loadercnt.addContent(LinearProgress)
    Loader.addContent(loadercnt)
    Loader.addContent(loadertext)

    return Loader

def Error(Component, *args, **kwargs):
    Component.addStateVariable(
        kwargs.get("error_status", "error_status"),
        {"type": "string", "defaultValue": ""},
    )
    Component.addStateVariable(
        kwargs.get("error_open", "error_open"),
        {"type": "boolean", "defaultValue": False},
    )
    Error = TeleportElement(MaterialContent(elementType="Dialog"))
    Error.content.attrs["open"] = {
        "type": "dynamic",
        "content": {
            "referenceType": "state",
            "id": kwargs.get("error_open", "error_open"),
        },
    }
    Error.content.attrs["fullWidth"] = True
    Error.content.attrs["maxWidth"] = "xs"
    DialogContent = TeleportElement(MaterialContent(elementType="DialogContent"))
    DialogContent.content.style = {"textAlign": "center", "overflow": "hidden"}

    Typography = TeleportElement(MaterialContent(elementType="Typography"))
    Typography.content.attrs["variant"] = "h6"
    TypographyText = TeleportStatic(content=kwargs.get("title", "Error Message"))
    Typography.addContent(TypographyText)

    Icon0 = TeleportElement(MaterialContent(elementType="Icon"))
    Icon0.content.style = {"position": "absolute", "top": "10px", "left": "10px"}
    IconText0 = TeleportStatic(content="error")
    Icon0.addContent(IconText0)

    IconButton = TeleportElement(MaterialContent(elementType="IconButton"))
    IconButton.content.style = {
        "position": "absolute",
        "top": "10px",
        "right": "10px",
    }

    Icon = TeleportElement(MaterialContent(elementType="Icon"))
    IconText = TeleportStatic(content="close")
    Icon.addContent(IconText)
    IconButton.addContent(Icon)
    IconButton.content.events["click"] = [
        {
            "type": "stateChange",
            "modifies": kwargs.get("error_open", "error_open"),
            "newState": False,
        }
    ]

    DialogTitle = TeleportElement(MaterialContent(elementType="DialogTitle"))
    DialogTitle.content.attrs["disableTypography"] = True
    DialogTitle.content.style = {
        "textAlign": "center",
        "backgroundColor": "#d95c5c",
    }
    DialogTitle.addContent(IconButton)
    DialogTitle.addContent(Typography)
    DialogTitle.addContent(Icon0)

    DialogContent.addContent(
        TeleportDynamic(
            content={
                "referenceType": "state",
                "id": kwargs.get("error_status", "error_status"),
            }
        )
    )
    DialogContent.content.style = {"textAlign": "center"}

    Error.addContent(DialogTitle)
    Error.addContent(DialogContent)

    return Error
