'''
ModestMapLayer uses Stamen modestmaps-py
https://github.com/stamen/modestmaps-py
'''

import sys
import pyproj
import PySide
from PySide.QtCore import *
from PySide.QtGui import *
sys.modules['PyQt4'] = PySide
from PIL import Image, ImageDraw
from PIL.ImageQt import ImageQt
from map_qt import *

try:
    import ModestMaps as MM
except ImportError:
    print('ModestMaps Import Error')

class ModestMapLayer(Layer):

    def __init__(self,map,opts):
        ''' Initialise from map bounds and zoom option '''
        super(ModestMapLayer,self).__init__(map, opts)

        self.mm = None
        self.project()
        self.renderImage()


    def pil2qpixmap(self,pil_image):
        ''' Convert PIL image to QPixmap '''
        w, h = pil_image.size
        data = pil_image.tostring("raw", "BGRX")
        qimage = QImage(data, w, h, QImage.Format_RGB32)
        qpixmap = QPixmap(w,h)
        pix = QPixmap.fromImage(qimage)
        return pix

    def updateCanvasSize(self):

        self.project()
        self.renderImage()

    def project(self):
        ''' Set map extent from lnglat bounds and zoom '''
        bnds = self.map.lngLatBounds

        sw = MM.Geo.Location(bnds.b, bnds.l)
        ne = MM.Geo.Location(bnds.t, bnds.r)
        z = self.opts['zoom']

        #provider = MM.Microsoft.RoadProvider()
        provider = MM.OpenStreetMap.Provider()

        mm = MM.mapByExtentZoom(provider, sw, ne, z)
        self.mm = mm

        epsg3857 = pyproj.Proj(init='epsg:3857')
        epsg4326 = pyproj.Proj(init='epsg:4326')

        # Resize map to dimensions of tiles
        psw = pyproj.transform(epsg4326,epsg3857,bnds.l,bnds.b)
        pne = pyproj.transform(epsg4326,epsg3857,bnds.r,bnds.t)
        self.map.projBounds.set(psw[0],psw[1],pne[0],pne[1])

        self.map.canvasW = self.viewW = mm.dimensions.x
        self.map.canvasH = self.viewH = mm.dimensions.y
        self.map.projToViewScale = self.map.viewW/self.map.projBounds.width
        self.map.setViewBounds()

    def renderImage(self):
        self.render(None)

    def render(self,qp):
        ''' Load map tiles and render to QPixmap '''
        pilImage = self.mm.draw()
        self.image = self.pil2qpixmap(pilImage)


if __name__ == '__main__':

    config_obj = {
    "layers":[
        {
            "type":"modestmap",
            "id":"modestmap",
            "proj":"+init=EPSG:4326",
            "zoom":2
        },
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
                {"id":"created",    "field":"last_edit_timestamp",     "type":"wiki_datetime",    "name":"Last Edit"},
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
        "styles":{"background-color":"#ffffff"}

    }
    }

    app = QApplication(sys.argv)
    m = MapQt(config_obj)


    layers = config_obj['layers']
    for layerOpts in layers:
        t = layerOpts['type']
        l = None
        if t=='modestmap':
            l = ModestMapLayer(m,layerOpts)
        elif t=='geojson':
            l = GeojsonLayer(m,layerOpts)
        elif t=='data':
            l = PointDataLayer(m,layerOpts)

        if l:
            m.addLayer(l)


    dialog = MapDialog(m)
    dialog.addGeojsonUI()
    dialog.addDataUI()
    dialog.addCaptureButton()
    dialog.show()

    m.repaint()
    sys.exit(app.exec_())