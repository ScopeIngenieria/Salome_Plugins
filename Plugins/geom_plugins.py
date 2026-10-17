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

def pad_partition(context):
  import geom_pad_partition
  from importlib import reload
  reload(geom_pad_partition)

def midsurface(context):
  import sys
  from importlib import reload
  sys.modules.pop("midsurface_pairing", None)
  sys.modules.pop("geom_midsurface", None)
  import midsurface_pairing
  import geom_midsurface
  reload(midsurface_pairing)
  reload(geom_midsurface)
  geom_midsurface.MidSurface(context)

def get_all_beams(context):
  import sys
  from importlib import reload
  sys.modules.pop("get_all_beams", None)
  sys.modules.pop("geom_get_all_beams", None)
  import get_all_beams as get_all_beams_eng
  import geom_get_all_beams
  reload(get_all_beams_eng)
  reload(geom_get_all_beams)
  geom_get_all_beams.GetAllBeams(context)

salome_pluginsmanager.AddFunction('Scope Plugins/Create Groups from Filter',
                                  'Create Groups Based on Multiple Criteria',
                                  filter_group)
salome_pluginsmanager.AddFunction('Scope Plugins/Detect 3D contacts',
                                  'Automatically Detect 3D contacts of two o more parts',
                                  contact)
salome_pluginsmanager.AddFunction('Scope Plugins/Pass Geometrical Groups',
                                  'Transfer similar groups from one part to another',
                                  pass_group)
salome_pluginsmanager.AddFunction('Scope Plugins/Lines from circles',
                                  'Create Edges/Lines between two groups of circles',
                                  line_from_circle)
salome_pluginsmanager.AddFunction('Scope Plugins/Hole Partition',
                                  'Creates a radial “pad” layout, splitting the area around a hole into four blocks suitable for mapped meshing',
                                  pad_partition)
salome_pluginsmanager.AddFunction('Scope Plugins/Mid surface',
                                  'Extract mid surfaces from thin solids by pairing opposite faces',
                                  midsurface)
salome_pluginsmanager.AddFunction('Scope Plugins/Get all beams',
                                  'Extract centerline edges (beams) from selected 3D solids or compounds',
                                  get_all_beams)
