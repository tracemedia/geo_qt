'''
Map, layer and dialog classes for timeline map

TimelineMap: Overrides MapQt to include date ranges

TimelineDataLayer: Overrides ThematicPointLayer with date range as rendering parameter

TimelineDialog: Overrides MapDialog with timeline UI components

'''


import math
from thematic_point_layer import ThematicPointLayer
from map_qt import *

class TimelineDataLayer(ThematicPointLayer):
    ''' ThematicPointLayer with data and view date ranges '''
    def __init__(self,map,opts):
        self.dataMinDate = None
        self.dataMaxDate = None
        super(TimelineDataLayer,self).__init__(map, opts)


    def loadData(self):
        ''' Override includes calculation of min and max data date range '''
        datatype = self.opts['datatype']
        if datatype == "csv":
            self.data = LoaderUtils.loadCSV(self.opts)

        items = self.data
        nItems = len(items)

        optMinDate = Utils.str2utc(self.opts["animation"]["min_date"])
        optMaxDate = Utils.str2utc(self.opts["animation"]["max_date"])
        # "max_date":"2015-01-01 00:00:00",

        maxDate = Utils.str2utc('2000-01-01','%Y-%m-%d')
        minDate = datetime.now(UTC())
        for i in range(0,nItems):
            item = items[i]
            item.fs = {}
            if item.created<minDate and item.created>=optMinDate:
                minDate = item.created
            if item.created>maxDate and item.created<=optMaxDate:
                maxDate = item.created

        self.dataMinDate = copy.deepcopy(minDate)
        self.dataMaxDate = copy.deepcopy(maxDate)

        self.processStyles()

    def filterItem(self,item):
        # b =  self.map.lngLatBounds.within(item.lng,item.lat) and item.created>self.map.viewMinDate and item.created<self.map.viewMaxDate
        b = item.vx and item.vy and item.created>self.map.viewMinDate and item.created<self.map.viewMaxDate
        return b

    def getItemIndices(self):
        indices = [0,len(self.data)]
        # if data ordered by date, find min and max indices
        if 'orderby' in self.opts:
            if self.opts['orderby']=='created':
                indices = self.getFeatureIndicesByDate([self.map.viewMinDate, self.map.viewMaxDate])
                if indices[0]==-1:
                    indices=[0,0]
                else:
                    indices[1]+=1
        return indices


    def render(self,qp):
        ''' Use currently selected date range to render data '''
        # Map data needs to be initialised before rendering
        if self.map.viewMinDate == None:
            return

        if 'grid' in self.styles:
            self.renderGrid(qp)
            return

        items = self.data
        nItems = len(items)
        t0 = time.time()
        qp.setCompositionMode(QPainter.CompositionMode_SourceOver)

        if self.defaultFeatureStyles['isText']:
            weight = self.defaultFeatureStyles['fontWeight']
            family = self.defaultFeatureStyles['fontFamily']
            self.font = QFont(family, self.defaultFeatureStyles['fontSize'], weight)
            qp.setFont(self.font)

        tf = 0.2
        if 'transition-fraction' in self.styles:
            tf = self.styles['transition-fraction']

        minDate = self.map.viewMinDate
        maxDate = self.map.viewMaxDate

        viewSecs = (maxDate-minDate).total_seconds()

        fs = copy.deepcopy(self.defaultFeatureStyles)
        coords = {}

        indices = self.getItemIndices()

        for i in range(indices[0],indices[1]):
            item = items[i]
            if i%1000 == 0:
                self.progress("Render data:",t0,i,nItems)

            # if item.created>minDate and item.created<maxDate:
                # if self.map.lngLatBounds.within(item.lng,item.lat):
                # if item.vx and item.vy:
            if self.filterItem(item):

                # Overlap cull causes features to appear and disappear between frames - fix by pre-culling
                # coordStr = str(int(item.vx))+'_'+str(int(item.vy))
                # if not (coordStr in coords):
                # coords[coordStr]=1

                # Find alpha as function of date range and DataItem.created property
                itemSecs = (item.created-minDate).total_seconds()
                n = float(itemSecs)/viewSecs
                # alpha = math.sin(n*math.pi)
                alpha = 1.0
                # transition fraction

                if n<tf:
                    alpha = math.sin(n*0.5*math.pi/tf) # [0,0.5]
                elif n>1.0-tf:
                    alpha = math.sin(((n-(1.0-tf))/tf*0.5+0.5)*math.pi) # [0.5,1.0]

                for styleId in self.thematicStyles:
                    if styleId in item.fs:
                        fs[styleId] = item.fs[styleId]

                self.renderFeature(qp,item,fs,alpha)

        t1 = time.time()
        print('Data Render:',t1-t0)


    def getFeatureIndicesByDate(self,dateValues):
        items = self.data
        # nItems = len(items)
        retIndices = [-1, -1]
        if items[0].created > dateValues[1] or items[-1].created < dateValues[0]:
            return retIndices

        elif dateValues[0] == dateValues[1]:
            return retIndices

        else:
            retIndices[0] = self.getFeatureIndexByDate(dateValues[0], "gte")
            retIndices[1] = self.getFeatureIndexByDate(dateValues[1], "lte")
            if retIndices[1] < retIndices[0]:
                retIndices = [-1, -1]
                return retIndices

        return retIndices


    def getFeatureIndexByDate(self,dateValue, funcStr):

        items = self.data
        nItems = len(items)
        retVal = 0
        if items[0].created >= dateValue:
            retVal = 0

        elif items[-1].created <= dateValue:
            retVal = nItems - 1

        else:
            bFound = False
            count = 0
            curIndex = int(math.floor(nItems / 2))
            inc = int(nItems / 2)
            while bFound == False and count < 100:
                inc = int(math.floor(inc / 2))
                inc = max(inc, 1)

                if items[curIndex].created == dateValue:
                    bFound = True

                elif curIndex == nItems - 1:
                    if (funcStr == "lte"):
                        curIndex = nItems - 2
                    bFound = True

                elif curIndex == 0:
                    if funcStr == "gte":
                        curIndex = 1
                    bFound = True

                elif items[curIndex].created < dateValue and items[curIndex + 1].created > dateValue:
                    if funcStr == "gte":
                        curIndex += 1
                    bFound = True

                elif items[curIndex].created < dateValue:
                    curIndex += inc

                else: # items[curIndex].created>dateValue
                    curIndex -= inc


                count += 1

            retVal = curIndex

        return retVal






