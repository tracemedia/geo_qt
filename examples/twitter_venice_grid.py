import sys
from PySide.QtCore import *
from PySide.QtGui import *
from geo_qt import *


def main():
    # Example Geojson layer, point data layers, and Map options
    config_obj = {
        "layers": [
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
                "type": "data_pt",
                "id": "twitter_venice_2014_pt",
                "path": "../test_data/twitter/",
                "datatype": "csv",
                "files": ["venice_2014_tweets_no_text.csv"],
                "delimiter": ",",
                "quotechar": "\"",
                "fields": [
                    {"id": "lat", "field": "geo_lat", "type": "float", "name": "Latitude"},
                    {"id": "lng", "field": "geo_long", "type": "float", "name": "Longitude"}

                ],
                "proj": "+init=EPSG:4326",
                "styles": {
                    "grid":{
                        "values":[1,2,3,5,10,25,50,100],
                        # "colors":["#bbbbbb","#aaaaaa","#999999","#888888","#777777","#555555","#333333","#000000"],
                        "colors":["#888888","#999999","#aaaaaa","#bbbbbb","#cccccc","#dddddd","#eeeeee","#fffffff"],
                        "size":1
                    }
                }
            }

        ],

        "mapOpts": {
            "bounds": [12.299221, 45.422284, 12.370022, 45.450230],
            "canvasSize": [1600, 900],
            "proj": "+init=epsg:3857",
            # "styles": {"background-color": "#ffffff"},
            "styles": {"background-color": "#000000"},
            "capture_path": "../grabs/"
        }
    }

    app = QApplication(sys.argv)
    m = TimelineMap(config_obj)

    dialog = TimelineDialog(m)
    layers = config_obj['layers']
    for layerOpts in layers:
        t = layerOpts['type']
        if t=='geojson_':
            l = GeojsonLayer(m,layerOpts)
            m.addLayer(l)
            dialog.addGeojsonUI(l)

        elif t=='data_pt':
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