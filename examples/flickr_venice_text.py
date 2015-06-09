import sys
import string
from PySide.QtCore import *
from PySide.QtGui import *
from geo_qt import MapQt,MapDialog,GeojsonLayer,PointDataLayer,ModestMapLayer,ThematicPointLayer,TimelineMap,TimelineDataLayer,TimelineDialog


def main():

    debug = False
    if debug:
        filename = "venice_photos_2005_2014_sample.csv"
    else:
        filename = "venice_photos_2011_2014.csv"

    config_obj = {
            "layers":[
                 {
                "type": "geojson",
                "id": "venice_polygons",
                "geojson": "../test_data/osm/venice_01_polygon.geojson",
                "proj": "+init=EPSG:4326",
                "styles": {
                    "line-width": 0.5,
                    "line-color": "#99999966",
                    "fill-color": "#cccccc00"
                }
            },

            {
                "type":"data",
                "id":"flickr_venice_anim",
                "path":"../test_data/flickr/",
                "datatype":"csv",
                "files":[filename],#["venice_photos_2011_2014.csv"],
                "delimiter":",",
                "orderby":"created",
                "quotechar":"\"",
                # 'photo_id','owner','title','latitude','longitude','woeid','datetaken','tags','views'
                "fields":[
                    {"id":"title",      "field":"title",        "type":"string",    "name":"Text"},
                    {"id":"created",    "field":"date_taken",    "type":"datetime", "name":"Date Taken", "format":"%Y-%m-%d %H:%M:%S"},
                    {"id":"lat",        "field":"latitude",     "type":"float",     "name":"Latitude"},
                    {"id":"lng",        "field":"longitude",    "type":"float",     "name":"Longitude"},
                    {"id":"tags",       "field":"tags",         "type":"string",    "name":"Tags"},
                    {"id":"views",       "field":"views",        "type":"int",       "name":"Views"},

                ],
                "proj": "+init=EPSG:4326",
                "styles": {
                    # quintile: [0.0, 6.0, 19.0, 49.0, 134.0, 639122.0]

                    "font-size": {
                        "property": "views",
                        "values": [0, 6, 20, 50, 134, 2000],
                        "sizes": [5,6,7,10,15,30]
                    },
                    "text-length": 16,
                    "font-alpha": {
                        "property": "views",
                        "values": [0, 6, 20, 50, 134, 2000],
                        "alphas": [0.7, 0.7, 0.7, 0.7, 0.6, 0.4],

                    },
                    "font-color": {
                        "colors": ["#aaaaaa", "#333333"],
                        "fn": "random"
                    },
                    "font-family":"courier",
                    "font-weight":50,
                    "transition-fraction":0.5



                },
                "animation":{
                    "min_date":"2011-01-01 00:00:00",
                    "max_date":"2015-01-01 00:00:00",
                    "fps":25,
                    "type":"range", # "cumulative"
                    "timespan_d":5,
                    "duration_s":600
                }


            }
        ],

        "mapOpts":{
            "bounds": [12.299221,45.422284,12.370022,45.450230], # Venice 16:9 aspect in web mercator
            "canvasSize":[2400,1200],
            "proj":"+init=epsg:3857",
            "styles":{"background-color":"#ffffff"},
            "capture_path":"../grabs/"
        }
    }
    app = QApplication(sys.argv)
    m = TimelineMap(config_obj)

    dialog = TimelineDialog(m)
    layers = config_obj['layers']
    for layerOpts in layers:
        t = layerOpts['type']

        if t=='geojson':
            l = GeojsonLayer(m,layerOpts)
            m.addLayer(l)
            dialog.addGeojsonUI(l)

        elif t=='data':
            l = TimelineDataLayer(m,layerOpts)
            m.addLayer(l)
            m.addAnimLayer(l)
            dialog.addDataUI(l)
            dialog.addTimeline(layerOpts,l.dataMinDate,l.dataMaxDate)


    dialog.addMousePos()
    dialog.addCaptureButton()
    dialog.addStatus()
    dialog.show()

    m.renderAnimLayers()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()