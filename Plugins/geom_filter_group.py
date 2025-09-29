# -*- coding: utf-8 -*-
# Create groups form filters script
# Autor: Lucio Gomez (psicofil@gmail.com)
# Creation Date: 25/10/16
# Version: 29/09/2025

## Import necesary Libreries
from qtsalome import *

import salome
import GEOM
from salome.geom import geomBuilder
import math

# Detect current study
geompy = geomBuilder.New()
salome.salome_init()

### START OF MACRO

class GeomFilterGroup(QWidget):
    def __init__(self):
        super(GeomFilterGroup, self).__init__()
        self.initUI()
        #self.selectGroupRef()
    def __del__(self):
        return
    def initUI(self):
        self.l_ref_g  = QLabel("Reference Group:",self)
        self.pb_ref_g = QPushButton()
        self.pb_ref_g.setText("Select")
        self.le_ref_g = QLineEdit()
        self.l_nam_g  = QLabel("Name result Group:",self)
        self.sb_gap = QDoubleSpinBox()
        self.le_nam_g = QLineEdit()
        self.le_nam_g.setText("Group_R")
        self.l_crit   = QLabel("Criteriums:")
        self.cb_size  = QCheckBox("Size")
        self.cb_size.setChecked(Qt.Checked)
        self.cb_locx  = QCheckBox("Location X")
        self.cb_locy  = QCheckBox("Location Y")
        self.cb_locz  = QCheckBox("Location Z")
        self.cb_norm  = QCheckBox("Normal")
        self.cb_norm.setEnabled(False)
        self.l_tol    = QLabel("% Tolerance:")
        self.sb_tol   = QDoubleSpinBox()
        self.sb_tol.setValue(0.01)
        self.sb_tol.setMaximum(1.00)
        self.sb_tol.setMinimum(0.01)
        # Ok buttons:
        self.okbox = QDialogButtonBox(self)
        self.okbox.setOrientation(Qt.Horizontal)
        self.okbox.setStandardButtons(QDialogButtonBox.Cancel | QDialogButtonBox.Ok)
        # Progress Bar
        self.l_progress_bar  = QLabel("Progress:",self)
        self.progress_bar = QProgressBar(self)
        self.progress_bar.setValue(0)
        # Layout:
        layout = QGridLayout()
        layout.addWidget(self.l_ref_g,1,0)
        layout.addWidget(self.pb_ref_g,2,0)
        layout.addWidget(self.le_ref_g,2,1)
        layout.addWidget(self.l_nam_g,3,0)
        layout.addWidget(self.le_nam_g,3,1)
        layout.addWidget(self.l_crit,4,0)
        layout.addWidget(self.cb_size,5,1)
        layout.addWidget(self.cb_locx,6,1)
        layout.addWidget(self.cb_locy,7,1)
        layout.addWidget(self.cb_locz,8,1)
        layout.addWidget(self.cb_norm,9,1)
        layout.addWidget(self.l_tol,10,0)
        layout.addWidget(self.sb_tol,11,1)
        layout.addWidget(self.l_progress_bar,12,0)
        layout.addWidget(self.progress_bar,12,1)
        layout.addWidget(self.okbox,13,1)
        self.setLayout(layout)
        # Connectors:
        self.okbox.accepted.connect(self.proceed)
        self.okbox.rejected.connect(self.cancel)
        self.pb_ref_g.clicked.connect(self.selectGroupRef)
    ##
    def selectGroupRef(self):
        try:
            selected=salome.sg.getSelected(0)
            selobjID=salome.myStudy.FindObjectID(selected)
            selobj=selobjID.GetObject()
            type_o = str(selobj.GetShapeType())
            # Set object Name
            self.le_ref_g.setText(selobj.GetName())
            self.source_obj = selobj
            # Set normal availble
            if type_o=='FACE':
                self.cb_norm.setEnabled(True)
            else:
                self.cb_norm.setEnabled(False)
        except:
            QMessageBox.critical(None,'Error',"error whit selected group",QMessageBox.Abort)
    ##
    def proceed(self):
        try:
            self.source_obj.GetName()
        except:
            QMessageBox.critical(None,'Error',"Select a valid geometrical group first",QMessageBox.Abort)
        try:
            # Is a group?
            isgroup = geompy.ShapeIdToType(self.source_obj.GetType()) == 'GROUP'
            # The father of group
            father = geompy.GetMainShape(self.source_obj)
            # Type of element
            elem = str(self.source_obj.GetShapeType())
            # Size
            props = geompy.BasicProperties(self.source_obj)
            if elem=="EDGE":
                Sref = props[0]
            if elem=="FACE":
                Sref = props[1]
            if elem=="SOLID":
                Sref = props[2]
            # Location
            cm_ref = geompy.MakeCDG(self.source_obj)
            coords_ref = geompy.PointCoordinates(cm_ref)
            # Normal (Element==Face)
            if elem=="FACE":
                vnorm_ref = geompy.GetNormal(self.source_obj)
            else:
                vnorm_ref = None
            # Create container group
            group=list()
            # All Object elements of type elem
            elements = geompy.ExtractShapes(father, geompy.ShapeType[elem], True)
            # Create group
            Group_f = geompy.CreateGroup(father, geompy.ShapeType[elem])
            # Options
            name_g = str(self.le_nam_g.text())
            pr = eval(str(self.sb_tol.text()))
        except:
            QMessageBox.critical(None,'Error',"error 1",QMessageBox.Abort)
        try:
            # Selected elements for the group whit the desired conditios
            j=1
            for i in elements:
                props = geompy.BasicProperties(i)
                cm = geompy.MakeCDG(i)
                coords = geompy.PointCoordinates(cm)
                # Element i coordinates
                x = coords[0]
                y = coords[1]
                z = coords[2]
                # Element i size
                if elem=="EDGE":
                    S = props[0]
                if elem=="FACE":
                    S = props[1]
                if elem=="SOLID":
                    S = props[2]
                # Element==Face i Normal
                if vnorm_ref==None:
                    vnorm=None
                else:
                    vnorm = geompy.GetNormal(i)
                    angle = geompy.GetAngle(vnorm_ref, vnorm)
                # Comparations
                cond = list()
                if self.cb_size.isChecked():
                    cond.append(S<Sref*(1+pr) and S>Sref*(1-pr))
                else:
                    cond.append(True)
                if self.cb_locx.isChecked():
                    if coords_ref[0]>=0:
                        cond.append(x<coords_ref[0]*(1+pr) and x>coords_ref[0]*(1-pr))
                    else:
                        cond.append(x>coords_ref[0]*(1+pr) and x<coords_ref[0]*(1-pr))
                else:
                    cond.append(True)
                if self.cb_locy.isChecked():
                    if coords_ref[1]>=0:
                        cond.append(y<coords_ref[1]*(1+pr) and y>coords_ref[1]*(1-pr))
                    else:
                        cond.append(y>coords_ref[1]*(1+pr) and y<coords_ref[1]*(1-pr))
                else:
                    cond.append(True)
                if self.cb_locz.isChecked():
                    if coords_ref[2]>=0:
                        cond.append(z<coords_ref[2]*(1+pr) and z>coords_ref[2]*(1-pr))
                    else:
                        cond.append(z>coords_ref[2]*(1+pr) and z<coords_ref[2]*(1-pr))
                else:
                    cond.append(True)
                if  self.cb_norm.isChecked() and vnorm != None:
                    cond.append(angle<0.0+0.001 and angle>0.0-0.001)
                else:
                    cond.append(True)
                if cond[0] and cond[1] and cond[2] and cond[3] and cond[4]:
                    ID = geompy.GetSubShapeID(father,i)
                    group.append(ID)
                    cond.append(cond)
                j=j+1
                self.progress_bar.setValue(100*j/len(elements))
        except:
            QMessageBox.critical(None,'Error',"Unexpected error in Filter Group!",QMessageBox.Abort)
        # Add elements desired to Group
        try:
            geompy.UnionIDs(Group_f, group)
            ## Add group in hte gui
            resGroup = geompy.addToStudyInFather(father, Group_f, name_g)
            ## View group
            gg = salome.ImportComponentGUI("GEOM")
            # Set color of the group
            gg.setColor(resGroup,255,0,0)
            gg.createAndDisplayGO(resGroup)
            ## Update Object Browser
            salome.sg.updateObjBrowser()
        except:
            QMessageBox.critical(None,'Error',"error 3",QMessageBox.Abort)
    # cancel function
    def cancel(self):
        self.close()
        d.close()


d = QDockWidget()
d.setWidget(GeomFilterGroup())
d.setAttribute(Qt.WA_DeleteOnClose)
d.setWindowFlags(d.windowFlags() | Qt.WindowStaysOnTopHint)
d.setWindowTitle(" Create Group from Filter ")
d.setGeometry(600, 300, 400, 400)
d.show()




