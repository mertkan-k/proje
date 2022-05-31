from sys import *
from PyQt5.QtWidgets import *
from PyQt5.QtGui import QIcon, QPixmap, QColor, QImage, QTextFormat, QPainter
from PyQt5.QtCore import pyqtSlot, Qt, pyqtSignal, QTimer, QRect, QSize
import cv2, traceback
from datetime import datetime
from time import sleep
import threading

class App(QWidget):

	class QLineNumberArea(QWidget):
		def __init__(self, editor):
			super().__init__(editor)
			self.codeEditor = editor

		def sizeHint(self):
			return QSize(self.editor.lineNumberAreaWidth(), 0)

		def paintEvent(self, event):
			self.codeEditor.lineNumberAreaPaintEvent(event)

	class QCodeEditor(QPlainTextEdit):
		def __init__(self, parent=None):
			super().__init__(parent)
			self.lineNumberArea = App.QLineNumberArea(self)
			self.blockCountChanged.connect(self.updateLineNumberAreaWidth)
			self.updateRequest.connect(self.updateLineNumberArea)
			self.cursorPositionChanged.connect(self.highlightCurrentLine)
			self.updateLineNumberAreaWidth(0)

		def lineNumberAreaWidth(self):
			digits = 1
			max_value = max(1, self.blockCount())
			while max_value >= 10:
				max_value /= 10
				digits += 1
			space = 3 + self.fontMetrics().width('9') * digits
			return space

		def updateLineNumberAreaWidth(self, _):
			self.setViewportMargins(self.lineNumberAreaWidth(), 0, 0, 0)

		def updateLineNumberArea(self, rect, dy):
			if dy:
				self.lineNumberArea.scroll(0, dy)
			else:
				self.lineNumberArea.update(0, rect.y(), self.lineNumberArea.width(), rect.height())
			if rect.contains(self.viewport().rect()):
				self.updateLineNumberAreaWidth(0)

		def resizeEvent(self, event):
			super().resizeEvent(event)
			cr = self.contentsRect()
			self.lineNumberArea.setGeometry(QRect(cr.left(), cr.top(), self.lineNumberAreaWidth(), cr.height()))

		def highlightCurrentLine(self):
			extraSelections = []
			if not self.isReadOnly():
				selection = QTextEdit.ExtraSelection()
				lineColor = QColor("#073642")
				selection.format.setBackground(lineColor)
				selection.format.setProperty(QTextFormat.FullWidthSelection, True)
				selection.cursor = self.textCursor()
				selection.cursor.clearSelection()
				extraSelections.append(selection)
			self.setExtraSelections(extraSelections)

		def lineNumberAreaPaintEvent(self, event):
			painter = QPainter(self.lineNumberArea)

			painter.fillRect(event.rect(), QColor("#073642"))

			block = self.firstVisibleBlock()
			blockNumber = block.blockNumber()
			top = self.blockBoundingGeometry(block).translated(self.contentOffset()).top()
			bottom = top + self.blockBoundingRect(block).height()

			# Just to make sure I use the right font
			height = self.fontMetrics().height()
			while block.isValid() and (top <= event.rect().bottom()):
				if block.isVisible() and (bottom >= event.rect().top()):
					number = str(blockNumber + 1)
					# painter.setPen(Qt.black)
					painter.setPen(QColor("#8A7852"))
					painter.drawText(0, top, self.lineNumberArea.width(), height, Qt.AlignRight, number)

				block = block.next()
				top = bottom
				bottom = top + self.blockBoundingRect(block).height()
				blockNumber += 1

	informationText = pyqtSignal(str)

	def __init__(self):
		super().__init__()
		self.title = 'Dunyanin En Iyi Editoru'
		self.initUI()
		self.restore()

		self.informationText.connect(self.informationBox.setPlainText)

	def initUI(self):
		self.setWindowTitle(self.title)
		# self.setGeometry(self.left, self.top, self.width, self.height)

		self.layout = QGridLayout()

		self.label = QLabel()
		self.setLayout(self.layout)

		self.codeEditor = self.QCodeEditor()
		self.codeEditor.resize(300, 300)
		self.codeEditor.setPlaceholderText("kodlari yazin")
		self.codeEditor.setStyleSheet(
			"""QPlainTextEdit {background-color: #002B36;
							color: #839496;
							font-family: Courier;}""")

		self.intervalText = QLabel("Refresh Interval(sec.):")
		self.intervalLineEdit = QLineEdit()
		self.intervalLineEdit.setText("3")

		self.imageVariableText = QLabel("Image Variable Name:")
		self.imageVariableLineEdit = QLineEdit()
		self.imageVariableLineEdit.setText("image")

		self.informationBox = QPlainTextEdit()
		self.informationBox.resize(300, 300)
		self.informationBox.setPlaceholderText("information area")
		self.informationBox.setReadOnly(True)
		self.informationBox.setStyleSheet(
			"""QPlainTextEdit {background-color: #333;
							color: #79EC14;
							font-family: Courier;}""")

		self.image_label = QLabel()
		self.image_label.resize(300, 300)

		self.layout.addWidget(self.codeEditor, 0, 0, 5, 5)
		self.layout.addWidget(self.intervalText, 5, 0)
		self.layout.addWidget(self.intervalLineEdit, 5, 1)
		self.layout.addWidget(self.imageVariableText, 5, 3)
		self.layout.addWidget(self.imageVariableLineEdit, 5, 4)
		self.layout.addWidget(self.informationBox, 6, 0, 2, 5)

		self.layout.addWidget(self.image_label, 0, 5, 8, 2)


		self.timer = QTimer()
		self.timer.timeout.connect(self.ExecCommand)
		self.timer.start(100)

		self.show()

	def ExecCommand(self):
		loc = {}
		text = datetime.now().strftime('%d/%m/%Y %H:%M:%S') + '\n'
		text += "Compiling..\n"
		self.informationText.emit(text)

		try:
			exec(self.codeEditor.toPlainText(), {}, loc) # do the thing
			img = loc[self.imageVariableLineEdit.text()]
			cv2.imwrite("temp.png", img)
			with open('temp.png', 'rb') as f:
				pixmap = QPixmap()
				pixmap.loadFromData(f.read(), 'png')
				self.image_label.setPixmap(pixmap)
				text += "Compiled successfully."
		except Exception:
			# print(traceback.format_exc())
			text += traceback.format_exc()
			# self.informationText.emit(traceback.format_exc())
			# self.informationBox.setPlainText(traceback.format_exc())

		self.informationText.emit(text)

		interval = 3.0
		try:
			interval = float(self.intervalLineEdit.text())
		except: pass
		self.timer.setInterval(int(interval*1000))

	def closeEvent(self, event):
		self.save()
		event.accept()

	def save(self):
		try:
			with open('config.txt', 'w') as f:
				f.write(self.codeEditor.toPlainText())
		except: print(traceback.format_exc())

	def restore(self):
		try:
			with open('config.txt', 'r') as f:
				commands = f.read()
				self.codeEditor.setPlainText(commands)
		except: print(traceback.format_exc())

	def center(self):
		qr = self.frameGeometry()
		cp = QDesktopWidget().availableGeometry().center()
		qr.moveCenter(cp)
		self.move(qr.topLeft())

if __name__ == '__main__':
	app = QApplication([])
	windowExample = App()
	windowExample.resize(1200, 750)
	windowExample.show()

	windowExample.center()

	exit(app.exec_())
