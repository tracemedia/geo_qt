'''
Utility functions
'''

from datetime import datetime, tzinfo, timedelta
import numpy

TIMEDELTA_ZERO = timedelta(0)

class UTC(tzinfo):
    ''' UTC '''
    def utcoffset(self, dt):
        return TIMEDELTA_ZERO

    def tzname(self, dt):
        return "UTC"

    def dst(self, dt):
        return TIMEDELTA_ZERO



class Utils(object):
    ''' Date and interpolation helper functions '''
    SECS_IN_DAY = 86400

    @staticmethod
    def str2utc(utcStr,format='%Y-%m-%d %H:%M:%S'):
        # default format '2011-01-21 02:37:21'
        from_zone = UTC()
        utc = datetime.strptime((utcStr), format)
        utc = utc.replace(tzinfo=from_zone)
        return utc

    @staticmethod
    def timestamp2utc(timestamp):
        from_zone = UTC()
        utc = datetime.fromtimestamp(timestamp)
        utc = utc.replace(tzinfo=from_zone)
        return utc

    @staticmethod
    def utc2str(dt):
        return dt.strftime('%Y-%m-%d %H:%M:%S')

    @staticmethod
    def interpParams(val,d):
        '''
        Return index i of val in list d and normalized value between d[i] and d[i+1]
        :param val: float
        :param d: list of floats
        :return: normalised value, index in d
        '''
        if val<=d[0]:
            return 0,0
        elif val>=d[-1]:
            idx = len(d)-1
            return 0,idx
        else:
            # i = next(j for j,v in enumerate(d) if v > val)
            for i in range(1,len(d)):
                if val<d[i]:
                    n = float(val-d[i-1])/(d[i]-d[i-1])
                    return n,i-1


    @staticmethod
    def interp_np(val,d,r):
        return numpy.interp(val, d, r)

    @staticmethod
    def interp(val, s, e):
        return s + (e-s)*val

    @staticmethod
    def interpList(val,d,r):
        '''  Piecewise linear interpolant '''
        if val<=d[0]:
            return r[0]
        elif val>=d[-1]:
            return r[-1]
        else:
            for i in range(1,len(d)):
                if val<d[i]:
                    n = float(val-d[i-1])/(d[i]-d[i-1])
                    r = r[i-1]+n*(r[i]-r[i-1])
                    return r

    @staticmethod
    def transition(value, maximum, start_point, end_point):
        return start_point + (end_point - start_point)*value/maximum

    @staticmethod
    def transition3(value, maximum, (s1, s2, s3), (e1, e2, e3)):
        r1= Utils.transition(value, maximum, s1, e1)
        r2= Utils.transition(value, maximum, s2, e2)
        r3= Utils.transition(value, maximum, s3, e3)
        return (r1, r2, r3)

    @staticmethod
    def interpListHSV(val,d,r):
        if val<=d[0]:
            return r[0]
        elif val>=d[-1]:
            return r[-1]
        else:
            for i in range(1,len(d)):
                if val<d[i]:
                    n = float(val-d[i-1])/(d[i]-d[i-1])
                    maximum = 1.0
                    c = Utils.transition3(n, maximum, d[i-1], d[i])
                    return c

    @staticmethod
    def interpHSV(norm,s,e):
        maximum = 1.0
        c =  Utils.transition3(norm, maximum, s, e)
        return c

    @staticmethod
    def normalize(val,s,e):
        return float(val-s)/(e-s)

    @staticmethod
    def byteify(input):
        if isinstance(input, dict):
            return {Utils.byteify(key):Utils.byteify(value) for key,value in input.iteritems()}
        elif isinstance(input, list):
            return [Utils.byteify(element) for element in input]
        elif isinstance(input, unicode):
            return input.encode('utf-8')
        else:
            return input

    @staticmethod
    def to_json(o, level=0):
        ''' format JSON with no line break between list items '''
        INDENT = 3
        SPACE = " "
        NEWLINE = "\n"

        ret = ""
        if isinstance(o, dict):
            ret += "{" + NEWLINE
            comma = ""
            for k,v in o.iteritems():
                ret += comma
                comma = ",\n"
                ret += SPACE * INDENT * (level+1)
                ret += '"' + str(k) + '":' + SPACE
                ret += Utils.to_json(v, level + 1)

            ret += NEWLINE + SPACE * INDENT * level + "}"
        elif isinstance(o, basestring):
            ret += '"' + o + '"'
        elif isinstance(o, list):
            ret += "[" + ",".join([Utils.to_json(e, level+1) for e in o]) + "]"
        elif isinstance(o, bool):
            ret += "true" if o else "false"
        elif isinstance(o, int):
            ret += str(o)
        elif isinstance(o, float):
            ret += '%.7g' % o
        elif isinstance(o, numpy.ndarray) and numpy.issubdtype(o.dtype, numpy.integer):
            ret += "[" + ','.join(map(str, o.flatten().tolist())) + "]"
        elif isinstance(o, numpy.ndarray) and numpy.issubdtype(o.dtype, numpy.inexact):
            ret += "[" + ','.join(map(lambda x: '%.7g' % x, o.flatten().tolist())) + "]"
        else:
            raise TypeError("Unknown type '%s' for json serialization" % str(type(o)))
        return ret


class switch(object):
    def __init__(self, value):
        self.value = value
        self.fall = False

    def __iter__(self):
        """Return the match method once, then stop"""
        yield self.match
        raise StopIteration

    def match(self, *args):
        """Indicate whether or not to enter a case suite"""
        if self.fall or not args:
            return True
        elif self.value in args: # changed for v1.5, see below
            self.fall = True
            return True
        else:
            return False

# Example
# Empty suites are considered syntax errors, so intentional fall-throughs
# should contain 'pass'
# c = 'z'
# for case in switch(c):
#     if case('a'): pass # only necessary if the rest of the suite is empty
#     if case('b'): pass
#     # ...
#     if case('y'): pass
#     if case('z'):
#         print "c is lowercase!"
#         break
#     if case('A'): pass
#     # ...
#     if case('Z'):
#         print "c is uppercase!"
#         break
#     if case(): # default
#         print "I dunno what c was!"

# As suggested by Pierre Quentel, you can even expand upon the
# functionality of the classic 'case' statement by matching multiple
# cases in a single shot. This greatly benefits operations such as the

# uppercase/lowercase example above:
# import string
# c = 'A'
# for case in switch(c):
#     if case(*string.lowercase): # note the * for unpacking as arguments
#         print "c is lowercase!"
#         break
#     if case(*string.uppercase):
#         print "c is uppercase!"
#         break
#     if case('!', '?', '.'): # normal argument passing style also applies
#         print "c is a sentence terminator!"
#         break
#     if case(): # default
#         print "I dunno what c was!"

# Since Pierre's suggestion is backward-compatible with the original recipe,
# I have made the necessary modification to allow for the above usage.