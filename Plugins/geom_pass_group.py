# -*- coding: utf-8 -*-
# Pass groups from objects script
# Autor: Lucio Gomez (psicofil@gmail.com)
# Creation Date: 15/08/2017
# Version: 15/10/2026

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
            self.source_sobj = selobjID
        except:
            QMessageBox.critical(None,'Error',"error in selected shape",QMessageBox.Abort)
    def selectDestin(self):
        try:
            selected=salome.sg.getSelected(0)
            selobjID=salome.myStudy.FindObjectID(selected)
            selobj=selobjID.GetObject()
            self.le_dest.setText(selobj.GetName())
            self.destin_obj = selobj
            self.destin_sobj = selobjID
        except:
            QMessageBox.critical(None,'Error',"error in selected shape",QMessageBox.Abort)

    def studyEntry(self, obj):
        try:
            entry = salome.ObjectToID(obj)
            if entry:
                return str(entry)
        except:
            pass
        try:
            return str(geompy.GetStudyEntry(obj))
        except:
            return ""

    def childCompounds(self, obj, groups):
        """Return direct child compounds, excluding GEOM groups."""
        sobj = getattr(self, "source_sobj", None)
        if sobj is None:
            entry = self.studyEntry(obj)
            if entry:
                sobj = theStudy.FindObjectID(entry)
        if sobj is None:
            return []

        group_entries = set(self.studyEntry(group) for group in groups)
        compounds = []
        try:
            iterator = theStudy.NewChildIterator(sobj)
        except:
            try:
                iterator = sobj.NewChildIterator()
            except:
                return compounds

        while iterator.More():
            child_sobj = iterator.Value()
            iterator.Next()
            try:
                child = child_sobj.GetObject()
                if (self.studyEntry(child) not in group_entries and
                        str(child.GetShapeType()).upper() == "COMPOUND"):
                    compounds.append(child)
            except:
                pass
        return compounds

    def groupElements(self, group):
        """Get the actual sub-shapes referenced by a GEOM group."""
        elements = []
        try:
            for sub_id in group.GetSubShapeIndices():
                elements.append(geompy.GetSubShape(self.source_obj, [sub_id]))
        except:
            pass
        return [element for element in elements if element is not None]

    def compoundElements(self, compound):
        """Return maximal pieces, including those of mixed compounds."""
        elements = []
        for type_name in ("SOLID", "FACE", "EDGE", "VERTEX"):
            try:
                candidates = geompy.ExtractShapes(
                    compound, geompy.ShapeType[type_name], True) or []
            except:
                candidates = []
            for candidate in candidates:
                contained = False
                for parent in elements:
                    try:
                        contained = geompy.GetSame(parent, candidate) is not None
                    except:
                        contained = False
                    if contained:
                        break
                if not contained:
                    elements.append(candidate)
        return elements

    def sameShape(self, shape):
        try:
            return geompy.GetSame(self.destin_obj, shape)
        except:
            return None

    def passGroup(self, group):
        elements = self.groupElements(group)
        if not elements:
            return "not"

        type_name = str(elements[0].GetShapeType())
        if type_name not in geompy.ShapeType:
            return "not"

        result = geompy.CreateGroup(
            self.destin_obj, geompy.ShapeType[type_name])
        matched = 0
        for element in elements:
            same = self.sameShape(element)
            if same is None:
                continue
            try:
                sub_id = geompy.GetSubShapeID(self.destin_obj, same)
                geompy.AddObject(result, sub_id)
                matched += 1
            except:
                pass

        if matched == 0:
            return "not"
        geompy.addToStudyInFather(
            self.destin_obj, result, group.GetName())
        return "passed" if matched == len(elements) else "partial"

    def passCompound(self, compound):
        elements = self.compoundElements(compound)
        if not elements:
            return "not"

        matched = []
        matched_ids = set()
        for element in elements:
            same = self.sameShape(element)
            if same is None:
                continue
            try:
                marker = geompy.GetSubShapeID(self.destin_obj, same)
            except:
                marker = id(same)
            if marker not in matched_ids:
                matched.append(same)
                matched_ids.add(marker)

        if not matched:
            return "not"

        result = geompy.MakeCompound(matched)
        geompy.addToStudyInFather(
            self.destin_obj, result, compound.GetName())
        return "passed" if len(matched) == len(elements) else "partial"

    def proceed(self):
        passed = {"Groups": [], "Compounds": []}
        partial = {"Groups": [], "Compounds": []}
        not_passed = {"Groups": [], "Compounds": []}

        try:
            groups_source = geompy.GetGroups(self.source_obj)
        except:
            QMessageBox.critical(None,'Error',"Select a valid source shape first",QMessageBox.Abort)
            return
        try:
            self.destin_obj.GetName()
        except:
            QMessageBox.critical(None,'Error',"Select a valid Destination shape first",QMessageBox.Abort)
            return

        compounds_source = self.childCompounds(
            self.source_obj, groups_source)
        objects = ([("Groups", group) for group in groups_source] +
                   [("Compounds", compound)
                    for compound in compounds_source])
        if not objects:
            QMessageBox.information(
                None, "Information",
                "The source shape has no groups or child compounds.",
                QMessageBox.Ok)
            return

        for index, (kind, obj) in enumerate(objects):
            try:
                status = (self.passGroup(obj) if kind == "Groups"
                          else self.passCompound(obj))
            except:
                status = "not"
            destination = (passed if status == "passed" else
                           partial if status == "partial" else not_passed)
            destination[kind].append(obj.GetName())
            self.progress_bar.setValue(
                int(100 * (index + 1) / len(objects)))

        message = (
            "Groups passed:\n{0}\n\n"
            "Groups partially passed:\n{1}\n\n"
            "Groups not passed:\n{2}\n\n"
            "Compounds passed:\n{3}\n\n"
            "Compounds partially passed:\n{4}\n\n"
            "Compounds not passed:\n{5}"
        ).format(
            passed["Groups"], partial["Groups"], not_passed["Groups"],
            passed["Compounds"], partial["Compounds"],
            not_passed["Compounds"])
        QMessageBox.information(
            None, "Information", message, QMessageBox.Ok)
        salome.sg.updateObjBrowser()
    # cancel function
    def cancel(self):
        self.close()
        d.close()

d = QDockWidget()
d.setWidget(PassGroups())
d.setAttribute(Qt.WA_DeleteOnClose)
d.setWindowFlags(d.windowFlags() | Qt.WindowStaysOnTopHint)
d.setWindowTitle(" Pass Groups and Child Compounds ")
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
