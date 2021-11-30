from glLibLocals import *
from glLibMath import *
from glLibTexturing import glLibTexture2D

def glLibInternal_CheckMaterial(mtllib):
    for material in mtllib.values():
        if "Ka" in material:
            for element in material["Ka"]:
                if element < 0.0 or element > 1.0: raise glLibError("Material's ambient component "+str(material["Ka"])+" is not in the range [0.0,1.0].")
        if "Kd" in material:
            for element in material["Kd"]:
                if element < 0.0 or element > 1.0: raise glLibError("Material's diffuse component "+str(material["Kd"])+" is not in the range [0.0,1.0].")
        if "Ks" in material:
            for element in material["Ks"]:
                if element < 0.0 or element > 1.0: raise glLibError("Material's specular component "+str(material["Ks"])+" is not in the range [0.0,1.0].")
        if "Ns" in material:
            for element in material["Ns"]:
                if element < 0.0 or element > 128.0: raise glLibError("Material's shininess exponent "+str(material["Ns"])+" is not in the range [0.0,128.0].")

def glLibInternal_Material(filename,name,filtering,mipmapping):
    contents = {}
    mtl = None
    mtlfilename = os.path.join(*filename[:-1]+[name])
    try:
        for line in open(mtlfilename, "r"):
            if line.startswith('#'): continue
            values = line.split()
            if not values: continue
            if values[0] == 'newmtl':
                mtl = contents[values[1]] = {}
            elif mtl is None:
                raise ValueError("mtl file doesn't start with newmtl stmt")
            elif values[0] == 'map_Kd':
                try:
                    surf = pygame.image.load(os.path.join(*filename[:-1]+[values[1]]))
                    mtl['texture_Kd'] = glLibTexture2D(surf,GLLIB_ALL,GLLIB_RGBA,filtering,mipmapping)
                except:
                    raise glLibError("Cannot open "+os.path.join(*filename[:-1]+[values[1]])+"!")
            else:
                mtl[values[0]] = list(map(float, values[1:]))
                if len(mtl[values[0]]) == 3: mtl[values[0]] = mtl[values[0]]+[1.0]
##        glLibInternal_CheckMaterial(contents)
        return contents
    except IOError:
        raise glLibError(".mtl library "+mtlfilename+" not found!")
 
