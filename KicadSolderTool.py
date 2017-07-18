#!/usr/bin/env python

"""PySide port of the painting/svgviewer example from Qt v4.x"""

import sys
from PySide import QtCore, QtGui, QtSvg 
import query_footprints
import kicad_handler
import kicad_bom_parser

class TransfomationPointState(object):
    Nope = 0
    TopLeft = 1
    BottomRight = 2
    
class MainWindow(QtGui.QMainWindow):
    def __init__(self):
        QtGui.QMainWindow.__init__(self)
        self.transformationPointState = TransfomationPointState.Nope
        self.svg_filename_top = ''

        self.currentPath = ""
        self.pcb_fileName = ""
        
        self.area = SvgWindow(self)

        fileMenu = QtGui.QMenu(self.tr("&File"), self)
        self.openAction = fileMenu.addAction(self.tr("&Open..."))
        self.openAction.setShortcut(QtGui.QKeySequence(self.tr("Ctrl+O")))
        self.openRecentAction = fileMenu.addAction(self.tr("&Open recent..."))
        self.openTransformationAction = fileMenu.addAction(self.tr("&Open transformation..."))
        self.quitAction = fileMenu.addAction(self.tr("E&xit"))
        self.quitAction.setShortcut(QtGui.QKeySequence(self.tr("Ctrl+Q")))

        self.menuBar().addMenu(fileMenu)
        
        self.connect(self.openAction, QtCore.SIGNAL("triggered()"), self.openFile)
        self.connect(self.openRecentAction, QtCore.SIGNAL("triggered()"), self.openRecent)
        self.connect(self.quitAction, QtCore.SIGNAL("triggered()"), QtGui.qApp, QtCore.SLOT("quit()"))
        self.connect(self.openTransformationAction, QtCore.SIGNAL("triggered()"), self.openTransformation)

        self.spin_transformation_a_x = QtGui.QSpinBox()
        self.spin_transformation_a_y = QtGui.QSpinBox()
        self.spin_transformation_b_x = QtGui.QSpinBox()
        self.spin_transformation_b_y = QtGui.QSpinBox()
        
        self.btn_find_top_left = QtGui.QPushButton("fetch on top left");
        self.btn_find_bot_right = QtGui.QPushButton("fetch on bot right");
        
        self.c_widget = QtGui.QWidget(self)
        
        self.spin_offset_x = QtGui.QSpinBox()
        self.spin_offset_y = QtGui.QSpinBox()
        
        #self.setCentralWidget(self.area)
        self.gridlayout = QtGui.QGridLayout()
        self.gridlayout.addWidget(QtGui.QLabel("offset x:"),0,0)
        self.gridlayout.addWidget(self.spin_offset_x,0,1)
        self.gridlayout.addWidget(QtGui.QLabel("offset y:"),1,0)
        self.gridlayout.addWidget(self.spin_offset_y,1,1)
        self.gridlayout.addWidget(QtGui.QLabel("transformation point left:"),0,2)
        self.gridlayout.addWidget(QtGui.QLabel("transformation point top:"),1,2)
        self.gridlayout.addWidget(self.spin_transformation_a_x,0,3)
        self.gridlayout.addWidget(self.spin_transformation_a_y,1,3)
        self.gridlayout.addWidget(QtGui.QLabel("mm@:"),0,4)
        self.gridlayout.addWidget(QtGui.QLabel("mm@"),1,4)  
        
        self.gridlayout.addWidget(self.btn_find_top_left,0,5)
        
        self.gridlayout.addWidget(QtGui.QLabel("transformation point right:"),0,6)
        self.gridlayout.addWidget(QtGui.QLabel("transformation point bottom:"),1,6)  
        
        self.gridlayout.addWidget(self.spin_transformation_b_x,0,7)
        self.gridlayout.addWidget(self.spin_transformation_b_y,1,7)
        self.gridlayout.addWidget(QtGui.QLabel("mm@:"),0,8)
        self.gridlayout.addWidget(QtGui.QLabel("mm@"),1,8)  
        self.gridlayout.addWidget(self.btn_find_bot_right,0,9)
        self.gridlayout.addWidget(self.area,2,0,2,0)
        self.c_widget.setLayout(self.gridlayout)
        self.setCentralWidget(self.c_widget)
        self.setWindowTitle(self.tr("Kicad Solder Tool"))
        
        self.spin_transformation_a_x.setMaximum(100000)
        self.spin_transformation_a_x.setMinimum(-100000)
        self.spin_transformation_a_x.setValue(0)
        
        self.spin_transformation_a_y.setMaximum(100000)
        self.spin_transformation_a_y.setMinimum(-100000)
        self.spin_transformation_a_y.setValue(0)
        
        self.spin_transformation_b_x.setMaximum(100000)
        self.spin_transformation_b_x.setMinimum(-100000)
        self.spin_transformation_b_x.setValue(160)
        
        self.spin_transformation_b_y.setMaximum(100000)
        self.spin_transformation_b_y.setMinimum(-100000)
        self.spin_transformation_b_y.setValue(100)
        
        self.spin_offset_x.setMaximum(100000)
        self.spin_offset_x.setMinimum(-100000)
        
        self.spin_offset_y.setMaximum(100000)
        self.spin_offset_y.setMinimum(-100000)
        
        self.spin_offset_x.setSingleStep(10)
        self.spin_offset_y.setSingleStep(10)
        self.connect(self.spin_transformation_a_x, QtCore.SIGNAL("valueChanged(int)"), self.calc_transform)
        self.connect(self.spin_transformation_a_y, QtCore.SIGNAL("valueChanged(int)"), self.calc_transform)
        self.connect(self.spin_transformation_b_x, QtCore.SIGNAL("valueChanged(int)"), self.calc_transform)
        self.connect(self.spin_transformation_b_y, QtCore.SIGNAL("valueChanged(int)"), self.calc_transform)        
        self.connect(self.spin_offset_x, QtCore.SIGNAL("valueChanged(int)"), self.on_offset_change)
        self.connect(self.spin_offset_y, QtCore.SIGNAL("valueChanged(int)"), self.on_offset_change)
        self.connect(self.btn_find_top_left, QtCore.SIGNAL("clicked(bool)"), self.on_fetch_top_left)
        self.connect(self.btn_find_bot_right, QtCore.SIGNAL("clicked(bool)"), self.on_fetch_bottom_right)
        self.transFormMatrix = QtGui.QMatrix();
        self.transform_target_topleft = QtCore.QPoint(0,0)
        self.transform_target_bottom_right = QtCore.QPoint(1,2)
        
        self.area.cursor().setShape(QtCore.Qt.CrossCursor)
        self.startTimer(250);
        

    def openTransformation(self):
        fileName = QtGui.QFileDialog.getOpenFileName(self, self.tr("Open Kicad board File"),
                                                        self.currentPath, "*.trans")[0]
        if fileName!="":
            settings = QtCore.QSettings(fileName,QtCore.QSettings.IniFormat)
            
            self.spin_transformation_a_x.setValue(int(settings.value("pcb_ax",0)))
            self.spin_transformation_a_y.setValue(int(settings.value("pcb_ay",0)))
            self.spin_transformation_b_x.setValue(int(settings.value("pcb_bx",1)))
            self.spin_transformation_b_y.setValue(int(settings.value("pcb_by",1)))
            self.spin_offset_x.setValue(int(settings.value("off_x",1)))
            self.spin_offset_y.setValue(int(settings.value("off_y",1)))
            self.transform_target_topleft.setX(int(settings.value("view_ax",0)))
            self.transform_target_topleft.setY(int(settings.value("view_ay",0)))
            self.transform_target_bottom_right.setX(int(settings.value("view_bx",1)))
            self.transform_target_bottom_right.setY(int(settings.value("view_by",1)))
            self.calc_transform(0)

    def saveTransformation(self):
        if self.pcb_fileName!="":
            print(self.pcb_fileName+'.trans')
            settings = QtCore.QSettings(self.pcb_fileName+'.trans',QtCore.QSettings.IniFormat)
            
            settings.setValue("pcb_ax",self.spin_transformation_a_x.value())
            settings.setValue("pcb_ay",self.spin_transformation_a_y.value())
            settings.setValue("pcb_bx",self.spin_transformation_b_x.value())
            settings.setValue("pcb_by",self.spin_transformation_b_y.value())
            settings.setValue("off_x",self.spin_offset_x.value())
            settings.setValue("off_y",self.spin_offset_y.value())
            settings.setValue("view_ax",self.transform_target_topleft.x())
            settings.setValue("view_ay",self.transform_target_topleft.y())
            settings.setValue("view_bx",self.transform_target_bottom_right.x())
            settings.setValue("view_by",self.transform_target_bottom_right.y())
            settings.sync()
            
            
    def openRecent(self):
        fileName = QtCore.QSettings("./KicadSolderTool.ini",QtCore.QSettings.IniFormat).value("recent_file","");
        self.openFile(fileName)
        
    def openFile(self, path=""):
        if path=="":
            fileName = QtGui.QFileDialog.getOpenFileName(self, self.tr("Open Kicad board File"),
                                                        self.currentPath, "*.kicad_pcb")[0]
        else:
            fileName = path

        if fileName!="":
            self.pcb_fileName = fileName
            QtCore.QSettings("./KicadSolderTool.ini",QtCore.QSettings.IniFormat).setValue("recent_file",fileName);
            self.transform_target_topleft_set = False
            self.transform_target_bottom_right_set = False
            svg_filename_top = fileName+'top.svg'
            svg_filename_bot = fileName+'bot.svg'
            kicad_handler.pcb_to_svg(fileName,svg_filename_top,svg_filename_bot )
            self.footprintlist = query_footprints.query_and_sort(fileName)
            self.showFile(svg_filename_top,svg_filename_bot)
            self.footprintlist_window = FootPrintList(self,self.footprintlist)
            
    def on_offset_change(self,i):
        self.area.setOffset(self.spin_offset_x.value(), self.spin_offset_y.value())
    
    def on_fetch_top_left(self,i):
        self.area.set_marker(self.transFormMatrix.map(QtCore.QPoint(self.spin_transformation_a_x.value(),self.spin_transformation_a_y.value())),False)
        self.transformationPointState = TransfomationPointState.TopLeft
        
    def on_fetch_bottom_right(self,i):
        self.area.set_marker(self.transFormMatrix.map(QtCore.QPoint(self.spin_transformation_b_x.value(),self.spin_transformation_b_y.value())),False)
        self.transformationPointState = TransfomationPointState.BottomRight
            
    def showFile(self,svg_filename_top,svg_filename_bot):
        self.area.openFile(svg_filename_top,svg_filename_bot)
        if (self.svg_filename_top != svg_filename_top):
            self.svg_filename_top = svg_filename_top
            if not svg_filename_top.startswith(":/"):
                self.currentPath = svg_filename_top
                self.setWindowTitle(self.tr("%s - SVGViewer") % self.currentPath)

    def setPositionClicked(self,x,y):
        x = round(x)
        y = round(y)
        if self.transformationPointState == TransfomationPointState.TopLeft:
            self.btn_find_top_left.setText("pos: "+str(x)+"/"+str(y))
            self.transform_target_topleft.setX(x)
            self.transform_target_topleft.setY(y)
            self.transform_target_topleft_set = True
            
        elif self.transformationPointState == TransfomationPointState.BottomRight:
            self.btn_find_bot_right.setText("pos: "+str(x)+"/"+str(y))
            self.transform_target_bottom_right.setX(x)
            self.transform_target_bottom_right.setY(y)
            self.transform_target_bottom_right_set = True
        self.calc_transform(0)
        
        if self.transformationPointState == TransfomationPointState.TopLeft:
            self.area.set_marker(self.transFormMatrix.map(QtCore.QPoint(self.spin_transformation_a_x.value(),self.spin_transformation_a_y.value())),False)
        elif self.transformationPointState == TransfomationPointState.BottomRight:
            self.area.set_marker(self.transFormMatrix.map(QtCore.QPoint(self.spin_transformation_b_x.value(),self.spin_transformation_b_y.value())),False)
            
        self.transformationPointState = TransfomationPointState.Nope

        
    def calc_transform(self,i):
        if self.transform_target_bottom_right_set and self.transform_target_topleft_set:
            pcb_width = float(self.spin_transformation_b_x.value() - self.spin_transformation_a_x.value())
            pcb_height = float(self.spin_transformation_b_y.value() - self.spin_transformation_a_y.value())
            view_width = -self.transform_target_topleft.x() + self.transform_target_bottom_right.x()
            view_height = -self.transform_target_topleft.y() + self.transform_target_bottom_right.y()
            print("view "+ str(view_width)+" "+str(view_height))
            print("pcb "+ str(pcb_width)+" "+str(pcb_height))
            self.transFormMatrix = QtGui.QMatrix()
            
            self.transFormMatrix.translate(self.transform_target_topleft.x(),self.transform_target_topleft.y())            
            self.transFormMatrix.scale(view_width/pcb_width,view_height/pcb_height)
            self.transFormMatrix.translate(-self.spin_transformation_a_x.value(),-self.spin_transformation_a_y.value())
            self.saveTransformation()
            

    def timerEvent(self,event):
        #self.area.blink_marker()
        pass
        
    def set_marker(self,point,is_bot):
        self.area.set_marker(self.transFormMatrix.map(point),is_bot)
        
