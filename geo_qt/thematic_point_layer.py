'''
ThematicPointLayer is a base class for rendering thematic maps from point data.
Data properties and functions are mapped to point and text styles.
The styles are specified in JSON format.

Examples

1. Renders text with property page_len mapped to font size and alpha, constant font colour

"styles":{
    "font-size":{
        "property":"page_len",
        "values":[0,1000,2000,5000],
        "sizes":[3,5,15,30]

    },
    "font-alpha":{
        "property":"page_len",
        "values":[0,1000,2000,5000],
        "alphas":[1.0,1.0,0.7,0.1]

    },
    "font-color":"#999999",
}

2. Renders text with property page_len mapped to font size,
random font color between two hex values, constant font alpha

"styles":{
    "font-size":{
        "property":"page_len",
        "values":[0,1000,2000,5000],
        "sizes":[3,5,15,30]

    },
    "font-color":{
        "fn":"random",
        "colors":["#009900","#0000ff"]
    },
    "font-alpha":0.7,
}


3. Renders points with property page_len mapped to point size and colour, constant alpha

"styles":{
    "point-size":{
        "property":"page_len",
        "values":[0,1000,2000,5000],
        "sizes":[3,5,7,10]

    },
    "point-alpha":0.5,
    "point-color":{
        "property":"page_len",
        "values":[0,1000,2000,5000],
        "colors":["#ff0000","#ffff00","#00ffff","#ff00ff"]
    }
}

'''

import colorsys
import random
import string

from map_qt import *