class TimelineMap(MapQt):

    def __init__(self,config):
        super(TimelineMap, self).__init__(config)
        self.minDate = None
        self.maxDate = None
        self.viewMinDate = None
        self.viewMaxDate = None
        self.animLayers = []

        self.isOverlay = True

        self.isPainting = False

    def addAnimLayer(self,layer):
        self.animLayers.append(layer)


    def setDateRange(self,min_dt,max_dt):
        self.minDate = min_dt
        self.maxDate = max_dt

    def setViewDateRange(self,min_dt,max_dt):
        self.viewMinDate = min_dt
        self.viewMaxDate = max_dt

    def renderAnimLayers(self):

        for l in self.animLayers:
            l.renderImage()
        self.update()

    def renderOverlay(self,qp):

        if self.viewMinDate and self.viewMinDate:
            qp.setFont(QFont('Consolas',15,10)) #  'Inconsolata'
            qp.setPen("#dddddd")
            txt = self.viewMinDate.strftime('%Y.%m.%d') + "  -  " + self.viewMaxDate.strftime('%Y.%m.%d')
            qp.drawText(15,self.canvasH-15,txt)


    def getCaptureName(self):
        id = 'anim'
        if 'id' in self.mapOpts:
            id = self.mapOpts['id']

        minStr = self.viewMinDate.strftime('%Y%m%d_%H%M%S')
        maxStr = self.viewMaxDate.strftime('%Y%m%d_%H%M%S')
        format = "png"
        return id+"_"+minStr+"_"+maxStr+"."+format,format