class SvgWindow(QtGui.QGraphicsView):
    def __init__(self,parent):
        QtGui.QGraphicsView.__init__(self)
        self.parent = parent;
        self.setTransformationAnchor(QtGui.QGraphicsView.AnchorUnderMouse);
        self.setDragMode(QtGui.QGraphicsView.ScrollHandDrag);
        self.setViewportUpdateMode(QtGui.QGraphicsView.FullViewportUpdate);
        self.setRenderHints(0);
        self.scene = QtGui.QGraphicsScene();
        self.setScene(self.scene)
        self.offset_x = 0;
        self.offset_y = 0;
        self.marker_set = False
        self.marker_is_visible = True
        self.is_flipped = False

    def openFile(self,path_top, path_bot):
        self.svg_item_bot = QtSvg.QGraphicsSvgItem(path_bot)
        self.svg_item_top = QtSvg.QGraphicsSvgItem(path_top)
        self.scene.addItem(self.svg_item_bot);
        self.scene.addItem(self.svg_item_top);
        self.setCursor(QtCore.Qt.CrossCursor)
        
    def setOffset(self,x,y):
        self.offset_x = x;
        self.offset_y = y;
        rect = self.svg_item_top.boundingRect();
        rect.moveTo(x,y)
        self.setSceneRect(rect)        

    def wheelEvent(self, event):
        factor = pow(1.2, event.delta() / 240.0);
        self.scale(factor, factor);

    def mousePressEvent(self,event):
        scene_point = self.mapToScene(event.x(),event.y())
        self.parent.setPositionClicked(scene_point.x(),scene_point.y())
        QtGui.QGraphicsView.mousePressEvent(self,event)

    def blink_marker(self):
        if self.marker_set:
            self.marker_ellipse.setVisible(self.marker_is_visible)
            self.marker_line_h.setVisible(self.marker_is_visible)
            self.marker_line_v.setVisible(self.marker_is_visible)
            if self.marker_is_visible:
                self.marker_is_visible = False
            else:
                self.marker_is_visible = True
            
    def set_marker(self,point, bot):
        scene_point = point
        if self.marker_set:
            self.scene.removeItem(self.marker_ellipse)
            self.scene.removeItem(self.marker_line_h)
            self.scene.removeItem(self.marker_line_v)
            
        color = QtGui.QColor()
        if bot:
            color = QtGui.QColor(QtCore.Qt.red)
        else:
            color = QtGui.QColor(QtCore.Qt.darkGreen)
        color.setAlpha(100)
        pen = QtGui.QPen()
        pen.setWidth(2)
        pen.setColor(color)
        self.marker_ellipse = self.scene.addEllipse(scene_point.x()-10,scene_point.y()-10,20,20,pen);
        self.marker_line_h = self.scene.addLine(scene_point.x()-10,scene_point.y(),scene_point.x()+10,scene_point.y(),pen);
        self.marker_line_v = self.scene.addLine(scene_point.x(),scene_point.y()-10,scene_point.x(),scene_point.y()+10,pen);
        self.marker_set = True
        if bot:
            self.svg_item_bot.setVisible(True)
            self.svg_item_top.setVisible(False)
            if not self.is_flipped:
                self.scale(-1,1)
                self.is_flipped = True
        else:
            self.svg_item_bot.setVisible(False)
            self.svg_item_top.setVisible(True)
            if self.is_flipped:
                self.scale(-1,1)   
                self.is_flipped = False

