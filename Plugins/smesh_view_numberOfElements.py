# -*- coding: utf-8 -*-
# Displays a three-dimensional visualization of the number of mesh elements along each edge of a mesh or mesh group, providing an immediate view of edge-wise element distribution.
# Autor: Lucio Gomez (psicofil@gmail.com)
# Creation Date: 05/10/25
# Version: 06/10/2025

## Import necesary Libreries
from qtsalome import *

import salome
import GEOM
from salome.geom import geomBuilder
import math
import SALOMEDS
import SMESH, SALOMEDS
from salome.smesh import smeshBuilder
from salome.geom.geomtools import GeomStudyTools

#
gg = salome.ImportComponentGUI("GEOM")
geompy = geomBuilder.New()
smesh = smeshBuilder.New()
salome.salome_init()
gst = GeomStudyTools()
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
        self.pb_loadmesh.setText("Load Mesh or Group Mesh")
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
        layout.addWidget(self.l_mesh, 1, 0)
        layout.addWidget(self.le_mesh, 2, 1)
        layout.addWidget(self.pb_loadmesh, 2, 0)
        layout.addWidget(self.l_progress_bar,3,0)
        layout.addWidget(self.progress_bar,3,1)
        layout.addWidget(self.okbox,4,1)
        self.setLayout(layout)
        # Connectors:
        self.okbox.accepted.connect(self.proceed)
        self.okbox.rejected.connect(self.cancel)
        self.pb_loadmesh.clicked.connect(self.selectMesh)
    ##
    def selectMesh(self):
        try:
            selected=salome.sg.getSelected(0)
            selobjID=salome.myStudy.FindObjectID(selected)
            mesh=selobjID.GetObject()
            mName=selobjID.GetName().replace(" ","_")
            try:
                geometry = mesh.GetShapeToMesh() #mesh.GetShapeToMesh()
            except:
                geometry = mesh.GetShape() #mesh.GetShapeToMesh()
                mesh = mesh.GetMesh()
            self.le_mesh.setText(mName)
            self.mesh = mesh
            self.geometry = geometry
            self.selectedID = selected
        except:
            QMessageBox.critical(None,'Error',"error in selected mesh",QMessageBox.Abort)
    ##
    def proceed(self):
        try:
            self.clearDisplay()
        except:
            None
        try:
            Edges_List = geompy.ExtractShapes(self.geometry, geompy.ShapeType["EDGE"], True)
            ##
            Edges_ID_List = []
            group_List = []
            j = 1
            salome.sg.DisplayOnly(self.selectedID)
            for edges in Edges_List:
                ## 4 -  Grear Grupos de Mallas de los ejes explotados
                group = self.mesh.CreateGroupFromGEOM(SMESH.EDGE,'E'+str(j),edges)
                group_List.append(group)
                ## 5 - Obtener Numero de nodos de cada eje
                # Nn = group.GetNumberOfNodes() #GetNumberOfNodes() GetNumberOfElements()
                Nn = group.GetNbElementsByType()
                Nn = Nn[2]
                ## 5 - Eliminar Grupos de ejes creados
                self.mesh.RemoveGroup(group)
                edges.SetName(str(Nn))
                Edges_ID = geompy.addToStudyInFather(self.geometry, edges,str(Nn))
                Edges_ID_List.append(Edges_ID)
                gg.setNameMode(Edges_ID, True)
                salome.sg.Display(Edges_ID) #
                j+=1
                self.progress_bar.setValue(100*j/len(Edges_List))
            salome.sg.UpdateView()
            self.Edges_ID = Edges_ID_List
        except:
            QMessageBox.critical(None,'Error',"Unexpected error",QMessageBox.Abort)
    ### CLEAR
    def clearDisplay(self):
        ## 9 - Eliminar del estudio los ejes geometricos y sus grupos de malla del estudio (AL SALIR)
        for edges_id in self.Edges_ID:
            salome.sg.Erase(edges_id)
        salome.sg.UpdateView()
        for edges_id in self.Edges_ID:
            # gst.eraseShapeByEntry(edges_id)            ## sólo saca del viewer
            gst.removeFromStudy(edges_id)              ## despublica del Study (no destruye el GEOM)
    # cancel function
    def cancel(self):
        try:
            self.clearDisplay()
        except:
            None
        salome.sg.updateObjBrowser()
        self.close()
        d.close()


d = QDockWidget()
d.setWidget(GeomGroups())
d.setAttribute(Qt.WA_DeleteOnClose)
d.setWindowFlags(d.windowFlags() | Qt.WindowStaysOnTopHint)
d.setWindowTitle(" 3D view of Number of Elements ")
d.show()
try:
    widget_sel=d.widget()
    widget_sel.selectMesh()
except:
    None

#


