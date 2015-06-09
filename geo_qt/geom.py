'''
Geometry classes
'''

class Point:
    ''' Point '''
    def __init__(self, x, y):
        self.x = x
        self.y = y

    def __repr__(self):
        return '(%(x).3f, %(y).3f)' % self.__dict__


class Rectangle:
    ''' Rectangle with bounding box functions '''
    def __init__(self, l=0, b=0, r=0, t=0):
        self.set(l,b,r,t)

    def set(self, l, b, r, t):
        self.l = l
        self.b = b
        self.r = r
        self.t = t

    def fromList(self, a):
        self.l = a[0]
        self.b = a[1]
        self.r = a[2]
        self.t = a[3]

    def toList(self):
        return [self.l,self.b,self.r,self.t]

    def getCentre(self):
        return[(self.l+self.r)/2,(self.b+self.t)/2]

    def extend(self,pt):
        if pt[0]<self.l: self.l=pt[0]
        if pt[1]<self.b: self.b=pt[1]
        if pt[0]>self.r: self.r=pt[0]
        if pt[1]>self.t: self.t=pt[1]


    @property
    def left(self):
        return self.l
    @property
    def bottom(self):
        return self.b
    @property
    def right(self):
        return self.r
    @property
    def top(self):
        return self.t

    @property
    def width(self):
        return self.r-self.l
    @property
    def height(self):
        return self.t-self.b

    def within(self,x,y):
        if(x>=self.l and x<=self.r and y>=self.b and y<=self.t):
            return True
        else:
            return False

class Grid2d:
    ''' 2d grid '''
    def __init__(self,bounds=Rectangle(0,0,1,1),dx=10,dy=10):
        self.array = [[[] for y in range(dy)] for x in range(dx)]
        self.bounds = bounds
        self.dx = dx
        self.dy = dy

    def insert(self,obj,x,y):
        if(self.bounds.within(x,y)):
            idx = (x-self.bounds.l)*self.dx/self.bounds.width
            idy = (y-self.bounds.b)*self.dy/self.bounds.height
            self.array[idy][idx].append(obj)
            return True
        else:
            return False

    def get(self,x,y):
        if(self.bounds.within(x,y)):
            idx = (x-self.bounds.l)*self.dx/self.bounds.width
            idy = (y-self.bounds.b)*self.dy/self.bounds.height
            return self.array[idy][idx]
        else:
            return None


