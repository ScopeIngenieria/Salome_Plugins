# -*- coding: utf-8 -*-

import salome_pluginsmanager

def geom_group(context):
  import smesh_geom_group
  reload(smesh_geom_group)

def mesh_gmsh(context):
  import smesh_gmsh_mesh
  reload(smesh_gmsh_mesh)
  
def calculix_export(context):
  import smesh_calculix_export
  reload(smesh_calculix_export)
  


salome_pluginsmanager.AddFunction('Psicofil Plugins/Gmsh Plugin',
                                  'Create a mesh whit GMSH',
                                  mesh_gmsh)

salome_pluginsmanager.AddFunction('Psicofil Plugins/Belong to geometry',
                                  'Create mesh groups from geometry references',
                                  geom_group)

salome_pluginsmanager.AddFunction('Psicofil Plugins/Export to CalculiX',
                                  'Export selected mesh and his groups to CalculiX format',
                                  calculix_export)

