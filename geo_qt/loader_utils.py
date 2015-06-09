'''
Data loading utilities
'''

import csv
import time

from utils import *
from geom import Rectangle

class DataItem(object):
    def __init__(self):
        self.id = ''
        self.lng = 0.0
        self.lat = 0.0

class LoaderUtils(object):
    @staticmethod
    def loadCSV(params):
        '''
        :param params:
        {
            "path":<path>,
            "files":[<filename>],
            "delimiter":<str>,
            "quotechar":<str>,
            "fields":[
                {"id":<property of DataItem>,    "field":<filed in CSV>,  "type":<data type>,    "name":<name>},
            ]
        }
        '''

        items = []
        itemId = 0

        bounds = None
        if 'bounds' in params:
            bounds = Rectangle()
            bounds.fromList(params['bounds'])


        fieldsParam = params['fields']
        fields = {}
        for fieldData in fieldsParam:
            fields[fieldData['field']] = fieldData

        start = time.time()
        for filename in params["files"]:
            file = params["path"]+filename
            with open(file, 'rb') as csvfile:
                reader = csv.DictReader(csvfile, delimiter=params['delimiter'], quotechar=params['quotechar'],escapechar='\\')
                for row in reader:
                    item = DataItem()
                    for field in fields:
                        fieldData = fields[field]
                        id = fieldData['id']
                        type = fieldData['type']
                        val = row[field]

                        if type=='string':
                            value = val

                        elif type=='int':
                            if val =='' or val == 'NULL':
                                value = 0
                            else:
                                value = int(val)
                        elif type=='float':
                            if val =='' or val == 'NULL':
                                value = 0.0
                            else:
                                value = float(val)
                        elif type=='datetime':
                            if val=='' or val=='0':
                                value = datetime.now()
                            else:
                                value = Utils.str2utc(val,fieldData['format'])
                        elif type=='timestamp':
                            if val=='':
                                value = datetime.now()
                            else:
                                value = Utils.timestamp2utc(float(val))
                        else:
                            value = val

                        setattr(item, id, value)

                    if bounds==None or bounds.within(item.lng,item.lat):
                        items.append(item)


                itemId += 1

        end = time.time()
        print ('CSVLoader:', end-start)
        return items