class PartTreeWidget(QtGui.QTreeWidget):
    def __init__(self, parent):
        QtGui.QTreeWidget.__init__(self, parent)

    def keyPressEvent(self, event):
        if event.key() == QtCore.Qt.Key_Space:
            item = self.selectedItems()[0]
            item.setCheckState(0,QtCore.Qt.Checked)  
            index = self.indexOfTopLevelItem(item)
            item = self.itemBelow(item)
            self.setCurrentItem(item)
       
        
class FootPrintList(QtGui.QDialog):
    def __init__(self, parent, footprintlist):
        QtGui.QDialog.__init__(self, parent)
        self.owner = parent
        self.combo_param_name = QtGui.QComboBox();
        self.combo_param_name.setEditable(True)
        self.footprint_list = footprintlist
        self.list_widget = PartTreeWidget(self)
        self.list_widget.setColumnCount(4)
        self.btn_load_bom = QtGui.QPushButton("load Field from xml-BOM")
        self.gridlayout = QtGui.QGridLayout()
        self.label = QtGui.QLabel("Field name:")
        self.gridlayout.addWidget(self.label,0,0,1,0)
        self.gridlayout.addWidget(self.btn_load_bom,1,1)
        self.gridlayout.addWidget(self.combo_param_name,1,0)
        self.gridlayout.addWidget(self.list_widget,2,0,1,0)
        self.label.setSizePolicy(QtGui.QSizePolicy.Minimum,QtGui.QSizePolicy.Minimum)
        self.combo_param_name.setSizePolicy(QtGui.QSizePolicy.Minimum,QtGui.QSizePolicy.Minimum)
        self.list_widget.setSizePolicy(QtGui.QSizePolicy.MinimumExpanding,QtGui.QSizePolicy.MinimumExpanding)
        self.param_names = []
        settings = QtCore.QSettings("./KicadSolderTool.ini",QtCore.QSettings.IniFormat)
        size = settings.beginReadArray("param_names")
        for i in range(size):
            settings.setArrayIndex(i)
            self.param_names.append(settings.value("key"))

        settings.endArray()
        self.combo_param_name.addItems(self.param_names)
        self.combo_param_name.setCurrentIndex(int(settings.value("recent_field_name",0)))
        
        self.setLayout(self.gridlayout)
        for footprint in self.footprint_list:        
            if footprint['bot']:
                caption = 'bot'
            else:
                caption = 'top'
            if footprint['other_side']:
                caption += "(also other side)"
            item = QtGui.QTreeWidgetItem(caption)
            item.setText(0,footprint['ref'])
            item.setText(1,caption)
            item.setText(2,footprint['val'])
            item.setCheckState(0,QtCore.Qt.Unchecked)   
            
            self.list_widget.addTopLevelItem(item)
        for i in range(self.list_widget.columnCount()):
            self.list_widget.resizeColumnToContents(i);
        self.setMinimumWidth(600)
        self.show()

        self.connect(self.list_widget, QtCore.SIGNAL("itemSelectionChanged()"), self.on_select)
        self.connect(self.btn_load_bom, QtCore.SIGNAL("clicked()"), self.on_load_bom)
        
    def on_select(self):
        item = self.list_widget.selectedItems()[0]
        index = self.list_widget.indexOfTopLevelItem(item)
        x = self.footprint_list[index]['x']/1000000.0
        y = self.footprint_list[index]['y']/1000000.0
        self.owner.set_marker(QtCore.QPointF(x,y),self.footprint_list[index]['bot'])
        

    def on_load_bom(self):
        fileName = QtGui.QFileDialog.getOpenFileName(self, self.tr("Open Kicad board File"),
                                                    "", "*.xml")[0]
        if fileName != "":
            settings = QtCore.QSettings("./KicadSolderTool.ini",QtCore.QSettings.IniFormat)
            if self.combo_param_name.findText(self.combo_param_name.currentText()) == -1:
                self.param_names.insert(0,self.combo_param_name.currentText())
                self.combo_param_name.clear()
                self.combo_param_name.addItems(self.param_names)
                self.combo_param_name.setCurrentIndex(0)
                settings.beginWriteArray("param_names")
                for idx, value in enumerate(self.param_names):
                    settings.setArrayIndex(idx)
                    settings.setValue("key", value)
                settings.endArray()
            settings.setValue("recent_field_name",self.combo_param_name.currentIndex())
            bomparser = kicad_bom_parser.BOMparser(fileName)
            index = 0
            for part in self.footprint_list:
                info = bomparser.get_part_info(part['ref'],self.combo_param_name.currentText())
                item = self.list_widget.topLevelItem(index)
                index += 1
                item.setText(3,info['value'])
        
        
        
if __name__ == '__main__':
    app = QtGui.QApplication(sys.argv)

    window = MainWindow()
    if len(sys.argv) == 2:
        window.openFile(sys.argv[1])
    else:
        print("");
    window.show()
    sys.exit(app.exec_())
 
