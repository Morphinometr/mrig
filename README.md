# Fork Space Switcher for modern Blender
# Space Switcher

This addon is targeted to riggers that want to implement an easier and more user-friendly IK/FK switch for animators.

[example video and blend file](https://gitlab.com/AquaticNightmare/space_switcher/-/wikis/home)

Step by step tutorial:

Before we start I assume you already have a working IK/FK limb that is driven by a custom property. 
This tutorial also assumes that the custom property should be 0 to work in FK and 1 to work in IK.
Once the addon is installed you will see the space switcher panel in the 3D view in the "Item" panel. 
It will only appear when you have an armature selected and you will only be able to interact with it in pose mode.

1. enable the edit mode

    - ![](images/01.png)

2. create a new space switcher

    - ![](images/02.png)

3. edit the created space switcher

    - ![](images/03.png)

4. fill in the basic information:
    - field 1 (name): whatever you want to call your switch
    - field 2 (datapath): copy here the datapath of the driver that controls your IK/FK switch

    - ![](images/04.png)

5. click on the '+' button to create the first bone pair.
    - first of all lets fill in the last two fields with "FK" and "IK"

    - ![](images/05.png)

6. we will now start filling the names of the bones and how the locations/rotations/scale will be copied when switching spaces
    - first field is the FK bone, we will put here the first FK control bone in the chain
    - the second field is the direction in which the bone location/rotation/scale is copied, in this case we choose '<-' (from the IK bone to the FK bone)
    - the third field is the IK bone, we will put here the first bone in the chain of the bones being driven by the IK

    - ![](images/06.png)
    - once this is done, when we disable the edit mode and click on the "FK" button two things will happen:
        - the custom property will be set to 0
        - the location/rotation/scale of the IK bone will be copied over to the FK control bone


7. we now have to fill the rest of the bones like shown below
    - (right now the transformatiosn will be applied in order from top to bottom, so make sure parent bones appear higher in this list than their children)
    - here the IK to FK is configured:
    - ![](images/ik_fk.png)
    - and here the FK to IK:
    - ![](images/fk_ik.png)
    - resulting in:
    - ![](images/07.png) 

8. after we disable the edit mode (step 3) if the datapath and bones are correct we will have everything working
    - ![](images/08.png)
    - clicking on the "FK" button will set the custom property to 0 and the transformations of the IK bones will be copied to the FK bones
    - clicking on the "IK" button will se the custom property to 1 and the transformations of the FK bones will be copied to the IK bones

extra notes:
- If you are using auto keying, a keyframe will be created for the custom property and the bones loc/rot/scale when switching spaces
- inside the space switch editor there is a button to apply a hide driver to the bones inside it. This driver will hide the corresponding bones when the custom property is 0 or 1
