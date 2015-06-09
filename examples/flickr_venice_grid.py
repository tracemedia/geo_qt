import sys
from PySide.QtCore import *
from PySide.QtGui import *
from geo_qt import MapQt,MapDialog,GeojsonLayer,PointDataLayer
from geo_qt.thematic_point_layer import ThematicPointLayer


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
                "delimiter":",",
                "quotechar":"\"",
                # 'photo_id','owner','title','latitude','longitude','woeid','datetaken','tags','views'
                "fields":[
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
            l = ThematicPointLayer(m,layerOpts)
            m.addLayer(l)
            dialog.addDataUI(l)


    dialog.addMousePos()
    dialog.addCaptureButton()
    dialog.addStatus()
    dialog.show()

    m.update()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()