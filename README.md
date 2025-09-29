# Salome_Plugins

Collection of scripts for the Salome platform.

# Install Instructions

On Linux:

Copy the Plugins folder and its contents to the following address:

* /home/USER_NAME/.config/salome

change USER_NAME by your username

On Windows:

Copy the Plugins folder and its contents to the following address:

* C:/Users/USER_NAME/.config/salome

change USER_NAME by your username

## Geom Plugins

Video Demostration: https://www.youtube.com/watch?v=W_JMXui-vkI

### Filter Group

Creating Geometry groups in the GEOM module using features and properties of another group.

![ScreenShot](Previews/geom_filter_group.png)

Original Source: https://github.com/psicofil/Salome_Scripts

Autor: @psicofil (Lucio Gomez)

Video Idea Demostration (Old Video): https://www.youtube.com/watch?v=Nil1zQtyf_8

### 3D Contact

Script to automatically detect contacts of two o more parts.

![ScreenShot](Previews/geom_contact_3d.png)

Original Source: https://github.com/psicofil/Salome_Scripts

Autor: @psicofil (Lucio Gomez)

Video Idea Demostration (Old Video): https://www.youtube.com/watch?v=QTaSs1JFrHw

### Pass similar Group

After an operation in the geometry module the groups are lost and must be done again. 
With this script you can pass the groups (or the majority) after performing an operation to the part.

![ScreenShot](Previews/geom_pass_group.png)

Original Source: https://github.com/psicofil/Salome_Scripts

Autor: @psicofil (Lucio Gomez)


## Mesh Plugins

### Belong to Geometry

Create mesh groups from geometry, even if the link does not exist.

![ScreenShot](Previews/smesh_belong_geom.png)

Original Source: https://github.com/psicofil/Salome_Scripts

Autor: @psicofil (Lucio Gomez)

### Export Salome Mesh to CalcuiX 

A python script that outputs a Salome mesh to Calculix using unical converter for Bernhardi, Aug 2011

#### Important: You need a Unical converter binary

![ScreenShot](Previews/smesh_calculix_export.png)

Original Source: https://github.com/psicofil/SalomeToCalculix
Unical Source: https://github.com/prool/unical1
Psicofil Unical Source: https://github.com/psicofil/SalomeToCalculix

Autor: @psicofil (Lucio Gomez)
Unical Autor: Bernhardi & prool

Video Idea Demostration (Old Video): https://www.youtube.com/watch?v=yxqawAr1H3s

