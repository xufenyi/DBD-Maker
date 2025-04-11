import sys
import os
from PySide2.QtCore import Signal, QRegExp
from PySide2.QtWidgets import *
from PySide2.QtGui import QFont, QIntValidator, QRegExpValidator
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.patches as patches
from read_dbd import read_dbd


def mm2inch(value, round_count=3):
    return round(value / 25.4, round_count)


def inch2mm(value, round_count=3):
    return round(value * 25.4, round_count)   


class Point:
    def __init__(self, x=0, y=0, action='jump'):
        self.x = float(x)
        self.y = float(y)
        self.action = action

    def __str__(self):
        return f'({self.x}, {self.y})'


class Line:
    def __init__(self, point1=Point(), point2=Point()):
        self.point1 = point1
        self.point2 = point2

    def x1x2(self):
        return self.point1.x, self.point2.x

    def y1y2(self):
        return self.point1.y, self.point2.y

    def color(self):
        return 'blue' if self.point2.action == 'jump' else 'red'

    def __str__(self):
        return f'{self.point1} -> {self.point2}'
    

class CanvasParams:
    def __init__(self):
        self.X = 30
        self.Y = 0
        self.R = 40
    
    def x(self, unit='mm'):
        return self.X if unit == 'mm' else mm2inch(self.X)
    
    def y(self, unit='mm'):
        return self.Y if unit == 'mm' else mm2inch(self.Y)
    
    def r(self, unit='mm'):
        return self.R if unit == 'mm' else mm2inch(self.R)

    def xlim(self, unit='mm'):
        return self.x(unit) - 1.125*self.r(unit), self.x(unit) + 1.125*self.r(unit)
    
    def ylim(self, unit='mm'):
        return self.y(unit) - 1.125*self.r(unit), self.y(unit) + 1.125*self.r(unit)


