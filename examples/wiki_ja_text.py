import sys
import json

from PySide.QtCore import *
from PySide.QtGui import *
from geo_qt import *


def main():

    config_obj = {
        "layers":[
            {
                "type":"geojson",
                "id":"world_borders",
                "geojson":"../test_data/tm_world_borders_simpl.geojson",
                "proj":"+init=EPSG:4326",
                "styles":{
                    "fill-color": "#cccccc11",
                    "line-color": "#99999999",
                    "line-width": 0.2
                }
            },
            {
                "type":"data_pt",
                "id":"wiki_data_pt",
                "path":"../test_data/wikipedia/",
                "datatype":"csv",
                "files":["wiki_ja__geo_tags__info__edits.tsv"],
                "delimiter":"\t",
                "quotechar":"\"",
                "fields":[
                    {"id":"lat",        "field":"gt_lat",       "type":"float",     "name":"Latitude"},
                    {"id":"lng",        "field":"gt_lon",       "type":"float",     "name":"Longitude"}

                ],
                "proj":"+init=EPSG:4326",
                "styles":{
                    "point-color":"#bbbbbb",
                    "point-size":1.2

                }

            },
            {
                "type":"data",
                "id":"wiki_data",
                "path":"../test_data/wikipedia/",
                "datatype":"csv",
                "files":["wiki_ja__geo_tags__info__edits.tsv"],
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
                    {"id":"lng",        "field":"gt_lon",       "type":"float",     "name":"Longitude"},

                ],
                "proj":"+init=EPSG:4326",
                "styles":{
                    "font-size":{
                        "property":"page_len",
                        "values":[50,2000,3500,5000,7500,13000,100000],
                        "sizes":[1,2,3,4,7,15,50]

                    },
                    "font-alpha":0.8,
                    "font-color":{
                        "fn":"random",
                        "colors":["#000000","#7777777"]
                    },
                    "font-weight":75,
                    "transition-fraction":0.4,
                    "text-length":1


                },
                "animation":{
                    "min_date":"2001-01-01 00:00:00",
                    "max_date":"2015-01-01 00:00:00",
                    "fps":25,
                    "type":"range", # "cumulative"
                    "timespan_d":180,
                    "duration_s":100
                }

            }

        ],

        "mapOpts":{
            "bounds":[119.838948,30.929449,154.526447,46.095240], # 16/9 bounds  [125.976643,30.929449, 148.388752,46.095240], # bounds
            "canvasSize":[1600,900],
            "proj":"+proj=laea +lat_0=37.7624 +lon_0=136.881  +ellps=WGS84 +datum=WGS84 +units=m +no_defs",
            "styles":{"background-color":"#ffffff"},
            "capture_path":"../grabs/"
        }
    }


    app = QApplication(sys.argv)

    m = TimelineMap(config_obj)

    layers = config_obj['layers']
    dataOpts = None
    for layerOpts in layers:
        t = layerOpts['type']
        if t=='geojson':
            l = GeojsonLayer(m,layerOpts)
            m.addLayer(l)
        elif t=='data_pt':
            pdl = ThematicPointLayer(m,layerOpts)
            m.addLayer(pdl)

        elif t=='data':
            dl = TimelineDataLayer(m,layerOpts)
            dataOpts = layerOpts
            m.addAnimLayer(dl)
            m.addLayer(dl)

    dialog = TimelineDialog(m)
    dialog.addGeojsonUI()
    dialog.addDataUI(pdl,50)
    dialog.addDataUI(dl)
    dialog.addTimeline(dataOpts,dl.dataMinDate,dl.dataMaxDate)
    dialog.addMousePos()
    dialog.addCaptureButton()
    dialog.addStatus()
    dialog.show()

    m.renderAnimLayers()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
