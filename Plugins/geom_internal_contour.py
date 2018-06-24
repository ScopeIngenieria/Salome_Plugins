# -*- coding: utf-8 -*-
# Script to Detect and create internal surface or volume from a solid
# Autor: Lucio Gomez (psicofil@gmail.com)
# Creation Date: 15/01/2018
# Version: 05/02/2018

# Import the necessary
try:
    from PyQt4 import QtGui,QtCore
    from PyQt4.QtGui import *
    from PyQt4.QtCore import *
except:
    from PyQt5.QtWidgets import QWidget, QMessageBox
    from PyQt5 import QtCore, QtGui
    import PyQt5.QtCore as QtCore
    from PyQt5.QtWidgets import *
    from PyQt5.QtCore import Qt

import salome
import GEOM
from salome.geom import geomBuilder
import math

gg = salome.ImportComponentGUI("GEOM")

# Detect current study
theStudy = salome.myStudy
geompy = geomBuilder.New(theStudy)
salome.salome_init()


class InternalSurface(QWidget):
    def __init__(self):
        super(InternalSurface, self).__init__()
        self.initUI()
        #self.selectParts()
    def initUI(self):       
        self.rb_surface = QRadioButton("  Internal Surfaces",self)
        self.rb_surface.setChecked(Qt.Checked)
        self.rb_volume = QRadioButton("  Internal Volume",self)
        self.l_parts = QLabel("References Surfaces: ", self)
        self.tb_parts = QTextBrowser()
        self.pb_loadpart = QPushButton()
        self.pb_loadpart.setText("Load selected")
        # Preview
        self.btn_preview = QPushButton("Preview",self)
        self.btn_preview.setEnabled(False)
        # Ok buttons:
        self.okbox = QDialogButtonBox(self)
        self.okbox.setOrientation(Qt.Horizontal)
        self.okbox.setStandardButtons(QDialogButtonBox.Cancel | QDialogButtonBox.Ok)
        # Progress Bar
        self.progress_bar = QProgressBar(self)
        # Layout:
        layout = QGridLayout()
        layout.addWidget(self.rb_surface, 1, 0)
        layout.addWidget(self.rb_volume, 2, 0)
        layout.addWidget(self.l_parts, 3, 0)
        layout.addWidget(self.tb_parts, 4, 0)
        layout.addWidget(self.pb_loadpart, 5, 0)
        layout.addWidget(self.btn_preview, 6, 0)
        layout.addWidget(self.okbox, 7, 0)
        layout.addWidget(self.progress_bar, 8, 0)
        self.setLayout(layout)
        # Connectors:
        self.okbox.accepted.connect(self.proceed)
        self.okbox.rejected.connect(self.cancel)
        self.pb_loadpart.clicked.connect(self.selectParts)
        
    def selectParts(self):
        try:
	  selCount = salome.sg.SelectedCount()
          selobj = list()
          self.tb_parts.clear()
          for i in range(0, selCount):
	    sel_i=salome.sg.getSelected(i)
	    selobj_i=salome.myStudy.FindObjectID(sel_i).GetObject()
	    selobj.append(selobj_i)
	    self.tb_parts.append(selobj[i].GetName())
	  self.parts = selobj 
        except:
	  QMessageBox.critical(None,'Error',"error in selected parts",QMessageBox.Abort)
          
    def proceed(self):
      selobj = self.selectParts()
      try:
	selobj = self.parts
        selobj_i = selobj[0]
        selCount = len(selobj)
      except:
	QMessageBox.critical(None,'Error',"Select 1 or more references surface First",QMessageBox.Abort)
      father = geompy.GetMainShape(selobj[0])
      self.progress_bar.setValue(1.0)
      RemoveIntWires_1 = geompy.SuppressInternalWires(father, [])
      self.progress_bar.setValue(2)
      SuppressHoles_1 = geompy.SuppressHoles(RemoveIntWires_1, [])
      self.progress_bar.setValue(8)
      list_shell = geompy.ExtractShapes(SuppressHoles_1, geompy.ShapeType["SHELL"], True)
      self.progress_bar.setValue(38)
      n_shells = len(list_shell)
      num_cont = 0
      list_result = list()
      if self.rb_surface.isChecked():
	Group_ob = geompy.CreateGroup(father, geompy.ShapeType["FACE"])
      for j in range(0, selCount):
	self.progress_bar.setValue((90.0/selCount)*(j+1))
	for i in range(0,n_shells):
	  isOk, res1, res2 = geompy.FastIntersect(list_shell[i], selobj[j], 0)
	  if isOk > 0:
	    common1 = geompy.MakeCommon(selobj[j], list_shell[i])
	    props = geompy.BasicProperties(common1)
	    area_com = props[1]
	    if area_com > 0:
	      if self.rb_volume.isChecked():
		volume = geompy.MakeCompound([list_shell[i]])
		try:
		  list_result.append(volume)
		except:
		  QMessageBox.critical(None,'Error',"Error 2",QMessageBox.Abort)
	      else:
		list_faces = geompy.ExtractShapes(list_shell[i], geompy.ShapeType["FACE"], True)
		nlist = len(list_faces)
		for i in range(0,nlist):
		  try:
		    ID = geompy.GetSubShapeID(father, list_faces[i])
		    geompy.AddObject(Group_ob, ID)
		  except:
		    pass
      if self.rb_surface.isChecked():
	Group_ob_ID = geompy.addToStudyInFather(father, Group_ob, 'InternalSurface')
	gg.setColor(Group_ob_ID,255,0,0)
	gg.createAndDisplayGO(Group_ob_ID)
      if self.rb_volume.isChecked():
	volume = geompy.MakeCompound(list_result)
	try:
	  volume = geompy.MakeSolid([volume])
	except:
	  pass
	resVolume = geompy.addToStudy(volume, 'InternalVolume' )
	gg.createAndDisplayGO(resVolume)
	gg.setDisplayMode(resVolume,2)
	gg.setColor(resVolume,255,0,0)
      self.progress_bar.setValue(100)
      if salome.sg.hasDesktop():
	salome.sg.updateObjBrowser(1)
	  
    # cancel function
    def cancel(self):
        self.close()
        d.close()

d = QDockWidget()
d.setWidget(InternalSurface())
d.setAttribute(Qt.WA_DeleteOnClose)
d.setWindowFlags(d.windowFlags() | QtCore.Qt.WindowStaysOnTopHint)
d.setWindowTitle(" Internal Contour ")
d.setGeometry(600, 300, 400, 400)
d.show()


