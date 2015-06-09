'''
Contains the main map, layer and dialog classes
Maps are rendered as image layers using PySide

MapQT: map class

Layer: Abstract layer class
GeojsonLayer: Geojson layer base class. Override for custom map projections and rendering styles
PointDataLayer: Point data base class. Override for custom datasets and rendering

MapDialog: PySide dialog to interactively change map and layer properties.

'''

import sys
import json
import copy

import pyproj
from builtins import range
from PySide.QtCore import *
from PySide.QtGui import *

from geom import Rectangle
from loader_utils import *
from map_utils import MapUtils
from utils import *


class Layer(object):
    ''' Abstract map layer '''
    def __init__(self,map,opts):
        # parent MapQt object
        self.map = map
        # Layer options dict
        self.id=''
        self.opts = opts
        if 'id' in opts:
            self.id = opts['id']
        self.type=''
        if 'type' in opts:
            self.type = opts['type']
        # Layer Styles
        self.styles = {}
        if 'styles' in opts:
            self.styles = opts['styles']
        # QImage or QPixmap
        self.image = None
        self.opacity = 1.0
        # Bounding box of projected coords
        self.projBounds = None
        # Proj4 source projection
        self.projSrc = None
        if 'proj' in opts:
            self.projSrc = pyproj.Proj(opts['proj'])
        # Layer data
        self.data = None


    def setImageSize(self,w,h):
        self.image = QImage(w,h,QImage.Format_ARGB32)
        self.image.fill(QColor(0, 0, 0, 0).rgba())

    def clearImage(self):
        self.image.fill(Qt.transparent)

    def setCanvasSize(self,w,h):
        ''' Resize canvas and render map '''
        assert False, 'Layer is an abstract class'

    def project(self):
        ''' Project geometry '''
        assert False, 'Layer is an abstract class'

    def renderImage(self):
        ''' Render layer to QImage '''
        qp = QPainter(self.image)
        qp.setRenderHint(QPainter.Antialiasing)
        self.clearImage()
        self.render(qp)
        qp.end()

    def render(self,qp):
        ''' Render geometry using QPainter qp '''
        assert False, 'Layer is an abstract class'

    def getOpacity(self):
        ''' Get opacity form style '''
        if 'opacity' in self.styles:
            self.opacity = float(self.styles['opacity'])
        return self.opacity


class GeojsonLayer(Layer):
    ''' Geojson map layer. Override for custom map projections and rendering. '''

    def __init__(self,map,opts):
        ''' Initialise with map object and layer options '''
        super(GeojsonLayer,self).__init__(map, opts)
        self.projGeojson = None
        self.loadData()
        self.updateCanvasSize()

    def loadData(self):
        self.geojson = MapUtils.loadGeoJson(self.opts['geojson'])


    def setStyles(self,styles):
        ''' Set styles used by renderer '''
        self.styles = styles
        self.renderImage()

    def updateCanvasSize(self):
        self.setImageSize(self.map.canvasW,self.map.canvasH)
        self.project()
        self.renderImage()

    def project(self):
        ''' Project Geojson geometry '''
        # copy JSON and write projected points into copy
        self.projGeojson = copy.deepcopy(self.geojson)
        features = self.projGeojson['features']

        for feature in features:
            # name = feature['properties']['NAME'] # example property
            polys = feature['geometry']['coordinates']

            for l in range(0,len(polys)):
                if feature['geometry']['type']=="MultiPolygon":
                    line = polys[l][0]
                else:
                    line = polys[l]

                for i in range(0,len(line)):
                    p = line[i]
                    try:
                        pt = pyproj.transform(self.projSrc,self.map.proj,p[0],p[1])
                        line[i] = [pt[0],pt[1]]

                    except RuntimeError as e:
                        line[i] = []


    def render(self,qp):
        ''' Render projected geometry using option styles '''
        qp.setBrush(Qt.cyan)
        qp.setPen(Qt.black)
        # Set QPainter styles
        MapUtils.setStylesFromJson(qp, self.styles)

        t0 = time.time()
        features = self.projGeojson['features']

        for feature in features:
            # name = feature['properties']['NAME'] # example property
            polys = feature['geometry']['coordinates']

            for l in range(0,len(polys)):
                if feature['geometry']['type']=="MultiPolygon":
                    line = polys[l][0]
                else:
                    line = polys[l]

                ptList = []
                validLine = True
                for i in range(0,len(line)):
                    p = line[i]
                    if len(p)==2:
                        pt = self.map.pointToView(p[0],p[1])
                        ptList.append(QPointF(pt[0],pt[1]))
                    else:
                        validLine = False

                if validLine:
                    qPoly = QPolygonF(ptList)
                    qp.drawPolygon(qPoly)

        t1 = time.time()
        print ('drawGeoJson:', t1-t0)


