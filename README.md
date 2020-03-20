# Nanohub - UIDL

A set of tools to create Javascript apps to consume nanohub WS

## Installation


```bashv
pip install nanohub-uidl
```

## Usage


```python
from nanohub.uidl.teleport import TeleportProject, TeleportElement
from nanohub.uidl.material import MaterialContent
from nanohub.uidl.auth import AUTH

Project = TeleportProject("My App")
Component = Project.root
Component.addStateVariable("myvariable", {"type":"boolean", "defaultValue": True})

STATE_LOADER_STATUS = "loader_status"
STATE_LOADER_OPEN = "loader_open"
STATE_ERROR_STATUS = "error_status"
STATE_ERROR_OPEN = "error_open"

Login, CLogin = Auth.Login(
    Project,
    Component,
    client_id = "MYAPPID",
    client_secret = "MYAPPSECRET",
    url = "https://nanohub.org/api/developer/oauth/token",   
    open_state = STATE_LOGIN_OPEN
)

Login.content.events["onError"]=[
    { "type": "stateChange", "modifies": STATE_ERROR_OPEN, "newState": True},
    { "type": "stateChange", "modifies": STATE_ERROR_STATUS, "newState": '$e'},
]

Login.content.events["onAuth"] = [ 
    { "type": "stateChange", "modifies": STATE_ERROR_OPEN, "newState": False},
    { "type": "stateChange", "modifies": STATE_LOADER_OPEN, "newState": False},
]

Grid = t.TeleportElement(MaterialContent(elementType="Grid"))
Button= MaterialBuilder.Button(
      title = "Reset Setting", 
      variant = "text", 
      onClickButton=[{ "type": "stateChange", "modifies": "parameters","newState": resetSettings}]
)
Grid.addContent(Button)

Component.addNode(Grid)
Project.buildReact("Myapp.html");

```


