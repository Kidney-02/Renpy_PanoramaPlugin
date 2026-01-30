# **Panorama displayable plugin for Renpy**

This is a renpy plugin that can display and move around a 360 panoramic image. It has targets that can launch python functions when view aligned.
Each displayable supports a background and 2 extra layers.
You can have multiple targets and overlapping them will call a supplied function that cacn be used for interaction.


Created by Kidney <br>
Github: https://github.com/Kidney-02/Renpy_PanoramaPlugin


## **Installation**

Download the *'PanoramaDisplayable.rpy'* file and add it to you renpy game's game/CDD folder.


## **How to use**

### **Creating a panorama**

To display a panorama you have to define it as an image.

```
image test_panorama = Panorama(background="360_image.png",
targets = {
    "Target_0": (0.1, 0.6, 0.12, 0.08, True),
    "Target_1": (0.5, 0.2, 0.1, 0.15, False)
    },)
```

you can then show it in game like an image

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
To turn it off you can add buttons to the screen or add the functionality to the callback function.

You have to input a background image, without it the displayable will fail to function.

### **Targets**

Targets allow you to define places of the image the player can interact with by looking at them. Targets can also be used to animate to. Each displayable can have any number of targets that have to be input at creation. You can turn target interaction on and off if you only want them for animation or to enable them during gameplay.

Targets have to be input as a [dictionary](https://www.w3schools.com/python/python_dictionaries.asp) and should be formatted like this:
```
{ Name : (target_center.x, target_center.y, target_width, target_width, Status)}
```
- Name - a string used to differentiate a target. Has to be unique.
- Target center x and y  floats are coordinates of target center in UV coordinates.
- Target width and height in floats are width and height of the target.
- Status - boolean declaring wether target can be interacted with.

The targets have to be defined in UV coordinates. This means that target coordinates have to be defined from 0 to 1 regardless of texture resolution with 0,0 coordinate being top-left corner of the image and 1,1 being bottom-left. To calculate the coordinate you can use rect selection in image editing software and dividing the coordinates by image resolution.

You can see targets in [debug mode](#debug). 

If a player looks at a target the callback function will be called and the hit target name will be passed to it, letting you react to player action.

### **Callback**



### **Debug**


## **Parameters**




`inline code`

```
Long Code
Add More Code here
```



