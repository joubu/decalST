#!/bin/python
# -*- coding: utf-8 -*-

from PyQt4.QtGui import *
from PyQt4.QtCore import *
from Ui_MainWindow import Ui_MainWindow
import signal
import datetime
import os
import re
import sys

# Quit sur CTRL-C
signal.signal(signal.SIGINT, signal.SIG_DFL)

REGEXP = "(..):(..):(..),(...) --> (..):(..):(..),(...)"


def format_ms(ms):
    if ms < 10:
        return "00%s" % ms
    elif ms < 100:
        return "0%s" % ms
    else:
        return str(ms)


def convert(filepath, delta, format_):
    new_srt = []
    fd = open(filepath, 'r')
    for line in fd.readlines():
        matches = re.compile(format_).findall(line)
        new_line = line
        if len(matches) != 0:
            b_h = int(matches[0][0])
            b_m = int(matches[0][1])
            b_s = int(matches[0][2])
            b_ms = int(matches[0][3])
            e_h = int(matches[0][4])
            e_m = int(matches[0][5])
            e_s = int(matches[0][6])
            e_ms = int(matches[0][7])
            b_dt = datetime.time(hour=b_h, minute=b_m, second=b_s, microsecond=b_ms)
            e_dt = datetime.time(hour=e_h, minute=e_m, second=e_s, microsecond=e_ms)

            new_b_dt = datetime.datetime.combine(datetime.date.today(), datetime.time(b_h, b_m,
                b_s, b_ms*1000)) + delta
            new_e_dt = datetime.datetime.combine(datetime.date.today(), datetime.time(e_h, e_m,
                e_s, e_ms*1000)) + delta

            new_line = "%s --> %s" % (new_b_dt.strftime("%H:%M:%S,") +
                    format_ms(new_b_dt.microsecond/1000), new_e_dt.strftime("%H:%M:%S,") +
                    format_ms(new_e_dt.microsecond/1000))
        
        new_srt.append(new_line)
    fd.close()
        
    return new_srt

class DecalST(QApplication):
    def __init__(self, *args):
        QApplication.__init__(self, *args)

class MainWindow(QMainWindow):

    def __init__(self):
        QMainWindow.__init__(self)
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.dir = os.path.expanduser("~")
        self.filepath = ""
        self.ui.lineEditFormat.setText(REGEXP)
        self.ui.lineEditPath.setText(self.filepath)

    @pyqtSignature("")
    def on_pushButtonBrowse_clicked(self):
        filepath = QFileDialog.getOpenFileName(self, 
                QApplication.translate("Main", "Ouvrir", None,
                QApplication.UnicodeUTF8),
                self.dir,
                "Sous-titres .srt (*.srt)")

        if not filepath:
            return

        self.dir = os.path.dirname(str(filepath))
        self.filepath = filepath
        self.ui.lineEditPath.setText(filepath)

    @pyqtSignature("")
    def on_pushButtonLaunch_clicked(self):
        self.ui.textEditResult.clear()
        sign = self.ui.comboBoxSign.itemText(self.ui.comboBoxSign.currentIndex())
        decal_m = self.ui.spinBoxM.value()
        decal_s = self.ui.spinBoxS.value()
        decal_ms = self.ui.spinBoxMS.value()
        format_ = str(self.ui.lineEditFormat.text())
        filepath = str(self.ui.lineEditPath.text())

        if not filepath:
            return

        if sign == "+":
            delta = datetime.timedelta(minutes=decal_m, seconds=decal_s,
                    microseconds=decal_ms*1000)
        else:
            delta = datetime.timedelta(minutes=-decal_m, seconds=-decal_s,
                    microseconds=-decal_ms*1000)
        new_lines = convert(filepath, delta, format_)
        for l in new_lines:
            self.ui.textEditResult.appendPlainText(l.replace("\r\n", "").replace("\n", ""))

        vScrollBar = self.ui.textEditResult.verticalScrollBar()
        vScrollBar.setSliderPosition(0)

    @pyqtSignature("")
    def on_pushButtonCopy_clicked(self):
        self.ui.textEditResult.selectAll()
        self.ui.textEditResult.copy()

    @pyqtSignature("")
    def on_pushButtonOverwrite_clicked(self):
        try:
            os.rename(self.filepath, self.filepath+'.org')
            fd = open(self.filepath, 'w')
            fd.write(self.ui.textEditResult.toPlainText())
            fd.close()
            self.ui.statusbar.showMessage(u"Le fichier a bien été écrasé. Une sauvegarde a été effectuée")
        except Exception, e:
            self.ui.statusbar.showMessage(u"Le fichier n'a pas été bien généré. Voir la sortie d'erreur")
        

if __name__ == "__main__":
    app = DecalST(sys.argv)
    
    window = MainWindow()
    app.ui = window
    window.show()
    
    ret = app.exec_()
    app.closeAllWindows()
    window = None # FIX Segmentation Fault
    sys.exit(ret)
