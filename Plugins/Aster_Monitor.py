import matplotlib.pyplot as plt
import glob
from matplotlib import style
import matplotlib.animation as animation

style.use('fivethirtyeight')

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

class MonitorCA(QWidget):
    def __init__(self):
        super(MonitorCA, self).__init__() 
        self.initUI()
    def __del__(self):
        return
    def initUI(self):
        self.l_plot  = QLabel("Plots:")
        self.cb_time = QCheckBox("  Time Step", self)
        self.cb_time.setChecked(Qt.Checked)
        self.cb_residual = QCheckBox("  Residuals", self)
        self.cb_residual.setChecked(Qt.Checked)
        self.cb_contact = QCheckBox("  Conctact", self)
        # Ok buttons:
        self.okbox = QDialogButtonBox(self)
        self.okbox.setOrientation(Qt.Horizontal)
        self.okbox.setStandardButtons(QDialogButtonBox.Cancel | QDialogButtonBox.Ok)
        # Layout:
        layout = QGridLayout()
        layout.addWidget(self.l_plot, 1, 0)
        layout.addWidget(self.cb_time, 2, 0)
        layout.addWidget(self.cb_residual, 3, 0)
        layout.addWidget(self.cb_contact, 4, 0)
        layout.addWidget(self.okbox, 5, 1)
        self.setLayout(layout)
        ### Connectors:
        self.okbox.accepted.connect(self.proceed)
        self.okbox.rejected.connect(self.cancel)
    def extract_data(self):
        file = glob.glob1("/tmp", "*pid*") 
        resi_abs = []
        resi_abs.append(0.0)
        resi_rela = []
        resi_rela.append(0.0)
        h = []
        h.append(0.0)
        h1 = []
        h1.append(0.0)
        intent = 0
        cont_var = []
        cont_var.append(0.0)
        try:
            with open("/tmp/" + str(file[0])) as origin:
                for line in origin:
                    if "|TANGENTE" in line:
                        resi_abs.append(float(line[line.find('|T')-15:line.find('|T')-4]))
                        resi_rela.append(float(line[line.find('|T')-32:line.find('|T')-21]))
                        try:
                            cont_var.append(float(line[line.find('|T')+19:line.find('|T')+26]))
                        except:
                            cont_var.append(0.0)
                        h1.append(h[len(h)-1])
                    if "|ELASTIQUE" in line:
                        resi_abs.append(float(line[line.find('|E')-15:line.find('|E')-4]))
                        resi_rela.append(float(line[line.find('|E')-32:line.find('|E')-21]))
                        try:
                            cont_var.append(float(line[line.find('|T')+19:line.find('|T')+26]))
                        except:
                            cont_var.append(0.0)
                        h1.append(h[len(h)-1])
                    if "Time of computation: " in line or "Instant de calcul: " in line:
                        h.append(float(line[line.find(': ')+1:len(line)]))
                    if "EXECUTION_CODE_ASTER_EXIT" in line:
                        fin = 1
                self.data = [h1,resi_abs,resi_rela,cont_var]
        except:
            self.data = [h1,resi_abs,resi_rela,cont_var]
            #return data
    def interactive_plot(self,i):  
        try:
            # extract data
            data1 = self.extract_data()
            data = self.data
            ## configuration figure 
            for j in range(0,self.cant_graf):
                try:
                    self.ax[j].clear()
                except:
                    self.ax.clear()
            plt.xlabel('Intent')
            #QMessageBox.critical(None,'HEYY',"Unexpected error",QMessageBox.Abort)
            if self.cant_graf == 1:
                if self.Residuals:
                    self.ax.set_ylabel('Residual')
                    self.ax.semilogy(data[1],linestyle='-', color='red')
                    self.ax.semilogy(data[2],linestyle='-', color='blue')
                    self.ax.text(0.95, 0.10, 'Current Absolut Residual: ' + str(data[1][len(data[1])-1]), color='red', verticalalignment='bottom', horizontalalignment='right', transform=self.ax.transAxes, bbox={'facecolor':'white', 'alpha':0.5, 'pad':10})
                    self.ax.text(0.95, 0.20, 'Current Relative Residual: ' + str(data[2][len(data[2])-1]), color='blue', verticalalignment='bottom', horizontalalignment='right', transform=self.ax.transAxes, bbox={'facecolor':'white', 'alpha':0.5, 'pad':10})
                if self.Contact:
                    self.ax.set_ylabel('Contact Convergence')
                    self.ax.plot(data[3],linestyle='-', color='magenta')
                    self.ax.text(0.95, 0.90, 'Current Value: ' + str(data[3][len(data[3])-1]), verticalalignment='bottom', horizontalalignment='right', transform=self.ax.transAxes, bbox={'facecolor':'white', 'alpha':1.0, 'pad':10})
                if self.Time_Step:
                    self.ax.set_ylabel('Time Step')
                    self.ax.plot(data[0],linestyle='-', color='red')
                    self.ax.set_ylim(plt.xlim()[0], data[0][len(data[0])-1]+0.1)
                    self.ax.text(0.95, 0.10, 'Current Time step: ' + str(data[0][len(data[0])-1]), verticalalignment='bottom', horizontalalignment='right', transform=self.ax.transAxes, bbox={'facecolor':'white', 'alpha':1.0, 'pad':10})
            if self.cant_graf == 2:
                if self.Time_Step:
                    self.ax[1].set_ylabel('Time Step')
                    self.ax[1].plot(data[0],linestyle='-', color='red')
                    self.ax[1].set_ylim(plt.xlim()[0], data[0][len(data[0])-1]+0.1)
                    self.ax[1].text(0.95, 0.10, 'Current Time step: ' + str(data[0][len(data[0])-1]), verticalalignment='bottom', horizontalalignment='right', transform=self.ax[1].transAxes, bbox={'facecolor':'white', 'alpha':1.0, 'pad':10})
                    if self.Residuals:
                        self.ax[0].set_ylabel('Residual')
                        self.ax[0].semilogy(data[1],linestyle='-', color='red')
                        self.ax[0].semilogy(data[2],linestyle='-', color='blue')
                        self.ax[0].text(0.95, 0.10, 'Current Absolut Residual: ' + str(data[1][len(data[1])-1]), color='red', verticalalignment='bottom', horizontalalignment='right', transform=self.ax[0].transAxes, bbox={'facecolor':'white', 'alpha':0.5, 'pad':10})
                        self.ax[0].text(0.95, 0.20, 'Current Relative Residual: ' + str(data[2][len(data[2])-1]), color='blue', verticalalignment='bottom', horizontalalignment='right', transform=self.ax[0].transAxes, bbox={'facecolor':'white', 'alpha':0.5, 'pad':10})
                    if self.Contact:
                        self.ax[0].set_ylabel('Contact Convergence')
                        self.ax[0].plot(data[3],linestyle='-', color='magenta')
                        self.ax[0].text(0.95, 0.90, 'Current Value: ' + str(data[3][len(data[3])-1]), verticalalignment='bottom', horizontalalignment='right', transform=self.ax[0].transAxes, bbox={'facecolor':'white', 'alpha':1.0, 'pad':10})
                else:
                    self.ax[0].set_ylabel('Residual')
                    self.ax[0].semilogy(data[1],linestyle='-', color='red')
                    self.ax[0].semilogy(data[2],linestyle='-', color='blue')
                    self.ax[0].text(0.95, 0.10, 'Current Absolut Residual: ' + str(data[1][len(data[1])-1]), color='red', verticalalignment='bottom', horizontalalignment='right', transform=self.ax[0].transAxes, bbox={'facecolor':'white', 'alpha':0.5, 'pad':10})
                    self.ax[0].text(0.95, 0.20, 'Current Relative Residual: ' + str(data[2][len(data[2])-1]), color='blue', verticalalignment='bottom', horizontalalignment='right', transform=self.ax[0].transAxes, bbox={'facecolor':'white', 'alpha':0.5, 'pad':10})
                    self.ax[1].set_ylabel('Contact Convergence')
                    self.ax[1].plot(data[3],linestyle='-', color='magenta')
                    self.ax[1].text(0.95, 0.90, 'Current Value: ' + str(data[3][len(data[3])-1]), verticalalignment='bottom', horizontalalignment='right', transform=self.ax[1].transAxes, bbox={'facecolor':'white', 'alpha':1.0, 'pad':10})
            if self.cant_graf == 3:
                self.ax[2].set_ylabel('Time Step')
                self.ax[2].plot(data[0],linestyle='-', color='red')
                self.ax[2].set_ylim(plt.xlim()[0], data[0][len(data[0])-1]+0.1)
                self.ax[2].text(0.95, 0.10, 'Current Time step: ' + str(data[0][len(data[0])-1]), verticalalignment='bottom', horizontalalignment='right', transform=self.ax[2].transAxes, bbox={'facecolor':'white', 'alpha':1.0, 'pad':10})
                self.ax[1].set_ylabel('Residual')
                self.ax[1].semilogy(data[1],linestyle='-', color='red')
                self.ax[1].semilogy(data[2],linestyle='-', color='blue')
                self.ax[1].text(0.95, 0.10, 'Current Absolut Residual: ' + str(data[1][len(data[1])-1]), color='red', verticalalignment='bottom', horizontalalignment='right', transform=self.ax[1].transAxes, bbox={'facecolor':'white', 'alpha':0.5, 'pad':10})
                self.ax[1].text(0.95, 0.20, 'Current Relative Residual: ' + str(data[2][len(data[2])-1]), color='blue', verticalalignment='bottom', horizontalalignment='right', transform=self.ax[1].transAxes, bbox={'facecolor':'white', 'alpha':0.5, 'pad':10})
                self.ax[0].set_ylabel('Contact Convergence')
                self.ax[0].plot(data[3],linestyle='-', color='magenta')
                self.ax[0].text(0.95, 0.90, 'Current Value: ' + str(data[3][len(data[3])-1]), verticalalignment='bottom', horizontalalignment='right', transform=self.ax[0].transAxes, bbox={'facecolor':'white', 'alpha':1.0, 'pad':10})
            # Configure Plots
            plt.minorticks_on()
            plt.grid(True,which='both', axis='y')
            plt.grid(True,which='major', axis='x')
            # Information
        except:
            plt.title('Simulation Finish',bbox={'facecolor':'green', 'alpha':1.0, 'pad':10})
    def proceed(self):
        try:
            self.file = glob.glob1("/tmp", "*pid*")
            if self.cb_residual.isChecked():
                self.Residuals = 1
            else:
                self.Residuals = 0
            if self.cb_contact.isChecked():
                self.Contact = 1
            else:
                self.Contact = 0
            if self.cb_time.isChecked():
                self.Time_Step = 1
            else:
                self.Time_Step = 0
            self.cant_graf = self.Residuals + self.Contact + self.Time_Step
            fig, self.ax = plt.subplots(self.cant_graf,1,sharey=False, sharex=True)
            plots = animation.FuncAnimation(fig, self.interactive_plot, interval=1000)
            plt.show()
            self.close()
            d.close()
        except:
            QMessageBox.critical(None,'Error 1',"Unexpected error",QMessageBox.Abort)
    # cancel function
    def cancel(self):
        self.close()
        d.close()

d = QDockWidget()
d.setWidget(MonitorCA())
d.setAttribute(Qt.WA_DeleteOnClose)
d.setWindowFlags(d.windowFlags() | QtCore.Qt.WindowStaysOnTopHint)
d.setWindowTitle(" Plots Code_Aster Mechanical ")
d.setGeometry(600, 300, 200, 150)
d.show()