class ThematicPointLayer(PointDataLayer):
    ''' Base class for thematic point data layer'''
    def __init__(self,map,opts):
        self.pStyles = None
        self.defaultFeatureStyles = {}
        self.thematicStyles = []
        super(ThematicPointLayer,self).__init__(map, opts)

    def loadData(self):
        super(ThematicPointLayer,self).loadData()
        for item in self.data:
            # Add Feature styles dict to DataItem
            item.fs = {}

        self.processStyles()

    def setTextLength(self,length):
        for item in self.data:
            item.text = item.title.decode('utf8')
            idx = string.rfind(item.text,' ',0,length)
            if idx==-1:
                idx = length
            item.text = item.text[:idx]

    def setStyles(self,styles):
        ''' Upate styles dict and render '''
        self.styles = styles
        self.processStyles()
        self.renderImage()

    def processStyles(self):
        ''' Set default styles and thematic styles '''
        t0 = time.time()

        # clear list of styles
        self.thematicStyles = []

        # copy style dict to use for internal data
        self.pStyles = copy.deepcopy(self.styles)
        styles = self.pStyles

         # Feature Styles

        self.defaultFeatureStyles = {}
        fs = self.defaultFeatureStyles

        styleToProp = {'font-size':'fontSize','font-color':'fontColor','font-alpha':'fontAlpha','font-weight':'fontWeight',
                       'font-line-color':'fontLineColor','font-line-width':'fontLineWidth',
                       'text-length':'textLength',
                       'point-size':'ptSize','point-color':'ptColor','point-alpha':'ptAlpha',
                       'point-line-color':'ptLineColor','point-line-width':'ptLineWidth'}


        fs['isText'] = any(style for style in styles if style[:4]=='font' or style[:4]=='text')
        fs['isPoint'] = any(style for style in styles if style[:5]=='point')

        lastTextLength = 0
        # initalise default styles
        if fs['isText']:
            fs['fontSize'] = 10
            fs['fontColor'] = QColor()
            fs['fontAlpha'] = 1.0
            fs['fontWeight'] = 99
            fs['fontLineColor'] = QColor()
            fs['fontLineWidth'] = 0.0
            fs['fontLineThresh'] = 20
            fs['fontFamily'] = 'Arial'
            if 'textLength' in fs:
                lastTextLength = fs['textLength']
            else:
                fs['textLength'] = 2


        if fs['isPoint']:
            fs['ptSize'] = 2.0
            fs['ptColor'] = QColor()
            fs['ptAlpha'] = 1.0
            fs['ptLineColor'] = QColor()
            fs['ptLineWidth'] = 0.0

        # set default styles from styles dict
        for styleId in styles:
            style = styles[styleId]

            # Create hsv colours from hex for interpolation
            if styleId[-5:]=='color':
                if 'colors' in style:
                    hsvColors = []
                    rgbColors = []
                    for hex in style['colors']:
                        c = MapUtils.hex2rgba(hex)
                        hsv = colorsys.rgb_to_hsv(float(c[0])/255,float(c[1])/255,float(c[2])/255)
                        rgbColors.append(c)
                        hsvColors.append((hsv[0]*255,hsv[1]*255,hsv[2]*255))
                    style['rgbColors'] = rgbColors
                    style['hsvColors'] = hsvColors

            # Set default styles
            if not(type(style) is dict) and not(type(style) is list):
                if styleId=='font-size':
                    fs['fontSize'] = float(style)
                elif styleId=='font-color':
                    fs['fontColor'] = MapUtils.hex2qcolor(style)
                    if "font-alpha" in styles and not(type(styles['font-alpha']) is dict):
                        fs['fontColor'].setAlphaF(styles['font-alpha'])
                    else:
                        fs['fontAlpha'] = fs['fontColor'].alphaF()
                elif styleId=='font-alpha':
                    fs['fontAlpha'] = float(style)
                elif styleId=='font-weight':
                    fs['fontWeight'] = int(style)
                elif styleId=='font-family':
                    fs['fontFamily'] = style
                elif styleId=='font-line-width':
                    fs['fontLineWidth'] = float(style)
                elif styleId=='font-line-threshold':
                    fs['fontLineThresh'] = float(style)
                elif styleId=='font-line-color':
                    fs['fontLineColor'] = MapUtils.hex2qcolor(style)
                    if "font-alpha" in styles and not(type(styles['font-alpha']) is dict):
                        fs['fontLineColor'].setAlphaF(styles['font-alpha'])

                elif styleId=='point-size':
                    fs['ptSize'] = float(style)
                elif styleId=='point-color':
                    fs['ptColor'] = MapUtils.hex2qcolor(style)
                    if "point-alpha" in styles and not(type(styles['point-alpha']) is dict):
                        fs['ptColor'].setAlphaF(styles['point-alpha'])
                    else:
                        fs['ptAlpha'] = fs['ptColor'].alphaF()
                elif styleId=='point-alpha':
                    fs['ptAlpha'] = float(style)
                elif styleId=='point-line-color':
                    fs['ptLineColor'] = MapUtils.hex2qcolor(style)
                elif styleId=='point-line-width':
                    fs['ptLineWidth'] = float(style)
                elif styleId=='text-length':
                    fs['textLength'] = int(style)


            else:
                if styleId in styleToProp:
                    self.thematicStyles.append(styleToProp[styleId])

        if fs['isText']:
            if type(fs['textLength']) is int:
                if fs['textLength']!=lastTextLength:
                    self.setTextLength(fs['textLength'])
        # Add styles to point data
        self.setDataStyles()

        t1 = time.time()
        print('Process Styles:',t1-t0)



    def setFeatureStyles(self,styles,item):
            ''' Add styles to individual data items '''
            item.fs = {}
            fs = item.fs

            for styleId in styles:
                style = styles[styleId]

                if type(style) is dict:

                    norm = 0.0
                    idx0 = 0
                    idx1 = 1
                    if 'property' in style:
                        p = style['property']
                        d = getattr(item, p)
                        if type(d)==str:
                            idx0 = style['values'].index(d) if d in style['values'] else len(style['values'])
                        else:
                            norm,idx0 = Utils.interpParams(d,style['values'])

                        if norm == 0.0:
                            idx1 = idx0
                        else:
                            idx1 = idx0+1

                    elif 'fn' in style:
                        if style['fn']=='random':
                            norm = random.random()
                            idx0 = 0
                            idx1 = 1

                    s = styleId
                    if s=="font-size":
                        if 'sizes' in style:
                            fs['fontSize'] = Utils.interp(norm,style['sizes'][idx0],style['sizes'][idx1])


                    elif s=="font-alpha":
                        if 'alphas' in style:
                            fs['fontAlpha'] = Utils.interp(norm,style['alphas'][idx0],style['alphas'][idx1])
                            if not 'fontColor' in fs:
                                fs['fontColor'] = QColor()
                            fs['fontColor'].setAlphaF(fs['fontAlpha'])

                    elif s=="font-color":
                        if 'colors' in style:
                            hsv = Utils.interpHSV(norm,style['hsvColors'][idx0],style['hsvColors'][idx1])
                            if not 'fontColor' in fs:
                                fs['fontColor'] = QColor()
                                if not 'fontAlpha' in fs:
                                    fs['fontAlpha'] = self.defaultFeatureStyles['fontAlpha']
                            fs['fontColor'].setHsv(hsv[0], hsv[1], hsv[2], fs['fontAlpha']*255)

                    elif s=="point-size":
                        if 'sizes' in style:
                            fs['ptSize'] = Utils.interp(norm,style['sizes'][idx0],style['sizes'][idx1])

                    elif s=="point-alpha":
                        if 'alphas' in style:
                            fs['ptAlpha'] = Utils.interp(norm,style['alphas'][idx0],style['alphas'][idx1])
                            if not 'ptColor' in fs:
                                fs['ptColor'] = QColor()
                            fs['ptColor'].setAlphaF(fs['ptAlpha'])

                    elif s=="point-color":
                        if 'colors' in style:
                            hsv = Utils.interpHSV(norm,style['hsvColors'][idx0],style['hsvColors'][idx1])
                            if not 'ptColor' in fs:
                                fs['ptColor'] = QColor()
                                if not 'ptAlpha' in fs:
                                    fs['ptAlpha'] = self.defaultFeatureStyles['ptAlpha']
                            fs['ptColor'].setHsv(hsv[0], hsv[1], hsv[2], fs['ptAlpha']*255)



    def setDataStyles(self):
        ''' Add styles to dataset '''
        items = self.data
        nItems = len(items)
        t0 = time.time()

        for i in range(0,nItems):
            item = items[i]
            if i%1000 == 0 or i == nItems-1:
                self.progress("Set styles:",t0,i,nItems-1)

            # if self.map.lngLatBounds.within(item.lng,item.lat):
            # if item.vx and item.vy:

            self.setFeatureStyles(self.pStyles,item)



    def render(self,qp):
        ''' Render data '''

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

        fs = copy.deepcopy(self.defaultFeatureStyles)
        coords = {}

        isOverlay = True
        if 'overlay-enabled' in self.styles:
            if int(self.styles['overlay-enabled'])==0:
                isOverlay = False

        for i in range(0,nItems):
            item = items[i]
            if i%1000 == 0 or i == nItems-1:
                self.progress("Render data:",t0,i,nItems-1)

            if self.filterItem(item):

                coordStr = str(int(item.vx))+'_'+str(int(item.vy))
                if not (coordStr in coords) or isOverlay:
                    coords[coordStr]=1

                    for styleId in self.thematicStyles:
                        if styleId in item.fs:
                            fs[styleId] = item.fs[styleId]

                    self.renderFeature(qp,item,fs,1.0)


        t1 = time.time()
        print('Data Render:',t1-t0)



    def renderFeature(self,qp,item,fs,alpha):
        '''
        Render text and or point
        :param qp: QPainter
        :param item: DataItem
        :param fs: Combined default and DateItem styles
        :param alpha: alpha multiplier used by timeline
        '''
        if fs['isText']:
            self.renderText(qp,item,fs,alpha)

        if fs['isPoint']:
            self.renderPoint(qp,item,fs,alpha)


    def renderText(self,qp,item,fs,alpha):

        textW = 1000
        textH = 400

        a =  fs['fontAlpha']
        a*=alpha
        fs['fontColor'].setAlphaF(a)

        self.font.setPointSizeF(fs['fontSize'])

        if fs['fontLineWidth']>0.0 and fs['fontSize'] > fs['fontLineThresh']:

            fm = QFontMetrics(self.font)
            pixW = fm.width(item.text)
            pixH = fm.height()

            # background rect
            # if alpha>0.7:
            #     qp.setPen(Qt.NoPen)
            #     qp.setBrush(QColor(255,255,255,220))
            #     qp.drawRect(item.vx-pixW/2,item.vy+3-pixH/2,pixW,pixH)


            self.font.setStyleStrategy(QFont.ForceOutline)
            path = QPainterPath()
            path.addText(item.vx-pixW/2,item.vy+pixH/2, self.font, item.text)
            fs['fontLineColor'].setAlphaF(a)
            qp.setPen(QPen(fs['fontLineColor'],fs['fontLineWidth']))
            qp.setBrush(fs['fontColor'])
            qp.drawPath(path)
            self.font.setStyleStrategy(QFont.PreferAntialias)

        else:
            qp.setPen(fs['fontColor'])
            qp.setFont(self.font)
            qp.drawText(QRect(item.vx-textW/2, item.vy-textH/2,textW,textH), Qt.AlignCenter,item.text)


    def renderPoint(self,qp,item,fs,alpha):

        if fs['ptLineWidth']>0.0:
            qp.setPen(QPen(fs['ptLineColor'],fs['ptLineWidth']))
        else:
            qp.setPen(Qt.NoPen)

        a =  fs['ptAlpha']
        a*=alpha
        fs['ptColor'].setAlphaF(a)
        qp.setBrush(fs['ptColor'])

        if fs['ptSize']>2:
            qp.drawEllipse(item.vx, item.vy, fs['ptSize'], fs['ptSize'])
        else:
            qp.drawRect(QRectF(int(item.vx-fs['ptSize']/2), int(item.vy-fs['ptSize']/2), fs['ptSize'], fs['ptSize']))


    def filterItem(self,item):
        b = item.vx and item.vy #self.map.lngLatBounds.within(item.lng,item.lat)
        return b

    def getItemIndices(self):
        indices = [0,len(self.data)]
        return indices

    def renderGrid(self,qp):
        ''' Render projected geometry using option styles. Override for custom styles and rendering. '''

        t0 = time.time()
        items = self.data
        nItems = len(items)

        qp.setCompositionMode(QPainter.CompositionMode_SourceOver)

        # Get Styles
        ptSize = 1.0
        colStrs = ["#bbbbbb","#aaaaaa","#999999","#888888","#777777","#555555","#333333","#000000"]
        values = [1,2,3,5,10,25,50,100]

        isPtInt=False
        if ptSize == int(ptSize):
            isPtInt = True

        if 'grid' in self.styles:
            gridStyles = self.styles['grid']
        if 'size' in gridStyles:
            ptSize = float(gridStyles['size'])
        if 'colors' in gridStyles:
            colStrs = gridStyles['colors']

        colors = []
        for col in colStrs:
            colors.append(MapUtils.hex2qcolor(col))

        if 'values' in gridStyles:
            valueStrs = gridStyles['values']
            values = []
            for val in valueStrs:
                values.append(int(val))

        nColors = len(colors)
        qp.setPen(Qt.NoPen)

        coords={}

        indices = self.getItemIndices()

        for i in range(indices[0],indices[1]):
            item = items[i]
            if i%1000 == 0 or i == nItems-1:
                self.progress("Render data:",t0,i,nItems-1)


            if self.filterItem(item):
                coordStr = str(int(item.vx/ptSize))+'_'+str(int(item.vy/ptSize))
                if not (coordStr in coords):
                    coords[coordStr]=1
                else:
                    coords[coordStr]+=1

        valFreq = [0] * len(values)
        for coord in coords:
            val = coords[coord]
            pt = coord.split('_')
            px = int(float(pt[0])*ptSize)
            py = int(float(pt[1])*ptSize)

            col = colors[-1]
            idx = len(values)-1
            for i in range(0,nColors):
                if val<=values[i]:
                    col = colors[i]
                    idx = i
                    break
            valFreq[idx]+=1
            qp.setBrush(col)


            qp.drawRect(QRectF(int(px-ptSize/2), int(py-ptSize/2), ptSize, ptSize))



        print(valFreq, values)
        t1 = time.time()
        print 'Render Data:', t1-t0


