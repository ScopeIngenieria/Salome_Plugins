# -*- coding: utf-8 -*-

import salome_pluginsmanager

def filter_group(context):
  import geom_filter_group
  reload(geom_filter_group)

def contact(context):
  import geom_3d_contact
  reload(geom_3d_contact)

def pass_group(context):
  import geom_pass_group
  reload(geom_pass_group)

def internal_group(context):
  import geom_internal_contour
  reload(geom_internal_contour)
    


salome_pluginsmanager.AddFunction('Psicofil Plugins/Create Group from Filter',
                                  'Create a similar group according criteria',
                                  filter_group)
salome_pluginsmanager.AddFunction('Psicofil Plugins/Detect 3D contacts',
                                  'Automatically detect 3D contacts of two o more parts.',
                                  contact)
salome_pluginsmanager.AddFunction('Psicofil Plugins/Pass Geometrical Groups',
                                  'Pass similar groups from a part to another',
                                  pass_group)
salome_pluginsmanager.AddFunction('Psicofil Plugins/Internal Contour',
                                  'Auto-selects the internal contour of a part. You have 2 options, select only the internal surface and set it as a group (for FEM), or create a new part with the control volume (for CFD).',
                                  internal_group)