class TimelineDialog(MapDialog):

    def __init__(self,view):
        MapDialog.__init__(self,view)
        self.isAnim = False
        self.isCapture = False
        self.dataMinDate = None
        self.dataMaxDate = None

    def dt2qdt(self,dt):
        return  QDateTime(dt.year,dt.month,dt.day,dt.hour,dt.minute,dt.second,Qt.UTC)

    def qdt2dt(self,qdt):
        return Utils.str2utc(qdt.toString('yyyy-MM-dd hh:mm:ss'))

    def setDataDateRange(self,min_dt,max_dt):
        self.dataMinDate = min_dt
        self.dataMaxDate = max_dt

    def addTimeline(self,options,dataMinDate=None,dataMaxDate=None):

        opts = options['animation']

        if dataMinDate!=None:
            self.dataMinDate = dataMinDate
        else:
            self.dataMinDate = Utils.str2utc(opts['min_date']) #'2001-01-01 00:00:00'

        if dataMaxDate!=None:
            self.dataMaxDate = dataMaxDate
        else:
            self.dataMaxDate = Utils.str2utc(opts['max_date'])

        # qdt = self.dt2qdt(self.dataMinDate)

        self.form_layout.addRow('',QLabel())
        self.dataDateLabel = QLabel()
        self.dataDateLabel.setText(self.dataMinDate.strftime('%Y/%m/%d')+" - "+self.dataMaxDate.strftime('%Y/%m/%d'))
        self.form_layout.addRow('Data Dates:',self.dataDateLabel)



        qdtmin = self.dt2qdt(self.dataMinDate)
        qdtmax = self.dt2qdt(self.dataMaxDate)
        self.minDateEdit = QDateTimeEdit(qdtmin)
        self.minDateEdit.setMinimumDateTime(qdtmin)
        self.minDateEdit.setMaximumDateTime(qdtmax)
        self.minDateEdit.setDisplayFormat("yyyy/MM/dd hh:mm")
        self.form_layout.addRow('Min Date',self.minDateEdit)

        self.maxDateEdit = QDateTimeEdit(qdtmax)
        self.maxDateEdit.setMinimumDateTime(qdtmin)
        self.maxDateEdit.setMaximumDateTime(qdtmax)
        self.maxDateEdit.setDisplayFormat("yyyy/MM/dd hh:mm")
        self.form_layout.addRow('Max Date',self.maxDateEdit)


        self.timespan = opts['timespan_d']
        self.timespanEdit = QLineEdit()
        self.timespanEdit.setText(str(self.timespan))
        self.timespanEdit.setFixedWidth(50)

        self.form_layout.addRow('Timespan (days)', self.timespanEdit)
        self.timespanEdit.returnPressed.connect(self.onTimespanSubmit)

        self.viewMinDateEdit = QDateTimeEdit()
        self.viewMinDateEdit.setMinimumDateTime(qdtmin)
        self.viewMinDateEdit.setMaximumDateTime(qdtmax)
        self.viewMinDateEdit.setDisplayFormat("yyyy/MM/dd hh:mm:ss")
        self.form_layout.addRow('Min View Date',self.viewMinDateEdit)
        self.viewMinDateEdit.editingFinished.connect(self.viewMinDateSubmit)

        self.viewMaxDateEdit = QDateTimeEdit()
        self.viewMaxDateEdit.setMinimumDateTime(qdtmin)
        self.viewMaxDateEdit.setMaximumDateTime(qdtmax)
        self.viewMaxDateEdit.setDisplayFormat("yyyy/MM/dd hh:mm:ss")
        self.form_layout.addRow('Max View Date',self.viewMaxDateEdit)
        self.updateViewMaxDate()


        self.slider = QSlider(Qt.Horizontal)
        self.slider.setFocusPolicy(Qt.StrongFocus)
        self.slider.setTickPosition(QSlider.TicksBothSides)
        self.slider.setTickInterval(10)
        self.slider.setSingleStep(1)
        self.slider.setMinimum(0)
        self.slider.setMaximum(self.editW)
        self.slider.setFixedWidth(self.editW)
        self.form_layout.addRow('Date Slider',self.slider)
        # self.slider.sliderMoved.connect(self.onSliderMoved) # Continuous update
        self.slider.sliderReleased.connect(self.onSliderReleased)


        self.animDuration = opts['duration_s']
        self.animDurationEdit = QLineEdit()
        self.animDurationEdit.setText(str(self.animDuration))
        self.animDurationEdit.setFixedWidth(50)
        self.form_layout.addRow('Anim Duration (s)',self.animDurationEdit)

        self.fps = int(opts['fps'])
        self.fpsEdit = QLineEdit()
        self.fpsEdit.setText(str(self.fps))
        self.fpsEdit.setFixedWidth(50)
        self.form_layout.addRow('Anim fps',self.fpsEdit)


        # Start button
        self.startBut = QPushButton('Start Anim', self)
        self.startBut.setAutoDefault(False)
        self.form_layout.addWidget(self.startBut)
        self.startBut.clicked.connect(self.onStartClick)

        # Stop button
        self.stopBut = QPushButton('Stop Anim', self)
        self.stopBut.setAutoDefault(False)
        self.form_layout.addWidget(self.stopBut)
        self.stopBut.clicked.connect(self.onStopClick)

        # Capture checkbox
        self.captureToggle = QCheckBox("")
        self.form_layout.addRow('Capture Anim',self.captureToggle)
        self.captureToggle.stateChanged.connect(self.captureToggleChanged)

        self.updateMapDates()


    def updateMapDates(self):

        self.view.setDateRange(self.qdt2dt(self.minDateEdit.dateTime()),self.qdt2dt(self.maxDateEdit.dateTime()))
        self.view.setViewDateRange(self.qdt2dt(self.viewMinDateEdit.dateTime()),self.qdt2dt(self.viewMaxDateEdit.dateTime()))


    def setViewMinDateFromFraction(self,value):
        rangeSecs = self.minDateEdit.dateTime().secsTo(self.maxDateEdit.dateTime())
        secs = rangeSecs*value
        dt = self.minDateEdit.dateTime().addSecs(secs)
        self.setViewMinDate(dt)

    def setViewMinDate(self,dt):
        self.viewMinDateEdit.setDateTime(dt)
        self.updateViewMaxDate()
        # print ('setViewMinDate',self.viewMinDateEdit.dateTime())


    def updateViewMaxDate(self):
        self.viewMaxDateEdit.setDateTime(self.viewMinDateEdit.dateTime().addSecs(float(self.timespan)*Utils.SECS_IN_DAY))

    def updateFrameTime(self):
        self.fps = int(self.fpsEdit.text())
        self.animDuration = int(self.animDurationEdit.text())
        nFrames = self.fps * self.animDuration
        dateRangeSecs = self.minDateEdit.dateTime().secsTo(self.maxDateEdit.dateTime())
        secsPerFrame = dateRangeSecs/nFrames

        # print ('t0',self.viewMinDateEdit.dateTime())
        dt = self.viewMinDateEdit.dateTime().addSecs(secsPerFrame)
        self.setViewMinDate(dt)
        self.setSliderFromDate(dt)
        # print ('t1',self.viewMinDateEdit.dateTime())

    def setSliderFromDate(self,dt):
        dateRangeSecs = self.minDateEdit.dateTime().secsTo(self.maxDateEdit.dateTime())
        viewMinDateOffset = self.minDateEdit.dateTime().secsTo(self.viewMinDateEdit.dateTime())
        n = float(viewMinDateOffset)/dateRangeSecs
        self.slider.setValue(n*self.slider.maximum())

    def startAnim(self):

        self.isAnim = True
        timespanSecs = float(self.timespan)*Utils.SECS_IN_DAY
        while self.isAnim == True:
            self.updateFrameTime()
            self.updateMapDates()
            # render animation layers
            self.view.renderAnimLayers()

            QCoreApplication.instance().processEvents()

            if self.isCapture:
                self.view.captureView()


            if self.viewMinDateEdit.dateTime().secsTo(self.maxDateEdit.dateTime())<1: #timespanSecs: # animate to end
                print('End anim')
                self.stopAnim()
                break

    def stopAnim(self):
        self.isAnim = False

    def sliderUpdate(self):
        # self.stopAnim()
        value = self.slider.value()
        n = float(value)/self.slider.maximum()
        self.setViewMinDateFromFraction(n)
        self.updateMapDates()
        if self.isAnim == False:
            self.view.renderAnimLayers()


    @Slot()
    def onSliderChanged(self,value):
        self.sliderUpdate()
        # print("onSliderChanged")

    @Slot()
    def onSliderMoved(self,pos):
        self.sliderUpdate()
        # print("onSliderMoved")

    @Slot()
    def onSliderReleased(self):
        self.sliderUpdate()
        # print("onSliderReleased")

    @Slot()
    def viewMinDateSubmit(self):
        self.setSliderFromDate(self.viewMinDateEdit.dateTime())
        self.updateViewMaxDate()

    @Slot()
    def onTimespanSubmit(self):
        val = self.timespanEdit.text()
        self.timespan  = float(val)
        self.updateViewMaxDate()
        print("Time span",val)

    @Slot()
    def onStartClick(self):
        self.startAnim()

    @Slot()
    def onStopClick(self):
        self.stopAnim()

    @Slot()
    def captureToggleChanged(self,value):
        b = self.captureToggle.isChecked()
        self.isCapture = b


