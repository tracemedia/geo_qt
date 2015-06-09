'''
BasemapLayer uses Matplotlib Basemap to render coastlines, countries, meridians and parallels to a PySide image
http://matplotlib.org/basemap/

'''
try:
    import matplotlib
    matplotlib.use('Qt4Agg')
    matplotlib.rcParams['backend.qt4']='PySide'
    from mpl_toolkits.basemap import Basemap
    import matplotlib.pyplot as plt
    import numpy as np
except ImportError:
    print('Basemap Import Error')

from map_qt import *

class BasemapLayer(Layer):
    ''' Basemap layer. Override for custom map projections and rendering. '''

    def __init__(self,map,opts):
        ''' Initialise with map object and layer options '''
        super(BasemapLayer,self).__init__(map, opts)
        self.coastlines = []
        self.countries = []
        self.meridians = []
        self.parallels = []
        self.boundary = None
        self.basemap = None
        self.createBasemap()
        self.updateCanvasSize()


    def createBasemap(self):
        '''
        Initialise basemap from projection options.
        Covert matplotlib paths and lines to PySide QPolgons
        '''

        self.qPolys = []

        projDict = self.opts['projOpts']

        # m = Basemap(projection='robin', lat_0=0, lon_0=0, ellps='WGS84',
        #               resolution='c', area_thresh=1000.0, llcrnrlon=-180, llcrnrlat=-85, urcrnrlon=180, urcrnrlat=85)

        self.basemap = Basemap(**projDict)
        m = self.basemap

        boundaryObj = m.drawmapboundary()
        if(type(boundaryObj) is plt.Polygon):
            boundary_path = m.drawmapboundary().get_path()
            self.boundary = self.poly2Qpolygon(boundary_path)

        coast_paths = m.drawcoastlines().get_paths()
        # use only the 91st biggest coastlines (i.e. no rivers)
        N_poly = 91
        mainCoasts = coast_paths[:N_poly]

        self.coastlines = self.polys2Qpolygons(mainCoasts)

        country_paths = m.drawcountries().get_paths()
        self.countries = self.polys2Qpolygons(country_paths)

        meridiansPaths = m.drawmeridians(range(-180, 180, 20))
        for meridian in meridiansPaths:
            md = meridiansPaths[meridian][0][0]
            self.meridians.append(self.line2Qpolygon(md))

        parallelsPaths = m.drawparallels(range(-90, 90, 20))
        for parallel in parallelsPaths:
            md = parallelsPaths[parallel][0][0]
            self.parallels.append(self.line2Qpolygon(md))

        print(m.proj4string)


    def line2Qpolygon(self,line2d):
        ''' Create QPolygon from matplotlib line2d '''

        xvalues = line2d.get_xdata()
        yvalues = line2d.get_ydata()
        nSegs = len(xvalues)
        ptList = []
        step = nSegs/100
        for i in range(0,nSegs,step):
            viewPt = self.map.pointToView(xvalues[i], yvalues[i])
            ptList.append(QPointF(viewPt[0],viewPt[1]))

        return QPolygonF(ptList)

    def poly2Qpolygon(self,poly_path):
        ''' Create QPolygon from matplotlib path '''

        # get the Basemap coordinates of each segment
        coords_cc = np.array(
            [(vertex[0],vertex[1])
             for (vertex,code) in poly_path.iter_segments(simplify=False)]
        )

        ptList = []
        for pt in coords_cc:
            viewPt = self.map.pointToView(pt[0], pt[1])
            ptList.append(QPointF(viewPt[0],viewPt[1]))

        return QPolygonF(ptList)

    def polys2Qpolygons(self,poly_paths, N_poly=-1):
        ''' Create QPolygon list matplotlib paths '''
        qPolys = []
        if N_poly==-1:
            N_poly = len(poly_paths)

        for i_poly in range(N_poly):
            path = poly_paths[i_poly]
            qPoly = self.poly2Qpolygon(path)
            qPolys.append(qPoly)

        return qPolys


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
        self.createBasemap()


    def render(self,qp):
        ''' Render projected geometry using option styles '''
        qp.setBrush(Qt.cyan)
        qp.setPen(Qt.black)
        # Set QPainter styles
        MapUtils.setStylesFromJson(qp, self.styles)

        t0 = time.time()

        for poly in self.coastlines:
            qp.drawPolygon(poly)

        for poly in self.countries:
            qp.drawPolyline(poly)

        if self.boundary:
            qp.drawPolyline(self.boundary)

        for line in self.parallels:
            qp.drawPolyline(line)

        for line in self.meridians:
            qp.drawPolyline(line)

        t1 = time.time()
        print ('drawGeoJson:', t1-t0)


if __name__ == '__main__':

    # Example Basemap layer, Geojson layer, point data layers, and Map options
    config_obj = {
        "layers":[
            {
                "type":"basemap",
                "id":"basemap",
                "projOpts":{
                    "projection":"robin",
                    "lat_0":0,
                    "lon_0":0,
                    "ellps":"WGS84",
                    "resolution":"c",
                    "area_thresh":1000.0,
                    "llcrnrlon":-180,
                    "llcrnrlat":-85,
                    "urcrnrlon":180,
                    "urcrnrlat":85
                },
                "styles":{
                    "line-width":1.0,
                    "line-color":"#99999999",
                    "fill-color":"#cccccc11"
                }
            },
            {
                "type":"geojson",
                "id":"world_borders",
                "geojson":"../test_data/tm_world_borders_simpl.geojson",
                "proj":"+init=EPSG:4326",
                "styles":{"line-width":1.0,
                         "line-color":"#99999999",
                         "fill-color":"#ffcccc33"
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
                    "point-color":"#00000099",
                    "point-size":1.3

                }

            }

        ],

        "mapOpts":{
            "bounds":[-180,-85,180,85],
            "canvasSize":[1500,1200],
            # proj derived from basemap proj4string instance variable
            "proj":"+a=6378137.0 +b=6356752.31425 +y_0=8625154.47185 +lon_0=0.0 +proj=robin +x_0=17005833.3305 +units=m +lat_0=0.0",
            "styles":{"background-color":"#ffffff"},
            "capture_path":"../grabs/"
        }
    }
    app = QApplication(sys.argv)
    m = MapQt(config_obj)

    layers = config_obj['layers']
    for layerOpts in layers:
        t = layerOpts['type']
        l = None
        if t=='basemap':
            l = BasemapLayer(m,layerOpts)

        elif t=='geojson':
            l = GeojsonLayer(m,layerOpts)

        elif t=='data':
            l = PointDataLayer(m,layerOpts)


        if l:
            m.addLayer(l)


    dialog = MapDialog(m)
    dialog.addGeojsonUI()
    dialog.addDataUI()
    dialog.addMousePos()
    dialog.addCaptureButton()
    dialog.addStatus()
    dialog.show()

    m.update()
    sys.exit(app.exec_())