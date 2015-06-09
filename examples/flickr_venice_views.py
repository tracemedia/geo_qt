import sys
from PySide.QtCore import *
from PySide.QtGui import *
from geo_qt import MapQt,MapDialog,GeojsonLayer,PointDataLayer,ModestMapLayer,ThematicPointLayer,TimelineMap,TimelineDataLayer,TimelineDialog


def main():

    config_obj = {
            "layers":[
             {
                "type":"geojson",
                "id":"venice_polygons",
                "geojson":"../test_data/osm/venice_01_polygon.geojson",
                "proj":"+init=EPSG:4326",
                "styles":{"line-width":0.25,
                         "line-color":"#99999966",
                         "fill-color":"#cccccc00"
                }
            },
            {
                "type":"data_pt",
                "id":"flickr_venice",
                "path":"../test_data/flickr/",
                "datatype":"csv",
                "files":["venice_photos_2011_2014.csv"],
                "delimiter":",",
                "quotechar":"\"",
               "fields":[
                    {"id":"lat",        "field":"latitude",     "type":"float",     "name":"Latitude"},
                    {"id":"lng",        "field":"longitude",    "type":"float",     "name":"Longitude"}

                ],
                "proj":"+init=EPSG:4326",
                "styles":{
                    "point-size":1.0,
                    "point-color":"#99999966"
                }
            },
            {
                "type":"data",
                "id":"flickr_venice_anim",
                "path":"../test_data/flickr/",
                "datatype":"csv",
                "files":["venice_photos_2011_2014.csv"],
                "delimiter":",",
                "quotechar":"\"",
                "orderby":"created",
                # 'photo_id','owner','title','latitude','longitude','woeid','datetaken','tags','views'
                "fields":[
                    {"id":"created",    "field":"date_taken",    "type":"datetime", "name":"Date Taken", "format":"%Y-%m-%d %H:%M:%S"},
                    {"id":"lat",        "field":"latitude",     "type":"float",     "name":"Latitude"},
                    {"id":"lng",        "field":"longitude",    "type":"float",     "name":"Longitude"},
                    {"id":"views",       "field":"views",        "type":"int",       "name":"Views"},

                ],
                "proj":"+init=EPSG:4326",
                "styles":{
                   #  quintile: [0.0, 6.0, 19.0, 49.0, 134.0, 639122.0]
                   "point-size": {
                      "property": "views",
                      "values": [0,6,20,50,134,2000],
                      "sizes": [1.3,2,4,6,10,50]
                   },
                   "point-alpha": {
                      "property": "views",
                      "values": [0,6,20,50,134,500],
                      "alphas": [0.7,0.7,0.7,0.5,0.4,0.3]
                   },
                   "point-color": "#333333",
                   "transition-fraction":0.5
                   # "point-line-width":2,
                   # "point-line-color":"#ff0000",



                },
                "animation":{
                    "min_date":"2005-01-01 00:00:00",
                    "max_date":"2015-01-01 00:00:00",
                    "fps":25,
                    "type":"range", # "cumulative"
                    "timespan_d":45,
                    "duration_s":50
                }


            }
        ],

        "mapOpts":{
            "bounds": [12.299221,45.422284,12.370022,45.450230],  # Venice 16:9 aspect in web mercator
            "canvasSize":[1600,900],
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

        elif t=='data_pt':
            l = ThematicPointLayer(m,layerOpts)
            m.addLayer(l)
            dialog.addDataUI(l)

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