class NumberLineEdit(QLineEdit):
    '''
    重写QLineEdit，使其只能输入数字和小数点
    '''
    editingFinishedWithInvalidPoint = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.validator = QRegExpValidator(QRegExp(r'^\d*(\.\d*)?$'))
        self.setValidator(self.validator)
        self.editingFinished.connect(self.check_and_emit)

    def check_and_emit(self):
        if self.text().endswith('.'):
            self.editingFinishedWithInvalidPoint.emit()
            self.setText(self.text()[:-1])
        if not self.text():
            self.setText('0')


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.canvas_update_needed = True

        # 基本设置
        self.setGeometry(100, 100, 1200, 800)
        self.setFont(QFont('Microsoft YaHei', 9))
        self.menu_bar = self.menuBar()

        # 菜单栏 -> 文件
        self.menu_file = self.menu_bar.addMenu('文件')

        self.action_new = QAction('新建', self)
        self.action_open = QAction('打开', self)
        self.action_save = QAction('保存', self)
        self.action_import = QAction('从csv文件导入', self)
        self.action_exit = QAction('关闭', self)

        self.action_new.setShortcut('Ctrl+N')
        self.action_open.setShortcut('Ctrl+O')
        self.action_save.setShortcut('Ctrl+S')
        self.action_import.setShortcut('Ctrl+I')
        self.action_exit.setShortcut('Ctrl+Q')

        self.menu_file.addAction(self.action_new)
        self.menu_file.addAction(self.action_open)
        self.menu_file.addAction(self.action_save)
        self.menu_file.addAction(self.action_import)
        self.menu_file.addAction(self.action_exit)

        self.action_new.triggered.connect(self.action_new_slot)
        self.action_open.triggered.connect(self.action_open_slot)
        self.action_save.triggered.connect(self.action_save_slot)
        self.action_import.triggered.connect(self.action_import_slot)
        self.action_exit.triggered.connect(self.close)

        # 菜单栏 -> 帮助
        self.help_menu = self.menu_bar.addMenu('帮助')

        self.action_about = QAction('关于', self)

        self.action_about.setShortcut('Ctrl+H')

        self.help_menu.addAction(self.action_about)

        self.action_about.triggered.connect(self.action_about_slot)

        # 布局
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # 水平布局0
        hbox0 = QHBoxLayout()
        central_widget.setLayout(hbox0)

        # 水平布局0 -> 垂直布局0
        vbox0 = QVBoxLayout()
        hbox0.addLayout(vbox0)

        # 水平布局0 -> 垂直布局0 -> 表格布局0
        self.grid0 = QGridLayout()
        vbox0.addLayout(self.grid0)
        self.grid0.addWidget(QLabel('文件名'), 0, 0)
        self.line_file = QLineEdit()
        self.grid0.addWidget(self.line_file, 0, 1)
        self.grid0.addWidget(QLabel('.dbd'), 0, 2)

        self.grid0.addWidget(QLabel('长度单位'), 1, 0)
        self.combo0 = QComboBox()
        self.combo0.addItem('mm')
        self.combo0.addItem('inch')
        self.combo0.setEditable(False)
        self.grid0.addWidget(self.combo0, 1, 1)
        self.grid0.addWidget(QLabel(), 1, 2)
        self.combo0.currentIndexChanged.connect(self.update_units)

        self.grid0.addWidget(QLabel('出光延迟'), 2, 0)
        self.line_laserOnDelay = NumberLineEdit()
        self.grid0.addWidget(self.line_laserOnDelay, 2, 1)
        self.grid0.addWidget(QLabel('ms'), 2, 2)

        self.grid0.addWidget(QLabel('关光延迟'), 3, 0)
        self.line_laserOffDelay = NumberLineEdit()
        self.grid0.addWidget(self.line_laserOffDelay, 3, 1)
        self.grid0.addWidget(QLabel('ms'), 3, 2)

        self.grid0.addWidget(QLabel('跳转速度'), 4, 0)
        self.line_jumpSpeed = NumberLineEdit()
        self.grid0.addWidget(self.line_jumpSpeed, 4, 1)
        self.grid0.addWidget(QLabel('mm/s'), 4, 2)

        self.grid0.addWidget(QLabel('烧结速度'), 5, 0)
        self.line_markSpeed = NumberLineEdit()
        self.grid0.addWidget(self.line_markSpeed, 5, 1)
        self.grid0.addWidget(QLabel('mm/s'), 5, 2)

        self.grid0.addWidget(QLabel('跳转延迟'), 6, 0)
        self.line_jumpDelay = NumberLineEdit()
        self.grid0.addWidget(self.line_jumpDelay, 6, 1)
        self.grid0.addWidget(QLabel('ms'), 6, 2)

        self.grid0.addWidget(QLabel('烧结延迟'), 7, 0)
        self.line_markDelay = NumberLineEdit()
        self.grid0.addWidget(self.line_markDelay, 7, 1)
        self.grid0.addWidget(QLabel('ms'), 7, 2)
        
        self.grid0.addWidget(QLabel('每步周期'), 8, 0)
        self.line_stepPeriod = NumberLineEdit()
        self.grid0.addWidget(self.line_stepPeriod, 8, 1)
        self.grid0.addWidget(QLabel('ms'), 8, 2)

        # 水平布局0 -> 垂直布局0 -> 横线
        hline0 = QFrame()
        hline0.setFrameShape(QFrame.HLine)
        hline0.setFrameShadow(QFrame.Sunken)
        vbox0.addWidget(hline0)
        
        # 水平布局0 -> 垂直布局0 -> 可编辑表格
        self.table = QTableWidget(0, 3)
        self.table.setHorizontalHeaderLabels(['X/mm', 'Y/mm', '动作'])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        vbox0.addWidget(self.table)
        self.table.itemChanged.connect(self.table_changed_slot)

        # 水平布局0 -> 垂直布局0 -> 水平布局1（`+`、`-`、`↑`、`↓`）
        hbox1 = QHBoxLayout()
        vbox0.addLayout(hbox1)

        self.button_table_add = QPushButton('+')
        self.button_table_del = QPushButton('-')
        self.button_table_up = QPushButton('↑')
        self.button_table_down = QPushButton('↓')

        self.button_table_del.setEnabled(False)
        self.button_table_up.setEnabled(False)
        self.button_table_down.setEnabled(False)

        hbox1.addWidget(self.button_table_add)
        hbox1.addWidget(self.button_table_del)
        hbox1.addWidget(self.button_table_up)
        hbox1.addWidget(self.button_table_down)

        self.button_table_add.clicked.connect(self.table_add_slot)
        self.button_table_del.clicked.connect(self.table_del_slot)
        self.button_table_up.clicked.connect(self.table_up_slot)
        self.button_table_down.clicked.connect(self.table_down_slot)

        # 水平布局0 -> 垂直布局1
        vbox1 = QVBoxLayout()
        hbox0.addLayout(vbox1)

        # 水平布局0 -> 垂直布局1 -> plt绘图窗口
        self.dynamic_canvas = FigureCanvas(Figure(figsize=(7, 7)))
        vbox1.addWidget(self.dynamic_canvas)
        self.axes = self.dynamic_canvas.figure.subplots()
        self._timer = self.dynamic_canvas.new_timer(50, [(self.update_canvas, (), {})])
        self._timer.start()

        # 水平布局0 -> 垂直布局1 -> 弹性占位符
        vbox1.addStretch(1)

        # 水平布局0 -> 垂直布局1 -> 水平布局2（弹性占位符，复选框）
        hbox2 = QHBoxLayout()
        vbox1.addLayout(hbox2)
        hbox2.addStretch(1)
        self.check_show_blue_line = QCheckBox('显示跳转')
        hbox2.addWidget(self.check_show_blue_line)
        self.check_show_blue_line.setChecked(True)
        self.check_show_blue_line.stateChanged.connect(self.set_canvas_update_needed)

        self.set_title()
        self.set_values()
        self.save_filepath = ''

    def set_title(self, filename='Untitled.dbd'):
        self.setWindowTitle(f'{filename} - DBD Maker')

    def set_values(self, file='Untitled', unit='mm',
        laserOnDelay='15', laserOffDelay='190', jumpSpeed='7379.995', markSpeed='500.000',
        jumpDelay='500', markDelay='500', stepPeriod='100'
    ):
        self.line_file.setText(file)
        self.combo0.setCurrentIndex(1 if unit == 'inch' else 0)
        self.line_laserOnDelay.setText(str(laserOnDelay))
        self.line_laserOffDelay.setText(str(laserOffDelay))
        self.line_jumpSpeed.setText(str(jumpSpeed))
        self.line_markSpeed.setText(str(markSpeed))
        self.line_jumpDelay.setText(str(jumpDelay))
        self.line_markDelay.setText(str(markDelay))
        self.line_stepPeriod.setText(str(stepPeriod))

    def action_new_slot(self):
        self.set_values()
        self.table.setRowCount(0)
        self.set_canvas_update_needed()
        self.save_filepath = ''

    def action_open_slot(self):
        filepath, _ = QFileDialog.getOpenFileName(
            self, '打开文件', '', 'DBD 文件 (*.dbd)'
        )
        if not filepath:
            return
        self.save_filepath = filepath
        result = read_dbd(filepath)
        
        try:
            self.set_values(
                file=result['File'], unit=result['Unit'],
                laserOnDelay=result['LaserOnDelay'], laserOffDelay=result['LaserOffDelay'],
                jumpSpeed=result['JumpSpeed'], markSpeed=result['MarkSpeed'],
                jumpDelay=result['JumpDelay'], markDelay=result['MarkDelay'],
                stepPeriod=result['StepPeriod']
            )
            self.set_title(result['File'])
        except KeyError:
            QMessageBox.critical(self, '错误', '文件信息缺失或有误。')
            self.set_values()
        
        try:
            movements = result['Movements']
        except KeyError:
            movements = []

        self.table.setRowCount(0)
        for movement in movements:
            self.table_add_line(
                self.table.rowCount(), movement[0], movement[1], movement[2]
            )

    def action_save_slot(self):
        if not self.save_filepath.endswith(f'{self.line_file.text()}.dbd'):
            form_filename = self.line_file.text()
            form_filename = form_filename if form_filename else 'Untitled'
            form_filename += '.dbd'
            filepath, _ = QFileDialog.getSaveFileName(
                self, '保存文件', form_filename, 'DBD 文件 (*.dbd)'
            )
            if not filepath:
                return
            self.line_file.setText(
                os.path.splitext(os.path.basename(filepath))[0]
            )
        else:
            filepath = self.save_filepath

        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(f'File: {os.path.basename(filepath)}\n')
            f.write(f'Unit: {self.combo0.currentText()}\n')
            f.write(f'Start_List\n')
            f.write(f'LaserOnDelay {self.line_laserOnDelay.text()}\n')
            f.write(f'LaserOffDelay {self.line_laserOffDelay.text()}\n')
            f.write(f'JumpSpeed {self.line_jumpSpeed.text()}\n')
            f.write(f'MarkSpeed {self.line_markSpeed.text()}\n')
            f.write(f'JumpDelay {self.line_jumpDelay.text()}\n')
            f.write(f'MarkDelay {self.line_markDelay.text()}\n')
            f.write(f'StepPeriod {self.line_stepPeriod.text()}\n')
            for x, y, action in self.get_table_data():
                f.write(f'{action}_abs {x} {y}\n')
            f.write(f'End_List\n')

    def action_import_slot(self):
        print("从csv文件导入")

    def action_about_slot(self):
        QMessageBox.about(
            self, '关于',
            '本程序可以创建适用于华曙打印机手动出光的控制文件，创建好的文件需要加密方可使用。'
        )

    def table_changed_slot(self, item):
        self.canvas_update_needed = True
        # 根据行数判断是否启用删除、上移、下移按钮
        row_count = self.table.rowCount()
        if row_count == 0:
            self.button_table_del.setEnabled(False)
            self.button_table_up.setEnabled(False)
            self.button_table_down.setEnabled(False)
            return
        self.button_table_del.setEnabled(True)
        self.button_table_up.setEnabled(True)
        self.button_table_down.setEnabled(True)
        # 遍历检查第0列、第1列是否为浮点数，若不是，则修改为0.000000
        for row in range(row_count):
            for col in range(2):
                item = self.table.item(row, col)
                try:
                    float(item.text())
                except (ValueError, TypeError, AttributeError):
                    self.table.setItem(row, col, QTableWidgetItem('0.000000'))

    def get_combo(self, current='jump'):
        combo = QComboBox()
        combo.addItems(('jump', 'mark'))
        combo.setCurrentIndex(0)
        combo.currentIndexChanged.connect(self.set_canvas_update_needed)
        if current == 'mark':
            combo.setCurrentText('mark')
        return combo

    def get_table_line_data(self, row: int):
        return (
            self.table.item(row, 0).text(),
            self.table.item(row, 1).text(),
            self.table.cellWidget(row, 2).currentText()
        )

    def get_table_data(self):
        row_count = self.table.rowCount()
        rows = []
        for row in range(row_count):
            x, y, action = self.get_table_line_data(row)
            rows.append((x, y, action))
        return rows

    def get_all_lines(self):
        if self.table.rowCount() == 0:
            return []
        
        table_data = self.get_table_data()
        points = [Point()]
        for x, y, action in table_data:
            points.append(Point(x, y, action))
        lines = []
        for i in range(len(points)-1):
            lines.append(Line(points[i], points[i+1]))
        return lines

    def table_add_line(self, row, x='0.000000', y='0.000000', action='jump'):
        self.table.insertRow(row)
        self.table.setItem(row, 0, QTableWidgetItem(x))
        self.table.setItem(row, 1, QTableWidgetItem(y))
        self.table.setCellWidget(row, 2, self.get_combo(action))

    def table_add_slot(self):
        row_count = self.table.rowCount()
        if row_count == 0:
            new_row = 0
        else:
            new_row = self.table.currentRow() + 1
        self.table_add_line(new_row)

    def table_del_slot(self):
        row = self.table.currentRow()
        self.table.removeRow(row)
    
    def table_move(self, direction: str):
        '''
        上移和下移共同的逻辑。
        若上移，则新行号为当前的减1，若下移，则新行号为当前的加1。
        '''
        row = self.table.currentRow()
        new_row = row-1 if direction == 'up' else row+1
        row_text = self.get_table_line_data(row)
        self.table.removeRow(row)
        self.table.insertRow(new_row)
        self.table.setItem(new_row, 0, QTableWidgetItem(row_text[0]))
        self.table.setItem(new_row, 1, QTableWidgetItem(row_text[1]))
        self.table.setCellWidget(new_row, 2, self.get_combo(row_text[2]))
        self.table.setCurrentCell(new_row, 0)

    def table_up_slot(self):
        row = self.table.currentRow()
        if row == 0:
            return
        self.table_move('up')
        
    def table_down_slot(self):
        row = self.table.currentRow()
        if row == self.table.rowCount()-1:
            return
        self.table_move('down')

    def set_canvas_update_needed(self):
        self.canvas_update_needed = True

    def update_canvas(self):
        if not self.canvas_update_needed:
            return
        self.canvas_update_needed = False

        self.axes.clear()
        params = CanvasParams()
        unit = self.combo0.currentText()
        circle_center = (params.x(unit), params.y(unit))
        circle_r = params.r(unit)
        axes_xlim = params.xlim(unit)
        axes_ylim = params.ylim(unit)
        circle = patches.Circle(circle_center, circle_r, edgecolor='black', facecolor='none')
        lines = self.get_all_lines()
        show_blue_line = self.check_show_blue_line.isChecked()
        if lines:
            for line in lines:
                if show_blue_line or line.color() == 'red':
                    self.axes.plot(line.x1x2(), line.y1y2(), color=line.color())
        
        self.axes.add_patch(circle)
        self.axes.set_xlim(*axes_xlim)
        self.axes.set_ylim(*axes_ylim)
        self.axes.set_aspect('equal')

        self.dynamic_canvas.draw()

    def update_units(self):
        unit = self.combo0.currentText()
        self.grid0.itemAtPosition(4, 2).widget().setText(f'{unit}/s')
        self.grid0.itemAtPosition(5, 2).widget().setText(f'{unit}/s')
        convert_function = mm2inch if unit == 'inch' else inch2mm
        self.line_jumpSpeed.setText(str(
            convert_function(float(self.line_jumpSpeed.text()))
        ))
        self.line_markSpeed.setText(str(
            convert_function(float(self.line_markSpeed.text()))
        ))
        self.table.setHorizontalHeaderLabels([f'X/{unit}', f'Y/{unit}', '动作'])


if __name__ == '__main__':
    app = QApplication(sys.argv)
    main_window = MainWindow()
    main_window.show()
    sys.exit(app.exec_())
