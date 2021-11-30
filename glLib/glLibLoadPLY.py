from glLibLocals import *
import struct

class element_spec(object):
    __slots__ = 'name', 'count', 'properties'
    def __init__(self, name, count):
        self.name = name
        self.count = count
        self.properties = []
    def load(self, format, stream):
        if format == 'ascii':
            stream = re.split('\s+', stream.readline())
        return map(lambda x: x.load(format, stream), self.properties)
    def index(self, name):
        for i, p in enumerate(self.properties):
            if p.name == name: return i
        return -1
class property_spec(object):
    __slots__ = 'name', 'list_type', 'numeric_type'
    def __init__(self, name, list_type, numeric_type):
        self.name = name
        self.list_type = list_type
        self.numeric_type = numeric_type
    def read_format(self, format, count, num_type, stream):
        if format == 'ascii':
            if (num_type == 's'):
                ans = []
                for i in xrange(count):
                    s = stream[i]
                    if len(s) < 2 or s[0] != '"' or s[-1] != '"': raise glLibError('Invalid string "'+str(s)+'"!')
                    ans.append(s[1:-1])
                stream[:count] = []
                return ans
            if (num_type == 'f' or num_type == 'd'): mapper = float
            else:                                    mapper = int
            ans = map(lambda x: mapper(x), stream[:count])
            stream[:count] = []
            return ans
        else:
            if (num_type == 's'):
                ans = []
                for i in xrange(count):
                    fmt = format + 'i'
                    data = stream.read(struct.calcsize(fmt))
                    length = struct.unpack(fmt, data)[0]
                    fmt = '%s%is' % (format, length)
                    data = stream.read(struct.calcsize(fmt))
                    s = struct.unpack(fmt, data)[0]
                    ans.append(s[:-1]) # strip the NULL
                return ans
            else:
                fmt = '%s%i%s' % (format, count, num_type)
                data = stream.read(struct.calcsize(fmt));
                return struct.unpack(fmt, data)
    def load(self, format, stream):
        if (self.list_type != None):
            count = int(self.read_format(format, 1, self.list_type, stream)[0])
            return self.read_format(format, count, self.numeric_type, stream)
        else:
            return self.read_format(format, 1, self.numeric_type, stream)[0]
class object_spec(object):
    __slots__ = 'specs'
    'A list of element_specs'
    def __init__(self):
        self.specs = []
    def load(self, format, stream):
        return dict([(i.name,[i.load(format, stream) for j in xrange(i.count) ]) for i in self.specs])
