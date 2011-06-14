#!/bin/python
# -*- coding: utf-8 -*-

from PyQt4.QtGui import *
from PyQt4.QtCore import *
from Ui_MainWindow import Ui_MainWindow
import signal
import datetime
import time
import os
import re
import sys

# Quit sur CTRL-C
signal.signal(signal.SIGINT, signal.SIG_DFL)

REGEXP = "(..):(..):(..),(...) --> (..):(..):(..),(...)"

ACTION_SHIFT = 0
ACTION_CONCAT = 1
ACTION_SPLIT = 2

def format_ms(ms):
    if ms < 10:
        return "00%s" % ms
    elif ms < 100:
        return "0%s" % ms
    else:
        return str(ms)

def format_delta(delta):
    return \
        time.strftime("%H:%M:%S,", time.gmtime(delta.seconds)) \
            + \
        format_ms(delta.microseconds/1000)


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

            new_b_delta = get_delta(b_h, b_m, b_s, b_ms) + delta
            new_e_delta = get_delta(e_h, e_m, e_s, e_ms) + delta

            new_line = "%s --> %s" % (
                    format_delta(new_b_delta), 
                    format_delta(new_e_delta)
                )
        
        new_srt.append(new_line)
    fd.close()
    return new_srt

def get_delta(decal_h, decal_m, decal_s, decal_ms, sign="+"):
    if sign == "+":
        return datetime.timedelta(hours=decal_h, minutes=decal_m, seconds=decal_s,
                microseconds=decal_ms*1000)
    else:
        return datetime.timedelta(hours=decal_h, minutes=-decal_m, seconds=-decal_s,
                microseconds=-decal_ms*1000)

def get_first_time(filepath, format_):
    fd = open(filepath, 'r')
    for line in fd.readlines():
        matches = re.compile(format_).findall(line)
        if len(matches) != 0:
            b_h = int(matches[0][0])
            b_m = int(matches[0][1])
            b_s = int(matches[0][2])
            b_ms = int(matches[0][3])

            return get_delta(b_h, b_m, b_s, b_ms)

    return get_delta(0, 0, 0, 0)

class DecalST(QApplication):
    def __init__(self, *args):
        QApplication.__init__(self, *args)

