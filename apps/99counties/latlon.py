import math

def dms2angle(d=0, m=0, s=0):
    dm = m * 60**-1
    ds = s * 60**-2
    return d + dm + ds
    return math.radians()

def dms2rad(d=0, m=0, s=0):
    return math.radians(dms2angle(d,m,s))


def spherical_distance(p1, p2, radius=1.0):
    lat1, lon1 = p1
    lat2, lon2 = p2

    dlat = math.radians(lat2-lat1)
    dlon = math.radians(lon2-lon1)
    a = math.sin(dlat/2) * math.sin(dlat/2) + math.cos(math.radians(lat1)) \
        * math.cos(math.radians(lat2)) * math.sin(dlon/2) * math.sin(dlon/2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    d = radius * c
    return d

def earth_distance(p1,p2):
    radius = 6378.1 #radius of earth in km
    return spherical_distance(p1,p2, radius)


N = dms2angle(43,30) #lat at north most point
S = dms2angle(40,23) #lat at south most point
E = dms2angle(90,8)  #lon at east most point
W = dms2angle(96,38) #lon at west most point
E2W = earth_distance((S,E), (S,W))
S2N = earth_distance((S,E), (N,E))

def iowa_relative(p):
    lat, lon = p
    lon = abs(lon)
    s2n = earth_distance((S,E), (lat, E))
    e2w = earth_distance((S,E), (S, lon))
    return 1.0-(e2w/E2W), s2n/S2N


