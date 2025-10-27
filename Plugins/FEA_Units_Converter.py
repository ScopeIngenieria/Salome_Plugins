from __future__ import annotations
from qtsalome import *
import math
import sys
from dataclasses import dataclass

# ----------------------------- Constants -------------------------------- #
INCH_TO_M = 0.0254            # exact
FOOT_TO_M = 0.3048            # exact
MM_TO_M   = 0.001             # exact
LBM_TO_KG = 0.45359237        # exact
SLUG_TO_KG = 14.59390294      # derived
SNAIL_LBM  = 386.2            # as requested (~386.0886 exact)
SNAIL_TO_KG = SNAIL_LBM * LBM_TO_KG

# ----------------------------- Unit Systems ----------------------------- #

@dataclass(frozen=True)
class UnitSystem:
    name: str
    # Base-to-SI factors: SI base is m, kg, s. Temperature handled via methods.
    L_to_m: float
    M_to_kg: float
    T_to_s: float
    # Absolute temperature base for this system ('K' or 'F')
    temp_abs: str
    # Temperature difference scaling to Kelvin (e.g., Δ°F * 5/9 → K)
    dtheta_to_K: float
    # Display symbols
    sym_L: str
    sym_M: str
    sym_F: str
    sym_T: str
    sym_Theta_abs: str
    sym_Theta_delta: str
    # Temperature conversions absolute
    def abs_to_K(self, value: float) -> float:
        if self.temp_abs == 'K':
            return value
        elif self.temp_abs == 'F':
            return (value - 32.0) * 5.0/9.0 + 273.15
        else:
            raise ValueError(f"Unsupported absolute temperature base: {self.temp_abs}")
    def K_to_abs(self, K: float) -> float:
        if self.temp_abs == 'K':
            return K
        elif self.temp_abs == 'F':
            return (K - 273.15) * 9.0/5.0 + 32.0
        else:
            raise ValueError(f"Unsupported absolute temperature base: {self.temp_abs}")

SYSTEMS = {
    'SI, Standard': UnitSystem(
        name='SI, Standard', L_to_m=1.0, M_to_kg=1.0, T_to_s=1.0,
        temp_abs='K', dtheta_to_K=1.0,
        sym_L='m', sym_M='kg', sym_F='N', sym_T='s', sym_Theta_abs='K', sym_Theta_delta='K'),
    'SI, mm': UnitSystem(
        name='SI, mm', L_to_m=MM_TO_M, M_to_kg=1000.0, T_to_s=1.0,  # 1 T = 1000 kg
        temp_abs='K', dtheta_to_K=1.0,
        sym_L='mm', sym_M='T', sym_F='N', sym_T='s', sym_Theta_abs='K', sym_Theta_delta='K'),
    'Imperial, inches': UnitSystem(
        name='Imperial, inches', L_to_m=INCH_TO_M, M_to_kg=SNAIL_TO_KG, T_to_s=1.0,
        temp_abs='F', dtheta_to_K=5.0/9.0,  # Δ°F → K
        sym_L='in', sym_M='snail', sym_F='lbf', sym_T='s', sym_Theta_abs='°F', sym_Theta_delta='°R'),
    'Imperial, feet': UnitSystem(
        name='Imperial, feet', L_to_m=FOOT_TO_M, M_to_kg=SLUG_TO_KG, T_to_s=1.0,
        temp_abs='F', dtheta_to_K=5.0/9.0,
        sym_L='ft', sym_M='slug', sym_F='lbf', sym_T='s', sym_Theta_abs='°F', sym_Theta_delta='°R'),
}

# ----------------------------- Quantities ------------------------------- #
QUANTITIES = [
    'Force', 'Mass', 'Length', 'Pressure', 'Acceleration', 'Density',
    'Energy', 'Power', 'Temperature', 'Heat Flux', 'Specific Heat',
    'Conductivity', 'Convection'
]

# Pretty unit string generator using base symbols

