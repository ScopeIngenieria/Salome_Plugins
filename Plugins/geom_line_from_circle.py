# -*- coding: utf-8 -*-
# Create lines from 2 groups of circles
# Autor: Lucio Gomez (psicofil@gmail.com)
# Creation Date: 25/01/2018
# Version: 29/09/2025

# Import the necessary
from qtsalome import *
import salome
salome.salome_init()
import GEOM
from salome.geom import geomBuilder

gg = salome.ImportComponentGUI("GEOM")

# Detect current study
theStudy = salome.myStudy
geompy = geomBuilder.New()
salome.salome_init()


class CreateLinesFromCircles(QWidget):
    def __init__(self):
        super(CreateLinesFromCircles, self).__init__()
        self.initUI()
        #self.selectPart()
    def initUI(self):
        self.l_group1  = QLabel("Group of Circles 1:")
        self.le_group1 = QLineEdit()
        self.pb_sour = QPushButton()
        self.pb_sour.setText("...")
        self.l_dest  = QLabel("Group of Circles 2:")
        self.le_dest = QLineEdit()
        self.pb_dest = QPushButton()
        self.pb_dest.setText("...")
        # Ok buttons:
        self.okbox = QDialogButtonBox(self)
        self.okbox.setOrientation(Qt.Horizontal)
        self.okbox.setStandardButtons(QDialogButtonBox.Cancel | QDialogButtonBox.Ok)
        # Progress Bar
        #self.l_progress  = QLabel("Progress:")
        self.progress_bar = QProgressBar(self)
        self.progress_bar.setValue(0)
        # Layout:
        layout = QGridLayout()
        layout.addWidget(self.l_group1, 1, 0)
        layout.addWidget(self.le_group1, 2, 0)
        layout.addWidget(self.pb_sour, 2, 1)
        layout.addWidget(self.l_dest, 3, 0)
        layout.addWidget(self.le_dest, 4, 0)
        layout.addWidget(self.pb_dest, 4, 1)
        boxlayout = QVBoxLayout()
        boxlayout.addLayout(layout)
        boxlayout.addStretch()
        boxlayout.addWidget(self.okbox)
        boxlayout.addWidget(self.progress_bar)
        self.setLayout(boxlayout)
        # Connectors:
        self.okbox.accepted.connect(self.proceed)
        self.okbox.rejected.connect(self.cancel)
        self.pb_sour.clicked.connect(self.selectSource)
        self.pb_dest.clicked.connect(self.selectDestin)
    ##
    def selectSource(self):
        try:
            selected=salome.sg.getSelected(0)
            selobjID=salome.myStudy.FindObjectID(selected)
            selobj=selobjID.GetObject()
            self.le_group1.setText(selobj.GetName())
            self.source_obj = selobj
        except:
            QMessageBox.critical(None,'Error',"error in selected shape",QMessageBox.Abort)
    ##
    def selectDestin(self):
        try:
            selected=salome.sg.getSelected(0)
            selobjID=salome.myStudy.FindObjectID(selected)
            selobj=selobjID.GetObject()
            self.le_dest.setText(selobj.GetName())
            self.destin_obj = selobj
        except:
            QMessageBox.critical(None,'Error',"error in selected shape",QMessageBox.Abort)
    ##
    def proceed(self):
        try:
            Solid = False
            Face_1 = geompy.MakeFaceWires(self.source_obj, 1)
            Face_2 = geompy.MakeFaceWires(self.destin_obj, 1)
            faces1 = geompy.ExtractShapes(Face_1, geompy.ShapeType["FACE"], True)
            if faces1 == []:
                faces1 = [Face_1]
            group1=list()
            faces2 = geompy.ExtractShapes(Face_2, geompy.ShapeType["FACE"], True)
            if faces2 == []:
                faces2 = [Face_2]
            group2=list()
            for i in faces1:
                Vertex_1 = geompy.MakeVertexOnSurface(i, 0.5, 0.5)
                #V1 = geompy.addToStudy( Vertex_1, 'V1' )
                group1.append(Vertex_1)
            for i in faces2:
                Vertex_2 = geompy.MakeVertexOnSurface(i, 0.5, 0.5)
                #V2 = geompy.addToStudy( Vertex_2, 'V2' )
                group2.append(Vertex_2)
            groupL=list()
            groupS=list()
            prop_c = geompy.BasicProperties(faces1[0])
            import math
            r = prop_c[0]/(2.0*math.pi)
            if len(group1)==len(group2):
                N = 0
                for i in range(0,len(group1)):
                    Line = geompy.MakeLineTwoPnt(group1[i], group2[i])
                    prop = geompy.BasicProperties(Line)
                    Cylinder = geompy.MakeCylinder(group1[i], Line, r, prop[0])
                    groupL.append(Line)
                    groupS.append(Cylinder)
                    N += 1
                    self.progress_bar.setValue(100*N/(len(group1)-1))
                compound = geompy.MakeCompound(groupL)
                compoundS = geompy.MakeCompound(groupS)
                if Solid == False:
                    beams = geompy.addToStudy( compound, 'Beams' )
                    gg.createAndDisplayGO(beams)
                else:
                    beamsS = geompy.addToStudy( compoundS, 'BeamsS' )
                    gg.createAndDisplayGO(beamsS)
            else:
                QMessageBox.critical(None,'Error',"The groups no same number of elements",QMessageBox.Abort)
            salome.sg.updateObjBrowser()
            salome.sg.UpdateView()
        except:
            QMessageBox.critical(None,'Error',"Error - Make sure to select groups of circles",QMessageBox.Abort)
    # cancel function
    def cancel(self):
        self.close()
        d.close()

d = QDockWidget()
d.setWidget(CreateLinesFromCircles())
d.setAttribute(Qt.WA_DeleteOnClose)
d.setWindowFlags(d.windowFlags() | Qt.WindowStaysOnTopHint)
d.setWindowTitle(" Create Edges/Lines between two groups of circles ")
d.setGeometry(600, 300, 400, 250)
d.show()

# ================
# Tests
# ================
#
# def main( args ):
#     import sys
#     app = QApplication(sys.argv)
#     Dialog = TShapeDialog()
#     ui = Ui_Dialog()
#     ui.setupUi(Dialog)
#     Dialog.show()
#     #sys.exit(app.exec_())
#
# if __name__=="__main__":
#     main(sys.argv)
