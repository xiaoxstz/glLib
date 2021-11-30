from glLibLocals import *
 
def glLibInternal_LoadRAWFile(filename):
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
            if   len(face) == 1: face_type = GL_POINTS
            elif len(face) == 2: face_type = GL_LINES
            elif len(face) == 3: face_type = GL_TRIANGLES
            elif len(face) == 4: face_type = GL_QUADS
        else:
            if (len(face) == 1 and face_type == GL_POINTS) or \
               (len(face) == 2 and face_type == GL_LINES) or \
               (len(face) == 3 and face_type == GL_TRIANGLES) or \
               (len(face) == 4 and face_type == GL_QUADS    ): pass
            else:
                raise glLibError("Object mixes polygon types!")
        for vertex in face:
            vertices.append(list(map(float,vertex)))
    file.close()

    return face_type, \
           vertices, [], faces, [vertices], \
           [[]], [[]], [[]], \
           [], \
           False, False, False

    

