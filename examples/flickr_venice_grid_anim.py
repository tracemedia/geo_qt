import sys
from PySide.QtCore import *
from PySide.QtGui import *
from geo_qt import *


def main():

    config_obj = {
            "layers":[
            {
                "type":"geojson",
                "id":"venice_polygons",
                "geojson":"../test_data/osm/venice_01_polygon.geojson",
                "proj":"+init=EPSG:4326",
                "styles":{
                    "line-width":0.5,
                    "line-color":"#99999955",
                    "fill-color":"#cccccc00"
                }
            },
            {
                "type":"data",
                "id":"flickr_venice",
                "path":"../test_data/flickr/",
                "datatype":"csv",
                "files":["venice_photos_2011_2014.csv"],
                # "files":["venice_photos_2005_2014_sample.csv"],
                "delimiter":",",
                "quotechar":"\"",
                "orderby":"created",
                # 'photo_id','owner','title','latitude','longitude','woeid','datetaken','tags','views'
                "fields":[
                    {"id":"created",    "field":"date_taken",    "type":"datetime", "name":"Date Taken", "format":"%Y-%m-%d %H:%M:%S"},
                    {"id":"lat",        "field":"latitude",     "type":"float",     "name":"Latitude"},
                    {"id":"lng",        "field":"longitude",    "type":"float",     "name":"Longitude"},
                ],
                "proj":"+init=EPSG:4326",
                "styles":{
                    "grid":{
                        "values":[1,2,3,5,10,25,50,100],
                        # "colors":['#cccccc','#bbbbbb','#aaaaaa','#999999','#777777','#555555','#333333','#000000'],
                        "colors":['#777777','#999999','#aaaaaa','#bbbbbb','#cccccc','#dddddd','#eeeeee','#fffffff'],
                        "size":1
                    }

                },
                "animation":{
                    "min_date":"2011-01-01 00:00:00",
                    "max_date":"2015-01-01 00:00:00",
                    "fps":25,
                    "type":"range", # "cumulative"
                    "timespan_d":60,
                    "duration_s":600
                }

            }

        ],

        "mapOpts":{
            "bounds":[12.299221,45.422284,12.370022,45.450230],
            "canvasSize":[1600,900],
            "proj":"+init=epsg:3857",
            # "styles":{"background-color":"#ffffff"},
             "styles":{"background-color":"#000000"},
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