if __name__ == '__main__':

    wiki_config = {
    "layers":[
        {
            "type":"geojson",
            "id":"world_borders",
            "geojson":"../test_data/tm_world_borders_simpl.geojson",
            "proj":"+init=EPSG:4326",
            "styles":{"line-width":1.0,
                     "line-color":"#99999933",
                     "fill-color":"#fafafaff"
            }
        },
        {
            "type":"data",
            "id":"wiki_data",
            "path":"../test_data/wikipedia/",
            "datatype":"csv",
            "files":["wiki_arz__geo_tags__info__edits.tsv"],
            "delimiter":"\t",
            "quotechar":"\"",
            "orderby":"created",
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
                "font-size":{
                    "property":"page_len",
                    "values":[0,1000,2000,5000,10000],
                    "sizes":[3,5,7,10,30]

                },
                "font-alpha":{
                    "property":"page_len",
                    "values":[0,1000,2000,5000,1000],
                    "alphas":[1.0,1.0,0.9,0.7,0.5]

                },
                "font-line-width":0.5,
                "font-color":"#999999",

                "point-color":"#33333399",
                "point-size":2.0,
                "point-alpha":0.65,
                "transition-fraction":0.25

            },
            "animation":{
                "min_date":"2005-01-01 00:00:00",
                "max_date":"2015-01-01 00:00:00",
                "fps":25,
                "type":"range", # "cumulative"
                "timespan_d":365,
                "duration_s":100
            }

        }

    ],

    "mapOpts":{
        "id":"wiki_de",
        "bounds":[-180,-85,180,85],
        "canvasSize":[1500,1200],
        #"proj":"+proj=robin +lon_0=0 +x_0=0 +y_0=0 +ellps=WGS84 +datum=WGS84 +units=m +no_defs"
        "proj":"+init=epsg:3857",
        "styles":{"background-color":"#ffffff"},
        "capture_path":"../grabs/"

    }
    }

    app = QApplication(sys.argv)
    m = TimelineMap(wiki_config)


    layers = wiki_config['layers']
    dataOpts = None
    for layerOpts in layers:
        t = layerOpts['type']
        if t=='geojson':
            l = GeojsonLayer(m,layerOpts)
            m.addLayer(l)

        elif t=='data':
            dl = TimelineDataLayer(m,layerOpts)
            dataOpts = layerOpts
            m.addAnimLayer(dl)
            m.addLayer(dl)

    dialog = TimelineDialog(m)
    dialog.addGeojsonUI()
    dialog.addDataUI()
    dialog.addTimeline(dataOpts,dl.dataMinDate,dl.dataMaxDate)
    dialog.addMousePos()
    dialog.addCaptureButton()
    dialog.addStatus()
    dialog.show()

    m.renderAnimLayers()
    sys.exit(app.exec_())