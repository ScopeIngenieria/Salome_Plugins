# -*- coding: utf-8 -*-

import salome_pluginsmanager

def external_interactive(context):
  import Aster_Interactive
  reload(Aster_Interactive)

def plot_monitor(context):
  import Aster_Monitor
  reload(Aster_Monitor)

salome_pluginsmanager.AddFunction('Monitoring Simulation/Interactive follow up',
                                  'Follow up simulations with terminal emulator',
                                  external_interactive)

salome_pluginsmanager.AddFunction('Monitoring Simulation/Monitoring Simulation Plots',
                                  'Time Step, Residuals or VARI_CONT Plots',
                                  plot_monitor)