def glLibInternal_LoadOBJFile(filename,filtering,mipmapping):
    vertices = []
    polygons = []
    normals = []
    texcoords = []
    faces = []

    face_type = None

    hasnormals = False
    hastexcoords = False
    hasmaterial = True

    filename = filename.split("/")
    mtllib = {}

    material = None
    file = open(os.path.join(*filename),"r")
    for line in file.readlines():
        line = line.strip()
        if line.startswith('#'): continue
        values = line.split()
        if not values: continue
        if   values[0] == 'v' : vertices.append (list(map(float,values[1:4]))); continue
        elif values[0] == 'vn': normals.append  (list(map(float,values[1:4]))); hasnormals   = True; continue
        elif values[0] == 'vt': texcoords.append(list(map(float,values[1:3]))); hastexcoords = True; continue
        elif values[0] == 'f' :
            facevertices = []
            facetexcoords = []
            facenormals = []
            for v in values[1:]:
                w = v.split('/')
                facevertices.append(int(w[0]))
                if len(w) >= 2 and len(w[1]) > 0: facetexcoords.append(int(w[1]))
                else:                             facetexcoords.append(0)
                if len(w) >= 3 and len(w[2]) > 0: facenormals.append(int(w[2]))
                else:                             facenormals.append(0)
            faces.append((facevertices,facenormals,facetexcoords,material))
            continue
        elif values[0] in ('usemtl','usemat'): material = values[1]; continue
        elif values[0] == 'mtllib':
            path = ""
            for word in values[1:]:
                path += word
                path += " "
            path = path[:-1]
            mtllib.update( glLibInternal_Material(filename,path,filtering,mipmapping) )
    file.close()

    lastmaterial = None
    materials = []
    
    vertexarrays = []
    indexed_vertexarrays = []
    normalarrays = []
    indexed_normalarrays = []
    texturecoordarrays = []
    tbnvectorarrays = []
    
    vertexarray = []
    indexed_vertexarray = []
    normalarray = []
    indexed_normalarray = []
    texturecoordarray = []
    tbnvectorarray = []
    if len(faces) == 0:
        raise glLibError("Object contains no polygons!")
    for face in faces:
        vertexindices, normalindices, texcoordindices, material = face
        if face_type == None:
            if   len(vertexindices) == 1: face_type = GL_POINTS
            elif len(vertexindices) == 2: face_type = GL_LINES
            elif len(vertexindices) == 3: face_type = GL_TRIANGLES
            elif len(vertexindices) == 4: face_type = GL_QUADS
            else:
                raise glLibError("Object polygon type of length "+str(len(vertexindices))+" not recognized!")
        else:
            if (len(vertexindices) == 1 and face_type == GL_POINTS) or \
               (len(vertexindices) == 2 and face_type == GL_LINES) or \
               (len(vertexindices) == 3 and face_type == GL_TRIANGLES) or \
               (len(vertexindices) == 4 and face_type == GL_QUADS    ): pass
            else:
                raise glLibError("Object mixes polygon types!")
        try:
            facemtl = mtllib[material]
            currentmaterial = dict(facemtl)
        except KeyError:
            currentmaterial = None
        if lastmaterial != currentmaterial:
            if lastmaterial != None:
                vertexarrays.append(vertexarray)
                normalarrays.append(normalarray)
                texturecoordarrays.append(texturecoordarray)
                tbnvectorarrays.append(tbnvectorarray)
                materials.append(lastmaterial)
                vertexarray = []
                indexed_vertexarray = []
                normalarray = []
                indexed_normalarray = []
                texturecoordarray = []
                tbnvectorarray = []
            lastmaterial = currentmaterial
        if   face_type == GL_POINTS   : points_per_poly = 1
        elif face_type == GL_LINES    : points_per_poly = 2
        elif face_type == GL_TRIANGLES: points_per_poly = 3
        elif face_type == GL_QUADS    : points_per_poly = 4
        polygon = [ [vertices[vertexindices[i]-1] for i in range(points_per_poly)] ]
        if hastexcoords:
            polygon.append([texcoords[texcoordindices[i]-1] for i in range(points_per_poly)])
        if hasnormals:
            polygon.append([normals[normalindices[i]-1] for i in range(points_per_poly)])
        
        if face_type == GL_TRIANGLES:
            has_vertex_tangents = False
            if hastexcoords and hasnormals:
                tritangents = glLibInternal_CalculateTangentArray(polygon)
                has_vertex_tangents = True
        for index in range(points_per_poly):
            vertexarray.append          (polygon[0][index])
            indexed_vertexarray.append  (vertexindices[index]-1)
            if hastexcoords:
                texturecoordarray.append(polygon[1][index])
                if hasnormals:
                    normalarray.append        (polygon[2][index])
                    indexed_normalarray.append(normalindices[index]-1)
            elif hasnormals:
                normalarray.append        (polygon[1][index])
                indexed_normalarray.append(normalindices[index]-1)
            if face_type == GL_TRIANGLES and has_vertex_tangents:
                tbnvectorarray.append   (tritangents[index])
        polygons.append(polygon[0])
    vertexarrays.append(vertexarray)
    indexed_vertexarrays.append(indexed_vertexarray)
    normalarrays.append(normalarray)
    indexed_normalarrays.append(indexed_normalarray)
    texturecoordarrays.append(texturecoordarray)
    if face_type == GL_TRIANGLES:
        tbnvectorarrays.append(tbnvectorarray)
    materials.append(currentmaterial)

    tbnvectorarrays2 = []
    if face_type == GL_TRIANGLES:
        if hastexcoords:
            for array in tbnvectorarrays:
                nparray = np.zeros((len(array),4),'f')
                index = 0
                for element in array:
                    nparray[index,0] = element[0]
                    nparray[index,1] = element[1]
                    nparray[index,2] = element[2]
                    nparray[index,3] = element[3]
                    index += 1
                tbnvectorarrays2.append(nparray.tostring())

    return face_type, \
           vertices, normals, polygons, vertexarrays, indexed_vertexarrays, \
           normalarrays, indexed_normalarrays, texturecoordarrays, tbnvectorarrays2, \
           materials, \
           hasnormals, hastexcoords, hasmaterial
    #face_type = type of face
    #vertices = list of vertices ("raw_vertices")
    #normals = list of normals ("raw_normals")
    #polygons = list of primitives, each containing 1 to 4 vertices
    #vertexarrays         = list containing (one for each sublist) lists of primitives, each containing 1 to 4 vertices
    #indexed_vertexarrays = list containing (one for each sublist) lists of primitives, each containing 1 to 4 vertex indices
    #normalarrays         = list containing (one for each sublist) lists of normals
    #indexed_normalarrays = list containing (one for each sublist) lists of normal indices
    #texturecoordarrays   = list containing (one for each sublist) lists of texture coordinates
    #tbnvectorarrays2     = list containing (one for each sublist) lists of tbn vectors
    #materials = list containing (one for each sublist) a dictionary containing material specifications
    #hasnormals, hastexcoords, hasmaterial = boolean for whether normals, texturecoordinates, materials are present, respectively
