# -*- coding: utf-8 -*-

import salome_pluginsmanager

def filter_group(context):
  import geom_filter_group
  from importlib import reload
  reload(geom_filter_group)

def contact(context):
  import geom_3d_contact
  from importlib import reload
  reload(geom_3d_contact)

def pass_group(context):
  import geom_pass_group
  from importlib import reload
  reload(geom_pass_group)

def line_from_circle(context):
  import geom_line_from_circle
  from importlib import reload
  reload(geom_line_from_circle)


salome_pluginsmanager.AddFunction('Scope Plugins/Create Groups from Filter.',
                                  'Create Groups Based on Multiple Criteria.',
                                  filter_group)
salome_pluginsmanager.AddFunction('Scope Plugins/Detect 3D contacts',
                                  'Automatically Detect 3D contacts of two o more parts.',
                                  contact)
salome_pluginsmanager.AddFunction('Scope Plugins/Pass Geometrical Groups',
                                  'Transfer similar groups from one part to another.',
                                  pass_group)
salome_pluginsmanager.AddFunction('Scope Plugins/Lines from circles',
                                  'Create Edges/Lines between two groups of circles.',
                                  line_from_circle)

