# -*- coding: utf-8 -*-

import salome_pluginsmanager

def geom_group(context):
  import smesh_geom_group
  from importlib import reload
  reload(smesh_geom_group)


salome_pluginsmanager.AddFunction('Scope Plugins/Creat a Groups from Geometry',
                                  'Create mesh groups from any geometry reference',
                                  geom_group)

