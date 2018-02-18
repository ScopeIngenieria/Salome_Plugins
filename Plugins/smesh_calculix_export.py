# -*- coding: utf-8 -*-
# Detect and create 3D contact script
# License: LGPL v 2.1
# Autor: Lucio Gomez (psicofil@gmail.com)
# Creation Date: 17/06/2017
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
import subprocess
import sys
import tempfile
import  SMESH, SALOMEDS
from salome.smesh import smeshBuilder
from platform import system

### START OF MACRO

class CalculixExport(QWidget):
    def __init__(self):
        super(CalculixExport, self).__init__()
        self.initUI()
        #self.selectParts()
    def __del__(self):
        return
    def initUI(self):
        # 3D parts selected
        self.l_inp_file   = QLabel("inp file result:", self)
	self.le_inp_file   = QLineEdit()
	self.pb_inp_file = QPushButton()
	self.pb_inp_file.setText("file result")
	self.l_selectMesh = QLabel("Selected Mesh:", self)
	self.le_selectMesh = QLineEdit()
	self.le_selectMesh.setEnabled(False)
	self.pb_sel_mesh = QPushButton()
	self.pb_sel_mesh.setText("Select Mesh")  
	self.okbox = QDialogButtonBox(self)
	self.okbox.setOrientation(QtCore.Qt.Horizontal)
	self.okbox.setStandardButtons(QDialogButtonBox.Cancel|QDialogButtonBox.Ok)
	self.l_options   = QLabel("Aditional options:", self)
	#self.rb_cgx = QCheckBox("Open the result with CGX at the end", self)
	#self.rb_cgx.setChecked(False)
	self.rb_delet_e_f = QCheckBox("Delete delete edges and faces in selected mesh", self)
        self.pb_unical_config = QPushButton(self)
        self.pb_unical_config.setText("Config Unical")
        self.le_unical_config = QLineEdit(self)
        self.le_unical_config.setEnabled(False)
        self.l_log = QLabel("Unical Log: ", self)
        self.tb_log = QTextBrowser()
	layout = QGridLayout()
	layout.addWidget(self.l_selectMesh,1,0)
	layout.addWidget(self.le_selectMesh,2,0)
	layout.addWidget(self.pb_sel_mesh,2,1)
	layout.addWidget(self.l_inp_file,3,0)
	layout.addWidget(self.le_inp_file,4,0)
	layout.addWidget(self.pb_inp_file,4,1)
	layout.addWidget(self.l_options,5,0)
	#layout.addWidget(self.rb_cgx,6,0)
	layout.addWidget(self.rb_delet_e_f,6,0)
	layout.addWidget(self.pb_unical_config,7,1)
	layout.addWidget(self.le_unical_config,7,0)
	boxlayout = QVBoxLayout()
	boxlayout.addLayout(layout)
	boxlayout.addWidget(self.l_log)
	boxlayout.addWidget(self.tb_log)
	boxlayout.addWidget(self.okbox)
	self.setLayout(boxlayout)
	# Connectors:
	self.pb_sel_mesh.clicked.connect(self.findSelectedMeshes)
	self.pb_inp_file.clicked.connect(self.meshFile)
	self.pb_unical_config.clicked.connect(self.Unical_Config)
	self.okbox.accepted.connect(self.proceed)
	self.okbox.rejected.connect(self.cancel)
        try:
	  Conf_file = open('cfg_CalculixSalome_Plug.cf', 'r')
	  self.le_unical_config.setText(str(Conf_file.read()))
	  Conf_file.close() 
	except:
	  self.le_unical_config.setText("")
	
    def Unical_Config(self):
        self.unical_bin_d = QFileDialog.getOpenFileName(self,'Select Unical binary')
        self.unical_bin = str(self.unical_bin_d[0])
        self.le_unical_config.setText(self.unical_bin)
        Conf_file = open('cfg_CalculixSalome_Plug.cf','w')
        Conf_file.write(self.unical_bin)
        Conf_file.close() 
        
    def findSelectedMeshes(self):
      selected=salome.sg.getSelected(0)
      try:
        selobjID=salome.myStudy.FindObjectID(selected)
        selobj=selobjID.GetObject()
        mName=selobjID.GetName().replace(" ","_")
        self.le_selectMesh.setText(mName)
        self.emesh = selobj
      except:
        QMessageBox.critical(None,'Error',"You have to select a mesh object and then run this script.",QMessageBox.Abort)
        
        
    def meshFile(self):
      PageName = QFileDialog.getSaveFileName(qApp.activeWindow(),'Select inp or msh file result ',"Result.inp",filter ="inp (*.inp *.);;msh (*.msh *.)")
      self.le_inp_file.setText(str(PageName[0]))      
                
    def proceed(self):
      meshes=self.emesh
      try:
	if not meshes == None:
	  temp_file = tempfile.mkstemp(suffix='.unv')[1]
	  meshes.ExportUNV(temp_file)
	file_inp = self.le_inp_file.text()
	unical_bin = self.le_unical_config.text()
	command = str(unical_bin) + ' ' + temp_file + ' ' + file_inp
	output = subprocess.check_output([command, '-1'], shell=True, stderr=subprocess.STDOUT,)
	self.tb_log.append(output)
	QMessageBox.information(None,'successful result','The mesh has been exported successfully in ' + file_inp,QMessageBox.Ok)
	print(command)
      except:
	QMessageBox.critical(None,'Error',"Unexpected error in Salome to Calculix Script: {}".format(sys.exc_info()[0]),QMessageBox.Abort)
	QMessageBox.critical(None,'Error whit the conmand ',command,QMessageBox.Abort)
      #if self.rb_cgx.isChecked():
	  #self.open_CGX()
      if self.rb_delet_e_f.isChecked():
	  self.delete_edges_and_faces_mesh()
	  
    #def open_CGX(self):
      #command_cgx = cgx_bin + '-c ' + self.le_inp_file.text()
      #try:
	#process = QtCore.QProcess()
	#process.startDetached('konsole -e ' + command_cgx)
      #except:
	#QMessageBox.critical(None,'Error',"Unexpected error in CGX process to open the result",QMessageBox.Abort)
	
    def delete_edges_and_faces_mesh(self):
      mesh=self.emesh
      if not mesh == None:
	Group_1 = mesh.CreateEmptyGroup(SMESH.FACE, 'Group_1' )
	nbAdd = Group_1.AddFrom( mesh.GetMesh() )
	Group_2 = mesh.CreateEmptyGroup( SMESH.EDGE, 'Group_2' )
	nbAdd = Group_2.AddFrom( mesh.GetMesh() )
	mesh.RemoveGroupWithContents(Group_1)
	mesh.RemoveGroupWithContents(Group_2)
	    
	    
    # cancel function
    def cancel(self):
        self.close()
        d.close()

d = QDockWidget()
d.setWidget(CalculixExport())
d.setAttribute(Qt.WA_DeleteOnClose)
d.setWindowFlags(d.windowFlags() | QtCore.Qt.WindowStaysOnTopHint)
d.setWindowTitle(" Salome to Calculix ")
d.setGeometry(600, 200, 400, 500)
d.show()



