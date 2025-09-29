# -*- coding: utf-8 -*-
# Pass groups from objects script
# Autor: Lucio Gomez (psicofil@gmail.com)
# Creation Date: 15/08/2017
# Version: 19/09/2025

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


class PassGroups(QWidget):
    def __init__(self):
        super(PassGroups, self).__init__()
        self.initUI()
        #self.selectPart()
    def initUI(self):
        self.l_sour  = QLabel("Source Shape:")
        self.le_sour = QLineEdit()
        self.pb_sour = QPushButton()
        self.pb_sour.setText("...")
        self.l_dest  = QLabel("Destination Shape:")
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
        layout.addWidget(self.l_sour, 1, 0)
        layout.addWidget(self.le_sour, 2, 0)
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
    def selectSource(self):
        try:
            selected=salome.sg.getSelected(0)
            selobjID=salome.myStudy.FindObjectID(selected)
            selobj=selobjID.GetObject()
            self.le_sour.setText(selobj.GetName())
            self.source_obj = selobj
        except:
            QMessageBox.critical(None,'Error',"error in selected shape",QMessageBox.Abort)
    def selectDestin(self):
        try:
            selected=salome.sg.getSelected(0)
            selobjID=salome.myStudy.FindObjectID(selected)
            selobj=selobjID.GetObject()
            self.le_dest.setText(selobj.GetName())
            self.destin_obj = selobj
        except:
            QMessageBox.critical(None,'Error',"error in selected shape",QMessageBox.Abort)
    def proceed(self):
        groups_passed = list()
        groups_no_passed = list()
        shape_1 = False
        shape_2 = False
        try:
            groups_source = geompy.GetGroups(self.source_obj)
            n_groups = len(groups_source)
            shape_1 = True
        except:
            QMessageBox.critical(None,'Error',"Select a valid source shape first",QMessageBox.Abort)
        try:
            self.destin_obj.GetName()
            shape_2 = True
        except:
            QMessageBox.critical(None,'Error',"Select a valid Destination shape first",QMessageBox.Abort)
        if shape_1 and shape_2:
            try:
                for i in range(0,n_groups):
                    group_p = groups_source[i]
                    name_g = group_p.GetName()
                    type_g = str(group_p.GetShapeType())
                    props = geompy.BasicProperties(group_p)
                    if type_g == "COMPOUND":
                        if props[2] == 0:
                            type_g = "FACE"
                        if props[1] == 0:
                            type_g = "EDGE"
                        if props[2] > 0:
                            type_g = "SOLID"
                    props = geompy.BasicProperties(group_p)
                    elements = geompy.ExtractShapes(group_p, geompy.ShapeType[type_g], True)
                    props = geompy.BasicProperties(group_p)
                    Group_ob = geompy.CreateGroup(self.destin_obj, geompy.ShapeType[type_g])
                    try:
                        if len(elements) > 1:
                            for elem in elements:
                                group_pass = geompy.GetSame(self.destin_obj, elem)
                                Element_ID = geompy.GetSubShapeID(self.destin_obj, group_pass)
                                geompy.AddObject(Group_ob, Element_ID)
                            geompy.addToStudyInFather(self.destin_obj, Group_ob, name_g)
                            groups_passed.append(name_g)
                        else:
                            group_pass = geompy.GetSame(self.destin_obj, group_p)
                            Element_ID = geompy.GetSubShapeID(self.destin_obj, group_pass)
                            geompy.AddObject(Group_ob, Element_ID)
                            geompy.addToStudyInFather( self.destin_obj, Group_ob, name_g )
                            groups_passed.append(name_g)
                    except:
                        groups_no_passed.append(name_g)
                    self.progress_bar.setValue(100*i/(n_groups-1))
                QMessageBox.information(None, "Informacion","Groups that passed:\n\n"+str(groups_passed)+"\n\n"+"Groups that No passed:\n\n"+ str(groups_no_passed), QMessageBox.Ok)
            except:
                QMessageBox.critical(None,'Error',"Error - No group has passed",QMessageBox.Abort)
        salome.sg.updateObjBrowser()
    # cancel function
    def cancel(self):
        self.close()
        d.close()

d = QDockWidget()
d.setWidget(PassGroups())
d.setAttribute(Qt.WA_DeleteOnClose)
d.setWindowFlags(d.windowFlags() | QtCore.Qt.WindowStaysOnTopHint)
d.setWindowTitle(" Pass Geometrical Groups ")
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
