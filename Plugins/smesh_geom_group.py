# -*- coding: utf-8 -*-
# Create mesh groups from geometry, even if the link does not exist.
# Autor: Lucio Gomez (psicofil@gmail.com)
# Creation Date: 01/09/2017
# Version: 06/02/2018

## Import necesary Libreries
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
import SALOMEDS
import SMESH, SALOMEDS
from salome.smesh import smeshBuilder

# Detect current study
theStudy = salome.myStudy
geompy = geomBuilder.New(theStudy)
smesh = smeshBuilder.New(theStudy)
salome.salome_init()

### START OF MACRO

class GeomGroups(QWidget):
    def __init__(self):
        super(GeomGroups, self).__init__()
        self.initUI()
        #self.selectMesh()
    def __del__(self):
        return
    def initUI(self):
        self.l_mesh  = QLabel("Mesh:")
        self.le_mesh = QLineEdit()
        self.pb_loadmesh = QPushButton()
        self.pb_loadmesh.setText("Load Mesh")
        self.l_groups = QLabel("Geometrical Shapes: ", self)
        self.tb_groups = QTextBrowser()
        self.pb_loadgroup = QPushButton()
        self.pb_loadgroup.setText("Load Geometrical Groups")
        self.rb_element = QRadioButton("  Elements",self)
        self.rb_element.setChecked(Qt.Checked)
        self.rb_nodes = QRadioButton("  Nodes",self)
        # Ok buttons:
        self.okbox = QDialogButtonBox(self)
        self.okbox.setOrientation(Qt.Horizontal)
        self.okbox.setStandardButtons(QDialogButtonBox.Cancel | QDialogButtonBox.Ok)
        # Layout:
        layout = QGridLayout()
        layout.addWidget(self.l_mesh, 1, 0)
        layout.addWidget(self.le_mesh, 2, 1)
        layout.addWidget(self.pb_loadmesh, 2, 0)
        layout.addWidget(self.rb_element, 3, 0)
        layout.addWidget(self.rb_nodes, 4, 0)
        boxlayout = QVBoxLayout()
        boxlayout.addLayout(layout)
        boxlayout.addWidget(self.l_groups)
        boxlayout.addWidget(self.tb_groups)
        boxlayout.addWidget(self.pb_loadgroup)
        boxlayout.addWidget(self.okbox)
        self.setLayout(boxlayout)
        # Connectors:
        self.okbox.accepted.connect(self.proceed)
        self.okbox.rejected.connect(self.cancel)
        self.pb_loadgroup.clicked.connect(self.selectGroups)
        self.pb_loadmesh.clicked.connect(self.selectMesh)
        
    def selectGroups(self):
        try:
	  selCount = salome.sg.SelectedCount()
          selobj = list()
          self.tb_groups.clear()
          for i in range(0, selCount):
	    sel_i=salome.sg.getSelected(i)
	    selobj_i=salome.myStudy.FindObjectID(sel_i).GetObject()
	    selobj.append(selobj_i)
	    self.tb_groups.append(selobj[i].GetName())
	  self.parts = selobj
	  self.selCount = len(self.parts)
        except:
	  QMessageBox.critical(None,'Error',"error in selected parts",QMessageBox.Abort)
	  
    def selectMesh(self):
        try:
            selected=salome.sg.getSelected(0)
            selobjID=salome.myStudy.FindObjectID(selected)
            mesh=selobjID.GetObject()
            mName=selobjID.GetName().replace(" ","_")
            self.le_mesh.setText(mName)
            self.source_mesh = mesh
        except:
	    QMessageBox.critical(None,'Error',"error in selected mesh",QMessageBox.Abort)
          
    def proceed(self):
      selobj = self.parts
      Mesh_1 = self.source_mesh
      groups_passed = list()
      groups_no_passed = list()
      for i in range(0,self.selCount):
	try:
	  name_geom_group = selobj[i].GetName()
	  elem = str(selobj[i].GetMaxShapeType())
	  if elem == "FACE":
	    type_g = SMESH.FACE
	  if elem == "EDGE":
	    type_g = SMESH.EDGE
	  if elem == "SOLID":
	    type_g = SMESH.VOLUME
	  if self.rb_nodes.isChecked():
	    type_g = SMESH.NODE
	  # Criterios
	  aCriteria = []
	  aCriterion1 = smesh.GetCriterion(type_g,SMESH.FT_BelongToGeom,SMESH.FT_Undefined,name_geom_group)
	  aCriteria.append(aCriterion1)
	  aFilter_1 = smesh.GetFilterFromCriteria(aCriteria)
	  aFilter_1.SetMesh(Mesh_1.GetMesh())
	  Group_1 = Mesh_1.CreateGroupFromFilter( type_g, name_geom_group, aFilter_1 )
	  smesh.SetName(Group_1, name_geom_group)
	  groups_passed.append(name_geom_group)
	except:
	  try:
	    groups_no_passed.append(name_geom_group)
	  except:
	    QMessageBox.critical(None,'Error 1',"Unexpected error",QMessageBox.Abort)
      QMessageBox.information(None, "Informacion","Groups that passed:\n\n"+str(groups_passed)+"\n\n"+"Groups that No passed:\n\n"+ str(groups_no_passed), QMessageBox.Ok)
      if salome.sg.hasDesktop():
	salome.sg.updateObjBrowser(1)
	  
    # cancel function
    def cancel(self):
        self.close()
        d.close()

d = QDockWidget()
d.setWidget(GeomGroups())
d.setAttribute(Qt.WA_DeleteOnClose)
d.setWindowFlags(d.windowFlags() | QtCore.Qt.WindowStaysOnTopHint)
d.setWindowTitle(" Groups from shapes ")
d.setGeometry(600, 300, 400, 400)
d.show()



