# **Panorama displayable plugin for Renpy**

This is a renpy plugin that can display and move around a 360 panoramic image. Move the image around by click-dragging.
Each displayable supports a background and 2 extra layers.
Each displayable can have multiple targets and if player looks at them a callback function wil be called.



Created by Kidney <br>
Github: https://github.com/Kidney-02/Renpy_PanoramaPlugin


## **Installation**

Download the *'PanoramaDisplayable.rpy'* file and add it to you renpy game's game/CDD folder.


## **How to use**

### **Creating a panorama**

To display a panorama, define it as an image.

```
image test_panorama = Panorama(background="360_image.png",
targets = {
    "Target_0": (0.1, 0.6, 0.12, 0.08, True),
    "Target_1": (0.5, 0.2, 0.1, 0.15, False)
    },)
```

Then show it in game like any image

```
show test_panorama
```
You can now view and move the image around, but clicking on screen will still progress dialogue. To stop that I recommend using a screen with modal set *False*.

```
screen test_screen():
    modal True
    image Panorama(background="360_image.png",
        targets = {
            "Target_0": (0.1, 0.6, 0.12, 0.08, True),
            "Target_1": (0.5, 0.2, 0.1, 0.15, False)
            },
        screen="test_screen", callback=callback_function)
```
This creates a screen that will pause the dialogue while it's shown. 
To turn it off add buttons to the screen or add the functionality to the callback function.

You must input a background image, without it the displayable will fail to function.

### **Targets**

Targets allow you to define places of the image the player can interact with by looking at them. Targets can also be used to animate to. Each displayable can have any number of targets that have to be input at creation. You can turn target interaction on and off if you only want them for animation or to enable them during gameplay.

Targets have to be input as a [dictionary](https://www.w3schools.com/python/python_dictionaries.asp) and should be formatted like this:

> { Name : (target_center.x, target_center.y, target_width, target_width, Status)}

- Name - a string used to differentiate a target. Has to be unique.
- Target center x and y  floats are coordinates of target center in UV coordinates.
- Target width and height in floats are width and height of the target.
- Status - boolean declaring wether target can be interacted with.

The targets have to be defined in UV coordinates. This means that target coordinates have to be defined from 0 to 1 regardless of texture resolution with 0,0 coordinate being top-left corner of the image and 1,1 being bottom-left. To calculate the coordinate you can use rect selection in image editing software and dividing the coordinates by image resolution.<br>
This also means that every target is gonna be more wide than it will be tall. Since the panoramic texture is "wrapped" on a sphere it spans two times more horizontaly than vertically 

Targets can be seen in [debug mode](#debug). 

If a player looks at a target the callback function will be called and the hit target name will be passed to it, letting you react to player action.

### **Callback**

On target hit a callback function is called if provided. This function has to be defined in python and must have an dictionary argument. If the fnction is unable to receive an argument the game will crash once it's called from displayable, so give it an argument even if you won't use it.
```
init python:
    def example_function(args:dict):
        pass
```

Pass it to the Panorama displayable like this:

```
image test_panorama = Panorama(background="360_image.png",
    targets = {"Target_0": (0.1, 0.6, 0.12, 0.08, True)},
    callback = example_function)
```
The function has to be passed without brackets.

Once the player looks at the target the function will be called with a dictionary as argument. This dictionary is laid out like this:
```
{       
    "self":         Reference to the Panorama Displayable that ran the function,
    "screen":       Name of the screen that was given to the Displayable,
    "target":       Name of the hit target,
    "direction":    Diretion that the target was hit from. False - Left, True - Right,
    "offset":       the coordinate at which the target was hit
}
```
Get these values inside the function by reading them from the argument like this:
```
def example_function(args:dict):
    displayable         = args["self"]
    screen_name         = args["screen"]
    store.target_hit    = args["target"]
    store.direction     = args["direction"]
    offset              = args["offset"]
```

*Self* reference is important here as it can be used to change behaviour of the displayable. There are four functions that can be called to do this:

> set_taget_status(target, new_status)

Sets active status of any target already assigned to the displayable. Use this to disable targets after interaction or enable new targets.
- target - Name of the target to change active status of.
- new_status - Active status of the target.

> set_callback(callback)

Change the callback function to be called on target hit.
- callback - new callback function.

> anim_to_target(target, total_time)

Animate to a named target. Mouse interaction is disabled during the animation and won't restart until player clicks again.
- target: Name of the target to animate to.
- total_time: Time in seconds, how long the animation will last.

> set_layer_alpha(layer, alpha)

Set Opacity of a layer.
- layer: Index of layer starting 0. Can be either 0 or 1.
- alpha: Opacty value between 0 and 1 as.


Example implementation:
```
screen test_screen():
    modal True
    image Panorama(background="360_image.png",
        layer_1 = "Layer1.png",
        targets = {
            "Target_0": (0.1, 0.6, 0.12, 0.08, True),
            "Target_1": (0.5, 0.2, 0.1, 0.15, False),
            "Target_2": (0.8, 0.8, 0.1, 0.15, False)
            "Target_1": (0.7, 0.3, 0.06, 0.1, False),
            },
        screen="test_screen", callback=testcallback)

default direction = False
default target_hit = ""

# Callback function to hide the screen
init python:
    def testcallback(args:dict):
        
        if args["target"] == "Target_0":
            args["self"].set_taget_status("Target_0", False)
            args["self"].set_taget_status("Target_2", True)
            args["self"].anim_to_target(target="Target_1", total_time=3.)
            return
        elif args["target"] == "Target_2":
            args["self"].set_layer_alpha(0, 1)
            args["self"].set_taget_status("Target_3", True)
            return

        
        screen_name = args["screen"]
        store.direction = args["direction"]
        store.target_hit = args["target"]

        Hide(screen_name, transition=dissolve)
        renpy.restart_interaction()
```
Once the *test_screen* is shown the callback function will be called 3 times. First when the player hits *Target_0*. It will then animate to *Target_1*. Second time when player hits *Target_2*. This will make layer 0 visible. Third once *Target_3* is hit this will store direction and last target hit, hide the screen and restart interaction.

As you can see you can call more than the displayable functions. Check out what else can be called in [Renpy Documentation](https://www.renpy.org/doc/html/screen_python.html).


### **Debug**

Debug modes

### **Layers**

How to use layers

## **Parameters**

- background (str)    : Name of background layer image.
- targets (dict)      : Dictionary of targets format - {Target_Name : Target_Coord.X, Target_Coord.Y, Target_Width, Target_Height}.
- layer_1 (str)       : Name of layer 1 image (include extension).
- layer_2 (str)       : Name of layer 2 image (include extension).
- alpha_1 (float)     : Opacity of layer 1 on startup.
- alpha_2 (float)     : Opacity of layer 2 on startup.
- offset (tuple)      : Coordinate where player is looking at creation of displayable (0 or 1 on X are on the edge of the image, 0.5 on Y is looking at middle of the image).
- callback (function) : Function to call when any active target is hit.
- screen (str)        : Name of a screen to be passed to the callback function. Use to track the parent of the displayable.
- speed (tuple)       : How fast the mouse moves the screen. Separate for X and Y. Default - (0.2, 0.2).
- frame_clamp (float) : The maximum movement a mouse can do per frame ignore if 0.
- zoom (float)        : Zoom in or out to panorama. 1 - default zoom. < 1 zooms in, > 1 zooms out. Negative values invert the image.


## **Notes**

`inline code`

```
Long Code
Add More Code here
```

>   asca
>ascac
>acasca