def unit_string(sys: UnitSystem, quantity: str, is_delta_temp: bool) -> str:
    L, M, F, T, ThtA, ThtD = sys.sym_L, sys.sym_M, sys.sym_F, sys.sym_T, sys.sym_Theta_abs, sys.sym_Theta_delta
    def frac(num_parts, den_parts):
        num = '·'.join(num_parts) if num_parts else '1'
        den = '·'.join(den_parts)
        return f"{num}/{den}" if den_parts else num
    if quantity == 'Force':
        return F
    if quantity == 'Mass':
        return M
    if quantity == 'Length':
        return L
    if quantity == 'Pressure':
        return frac([F], [f"{L}^2"])  # F/L^2
    if quantity == 'Acceleration':
        return frac([L], [f"{T}^2"])  # L/s^2
    if quantity == 'Density':
        return frac([M], [f"{L}^3"])  # M/L^3
    if quantity == 'Energy':
        return f"{F}·{L}"            # F·L  (e.g., N·m, lbf·ft)
    if quantity == 'Power':
        return frac([F, L], [T])      # F·L/s
    if quantity == 'Heat Flux':
        return frac([F, L], [T, f"{L}^2"])  # (F·L)/ (s·L^2) = F/(s·L)
    if quantity == 'Specific Heat':
        theta = ThtD if is_delta_temp else ThtA
        return frac([F, L], [M, theta])      # (F·L)/(M·Θ)
    if quantity == 'Conductivity':
        theta = ThtD if is_delta_temp else ThtA
        return frac([F, L], [T, L, theta])   # (F·L)/(s·L·Θ) = F/(s·Θ)
    if quantity == 'Convection':
        theta = ThtD if is_delta_temp else ThtA
        return frac([F, L], [T, f"{L}^2", theta])  # F/(s·L^2·Θ)
    if quantity == 'Temperature':
        return (ThtD if is_delta_temp else ThtA)
    return ''

# Core conversion logic via dimensional analysis
DIM_EXPS = {
    'Mass':          (1, 0, 0, 0),
    'Length':        (0, 1, 0, 0),
    'Force':         (1, 1, -2, 0),
    'Pressure':      (1, -1, -2, 0),
    'Acceleration':  (0, 1, -2, 0),
    'Density':       (1, -3, 0, 0),
    'Energy':        (1, 2, -2, 0),
    'Power':         (1, 2, -3, 0),
    'Heat Flux':     (1, 0, -3, 0),
    'Specific Heat': (-1, 2, -2, -1),
    'Conductivity':  (1, 1, -3, -1),
    'Convection':    (1, 0, -3, -1),
}


def factor_between(frm: UnitSystem, to: UnitSystem, quantity: str, is_delta_temp: bool=False) -> float:
    if quantity == 'Temperature':
        if is_delta_temp:
            return frm.dtheta_to_K / to.dtheta_to_K
        # absolute temp: multiplicative scale (K↔°F) around Δ units
        if frm.temp_abs == to.temp_abs:
            return 1.0
        return (9.0/5.0) if (frm.temp_abs == 'K' and to.temp_abs == 'F') else (5.0/9.0)
    M, L, T, TH = DIM_EXPS[quantity]
    rL = frm.L_to_m / to.L_to_m
    rM = frm.M_to_kg / to.M_to_kg
    rT = frm.T_to_s / to.T_to_s
    rTH = (frm.dtheta_to_K / to.dtheta_to_K) if TH != 0 else 1.0
    return (rM**M) * (rL**L) * (rT**T) * (rTH**TH)


def convert_value(frm: UnitSystem, to: UnitSystem, quantity: str, value: float, is_delta_temp: bool=False) -> float:
    if quantity == 'Temperature':
        if is_delta_temp:
            return value * factor_between(frm, to, quantity, True)
        K = frm.abs_to_K(value)
        return to.K_to_abs(K)
    return value * factor_between(frm, to, quantity, False)

# ------------------------------ GUI Layer ------------------------------- #

class UnitConverterDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Unit Converter")
        self.setMinimumWidth(560)
        self.setWindowModality(Qt.NonModal)
        self._build_ui()
        self._connect()
        self._on_quantity_changed(self.quantity_cb.currentText())
        self._update_output()
    #
    def _build_ui(self):
        self.quantity_cb = QComboBox(); self.quantity_cb.addItems(QUANTITIES)
        self.deltaT_chk = QCheckBox("ΔT (difference)")
        self.deltaT_chk.setToolTip("Use temperature-difference conversion (no offset)")
        self.deltaT_chk.setEnabled(False)
        self.from_cb = QComboBox(); self.from_cb.addItems(SYSTEMS.keys())
        self.to_cb   = QComboBox(); self.to_cb.addItems(SYSTEMS.keys()); self.to_cb.setCurrentIndex(1)
        # Show unit strings per system and quantity
        self.from_unit_lbl = QLabel("—")
        self.to_unit_lbl   = QLabel("—")
        for lbl in (self.from_unit_lbl, self.to_unit_lbl):
            lbl.setStyleSheet("color: gray")
        # Input accepts scientific notation
        self.input_le = QLineEdit()
        self.input_le.setPlaceholderText("Enter value (supports 1e6, 50e-3, etc.)")
        self.input_le.setText("1")
        self.out_val_le = QLineEdit(); self.out_val_le.setReadOnly(True)
        self.factor_le  = QLineEdit(); self.factor_le.setReadOnly(True)
        self.copy_val_btn = QPushButton("Copy value")
        self.copy_fac_btn = QPushButton("Copy factor")
        self.swap_btn = QPushButton("⇄ Swap systems")
        grid = QGridLayout(); row = 0
        grid.addWidget(QLabel("Quantity"), row, 0)
        grid.addWidget(self.quantity_cb, row, 1)
        grid.addWidget(self.deltaT_chk, row, 2)
        row += 1
        grid.addWidget(QLabel("From"), row, 0)
        grid.addWidget(self.from_cb, row, 1)
        grid.addWidget(self.from_unit_lbl, row, 2)
        row += 1
        grid.addWidget(QLabel("To"), row, 0)
        grid.addWidget(self.to_cb, row, 1)
        grid.addWidget(self.to_unit_lbl, row, 2)
        row += 1
        grid.addWidget(self.swap_btn, row, 1, 1, 2)
        row += 1
        grid.addWidget(QLabel("Input value"), row, 0)
        grid.addWidget(self.input_le, row, 1, 1, 2)
        row += 1
        grid.addWidget(QLabel("Converted value"), row, 0)
        grid.addWidget(self.out_val_le, row, 1, 1, 2)
        row += 1
        grid.addWidget(QLabel("Multiplicative factor"), row, 0)
        grid.addWidget(self.factor_le, row, 1, 1, 2)
        row += 1
        h = QHBoxLayout()
        h.addWidget(self.copy_val_btn)
        h.addWidget(self.copy_fac_btn)
        h.addStretch(1)
        outer = QVBoxLayout(self)
        outer.addLayout(grid)
        outer.addSpacing(6)
        outer.addLayout(h)
    #
    def _connect(self):
        self.quantity_cb.currentTextChanged.connect(self._on_quantity_changed)
        self.from_cb.currentIndexChanged.connect(self._update_output)
        self.to_cb.currentIndexChanged.connect(self._update_output)
        self.deltaT_chk.toggled.connect(self._update_output)
        self.input_le.textChanged.connect(self._update_output)
        self.swap_btn.clicked.connect(self._swap_systems)
        self.copy_val_btn.clicked.connect(lambda: QApplication.clipboard().setText(self.out_val_le.text()))
        self.copy_fac_btn.clicked.connect(lambda: QApplication.clipboard().setText(self.factor_le.text()))
    #
    def _on_quantity_changed(self, qty: str):
        self.deltaT_chk.setEnabled(qty == 'Temperature')
        self._update_unit_labels()
        self._update_output()
    #
    def _swap_systems(self):
        a, b = self.from_cb.currentIndex(), self.to_cb.currentIndex()
        self.from_cb.setCurrentIndex(b)
        self.to_cb.setCurrentIndex(a)
        self._update_output()
    #
    def _current(self):
        qty = self.quantity_cb.currentText()
        frm = SYSTEMS[self.from_cb.currentText()]
        to  = SYSTEMS[self.to_cb.currentText()]
        txt = self.input_le.text().strip()
        is_dT = self.deltaT_chk.isChecked()
        # parse scientific notation safely
        try:
            val = float(txt) if txt else 0.0
            ok = True
        except Exception:
            val = 0.0
            ok = False
        return qty, frm, to, val, is_dT, ok
    #
    def _fmt(self, x: float) -> str:
        if x == 0.0:
            return "0"
        return ("% .12g" % x).strip()
    #
    def _update_unit_labels(self):
        qty = self.quantity_cb.currentText()
        is_dT = self.deltaT_chk.isChecked()
        frm = SYSTEMS[self.from_cb.currentText()]
        to  = SYSTEMS[self.to_cb.currentText()]
        self.from_unit_lbl.setText(unit_string(frm, qty, is_dT))
        self.to_unit_lbl.setText(unit_string(to, qty, is_dT))
    #
    def _update_output(self):
        self._update_unit_labels()
        qty, frm, to, val, is_dT, ok = self._current()
        pal = self.input_le.palette()
        if not ok:
            pal.setColor(QPalette.Base, QColor('#ffe6e6'))
            self.input_le.setPalette(pal)
            self.out_val_le.setText("Invalid input")
            self.factor_le.setText("—")
            return
        else:
            pal.setColor(QPalette.Base, QColor('white'))
            self.input_le.setPalette(pal)
        try:
            out = convert_value(frm, to, qty, val, is_delta_temp=is_dT)
            fac = factor_between(frm, to, qty, is_delta_temp=is_dT)
            self.out_val_le.setText(self._fmt(out))
            self.factor_le.setText(self._fmt(fac))
        except Exception:
            self.out_val_le.setText("ERROR")
            self.factor_le.setText("ERROR")

# ------------------------------ Entrypoint ------------------------------ #

def show_dialog():
    app = QApplication.instance() or QApplication(sys.argv)
    dlg = UnitConverterDialog(); dlg.show()
    if 'salome' in sys.modules:
        return dlg
    else:
        return app.exec_()

if __name__ == '__main__':
    show_dialog()
