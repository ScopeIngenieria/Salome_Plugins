# -*- coding: utf-8 -*-

import salome_pluginsmanager

def units_converter(context):
  import FEA_Units_Converter
  FEA_Units_Converter.show_dialog()

salome_pluginsmanager.AddFunction('Units Converter',
                                  'FEA Units Converter GUI',
                                  units_converter)