class MainWindow(QMainWindow):

    def __init__(self, app):
        QMainWindow.__init__(self)
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.app = app
        self.dir = os.path.expanduser("~")
        self.filepathShiftIn   = ""
        self.filepathConcatIn1 = ""
        self.filepathConcatIn2 = ""
        self.filepathConcatOut = ""
        self.filepathSplitIn   = ""
        self.filepathSplitOut1 = ""
        self.filepathSplitOut2 = ""
        self.ui.lineEditFormat.setText(REGEXP)
        self.current_action = self.ui.tabs.currentIndex()
        self.ui.lineEditPathShiftIn.setText(self.filepathShiftIn)
        self.ui.lineEditPathConcatIn1.setText(self.filepathConcatIn1)
        self.ui.lineEditPathConcatIn2.setText(self.filepathConcatIn2)
        self.ui.lineEditPathSplitIn.setText(self.filepathSplitIn)

    def browse(self, lineEdit):
        filepath = QFileDialog.getOpenFileName(self, 
                QApplication.translate("Main", "Ouvrir", None,
                QApplication.UnicodeUTF8),
                self.dir,
                "Sous-titres .srt (*.srt)")

        if not filepath:
            return

        self.dir = os.path.dirname(str(filepath))
        lineEdit.setText(filepath)
        return filepath


    def launch_shift(self):
        self.ui.textEditShiftOut.clear()
        sign = self.ui.comboBoxSignShift.itemText(self.ui.comboBoxSignShift.currentIndex())
        h = self.ui.spinBoxShiftH.value()
        m = self.ui.spinBoxShiftM.value()
        s = self.ui.spinBoxShiftS.value()
        ms = self.ui.spinBoxShiftMS.value()
        format_ = str(self.ui.lineEditFormat.text())
        filepath = str(self.ui.lineEditPathShiftIn.text())

        if not filepath:
            return

        if self.ui.radioButtonBeginAt.isChecked():
            delta = get_delta(h, m, s, ms, "+")
            first = get_first_time(filepath, format_)
            delta = delta - first
        else:
            delta = get_delta(h, m, s, ms, sign)

        new_lines = convert(filepath, delta, format_)
        new_lines = "\n".join(line.replace("\r\n", "").replace("\n", "")
                for line in new_lines)
        self.ui.textEditShiftOut.appendPlainText(new_lines)

        cursor = self.ui.textEditShiftOut.cursorForPosition(QPoint(0,0))
        cursor.setPosition(QTextCursor.Start);
        self.ui.textEditShiftOut.setTextCursor(cursor);
        vScrollBar = self.ui.textEditShiftOut.verticalScrollBar()
        vScrollBar.setSliderPosition(0)

    def launch_concat(self):
        self.ui.textEditConcatOut.clear()
        sign = self.ui.comboBoxSignConcat.itemText(self.ui.comboBoxSignConcat.currentIndex())
        decal_h = self.ui.spinBoxConcatH.value()
        decal_m = self.ui.spinBoxConcatM.value()
        decal_s = self.ui.spinBoxConcatS.value()
        decal_ms = self.ui.spinBoxConcatMS.value()
        format_ = str(self.ui.lineEditFormat.text())
        filepathIn1 = str(self.ui.lineEditPathConcatIn1.text())
        filepathIn2 = str(self.ui.lineEditPathConcatIn2.text())

        if not filepathIn1 or not filepathIn2:
            return

        input_delta = get_delta(decal_h, decal_m, decal_s, decal_ms, sign)

        fd = open(filepathIn1, 'r')
        lines = fd.readlines()
        fd.close()
        last_lines = lines[len(lines)-10:len(lines)]
        for l in lines:
            self.ui.textEditConcatOut.appendPlainText(l.replace("\r\n", "").replace("\n", ""))

        last_delta = None
        for l in last_lines:
            matches = re.compile(format_).findall(l)
            if len(matches) != 0:
                
                e_h = int(matches[0][4])
                e_m = int(matches[0][5])
                e_s = int(matches[0][6])
                e_ms = int(matches[0][7])
                last_delta = get_delta(e_h, e_m, e_s, e_ms)
        
        total_delta = last_delta + input_delta
        new_lines2 = convert(filepathIn2, total_delta, format_)

        for l in new_lines2:
            self.ui.textEditConcatOut.appendPlainText(l.replace("\r\n", "").replace("\n", ""))

        vScrollBar = self.ui.textEditConcatOut.verticalScrollBar()
        vScrollBar.setSliderPosition(0)

    def launch_split(self):
        self.ui.textEditSplitOut1.clear()
        self.ui.textEditSplitOut2.clear()
        decal_h = self.ui.spinBoxSplitH.value()
        decal_m = self.ui.spinBoxSplitM.value()
        decal_s = self.ui.spinBoxSplitS.value()
        decal_ms = self.ui.spinBoxSplitMS.value()
        format_ = str(self.ui.lineEditFormat.text())
        filepathIn = str(self.ui.lineEditPathSplitIn.text())

        if not filepathIn:
            return

        split_delta = get_delta(decal_h, decal_m, decal_s, decal_ms)

        fd = open(filepathIn, 'r')
        lines = fd.readlines()
        fd.close()
        output = self.ui.textEditSplitOut1
        last_delta = get_delta(0, 0, 0, 0)
        for l in lines:
            matches = re.compile(format_).findall(l)
            new_line = l
            new_b_dt = 0
            new_e_dt = 0
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

                current_delta = get_delta(b_h, b_m, b_s, b_ms)
                zero_delta = get_delta(0, 0, 0, 0)

                if split_delta - current_delta > zero_delta:
                    new_b_delta = get_delta(b_h, b_m, b_s, b_ms)
                    new_e_delta = get_delta(e_h, e_m, e_s, e_ms)
                    last_delta = new_b_delta

                    new_line = "%s --> %s" % (
                            format_delta(new_b_delta), 
                            format_delta(new_e_delta)
                        )

                else:
                    output = self.ui.textEditSplitOut2

                    new_b_delta = get_delta(b_h, b_m, b_s, b_ms) - last_delta
                    new_e_delta = get_delta(e_h, e_m, e_s, e_ms) - last_delta

                    new_line = "%s --> %s" % (
                            format_delta(new_b_delta), 
                            format_delta(new_e_delta)
                        )

            output.appendPlainText(new_line.replace("\r\n", "\n").replace("\n", ""))


        output1 = self.ui.textEditSplitOut1.toPlainText()
        output2 = self.ui.textEditSplitOut2.toPlainText()

        # Récupération de la dernière ligne (correspondant au numéro)
        # pour la rajouter en début de 2è fichier
        cur1 = self.ui.textEditSplitOut1.cursorForPosition(QPoint(0,0))
        cur2 = self.ui.textEditSplitOut2.cursorForPosition(QPoint(0,0))
        cur1.movePosition(QTextCursor.End)
        cur2.movePosition(QTextCursor.Start)
        cur1.select(QTextCursor.LineUnderCursor)
        last1 = cur1.selectedText() + "\n"
        cur1.removeSelectedText()
        cur2.insertText(last1)
        

        vScrollBar2 = self.ui.textEditSplitOut2.verticalScrollBar()
        vScrollBar2.setSliderPosition(0)

    @pyqtSlot(str)
    def on_lineEditPathConcatIn1_textChanged(self, path):
        fd = open(path)
        for l in fd.readlines():
            self.ui.textEditConcatIn1.appendPlainText(l.replace("\r\n", "").replace("\n", ""))
        fd.close()


    @pyqtSlot(str)
    def on_lineEditPathConcatIn2_textChanged(self, path):
        fd = open(path)
        for l in fd.readlines():
            self.ui.textEditConcatIn2.appendPlainText(l.replace("\r\n", "").replace("\n", ""))
        fd.close()

    @pyqtSlot(str)
    def on_lineEditPathConcatOut_textChanged(self, path):
        self.filepathConcatOut = path

    @pyqtSlot(str)
    def on_lineEditPathSplitIn_textChanged(self, path):
        fd = open(path)
        for l in fd.readlines():
            self.ui.textEditSplitIn.appendPlainText(l.replace("\r\n", "").replace("\n", ""))
        fd.close()

    @pyqtSlot(str)
    def on_lineEditPathSplitOut1_textChanged(self, path):
        self.filepathSplitOut1 = path

    @pyqtSlot(str)
    def on_lineEditPathSplitOut2_textChanged(self, path):
        self.filepathSplitOut2 = path

    @pyqtSlot()
    def on_pushButtonBrowseShiftIn_clicked(self):
        self.filepathShiftIn = self.browse(self.ui.lineEditPathShiftIn)
    @pyqtSlot()
    def on_pushButtonBrowseConcatIn1_clicked(self):
        self.filepathConcatIn1 = self.browse(self.ui.lineEditPathConcatIn1)
    @pyqtSlot()
    def on_pushButtonBrowseConcatIn2_clicked(self):
        self.filepathConcatIn2 = self.browse(self.ui.lineEditPathConcatIn2)
    @pyqtSlot()
    def on_pushButtonBrowseConcatOut_clicked(self):
        self.filepathConcatOut = self.browse(self.ui.lineEditPathConcatOut)
    @pyqtSlot()
    def on_pushButtonBrowseSplitIn_clicked(self):
        self.filepathSplitIn = self.browse(self.ui.lineEditPathSplitIn)
    @pyqtSlot()
    def on_pushButtonBrowseSplitOut1_clicked(self):
        self.filepathSplitOut1 = self.browse(self.ui.lineEditPathSplitOut1)
    @pyqtSlot()
    def on_pushButtonBrowseSplitOut2_clicked(self):
        self.filepathSplitOut2 = self.browse(self.ui.lineEditPathSplitOut2)

    @pyqtSlot()
    def on_pushButtonLaunch_clicked(self):
        if self.current_action == ACTION_SHIFT:
            self.launch_shift()
        elif self.current_action == ACTION_CONCAT:
            self.launch_concat()
        elif self.current_action == ACTION_SPLIT:
            self.launch_split()
        else:
            print "Pas d'action correspondante pour %s" % self.current_action

    @pyqtSlot(int)
    def on_tabs_currentChanged(self, num):
        self.current_action = num

    @pyqtSlot()
    def on_pushButtonCopy_clicked(self):
        if self.current_action == ACTION_SHIFT:
            self.app.clipboard().clear()
            self.ui.textEditShiftOut.selectAll()
            self.app.clipboard().setText(self.ui.textEditShiftOut.toPlainText())
        elif self.current_action == ACTION_CONCAT:
            self.app.clipboard().clear()
            self.ui.textEditConcatOut.selectAll()
            self.app.clipboard().setText(self.ui.textEditConcatOut.toPlainText())
        elif self.current_action == ACTION_SPLIT:
            self.app.clipboard().clear()
            self.ui.textEditSplitOut1.selectAll()
            self.ui.textEditSplitOut2.selectAll()
            self.app.clipboard().setText(
                    self.ui.textEditSplitOut1.toPlainText() + self.ui.textEditSplitOut2.toPlainText()
                )
        else:
            print "Pas d'action correspondante pour %s" % self.current_action


    @pyqtSlot()
    def on_pushButtonOverwrite_clicked(self):
        try:
            if self.current_action == ACTION_SHIFT:
                if not self.filepathShiftIn:
                    return
                os.rename(self.filepathShiftIn, self.filepathShiftIn+'.org')
                fd = open(self.filepathShiftIn, 'w')
                fd.write(self.ui.textEditShiftOut.toPlainText())
                fd.close()
                self.ui.statusbar.showMessage(u"Le fichier a bien été écrasé. Une sauvegarde a été effectuée")
            elif self.current_action == ACTION_CONCAT:
                if not self.filepathConcatOut:
                    return
                fd = open(self.filepathConcatOut, 'w')
                fd.write(self.ui.textEditConcatOut.toPlainText())
                fd.close()
                self.ui.statusbar.showMessage(u"Le fichier a bien été écrit.")
            elif self.current_action == ACTION_SPLIT:
                if not self.filepathSplitOut1 or not self.filepathSplitOut2:
                    return
                fd = open(self.filepathSplitOut1, 'w')
                fd.write(self.ui.textEditSplitOut1.toPlainText())
                fd.close()

                fd = open(self.filepathSplitOut2, 'w')
                fd.write(self.ui.textEditSplitOut2.toPlainText())
                fd.close()

                self.ui.statusbar.showMessage(u"Les fichiers ont bien été écrit.")

            else:
                print "Pas d'action correspondante pour %s" % self.current_action

        except Exception, e:
            print e
            self.ui.statusbar.showMessage(u"Le fichier n'a pas été bien généré. Voir la sortie d'erreur")
        

if __name__ == "__main__":
    app = DecalST(sys.argv)
    
    window = MainWindow(app)
    app.ui = window
    window.show()
    
    ret = app.exec_()
    app.closeAllWindows()
    window = None # FIX Segmentation Fault
    sys.exit(ret)