if __name__ == '__main__':

    wiki_config = {
    "layers":[
        {
            "type":"geojson",
            "id":"world_borders",
            "geojson":"../test_data/tm_world_borders_simpl.geojson",
            "proj":"+init=EPSG:4326",
            "styles":{"line-width":1.0,
                     "line-color":"#999999aa",
                     "fill-color":"#ccccccaa",
                     "background-color":"#999999aa"
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
                    "values":[0,1000,2000,5000],
                    "sizes":[3,5,15,30]

                },
                "font-alpha":{
                    "property":"page_len",
                    "values":[0,1000,2000,5000],
                    "alphas":[1.0,1.0,0.7,0.5]

                },
                # "font-color":{
                #     "fn":"random",
                #     # "colors":["#ff0000","#00ff00"]
                #     "colors":["#cccccc","#ffffff"]
                # },
                "font-color":"#333333",
                "font-line-color":"#ff0000",
                "font-line-width":0.25,
                "font-line-threshold":20,
                "font-weight":75,
                "point-color":"#999999",
                "point-size":2.0,
                "point-alpha":0.5


            }

        }

    ],

    "mapOpts":{
        "bounds":[-180,-85,180,85],
        "canvasSize":[1500,1200],
        "proj":"+init=epsg:3857",
        "styles":{"background-color":"#ffffff"}

    }
    }

    app = QApplication(sys.argv)
    m = MapQt(wiki_config)

    layers = wiki_config['layers']
    for layerOpts in layers:
        t = layerOpts['type']

        if t=='geojson':
            l = GeojsonLayer(m,layerOpts)
        elif t=='data':
            l = ThematicPointLayer(m,layerOpts)

        m.addLayer(l)


    dialog = MapDialog(m)
    dialog.addGeojsonUI()
    dialog.addDataUI()
    dialog.addCaptureButton()
    dialog.addStatus()
    dialog.show()
    m.update()
    sys.exit(app.exec_())