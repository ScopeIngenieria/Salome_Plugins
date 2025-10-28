# -*- coding: utf-8 -*-

import salome_pluginsmanager

def geom_group(context):
  import smesh_geom_group
  from importlib import reload
  reload(smesh_geom_group)

def Edge_NumberOfElements(context):
  import smesh_view_numberOfElements
  from importlib import reload
  reload(smesh_view_numberOfElements)

def FreeNodes_to_0DNodes(context):
  import smesh_freeNodes_0DNodes
  from importlib import reload
  reload(smesh_freeNodes_0DNodes)

salome_pluginsmanager.AddFunction('Scope Plugins/Creat a Groups from Geometry',
                                  'Create mesh groups from any geometry reference',
                                  geom_group)
salome_pluginsmanager.AddFunction('Scope Plugins/Edge Element Distribution',
                                  'Visualizes in 3D the element distribution along edges of a mesh or selected groups',
                                  Edge_NumberOfElements)
salome_pluginsmanager.AddFunction('Scope Plugins/Convert Free Nodes to 0D elements',
                                  'For the selected mesh, detect free nodes and create 0D elements on them',
                                  FreeNodes_to_0DNodes)