def load_ply(filename):
    format = ''
    version = '1.0'
    format_specs = {'binary_little_endian':'<', 'binary_big_endian':'>', 'ascii':'ascii'}
    type_specs = {'char':'b', 'uchar':'B', 'int8':'b', 'uint8':'B', 'int16':'h', 'uint16':'H', 'int':'i', 'int32':'i', 'uint':'I', 'uint32':'I', 'float':'f', 'float32':'f', 'float64':'d', 'string':'s'}
    obj_spec = object_spec()
    file = open(filename,'rb')
    signature = file.readline()
    if (signature != 'ply\n'): raise glLibError("Signature line is invalid!")
    while True:
        tokens = re.split(r'[ \n]+',file.readline())
        if len(tokens) == 0: continue
        if tokens[0] == 'end_header': break
        elif tokens[0] == 'comment' or tokens[0] == 'obj_info': continue
        elif tokens[0] == 'format':
            if len(tokens) < 3:                      raise glLibError("Invalid format line!")
            if tokens[1] not in format_specs.keys(): raise glLibError("Unknown format!")
            if tokens[2] != version:                 raise glLibError('Unknown version "'+str(tokens[2])+'"!')
            format = tokens[1]
        elif (tokens[0] == 'element'):
            if len(tokens) < 3: raise glLibError("Invalid element line!")
            obj_spec.specs.append(element_spec(tokens[1], int(tokens[2])))
        elif (tokens[0] == 'property'):
            if not len(obj_spec.specs): raise glLibError("Property without element!")
            if tokens[1] == 'list':     obj_spec.specs[-1].properties.append(property_spec(tokens[4], type_specs[tokens[2]], type_specs[tokens[3]]))
            else:                       obj_spec.specs[-1].properties.append(property_spec(tokens[2], None, type_specs[tokens[1]]))
    obj = obj_spec.load(format_specs[format], file)
    file.close()

    uvindices = colindices = None
    # noindices = None # Ignore normals
    for el in obj_spec.specs:
        if el.name == 'vertex':
            vindices = vindices_x, vindices_y, vindices_z = (el.index('x'), el.index('y'), el.index('z'))
            # noindices = (el.index('nx'), el.index('ny'), el.index('nz'))
            # if -1 in noindices: noindices = None
            uvindices = (el.index('s'), el.index('t'))
            if -1 in uvindices: uvindices = None
            colindices = (el.index('red'), el.index('green'), el.index('blue'))
            if -1 in colindices: colindices = None
        elif el.name == 'face':
            findex = el.index('vertex_indices')
    mesh_faces = []
    mesh_uvs = []
    mesh_colors = []
    if uvindices or colindices:
        # If we have Cols or UVs then we need to check the face order.
        # EVIL EEKADOODLE - face order annoyance.
        def add_face(vertices, indices, uvindices, colindices):
            if len(indices)==4:
                if indices[2]==0 or indices[3]==0:
                    indices= indices[2], indices[3], indices[0], indices[1]
            elif len(indices)==3:
                if indices[2]==0:
                    indices= indices[1], indices[2], indices[0]
                add_face(vertices, indices, uvindices, colindices)
    else:
        def add_face(vertices, indices, uvindices, colindices):
            mesh_faces.append(indices)
            if uvindices:	mesh_uvs.append([ (vertices[index][uvindices[0]], 1.0 - vertices[index][uvindices[1]]) for index in indices])
            if colindices:	mesh_colors.append([ (vertices[index][colindices[0]], vertices[index][colindices[1]], vertices[index][colindices[2]]) for index in indices])
    verts = obj['vertex']
    if 'face' in obj:
        for f in obj['face']:
            ind = f[findex]
            len_ind = len(ind)
            if len_ind <= 4:
                add_face(verts, ind, uvindices, colindices)
            else:
                # Fan fill the face
                for j in xrange(len_ind - 2):
                    add_face(verts, (ind[0], ind[j + 1], ind[j + 2]), uvindices, colindices)
    mesh = Blender.Mesh.New()
    mesh.verts.extend([(v[vindices_x], v[vindices_y], v[vindices_z]) for v in obj['vertex']])
    if mesh_faces:
        mesh.faces.extend(mesh_faces, smooth=True, ignoreDups=True)
        if uvindices or colindices:
            if uvindices:	mesh.faceUV = True
            if colindices:	mesh.vertexColors = True
            for i, f in enumerate(mesh.faces):
                if uvindices:
                    ply_uv = mesh_uvs[i]
                    for j, uv in enumerate(f.uv):
                        uv[:] = ply_uv[j]
                if colindices:
                    ply_col = mesh_colors[i]
                    for j, col in enumerate(f.col):
                        col.r, col.g, col.b = ply_col[j]
    mesh.calcNormals()
def glLibInternal_LoadPLYFile(filename):
    vertices = []
    faces = []
    face_type = None
    filename = filename.split("/")
    file = open(os.path.join(*filename),"rb")
    materials = []
    for line in file.readlines():
        values = line.split()
        if not values: continue
        if len(values)==9:
            v1,v2,v3, v4,v5,v6, v7,v8,v9 = values
            face = [(v1,v2,v3), (v4,v5,v6), (v7,v8,v9)]
        if len(values)==12:
            v1,v2,v3, v4,v5,v6, v7,v8,v9, v10,v11,v12 = values
            face = [(v1,v2,v3), (v4,v5,v6), (v7,v8,v9), (v10,v11,v12)]
        faces.append(face)
        if face_type == None:
            if len(face) == 3: face_type = GL_TRIANGLES
            elif len(face) == 4: face_type = GL_QUADS
        else:
            if (len(face) == 3 and face_type == GL_TRIANGLES) or \
               (len(face) == 4 and face_type == GL_QUADS    ): pass
            else:
                raise glLibError("Object mixes polygon types!")
        for vertex in face:
            vertices.append(map(float,vertex))
    file.close()
    return face_type, \
           vertices, [], faces, [vertices], \
           [[]], [[]], [[]], \
           [], \
           False, False, False

    

