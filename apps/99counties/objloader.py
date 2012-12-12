

class BoundingBox3D(object):
    def __init__(self, points=None):
        self.x = float('inf')
        self.y = float('inf')
        self.z = float('inf')
        self.xmax = float('-inf')
        self.ymax = float('-inf')
        self.zmax = float('-inf')
        self.width = 0
        self.height = 0
        self.depth = 0
        self.cx = 0
        self.cy = 0
        self.cz = 0

    def add_point(self, x, y, z):
        self.x = min(x, self.x)
        self.y = min(y, self.y)
        self.z = min(z, self.z)
        self.xmax = max(x, self.xmax)
        self.ymax = max(y, self.ymax)
        self.zmax = max(y, self.zmax)

        self.width = self.xmax - self.x
        self.height = self.ymax - self.y
        self.depth = self.zmax - self.z
        self.pos = (self.x, self.y, self.z)
        self.cx = self.x + (self.width/2.0)
        self.cy = self.y + (self.height/2.0)
        self.cz = self.z + (self.depth/2.0)
        self.center = (self.cx, self.cy, self.cz)


class MeshData(object):
    def __init__(self, **kwargs):
        self.name = kwargs.get("name")
        self.vertex_format = [
            ('v_pos', 3, 'float'),
            ('v_normal', 3, 'float'),
            ('v_tc0', 2, 'float')]
        self.vertices = []
        self.indices = []



class ObjFile:

    def finish_object(self):
        if self._current_object == None:
            return

        mesh = MeshData()
        mesh.bounds = BoundingBox3D()
        idx = 0
        for f in self.faces:
            verts =  f[0]
            norms = f[1]
            for i in range(3):
                v = self.vertices[verts[i]-1]
                n = self.normals[norms[i]-1]
                data = [v[0], v[1], v[2], n[0], n[1], n[2], 0.0,0.0]
                mesh.bounds.add_point(v[0], v[1], v[2])
                mesh.vertices.extend(data)
            tri = [idx, idx+1, idx+2]
            mesh.indices.extend(tri)
            idx += 3
        self.objects[self._current_object] = mesh
        self.faces = []

    def __init__(self, filename, swapyz=False):
        """Loads a Wavefront OBJ file. """
        self.objects = {}
        self.vertices = []
        self.normals = []
        self.texcoords = []
        self.faces = []

        self._current_object = None

        material = None
        for line in open(filename, "r"):
            if line.startswith('#'): continue
            if line.startswith('s'): continue
            values = line.split()
            if not values: continue
            if values[0] == 'o':
                self.finish_object()
                self._current_object = values[1]
            elif values[0] == 'mtllib':
                self.mtl = MTL(values[1])
            elif values[0] in ('usemtl', 'usemat'):
                material = values[1]
            if values[0] == 'v':
                v = map(float, values[1:4])
                if swapyz:
                    v = v[0], v[2], v[1]
                self.vertices.append(v)
            elif values[0] == 'vn':
                v = map(float, values[1:4])
                if swapyz:
                    v = v[0], v[2], v[1]
                self.normals.append(v)
            elif values[0] == 'vt':
                self.texcoords.append(map(float, values[1:3]))
            elif values[0] == 'f':
                face = []
                texcoords = []
                norms = []
                for v in values[1:]:
                    w = v.split('/')
                    face.append(int(w[0]))
                    if len(w) >= 2 and len(w[1]) > 0:
                        texcoords.append(int(w[1]))
                    else:
                        texcoords.append(0)
                    if len(w) >= 3 and len(w[2]) > 0:
                        norms.append(int(w[2]))
                    else:
                        norms.append(0)
                self.faces.append((face, norms, texcoords, material))
        self.finish_object()


def MTL(filename):
    contents = {}
    mtl = None
    return
    for line in open(filename, "r"):
        if line.startswith('#'): continue
        values = line.split()
        if not values: continue
        if values[0] == 'newmtl':
            mtl = contents[values[1]] = {}
        elif mtl is None:
            raise ValueError, "mtl file doesn't start with newmtl stmt"
        mtl[values[0]] = values[1:]
    return contents



