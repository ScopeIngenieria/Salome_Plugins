# -*- coding: utf-8 -*-
# Create a pad for a circle for mesh porpuse
# Autor: Lucio Gomez (psicofil@gmail.com)
# Creation Date: 05/10/25
# Version: 06/10/2025

## Import necesary Libreries
from qtsalome import *

import salome
import GEOM
from salome.geom import geomBuilder
import math


# Detect current study
geompy = geomBuilder.New()
salome.salome_init()
CR = geompy.CanonicalRecognition()
#
try:
    selected = salome.sg.getSelected(0)
    selobjID=salome.myStudy.FindObjectID(selected)
    selobj=selobjID.GetObject()
    MainShape = selobjG.GetMainShape()
    NameMain = MainShape.GetName()+'_Pad'
except:
    NameMain = 'Pad_Partition'

### START OF MACRO

class GeomPad(QWidget):
    def __init__(self):
        super(GeomPad, self).__init__()
        self.initUI()
        #self.selectGroupRef()
    def __del__(self):
        return
    def initUI(self):
        self.l_ref_g  = QLabel("Reference Group:",self)
        self.pb_ref_g = QPushButton()
        self.pb_ref_g.setText("Select")
        self.le_ref_g = QLineEdit()
        self.l_nam_g  = QLabel("Name Results:",self)
        self.sb_gap = QDoubleSpinBox()
        self.le_nam_g = QLineEdit()
        self.le_nam_g.setText(NameMain)
        self.l_opt   = QLabel("Options:")
        self.qr_rect  = QRadioButton("Rectangular (orthogonal) split")
        self.qr_rect.setChecked(True)
        self.qr_tria  = QRadioButton("Triangular (diagonal) split")
        self.l_fact_t    = QLabel("Size Factor:")
        self.qr_fact_scale  = QRadioButton("Scale")
        self.qr_fact_scale.setChecked(Qt.Checked)
        self.qr_fact_dim  = QRadioButton("Dimension")
        self.l_fact    = QLabel("Value:")
        self.sb_fac   = QDoubleSpinBox()
        self.sb_fac.setValue(1.5)
        self.sb_fac.setMinimum(1.0)
        # Ok buttons:
        self.okbox = QDialogButtonBox(self)
        self.okbox.setOrientation(Qt.Horizontal)
        self.okbox.setStandardButtons(QDialogButtonBox.Cancel | QDialogButtonBox.Ok)
        # Progress Bar
        self.l_progress_bar  = QLabel("Progress:",self)
        self.progress_bar = QProgressBar(self)
        self.progress_bar.setValue(0)
        # Grups QRadioButton
        self.group_options = QButtonGroup(self)
        self.group_options.addButton(self.qr_rect)
        self.group_options.addButton(self.qr_tria)
        self.group_size = QButtonGroup(self)
        self.group_size.addButton(self.qr_fact_scale)
        self.group_size.addButton(self.qr_fact_dim)
        # Layout:
        layout = QGridLayout()
        layout.addWidget(self.l_ref_g,1,0)
        layout.addWidget(self.pb_ref_g,2,0)
        layout.addWidget(self.le_ref_g,2,1)
        layout.addWidget(self.l_nam_g,3,0)
        layout.addWidget(self.le_nam_g,3,1)
        layout.addWidget(self.l_opt,4,0)
        layout.addWidget(self.qr_rect,5,1)
        layout.addWidget(self.qr_tria,6,1)
        layout.addWidget(self.l_fact_t,7,0)
        layout.addWidget(self.qr_fact_scale,8,1)
        layout.addWidget(self.qr_fact_dim,9,1)
        layout.addWidget(self.l_fact,10,0)
        layout.addWidget(self.sb_fac,10,1)
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
        except:
            QMessageBox.critical(None,'Error',"Error whit selected group",QMessageBox.Abort)
    ##
    def proceed(self):
        try:
            self.source_obj.GetName()
        except:
            QMessageBox.critical(None,'Error',"Select a valid geometrical group first",QMessageBox.Abort)
        Edges_List = geompy.ExtractShapes(self.source_obj, geompy.ShapeType["EDGE"], True)
        pad_list = []
        j=0
        for selobj_group in Edges_List:
            prop_c = geompy.BasicProperties(selobj_group)
            r = prop_c[0]/(2.0*math.pi)
            ## check is a circle
            es_circ = CR.isCircle(selobj_group, 1e-7)
            if es_circ[0] == True:
                ## Add node in center of circle zone
                Face_1 = geompy.MakeFaceWires([selobj_group], 1)
                Vertex_1 = geompy.MakeVertexOnSurface(Face_1, 0.5, 0.5)
                fac = eval(str(self.sb_fac.text()))
                ## Add square face
                if self.qr_fact_dim.isChecked():
                    H = 2*(fac+r)
                else:
                    H = 2*fac*r
                Face_2 = geompy.MakeFaceObjHW(Face_1, H, H)
                ## Create paralell lines
                if self.qr_tria.isChecked():
                    pl_n = 0
                else:
                    pl_n = 0.5
                Translation_1_edge_8 = geompy.GetSubShape(Face_2, [8])
                Vertex_3 = geompy.MakeVertexOnCurve(Translation_1_edge_8, pl_n, True)
                Translation_1_edge_3 = geompy.GetSubShape(Face_2, [3])
                Vertex_4 = geompy.MakeVertexOnCurve(Translation_1_edge_3, pl_n, True)
                Translation_1_edge_6 = geompy.GetSubShape(Face_2, [6])
                Vertex_5 = geompy.MakeVertexOnCurve(Translation_1_edge_6, pl_n, True)
                Translation_1_edge_10 = geompy.GetSubShape(Face_2, [10])
                Vertex_6 = geompy.MakeVertexOnCurve(Translation_1_edge_10, pl_n, True)
                Line_1 = geompy.MakeLineTwoPnt(Vertex_3, Vertex_4)
                Line_2 = geompy.MakeLineTwoPnt(Vertex_5, Vertex_6)
                compoud = geompy.MakeCompound([Face_2, Line_1, Line_2])
                pad_list.append(compoud)
                j+=1
                self.progress_bar.setValue(100*j/len(Edges_List))
            else:
                QMessageBox.critical(None,'Error',"Select only circles",QMessageBox.Abort)
        try:
            Fcompoud = geompy.MakeCompound(pad_list)
            ## Main Shape Partition
            MainShape = self.source_obj.GetMainShape()
            Partition_1 = geompy.MakePartition([MainShape], [Fcompoud], [], [], geompy.ShapeType["SHELL"], 0, [], 0)
            Partition_ID = geompy.addToStudy( Partition_1, str(self.le_nam_g.text()) )
            salome.sg.Display(Partition_ID)
            salome.sg.UpdateView()
            salome.sg.updateObjBrowser()
        except:
            QMessageBox.critical(None,'Error',"Error in proceed",QMessageBox.Abort)
    # cancel function
    def cancel(self):
        self.close()
        d.close()


d = QDockWidget()
d.setWidget(GeomPad())
d.setAttribute(Qt.WA_DeleteOnClose)
d.setWindowFlags(d.windowFlags() | Qt.WindowStaysOnTopHint)
d.setWindowTitle(" Create Pad Circle partition ")
d.setGeometry(600, 300, 400, 400)
d.show()
try:
    widget_sel=d.widget()
    widget_sel.selectGroupRef()
except:
    None





