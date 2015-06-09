'''
MapQt utility functions
'''

import json
import pyproj

from PySide.QtGui import *


class MapUtils(object):

    @staticmethod
    def loadGeoJson(filename):
        '''  Load JSON from filename '''
        with open(filename) as json_file:
            geojson = json.load(json_file)

        return geojson

    @staticmethod
    def hex2rgba(value):
        '''  Hex #rrggbbaa to tuple range [0,255] '''
        value = value.lstrip('#')
        if len(value) == 3:
            value = ''.join([v*2 for v in list(value)])
        if len(value) < 8:
            value += "FF"
        value = tuple(int(value[i:i+2], 16) for i in range(0, 8, 2))
        return value

    @staticmethod
    def hex2qcolor(value):
        '''  Hex #rrggbbaa to PySide QColor '''
        c = MapUtils.hex2rgba(value)
        return QColor(c[0],c[1],c[2],c[3])

    @staticmethod
    def setStylesFromJson(qp,styles):
        '''  Set PySide QPen and QBrush from JSON styles '''
        pen = qp.pen()
        brush = qp.brush()

        for s in styles:
            val = styles[s]
            if s=="line-width":
                pen.setWidthF(float(val))
            elif s=="line-color":
                pen.setBrush(MapUtils.hex2qcolor(val))
            elif s=="fill-color":
                brush.setColor(MapUtils.hex2qcolor(val))

        qp.setBrush(brush)
        qp.setPen(pen)




    @staticmethod
    def projectedBounds(projSrc,projDest,llbbox=(-180, -90, 180, 90)):
        ''' Return projected bounding box using Proj4  '''
        lons = []
        lats = []

        minLon = llbbox[0]
        maxLon = llbbox[2]
        minLat = llbbox[1]
        maxLat = llbbox[3]

        def xfrange(start, stop, step):
            if stop > start:
                while start < stop:
                    yield start
                    start += step
            else:
                while stop < start:
                    yield start
                    start -= step

        lat_step = abs((maxLat - minLat) / 180.0)
        lon_step = abs((maxLon - minLon) / 360.0)

        for lat in xfrange(minLat, maxLat, lat_step):
            lons.append(minLon)
            lats.append(lat)
        for lon in xfrange(minLon, maxLon, lon_step):
            lons.append(lon)
            lats.append(maxLat)
        for lat in xfrange(maxLat, minLat, lat_step):
            lons.append(maxLon)
            lats.append(lat)
        for lon in xfrange(maxLon, minLon, lon_step):
            lons.append(lon)
            lats.append(minLat)

        plons,plats = pyproj.transform(projSrc,projDest,lons,lats)

        bounds = [min(plons),min(plats),max(plons),max(plats)]

        return bounds

    @staticmethod
    def getBoundsByAspect(bbList,aspect,projSrc,projDest):
        ''' Return bounds adjusted for aspect ratio '''
        bb = bbList
        bl = pyproj.transform(projSrc,projDest,bb[0],bb[1])
        tr = pyproj.transform(projSrc,projDest,bb[2],bb[3])

        projW = tr[0]-bl[0]
        projH = tr[1]-bl[1]
        projcx = (tr[0]+bl[0])/2
        projcy = (tr[1]+bl[1])/2

        pbb=[0,0,0,0]

        if projW/projH > aspect:
            pbb[0] = bl[0]
            pbb[2] = tr[0]
            pbb[1] = projcy-projW*0.5/aspect
            pbb[3] = projcy+projW*0.5/aspect
        else:
            pbb[1] = bl[1]
            pbb[3] = tr[1]
            pbb[0] = projcx-projH*0.5*aspect
            pbb[2] = projcx+projH*0.5*aspect

        nbl = pyproj.transform(projDest,projSrc,pbb[0],pbb[1])
        ntr = pyproj.transform(projDest,projSrc,pbb[2],pbb[3])

        return [nbl[0],nbl[1],ntr[0],ntr[1]]