class PointDataLayer(Layer):
    ''' Base class for point data layers '''

    def __init__(self,map,opts):
        super(PointDataLayer,self).__init__(map, opts)
        self.loadData()
        self.updateCanvasSize()

    def loadData(self):
        datatype = self.opts['datatype']
        if datatype == "csv":
            self.data = LoaderUtils.loadCSV(self.opts)

    def setStyles(self,styles):
        self.styles = styles
        self.renderImage()

    def updateCanvasSize(self):
        self.setImageSize(self.map.canvasW,self.map.canvasH)
        self.project()
        self.renderImage()

    def project(self):
        ''' Project points and transform to map view coords '''
        items = self.data
        nItems = len(items)

        t1 = time.time()

        for i in range(0,nItems):
            item = items[i]

            item.projLng = None
            item.projLat = None
            item.vx = None
            item.vy = None

            # if(self.map.lngLatBounds.within(item.lng,item.lat)):
            try:
                pt = pyproj.transform(self.projSrc,self.map.proj,item.lng,item.lat)
                item.projLng = pt[0]
                item.projLat = pt[1]
                viewPt = self.map.pointToView(item.projLng, item.projLat)
                item.vx = viewPt[0]
                item.vy = viewPt[1]

            except RuntimeError as e:
                pass

        t2 = time.time()
        print ('updateDataCoords:', t2-t1)


    def progress(self,txt,t0,i,total):
        ''' Display function progress '''
        t1 = time.time()
        if self.map.renderCallback:
            message = txt+" "+str(i+1)+" of " + str(total)+", "+"{:.2f}".format(t1-t0)+"s"
            self.map.renderCallback(message)
        QCoreApplication.instance().processEvents()


    def render(self,qp):
        ''' Render projected geometry using option styles. Override for custom styles and rendering. '''

        t0 = time.time()
        items = self.data
        nItems = len(items)

        qp.setCompositionMode(QPainter.CompositionMode_SourceOver)

        # Handles only point-size and point-color styles
        ptSize = 1.0
        if 'point-size' in self.styles:
            ptSize = self.styles['point-size']

        ptCol = QColor(0, 0, 0, 70)
        if 'point-color' in self.styles:
            ptColStr = self.styles['point-color']
            ptCol = MapUtils.hex2qcolor(ptColStr)

        qp.setPen(Qt.NoPen)
        qp.setBrush(ptCol)

        for i in range(0,nItems):
            item = items[i]
            if i%1000 == 0 or i == nItems-1:
                self.progress("Render data:",t0,i,nItems-1)

            # if self.map.lngLatBounds.within(item.lng,item.lat):
            if item.vx and item.vy:
                if ptSize>2:
                    qp.drawEllipse(item.vx, item.vy, ptSize, ptSize)
                else:
                    qp.drawRect(QRectF(int(item.vx-ptSize/2), int(item.vy-ptSize/2), ptSize, ptSize))

        t1 = time.time()
        print 'Render Data:', t1-t0




class MapWidget(QLabel):
    ''' Main QWidget, contains map layers '''
    def __init__(self,view):
        super(MapWidget, self).__init__()
        # Main window
        self.view = view
        # Track mouse when no button press
        self.setMouseTracking(True)

    def paintEvent(self, event):
        qp = QPainter()
        qp.begin(self)
        self.view.render(event,qp)
        qp.end()

    def mouseMoveEvent(self, event):
        ''' Callback to display mouse lng,lat '''
        x = event.x()
        y = event.y()
        self.view.onMouseMove(x,y)


