# -*- coding: utf-8 -*-
# Detect and create 3D contact script
# License: LGPL v 2.1
# Autor: Lucio Gomez (psicofil@gmail.com)
# Creation Date: 17/06/2017
# Version: 29/09/2025

## Import necesary Libreries
from qtsalome import *

import salome
import GEOM
from salome.geom import geomBuilder
import math

# Detect current study
theStudy = salome.myStudy
geompy = geomBuilder.New(theStudy)
salome.salome_init()

### START OF MACRO

class Conact3D(QWidget):
    def __init__(self):
        super(Conact3D, self).__init__()
        self.initUI()
        #self.selectParts()
    def __del__(self):
        return
    def initUI(self):
        # 3D parts selected 
        self.l_parts = QLabel("3D Parts for contact analysis: ", self)
        self.tb_parts = QTextBrowser()
        self.pb_loadpart = QPushButton()
        self.pb_loadpart.setText("Load selected")
        # Adjust Gap
        self.l_gap = QLabel("Gap: ")
        self.sb_gap = QDoubleSpinBox()
        self.sb_gap.setDecimals(3)
        self.sb_gap.setValue(0.000)
        self.sb_gap.setSingleStep(0.001)     
        self.cb_common = QCheckBox("  Compound Results",self)
        self.cb_common.setChecked(Qt.Checked)
        # Ok buttons:
        self.okbox = QDialogButtonBox(self)
        self.okbox.setOrientation(Qt.Horizontal)
        self.okbox.setStandardButtons(QDialogButtonBox.Cancel | QDialogButtonBox.Ok)
        # Progress Bar
        self.progress_bar = QProgressBar(self)
        # Layout:
        layout = QGridLayout()
        layout.addWidget(self.l_parts, 1, 0)
        layout.addWidget(self.tb_parts, 2, 0)
        layout.addWidget(self.pb_loadpart, 3, 0)
        layout.addWidget(self.l_gap, 4, 0)
        layout.addWidget(self.sb_gap, 5, 0)
        layout.addWidget(self.cb_common, 6, 0)
        layout.addWidget(self.okbox, 8, 0)
        layout.addWidget(self.progress_bar, 9, 0)
        self.setLayout(layout)
        # Connectors:
        self.okbox.accepted.connect(self.proceed)
        self.okbox.rejected.connect(self.cancel)
        self.pb_loadpart.clicked.connect(self.selectParts)
    ##
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
    ##
    def proceed(self):
        gap = eval(str(self.sb_gap.text()))
        if self.cb_common.isChecked():
            Common = True
        else:
            Common = False
        #selobj = self.selectParts()
        try:
            selobj = self.parts
            selobj_i = selobj[0]
            selobj_j = selobj[1]
            selCount = len(selobj)
        except:
            QMessageBox.critical(None,'Error',"Select 2 or more parts 3D first",QMessageBox.Abort)
        num_cont = 0
        self.progress_bar.setValue(1.0)
        for i in range(0, selCount):
            self.progress_bar.setValue((90.0/selCount)*(i+1))
            for j in range(1, selCount):
                    if i != j and i < j:
                        try:
                            isOk, res1, res2 = geompy.FastIntersect(selobj[i], selobj[j], gap)
                            if isOk > 0:
                                N_C = len(res1)
                                N_C2 = len(res2)
                                CONT  = geompy.SubShapes(selobj[i], res1)
                                CONT2 = geompy.SubShapes(selobj[j], res2)
                                cont_sf_i = list()
                                cont_sf_j = list()
                                for h in range(0, N_C):
                                    for k in range(0, N_C2):
                                        common1 = geompy.MakeCommon(CONT[h], CONT2[k])
                                        props = geompy.BasicProperties(common1)
                                        area_com = props[1]
                                        if Common == False:
                                            if area_com > 0.0:
                                                name_group_i = 'CZ_' + str(i) + str(j) + '_' + str(k)
                                                geompy.addToStudyInFather( selobj[i], CONT[h], name_group_i )
                                                name_group_j = 'CZ_' + str(j) + str(i) + '_' + str(h)
                                                geompy.addToStudyInFather( selobj[j], CONT2[k], name_group_j )
                                                num_cont += 1
                                        else:
                                            if area_com > 0.0:
                                                cont_sf_i.append(CONT[h])
                                                cont_sf_j.append(CONT2[k])
                                                num_cont += 1
                        except:
                            QMessageBox.critical(None,'Error',"No 3D contacts detected",QMessageBox.Abort)
                        if Common == True:
                            comp_sf_i = geompy.MakeCompound(cont_sf_i)
                            name_group_i = 'CZ_' + str(i) + str(j)
                            geompy.addToStudyInFather( selobj[i], comp_sf_i, name_group_i )
                            comp_sf_j = geompy.MakeCompound(cont_sf_j)
                            name_group_j = 'CZ_' + str(j) + str(i)
                            geompy.addToStudyInFather( selobj[j], comp_sf_j, name_group_j )
        self.progress_bar.setValue(100)
        msg_cont = "Number of pairs of contacts detected: " + str(num_cont)
        QMessageBox.information(None, "Information", msg_cont, QMessageBox.Ok)
        salome.sg.updateObjBrowser()
    # cancel function
    def cancel(self):
        self.close()
        d.close()

d = QDockWidget()
d.setWidget(Conact3D())
d.setAttribute(Qt.WA_DeleteOnClose)
d.setWindowFlags(d.windowFlags() | Qt.WindowStaysOnTopHint)
d.setWindowTitle(" Detect 3D contacts ")
d.setGeometry(600, 300, 400, 400)
d.show()