class MapQt(QMainWindow):
    ''' Map base class '''

    def __init__(self,config):
        super(MapQt, self).__init__()
        ''' Initialise with dict containing mapOpts field '''
        self.mapOpts = None
        self.layers = []

        self.epsg4326 = pyproj.Proj(init='epsg:4326')
        self.epsg3857 = pyproj.Proj(init='epsg:3857')

        # map container
        self.imageLabel = None
        # canvas width and height, max dimensions of map
        self.canvasW = 1500
        self.canvasH = 1200
        # dimensions of map
        self.viewW = self.canvasW
        self.viewH = self.canvasH

        # Proj4 map projection string
        self.proj = None
        # Projected map bounds
        self.projBounds=Rectangle()
        # lng lat map bounds
        self.lngLatBounds = Rectangle()
        # projection to view scale
        self.projToViewScale = 1.0

        # Dialog rendering progress callback
        self.renderCallback = None
        # Dialog mouse lng lat callback
        self.mousePosCallback = None
        # Render overlay
        self.isOverlay = False


        self.mapOpts = config['mapOpts']
        self.initUI()
        self.setMapOpts(self.mapOpts)




    def setMapOpts(self, mapOpts):
        ''' Set lnglat bounds, canvas size, map projection '''
        self.mapOpts = mapOpts

        self.canvasW = self.mapOpts['canvasSize'][0]
        self.canvasH = self.mapOpts['canvasSize'][1]
        self.proj = pyproj.Proj(self.mapOpts['proj'])

        bounds = Rectangle()
        bounds.fromList(self.mapOpts['bounds'])
        self.setMapBounds(bounds)
        self.setViewBounds()

    def addLayer(self, layer):
        self.layers.append(layer)

    def getLayersByType(self,layerType):
        return filter(lambda layer: layer.type == layerType, self.layers)


    def initUI(self):
        ''' Initialise the user interface '''
        self.setGeometry(10, 10, 1000, 800)
        self.setWindowTitle('Geo Qt')
        self.addMapWidget()
        self.show()


    def addMapWidget(self):
        ''' Add the map container '''
        self.imageLabel = MapWidget(self)
        self.imageLabel.setBackgroundRole(QPalette.Base)
        self.imageLabel.setSizePolicy(QSizePolicy.Ignored,QSizePolicy.Ignored)
        self.imageLabel.setScaledContents(True)

        self.scrollArea = QScrollArea()
        self.scrollArea.setBackgroundRole(QPalette.Dark)
        self.scrollArea.setWidget(self.imageLabel)
        self.setCentralWidget(self.scrollArea)

        styles = self.mapOpts['styles']
        bgCol = "#ffff66"#"rgb(255, 255, 255)"
        if 'background-color' in styles:
            bgCol = styles['background-color']
        else:
            styles['background-color'] = bgCol
        self.setBackgroundColor(bgCol)

    def setStatusMessage(self,text):
        self.statusBar().showMessage(text)
        self.statusBar().setVisible(True)

    def clearStatusMessage(self):
        self.statusBar().clearMessage()
        self.statusBar().setVisible(False)

    def setBackgroundColor(self,color):
        ''' Set colour behind map layers '''
        self.imageLabel.setStyleSheet("background-color: "+color)


    def setMapBounds(self,bounds):
        ''' Set map lng lat bounds '''
        self.lngLatBounds = bounds
        pb = MapUtils.projectedBounds(self.epsg4326,self.proj,bounds.toList())
        self.projBounds.fromList(pb)

    def setViewBounds(self):
        ''' Set map dimensions from canvas size
            Set projection to view transform
            Render layers
        '''
        maxW = self.canvasW
        maxH = self.canvasH

        projW = self.projBounds.width
        projH = self.projBounds.height
        if projW/maxW > projH/maxH:
            self.viewW = maxW
            self.projToViewScale = self.viewW/projW
            self.viewH = projH*self.projToViewScale
        else:
            self.viewH = maxH
            self.projToViewScale = self.viewH/projH
            self.viewW = projW*self.projToViewScale

        self.imageLabel.resize(self.canvasW,self.canvasH)
        print('viewW,viewH:',self.viewW,self.viewH)


    def updateCanvasSize(self,w,h):
        ''' Resize canvas and render layers '''
        self.canvasW = w
        self.canvasH = h
        self.setViewBounds()
        for layer in self.layers:
            layer.updateCanvasSize()

    def updateBounds(self,bounds):
        ''' Update map lng lat bounds, reproject and render '''

        self.setMapBounds(bounds)
        self.setViewBounds()

        for layer in self.layers:
            layer.project()
            layer.clearImage()
            layer.renderImage()

    def updateProjection(self,proj4Str):
        ''' Update map Proj4 projection, reproject and render '''
        self.proj=pyproj.Proj(proj4Str)
        self.updateBounds(self.lngLatBounds)


    def paintEvent(self, event):
        '''  Map rendering initiated by MapWidget '''
        # qp = QPainter()
        # qp.begin(self)
        # qp.end()
        pass


    def render(self,event,qp):
        ''' Render map layers '''
        for layer in self.layers:
            if layer.image:
                qp.setOpacity(layer.getOpacity())
                if type(layer.image) is QImage:
                    qp.drawImage(0,0,layer.image)
                elif type(layer.image) is QPixmap:
                    qp.drawPixmap(0,0,layer.image)

        if self.isOverlay:
            self.renderOverlay(qp)


    def renderOverlay(self,qp):
        qp.setFont(QFont('Arial',15,50))
        qp.setPen("#999999")
        qp.drawText(15,self.viewH-15,"Overlay text")

    def projPoint(self,lng,lat,projSrc='+init=epsg:4326'):
        ''' Project point from projSrc to map projection '''
        try:
            pt = pyproj.transform(projSrc,self.proj,lng,lat)
            return [pt[0],pt[1]]
        except RuntimeError as e:
            return None

    def pointToView(self,px,py):
        ''' Projected point to view coords '''
        pc = self.projBounds.getCentre()
        vx = self.canvasW/2 + (px-pc[0])*self.projToViewScale
        vy = self.canvasH/2 - (py-pc[1])*self.projToViewScale
        return[vx,vy]

    def viewToLngLat(self,x,y):
        ''' View coords to lng lat '''
        pc = self.projBounds.getCentre()
        px = pc[0] + (x-self.canvasW/2)/self.projToViewScale
        py = pc[1] - (y-self.canvasH/2)/self.projToViewScale
        try:
            pt = pyproj.transform(self.proj,self.epsg4326,px,py)
            return[pt[0],pt[1]]

        except RuntimeError as e:
            return None

    def getCaptureName(self):
        ''' Get image capture filename and format. Override for custom image capture. '''
        dtStr = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]
        format = "png"
        return "grab_"+dtStr+"."+format,format


    def captureView(self):
        ''' Capture map image '''
        path = ""
        if 'capture_path' in self.mapOpts:
            path = self.mapOpts['capture_path']

        name,format = self.getCaptureName()
        filename = path+name
        self.widgetCapture(self.imageLabel,filename,format)

        # filename = path+"draw_"+dtStr+"."+format
        # self.layerCapture(filename,format)

    def widgetCapture(self,widget, filename, fileformat='png'):
        ''' Capture map image using QPixmap.grabWidget '''
        pixmap =  QPixmap.grabWidget(widget,0,0,self.canvasW,self.canvasH)
        pixmap.save(filename, fileformat) # ,60


    def layerCapture(self, filename, fileformat='png'):
        ''' Capture map by rendering to Qimage '''
        image = QImage(self.canvasW,self.canvasH,QImage.Format_ARGB32)
        image.fill(QColor(255, 255, 255, 255).rgba())

        qp = QPainter(image)
        qp.setRenderHint(QPainter.Antialiasing)
        self.render(None,qp)
        qp.end()

        image.save(filename, fileformat)

    def setRenderCallback(self, callback):
        self.renderCallback = callback

    def setMousePosCallback(self, callback):
        self.mousePosCallback = callback

    def onMouseMove(self, x, y):
        ''' Called by MapWidget to display mouse lnglat '''
        if self.mousePosCallback:
            p = self.viewToLngLat(x,y)
            if p==None:
                txt = ""
            else:
                txt = "{:.5f}, {:.5f}".format(p[0],p[1])
            self.mousePosCallback(txt)

    def setOverlay(self, txt, x, y):
        self.overlay = txt





class MapDialog(QDialog):
    ''' Map Interface Components. Override for custom components '''

    def __init__(self,view):

        self.view = view
        self.mapOpts = view.mapOpts
        QDialog.__init__(self,view)
        self.dialogW = 550
        self.dialogH = 800
        # Width of edit boxes
        self.editW = 400

        self.setWindowTitle('Map Dialog')
        self.setMinimumWidth(self.dialogW)
        self.setMinimumHeight(self.dialogH)
        # Set position of the dialog
        self.setGeometry(QRect(QPoint(view.mapToGlobal(QPoint(view.size().width()+10,0))), self.size()))

        # Set dialog scroll area
        self.scrollArea = QScrollArea(self)
        self.scrollArea.setWidgetResizable(True)
        self.scrollArea.setFrameShape(QFrame.NoFrame)
        self.scrollAreaWidgetContents = QWidget(self.scrollArea)
        self.scrollAreaWidgetContents.setGeometry(QRect(0, 0, self.dialogW, self.dialogH))
        self.scrollArea.setWidget(self.scrollAreaWidgetContents)

        # dialog scroll area layout
        self.layoutV = QVBoxLayout(self)
        self.layoutV.setContentsMargins(0,10,0,10)
        self.layoutV.addWidget(self.scrollArea)

        # dialog scroll area contents layout
        self.layout = QVBoxLayout(self.scrollAreaWidgetContents)
        self.form_layout = QFormLayout()
        self.layout.addLayout(self.form_layout)

        self.uiList = []
        self.addDefaultUI()


    def addDefaultUI(self):
        ''' UI for Canvas size, projection string, Bounds lnglat, '''
        # Canvas
        self.canvas_edit = QLineEdit(self)
        self.canvas_edit.setText(str(self.view.canvasW)+','+str(self.view.canvasH))
        self.canvas_edit.setFixedWidth(self.editW)
        self.form_layout.addRow('Canvas Size', self.canvas_edit)
        self.canvas_edit.returnPressed.connect(self.on_canvas_submit)

        self.view_edit = QLineEdit(self)
        self.view_edit.setFixedWidth(self.editW)
        self.view_edit.setReadOnly(True)
        self.form_layout.addRow('Bounds Size', self.view_edit)
        self.updateViewBounds()

        # Projection
        projList = ["+init=epsg:4326", # LngLat
                    "+init=epsg:3857 +units=m", # Web Mercator
                    "+proj=robin +lon_0=0 +x_0=0 +y_0=0 +ellps=WGS84 +datum=WGS84 +units=m +no_defs", # Robinson
                    "+proj=laea +lat_0=90 +lon_0=-40 +x_0=0 +y_0=0 +ellps=WGS84 +datum=WGS84 +units=m +no_defs" # Albers Equal Area Conic (aea)
        ]
        self.proj_edit = QLineEdit(self)
        completer = QCompleter(projList, self)
        completer.setCaseSensitivity(Qt.CaseInsensitive)
        completer.setCompletionMode(QCompleter.UnfilteredPopupCompletion)
        self.proj_edit.setCompleter(completer)
        self.proj_edit.setText(self.view.proj.srs)
        self.proj_edit.setFixedWidth(self.editW)

        self.form_layout.addRow('Projection', self.proj_edit)
        self.proj_edit.returnPressed.connect(self.on_proj_submit)

        # Map Bounds
        self.bounds_edit = QLineEdit(self)
        boundsList = self.view.lngLatBounds.toList()
        boundsStr = ",".join(map(str,boundsList))
        self.bounds_edit.setText(boundsStr)
        self.bounds_edit.setFixedWidth(self.editW)

        self.form_layout.addRow('Bounds', self.bounds_edit)
        self.bounds_edit.returnPressed.connect(self.on_bounds_submit)

        # Background colour
        self.bg_edit = QLineEdit(self)
        self.bg_edit.setText(self.mapOpts['styles']['background-color'])
        self.bg_edit.setFixedWidth(self.editW)
        self.form_layout.addRow('Background', self.bg_edit)
        self.bg_edit.returnPressed.connect(self.on_bg_submit)

    def updateViewBounds(self):
        self.view_edit.setText("{:.2f}, {:.2f}".format(self.view.viewW,self.view.viewH))

    def addGeojsonUI(self,layer=None,height=100):
        ''' UI for Geojson styles '''
        if layer==None:
            geojsonLayers = self.view.getLayersByType('geojson')
            if len(geojsonLayers)>0:
                layer = geojsonLayers[0]

        if layer:
            geojsonEdit = QPlainTextEdit(self)
            geojsonStr = json.dumps(layer.styles, sort_keys=True, indent=4, separators=(',', ': '))
            geojsonEdit.setPlainText(geojsonStr)
            geojsonEdit.setFixedWidth(self.editW)
            geojsonEdit.setFixedHeight(height)
            label = QLabel()
            label.setText('Geojson\n'+layer.id)
            label.setAlignment(Qt.AlignRight)
            self.form_layout.addRow(label, geojsonEdit)
            # Update button
            geojsonButton = QPushButton('Update Geojson', self)
            geojsonButton.setAutoDefault(False)
            self.form_layout.addRow('',geojsonButton)
            geojsonButton.clicked.connect(lambda: self.on_data_update_click(geojsonEdit,layer))

            self.uiList.append(geojsonEdit)
            self.uiList.append(geojsonButton)



    def addDataUI(self,layer=None,height=150):
        ''' UI for data styles '''
        if layer==None:
            dataLayers = self.view.getLayersByType('data')
            if len(dataLayers)>0:
                layer = dataLayers[0]

        if layer:
            dataEdit = QPlainTextEdit(self)
            #styleStr = json.dumps(dataLayers[0].styles['property-styles'], sort_keys=True, indent=4)#, separators=(',', ': '))
            # Render JSON with no line breaks between list items
            styleStr = Utils.to_json(layer.styles)
            dataEdit.setPlainText(styleStr)
            dataEdit.setFixedWidth(self.editW)
            dataEdit.setFixedHeight(height)
            label = QLabel()
            label.setText('Data Layer\n'+layer.id)
            label.setAlignment(Qt.AlignRight)
            self.form_layout.addRow(label, dataEdit)
            dataUpdateButton = QPushButton('Update Data Styles', self)
            dataUpdateButton.setAutoDefault(False)
            self.form_layout.addRow('',dataUpdateButton)
            dataUpdateButton.clicked.connect(lambda: self.on_data_update_click(dataEdit,layer))

            self.uiList.append(dataEdit)
            self.uiList.append(dataUpdateButton)

    def addStatus(self):
        ''' Display function progress '''
        self.statusBox = QHBoxLayout()
        self.statusBox.addStretch(1)
        self.status = QLabel()
        self.statusBox.addWidget(self.status)
        self.layoutV.addLayout(self.statusBox)
        self.view.setRenderCallback(self.setStatusText)

    def setStatusText(self,txt):
        self.status.setText(txt)

    def addMousePos(self):
        ''' Display mouse lnglat '''
        self.mousePosEdit = QLineEdit(self)
        self.mousePosEdit.setText('')
        self.mousePosEdit.setFixedWidth(self.editW)
        self.form_layout.addRow('Mouse Lng,Lat', self.mousePosEdit)
        self.view.setMousePosCallback(self.setMousePosText)

    def setMousePosText(self,txt):
        self.mousePosEdit.setText(txt)

    def addCaptureButton(self):
        ''' Map image capture button '''
        # Add stretch to separate the form layout from the button
        self.layout.addStretch(1)

        # Create a horizontal box layout to hold the button
        self.button_box = QHBoxLayout()
        self.button_box.addStretch(1)

        # Capture button
        self.capture_button = QPushButton('Save Image', self)
        self.capture_button.setAutoDefault(False)
        self.button_box.addWidget(self.capture_button)
        self.capture_button.clicked.connect(self.on_capture_click)

        # Add the button box to the bottom of the main VBox layout
        self.layout.addLayout(self.button_box)


    @Slot()
    def on_canvas_submit(self):
        val = str(self.canvas_edit.text())
        if val:
            vals = map(int, val.split(','))
            self.view.updateCanvasSize(vals[0],vals[1])
            self.updateViewBounds()
            self.view.repaint()

    @Slot()
    def on_proj_submit(self):
        val = str(self.proj_edit.text())
        if val:
            try:
                proj=pyproj.Proj(val)
                self.view.updateProjection(val)
                self.updateViewBounds()
                self.view.repaint()
            except (RuntimeError,AttributeError) as e:
                print ("Invalid Projection", e)


    @Slot()
    def on_bounds_submit(self):
        val = str(self.bounds_edit.text())
        if val:
            boundsList = map(float, val.split(','))
            bounds = Rectangle()
            bounds.fromList(boundsList)
            self.view.updateBounds(bounds)
            self.updateViewBounds()
            self.view.repaint()

    @Slot()
    def on_bg_submit(self):
        val = str(self.bg_edit.text())
        if val:
            self.view.setBackgroundColor(val)



    @Slot()
    def on_data_update_click(self,edit,layer):
        jsonStr = str(edit.toPlainText())
        try:
            jsonObj = json.loads(jsonStr)
        except ValueError as e:
            print('Error parsing json:',e)
            return

        layer.setStyles(jsonObj)
        self.view.repaint()


    @Slot()
    def on_capture_click(self):
        self.view.captureView()




if __name__ == '__main__':

    # Example Geojson layer, point data layers, and Map options
    config_obj = {
        "layers":[
            {
                "type":"geojson",
                "id":"world_borders",
                "geojson":"../test_data/tm_world_borders_simpl.geojson",
                "proj":"+init=EPSG:4326",
                "styles":{"line-width":1.0,
                         "line-color":"#999999aa",
                         "fill-color":"#ccccccaa"
                }
            },
            {
                "type":"data",
                "id":"wiki_arz",
                "path":"../test_data/wikipedia/",
                "datatype":"csv",
                "files":["wiki_arz__geo_tags__info__edits.tsv"],
                "delimiter":"\t",
                "quotechar":"\"",
                "fields":[
                    {"id":"item_id",    "field":"page_id_pag",  "type":"string",    "name":"Page ID"},
                    {"id":"title",      "field":"page_title",   "type":"string",    "name":"Title"},
                    {"id":"page_len",   "field":"page_len",     "type":"int",       "name":"Page Length"},
                    {"id":"created",    "field":"first_edit_timestamp",     "type":"datetime",    "name":"Last Edit", "format":"%Y%m%d%H%M%S"},
                    {"id":"minor_edits","field":"minor_edits",  "type":"int",       "name":"Minor Edits"},
                    {"id":"gt_primary", "field":"gt_primary",   "type":"int",       "name":"Primary"},
                    {"id":"lat",        "field":"gt_lat",       "type":"float",     "name":"Latitude"},
                    {"id":"lng",        "field":"gt_lon",       "type":"float",     "name":"Longitude"}

                ],
                "proj":"+init=EPSG:4326",
                "styles":{
                    "point-color":"#00000099",
                    "point-size":1.3

                }

            }

        ],

        "mapOpts":{
            "bounds":[-180,-85,180,85],
            "canvasSize":[1000,800],
            "proj":"+init=epsg:3857",
            "styles":{"background-color":"#ffffff"},
            "capture_path":"../grabs/"
        }
    }
    app = QApplication(sys.argv)
    m = MapQt(config_obj)

    dialog = MapDialog(m)
    layers = config_obj['layers']
    for layerOpts in layers:
        t = layerOpts['type']
        if t=='geojson':
            l = GeojsonLayer(m,layerOpts)
            m.addLayer(l)
            dialog.addGeojsonUI(l)

        elif t=='data':
            l = PointDataLayer(m,layerOpts)
            m.addLayer(l)
            dialog.addDataUI(l)

    dialog.addMousePos()
    dialog.addCaptureButton()
    dialog.addStatus()
    dialog.show()
    m.setOverlay("test text",0,0)

    m.update()
    sys.exit(app.exec_())