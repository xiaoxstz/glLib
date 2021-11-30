from glLibLocals import *
from glLibLoadOBJ import *
from glLibLoadRAW import *
from glLibShader import *
from glLibMath import rndint, grid3D
from glLibMaterials import glLibGetMaterialParam
def glLibDrawScreenQuad(rect=GLLIB_AUTO,texture=False,uv_tile=1,uv_delta=0):
    if rect == GLLIB_AUTO:
        rect = glGetFloatv(GL_VIEWPORT)
        rect = [0,0,rect[2],rect[3]] #because the viewport transform makes this correct
##        rect = [-2,-2,rect[2]+4,rect[3]+4]
    if texture != False:
        try:texcoord_rect = [0,0,uv_tile[0],uv_tile[1]] #in two point form
        except:texcoord_rect = [0,0,uv_tile,uv_tile]
        for element in texcoord_rect:
            try: element += uv_delta[0]
            except: element += uv_delta
        try:
            if texture.type == GLLIB_TEXTURE_2D: glLibSelectTexture(texture)
        except: pass
        glBegin(GL_QUADS)
        glTexCoord2f(texcoord_rect[0],                 texcoord_rect[1]                 );glVertex2f(rect[0],        rect[1]        )
        glTexCoord2f(texcoord_rect[0]+texcoord_rect[2],texcoord_rect[1]                 );glVertex2f(rect[0]+rect[2],rect[1]        )
        glTexCoord2f(texcoord_rect[0]+texcoord_rect[2],texcoord_rect[1]+texcoord_rect[3]);glVertex2f(rect[0]+rect[2],rect[1]+rect[3])
        glTexCoord2f(texcoord_rect[0],                 texcoord_rect[1]+texcoord_rect[3]);glVertex2f(rect[0],        rect[1]+rect[3])
        glEnd()
    else:
        glBegin(GL_QUADS)
        glVertex2f(rect[0],        rect[1]        )
        glVertex2f(rect[0]+rect[2],rect[1]        )
        glVertex2f(rect[0]+rect[2],rect[1]+rect[3])
        glVertex2f(rect[0],        rect[1]+rect[3])
        glEnd()
class glLibQuad:
    def __init__(self,rect,texture=False):
        self.x = rect[0]
        self.y = rect[1]
        self.width = rect[2]
        self.height = rect[3]
        self.rect = list(rect)
        self.list = glGenLists(1)
        glNewList(self.list,GL_COMPILE)
        if texture != False:
            try: glLibSelectTexture(texture)
            except: pass
        glBegin(GL_QUADS)
        if texture != False: glTexCoord2f(0,0)
        glVertex3f(rect[0],        rect[1],        0)
        if texture != False: glTexCoord2f(1,0)
        glVertex3f(rect[0]+rect[2],rect[1],        0)
        if texture != False: glTexCoord2f(1,1)
        glVertex3f(rect[0]+rect[2],rect[1]+rect[3],0)
        if texture != False: glTexCoord2f(0,1)
        glVertex3f(rect[0],        rect[1]+rect[3],0)
        glEnd()
        glEndList()
    def draw(self):
        glCallList(self.list)
def glLibInternal_quadric(normals,normalflip,flipnormalflip,texture):
    quad = gluNewQuadric()
    if   normals == GLLIB_NONE:           gluQuadricNormals(quad,GLU_NONE)
    elif normals == GLLIB_FACE_NORMALS:   gluQuadricNormals(quad,GLU_FLAT)
    elif normals == GLLIB_VERTEX_NORMALS: gluQuadricNormals(quad,GLU_SMOOTH)
    if flipnormalflip:
        inside = GLU_OUTSIDE
        outside = GLU_INSIDE
    else:
        inside = GLU_INSIDE
        outside = GLU_OUTSIDE
    if normalflip: gluQuadricOrientation(quad,inside )
    else:          gluQuadricOrientation(quad,outside)
    if texture != False:
        if texture != True: glLibSelectTexture(texture)
        gluQuadricTexture(quad,GLU_TRUE)
    else:
        gluQuadricTexture(quad,GLU_FALSE)
    return quad
class glLibSphere:
    def __init__(self,size,detail,normals=GLLIB_VERTEX_NORMALS,normalflip=False,texture=False):
        self.radius = size
        self.list = glGenLists(1)
        glNewList(self.list,GL_COMPILE)
        Sphere = glLibInternal_quadric(normals,normalflip,False,texture)
        try: gluSphere(Sphere,size,detail,detail)
        except: gluSphere(Sphere,size,detail[0],detail[1])
        glEndList()
    def draw(self):
        glCallList(self.list)
class glLibCylinder:
    def __init__(self,length,r1,r2,detail,cap1=False,cap2=False,normals=GLLIB_VERTEX_NORMALS,normalflip=False,texture=False):
        self.list = glGenLists(1)
        glNewList(self.list,GL_COMPILE)
        Cylinder = glLibInternal_quadric(normals,normalflip,False,texture)
        try:    radialdetail,stacks = detail[0],detail[1]
        except: radialdetail,stacks = detail,1
        gluCylinder(Cylinder,r1,r2,length,radialdetail,stacks)
        if cap1 != False:
            disk1 = glLibInternal_quadric(normals,normalflip,True,texture)
            radius = 0.0
            if cap1 != True: radius = float(cap1)
            gluDisk(disk1,radius,r1,radialdetail,1)
        if cap2 != False:
            disk2 = glLibInternal_quadric(normals,normalflip,False,texture)
            radius = 0.0
            if cap2 != True: radius = float(cap2)
            glTranslatef(0,0,length)
            gluDisk(disk2,radius,r2,radialdetail,1)
            glTranslatef(0,0,-length)
        glEndList()
    def draw(self):
        glCallList(self.list)
class glLibDome:
    def __init__(self,size,detail,normals=GLLIB_VERTEX_NORMALS,texture=False):
        self.list = glGenLists(1)
        glNewList(self.list,GL_COMPILE)
        if texture: glLibSelectTexture(texture)
        vertical_step = 90.0/detail
        horizontal_step = 360.0/detail
        y_angle = 0.0
        for azimuth_angle in range(detail):
            height_low = size*sin(radians(y_angle))
            height_high = size*sin(radians(y_angle+vertical_step))
            glBegin(GL_QUAD_STRIP)
            x_angle = 0.0
            for angle in range(detail+1):
                v1 = [size*cos(radians(x_angle))*cos(radians(y_angle)),
                      height_low,
                      size*sin(radians(x_angle))*cos(radians(y_angle))]
                v2 = [size*cos(radians(x_angle))*cos(radians(y_angle+vertical_step)),
                      height_high,
                      size*sin(radians(x_angle))*cos(radians(y_angle+vertical_step))]
                if normals == GLLIB_VERTEX_NORMALS: glNormal3fv(normalize(v1))
                if texture: glTexCoord2f(x_angle/360.0,y_angle/90.0)
                glVertex3fv(v1)
                if normals == GLLIB_VERTEX_NORMALS: glNormal3fv(normalize(v2))
                if texture: glTexCoord2f(x_angle/360.0,(y_angle+vertical_step)/90.0)
                glVertex3fv(v2)
                x_angle += horizontal_step
            glEnd()
            y_angle += vertical_step
        glEndList()
    def draw(self):
        glCallList(self.list)
class glLibPlane:
    def __init__(self,size,normal,texture=False,uv_tile=1,uv_delta=0):
        self.lists = {}
        self.size = size
        self.normal = normal
        self.texture = texture
        self.uv_tile = uv_tile
        self.uv_delta = uv_delta
        self.glLibInternal_build_list("ff")
    def glLibInternal_vertex(self,scs,texcoord,normal):
        if self.texture != False:glTexCoord2f(*texcoord)
        xsc,ysc,zsc = scs
        try: glVertex3f(xsc*self.size[0],0,zsc*self.size[1])
        except: glVertex3f(xsc*self.size,0,zsc*self.size)
    def glLibInternal_build_list(self,shader,loc=None):
        self.lists[shader] = glGenLists(1)
        glNewList(self.lists[shader],GL_COMPILE)
        
        elevangle = degrees(atan2(hypot(self.normal[0],self.normal[2]),self.normal[1]))
        xzangle = degrees(atan2(self.normal[0],self.normal[2]))
        if self.texture and self.texture != True:
            glLibSelectTexture(self.texture)
        texcoord_rect = [None]*4
        if self.texture != False:
            try:texcoord_rect = [0,0,self.uv_tile[0],self.uv_tile[1]] #in two point form
            except:texcoord_rect = [0,0,self.uv_tile,self.uv_tile]
            try:
                texcoord_rect[0] += self.uv_delta[0]
                texcoord_rect[1] += self.uv_delta[1]
                texcoord_rect[2] += self.uv_delta[0]
                texcoord_rect[3] += self.uv_delta[1]
            except:
                for element in texcoord_rect:
                    element += self.uv_delta
        glPushMatrix()
        glRotatef(xzangle,0,1,0)
        glRotatef(elevangle,1,0,0)
        v1 = [  [-1, 0, 1],  [texcoord_rect[0],texcoord_rect[1]],  [0,1,0]  ]
        v2 = [  [ 1, 0, 1],  [texcoord_rect[2],texcoord_rect[1]],  [0,1,0]  ]
        v3 = [  [ 1, 0,-1],  [texcoord_rect[2],texcoord_rect[3]],  [0,1,0]  ]
        v4 = [  [-1, 0,-1],  [texcoord_rect[0],texcoord_rect[3]],  [0,1,0]  ]
        if shader == "ff":
            glNormal3f(0,1,0)
            glBegin(GL_QUADS)
            self.glLibInternal_vertex(*v1)
            self.glLibInternal_vertex(*v2)
            self.glLibInternal_vertex(*v3)
            self.glLibInternal_vertex(*v4)
            glEnd()
        else:
            glNormal3f(0,1,0)
            glBegin(GL_TRIANGLES)
            glVertexAttrib4f(*list([loc]+[1.0,0.0,0.0,1.0]))
            self.glLibInternal_vertex(*v4)
            glVertexAttrib4f(*list([loc]+[1.0,0.0,0.0,1.0]))
            self.glLibInternal_vertex(*v3)
            glVertexAttrib4f(*list([loc]+[1.0,0.0,0.0,1.0]))
            self.glLibInternal_vertex(*v2)
            
            glVertexAttrib4f(*list([loc]+[1.0,0.0,0.0,1.0]))
            self.glLibInternal_vertex(*v4)
            glVertexAttrib4f(*list([loc]+[1.0,0.0,0.0,1.0]))
            self.glLibInternal_vertex(*v2)
            glVertexAttrib4f(*list([loc]+[1.0,0.0,0.0,1.0]))
            self.glLibInternal_vertex(*v1)
            glEnd()
        glPopMatrix()
        glEndList()
    def build_shader_list(self,shader):
        glLibUseShader(shader)
        location = glGetAttribLocation(shader.program,"vert_tangent")
        if location != -1: self.glLibInternal_build_list(shader.str_name,location)
        else: print("Warning: .build_shader_list(...) failed!  Check that the shader is valid, compiled, and uses normalmapping to construct its final fragment color!")
        glLibUseShader(None)
    def draw(self,shader=None):
        if shader == None: glCallList(self.lists["ff"])
        else:
            try: glCallList(self.lists[shader.str_name])
            except:
                print("Warning: call .build_shader_list(...) with this shader first to generate required data!  Drawing without normalmapping data.")
                glCallList(self.lists["ff"])
class glLibObject:
    def __init__(self,path=None,filtering=False,mipmapping=False):
        if path==None: return
        if path.endswith(".obj"):
            self.type, \
                self.raw_vertices, self.raw_normals, self.raw_polygons, self.vertices, self.indexed_vertices, \
                self.normals, self.indexed_normals, self.texturecoords, self.tbnvectors, \
                self.materials, \
                self.hasnormcoords, self.hastexcoords, self.hasmaterial = glLibInternal_LoadOBJFile(path,filtering,mipmapping)
        elif path.endswith(".raw"):
            self.type, \
                self.raw_vertices, self.raw_normals, self.raw_polygons, self.vertices, \
                self.normals, self.texturecoords, self.tbnvectors, \
                self.materials, \
                self.hasnormcoords, self.hastexcoords, self.hasmaterial = glLibInternal_LoadRAWFile(path)
            self.indexed_vertices, self.indexed_normals = None, None
        else:
            raise glLibError("Object type at "+path+" not recognized!")
##        print self.type, \
##                len(self.raw_vertices), len(self.raw_normals), len(self.raw_polygons), len(self.vertices[0]), \
##                len(self.indexed_vertices[0]), \
##                len(self.normals[0]), len(self.indexed_normals[0]), len(self.texturecoords[0]), len(self.tbnvectors[0]), \
##                self.materials, \
##                self.hasnormcoords, self.hastexcoords, self.hasmaterial
        self.number_of_lists = len(self.vertices)
        self.light_volume_face_data = []
        self.transformed_vertices = {}
        self.transformed_normals = {}
        self.extremes = None
    def save_to_binary(self,filename): #doesn't save materials, etc.!
        data = pickle.dumps(
            [
             int(self.type),
             self.hasnormcoords,self.hastexcoords,self.hasmaterial,
             self.vertices,self.normals,self.texturecoords,
             self.materials,
             self.number_of_lists
            ],
            pickle.HIGHEST_PROTOCOL)
        data = zlib.compress(data,9)
        file = open(filename,"wb")
        file.write(data)
        file.close()
    def load_from_binary(self,filename):
        file = open(filename,"rb")
        data = file.read()
        file.close()
        data = zlib.decompress(data)

        self.type,\
            self.hasnormcoords,self.hastexcoords,self.hasmaterial,\
            self.vertices,self.normals,self.texturecoords,\
            self.materials,\
            self.number_of_lists = pickle.loads(data)
    def use_data(self,data): #incorrect results with shadow volumes
        self.vertices = data
    def glLibInternal_set_mtl(self, sublist,indices, lst_amb,lst_dif,lst_spc,lst_shn):
        material = self.materials[sublist]
        if material == None:
            glDisable(GL_TEXTURE_2D)
            glMaterialfv(GL_FRONT_AND_BACK,GL_AMBIENT,[0.2,0.2,0.2,1.0]); lst_amb = [0.2,0.2,0.2,1.0]
            glMaterialfv(GL_FRONT_AND_BACK,GL_DIFFUSE,[0.8,0.8,0.8,1.0]); lst_dif = [0.8,0.8,0.8,1.0]
            glMaterialfv(GL_FRONT_AND_BACK,GL_SPECULAR,[0.0,0.0,0.0,1.0]); lst_spc = [0.0,0.0,0.0,1.0]
            glMaterialfv(GL_FRONT_AND_BACK,GL_SHININESS,0.0); lst_shn = 0.0
        else:
            if "Ka" in material:
                ambient = material["Ka"]
                if lst_amb != ambient: glMaterialfv(GL_FRONT_AND_BACK,GL_AMBIENT,ambient); lst_amb = ambient
            else:
                glMaterialfv(GL_FRONT_AND_BACK,GL_AMBIENT,[0.2,0.2,0.2,1.0]); lst_amb = [0.2,0.2,0.2,1.0]
            if "Kd" in material:
                diffuse = material["Kd"]
                if lst_dif != diffuse: glMaterialfv(GL_FRONT_AND_BACK,GL_DIFFUSE,diffuse); lst_dif = diffuse
            else:
                glMaterialfv(GL_FRONT_AND_BACK,GL_DIFFUSE,[0.8,0.8,0.8,1.0]); lst_dif = [0.8,0.8,0.8,1.0]
            if "Ks" in material:
                specular = material["Ks"]
                if lst_spc != specular: glMaterialfv(GL_FRONT_AND_BACK,GL_SPECULAR,specular); lst_spc = specular
            else:
                glMaterialfv(GL_FRONT_AND_BACK,GL_SPECULAR,[0.0,0.0,0.0,1.0]); lst_spc = [0.0,0.0,0.0,1.0]
            if "Ns" in material:
                shininess = material["Ns"]
                if lst_shn != shininess: glMaterialfv(GL_FRONT_AND_BACK,GL_SHININESS,shininess); lst_shn = shininess
            else:
                glMaterialfv(GL_FRONT_AND_BACK,GL_SHININESS,0.0); lst_shn = 0.0
            if "texture_Kd" in material:
                if len(indices) > sublist:
                    index = indices[sublist]
                    if index != None:
                        glEnable(GL_TEXTURE_2D)
                        glLibActiveTexture(index-1); glLibSelectTexture(material["texture_Kd"]); glLibActiveTexture(0)
            else:
                glDisable(GL_TEXTURE_2D)
        return lst_amb,lst_dif,lst_spc,lst_shn
    def set_material(self,material):
        texture = None
        try:
            try:
                ambient,diffuse,specular,shininess = material[0]
                materialnumbers = [int(material[1])]
                try: texture = material[2]
                except: pass
            except:
                ambient,diffuse,specular,shininess = material
                materialnumbers = range(0,len(self.materials),1)
        except:
            try:
                ambient,diffuse,specular,shininess = glLibGetMaterialParam(material[0])
                materialnumbers = [int(material[1])]
            except:
                ambient,diffuse,specular,shininess = glLibGetMaterialParam(material)
                materialnumbers = range(0,len(self.materials),1)
        for materialnumber in materialnumbers:
            if ambient   != -1: self.materials[materialnumber]["Ka"] = list(ambient)
            if diffuse   != -1: self.materials[materialnumber]["Kd"] = list(diffuse)
            if specular  != -1: self.materials[materialnumber]["Ks"] = list(specular)
            if shininess != -1: self.materials[materialnumber]["Ns"] = shininess
            if texture   != -1:
                if texture != None:
                    self.materials[materialnumber]["texture_Kd"] = texture
    def get_extremes(self):
        if self.extremes == None:
            self.extremes = [[None,None],[None,None],[None,None]]
            for index in range(len(self.raw_vertices)):
                vertex = self.raw_vertices[index]
                if self.extremes[0][0]==None or vertex[0]<self.extremes[0][0]: self.extremes[0][0] = vertex[0]
                if self.extremes[0][1]==None or vertex[0]>self.extremes[0][1]: self.extremes[0][1] = vertex[0]
                if self.extremes[1][0]==None or vertex[1]<self.extremes[1][0]: self.extremes[1][0] = vertex[1]
                if self.extremes[1][1]==None or vertex[1]>self.extremes[1][1]: self.extremes[1][1] = vertex[1]
                if self.extremes[2][0]==None or vertex[2]<self.extremes[2][0]: self.extremes[2][0] = vertex[2]
                if self.extremes[2][1]==None or vertex[2]>self.extremes[2][1]: self.extremes[2][1] = vertex[2]
        return self.extremes
    def build_list(self,indices=[],withmaterials=True,withtexcoords=True,withnormals=True):
        self.list = glGenLists(1)
        glNewList(self.list,GL_COMPILE)
        self.draw_direct(indices=indices,withmaterials=withmaterials,withtexcoords=withtexcoords,withnormals=withnormals)
        glEndList()
    def build_vbo(self):
        if GLLIB_VBO_AVAILABLE:
            self.vertex_vbos = []
            self.normal_vbos = []
            self.texcoord_vbos = []
            self.vertex_attrib_vbos = []
            for sublist in range(self.number_of_lists):
                attributenum = 0
                attributes = []
                try:    attributes.append(self.vertices[sublist])
                except: attributes.append([])
                try:    attributes.append(self.normals[sublist])
                except: attributes.append([])
                try:    attributes.append(self.texturecoords[sublist])
                except: attributes.append([])
                try:    attributes.append(self.tbnvectors[sublist])
                except: attributes.append([])
                for attribute in attributes:
                    if not self.hasnormcoords and attributenum ==    1 : continue
                    if not self.hastexcoords  and attributenum in [2,3]: continue
                    singlelist = []
                    for vertex in attribute:
                        singlelist.append(vertex)
                    if   attributenum == 0: self.vertex_vbos.append(vbo.VBO(np.array(singlelist,"f"),usage='GL_STATIC_DRAW'))
                    elif attributenum == 1: self.normal_vbos.append(vbo.VBO(np.array(singlelist,"f"),usage='GL_STATIC_DRAW'))
                    elif attributenum == 2: self.texcoord_vbos.append(vbo.VBO(np.array(singlelist,"f"),usage='GL_STATIC_DRAW'))
                    elif attributenum == 3: self.vertex_attrib_vbos.append(vbo.VBO(self.tbnvectors[sublist],usage='GL_STATIC_DRAW'))
                    attributenum += 1
    ##        for vbos in [self.vertex_vbos,self.normal_vbos,self.texcoord_vbos,self.vertex_attrib_vbos]:
    ##            list = []
    ##            for vbo_obj in vbos:
    ##                list.append(len(vbo_obj))
    ##            print list
        else:
            raise glLibError("Error: VBOs not available; VBO cannot be built!")
    def build_light_volume_data(self):
        self.light_volume_face_data = {}
        for sublist in range(self.number_of_lists):
            self.light_volume_face_data[sublist] = []
            if self.type == GL_TRIANGLES:
                for index in range(0,len(self.indexed_vertices[sublist]),3):
                    p1   = self.indexed_vertices[sublist][index  ]
                    p2   = self.indexed_vertices[sublist][index+1]
                    p3   = self.indexed_vertices[sublist][index+2]
                    norm = self.indexed_normals [sublist][index  ]
                    self.light_volume_face_data[sublist].append([p1,p2,p3,norm])
            elif self.type == GL_QUADS:
                for index in range(0,len(self.indexed_vertices[sublist]),4):
                    p1 = self.indexed_vertices[sublist][index  ]
                    p2 = self.indexed_vertices[sublist][index+1]
                    p3 = self.indexed_vertices[sublist][index+2]
                    p4 = self.indexed_vertices[sublist][index+3]
                    norm = self.indexed_normals [sublist][index  ]
                    self.light_volume_face_data[sublist].append([p1,p2,p3,norm])
                    self.light_volume_face_data[sublist].append([p1,p3,p4,norm])
            self.light_volume_face_data[sublist] = np.array(self.light_volume_face_data[sublist])
    def draw_direct(self,indices=[],withmaterials=True,withtexcoords=True,withnormals=True):
        lst_amb=None;lst_dif=None;lst_spc=None;lst_shn=None
        if self.hasmaterial: glPushAttrib(GL_ENABLE_BIT|GL_LIGHTING_BIT)
        for sublist in range(self.number_of_lists):
            if withmaterials and self.hasmaterial:
                lst_amb,lst_dif,lst_spc,lst_shn = self.glLibInternal_set_mtl(sublist,indices, lst_amb,lst_dif,lst_spc,lst_shn)
            glBegin(self.type)
            for index in range(len(self.vertices[sublist])):
                if withnormals   and self.hasnormcoords: glNormal3f(*self.normals[sublist][index])
                if withtexcoords and self.hastexcoords: glTexCoord2f(*self.texturecoords[sublist][index])
                glVertex3f(*self.vertices[sublist][index])
            glEnd()
        if self.hasmaterial: glPopAttrib()
    def draw_list(self):
        glCallList(self.list)
    def draw_vbo(self,shader=None,indices=[],withmaterials=True,withtexcoords=True,withnormals=True,withtangents=True):
        lst_amb=None;lst_dif=None;lst_spc=None;lst_shn=None
        location = -1
        if shader != None:
##            glLibUseShader(shader)
            location = glGetAttribLocation(shader.program,b"vert_tangent")
        glEnableClientState(GL_VERTEX_ARRAY)
        if self.hasnormcoords and withnormals: glEnableClientState(GL_NORMAL_ARRAY)
        if self.hastexcoords and withtexcoords:
            glEnableClientState(GL_TEXTURE_COORD_ARRAY)
            if location != -1 and withtangents: glEnableVertexAttribArray(location)
        glPushAttrib(GL_ENABLE_BIT|GL_LIGHTING_BIT)
        for sublist in range(self.number_of_lists):
            if self.hasmaterial and withmaterials:
                lst_amb,lst_dif,lst_spc,lst_shn = self.glLibInternal_set_mtl(sublist,indices, lst_amb,lst_dif,lst_spc,lst_shn)
            self.vertex_vbos[sublist].bind()
##            glVertexPointerf(self.vertex_vbos[0])
            glVertexPointerf(self.vertex_vbos[sublist])
            if self.hasnormcoords and withnormals:
                self.normal_vbos[sublist].bind()
##                glNormalPointerf(self.normal_vbos[0])
                glNormalPointerf(self.normal_vbos[sublist])
            if self.hastexcoords and withtexcoords:
                self.texcoord_vbos[sublist].bind()
##                glTexCoordPointerf(self.texcoord_vbos[0])
                glTexCoordPointerf(self.texcoord_vbos[sublist])
            if location != -1 and withtangents:
                self.vertex_attrib_vbos[sublist].bind()
                glVertexAttribPointer(location,4,GL_FLOAT,GL_FALSE,0,None)
            glDrawArrays(self.type,0,len(self.vertices[sublist]))
        glPopAttrib()
        glBindBuffer(GL_ARRAY_BUFFER,0)
        if self.hastexcoords and withtexcoords:
            glDisableClientState(GL_TEXTURE_COORD_ARRAY)
            if location != -1 and withtangents: glDisableVertexAttribArray(location)
        if self.hasnormcoords and withnormals: glDisableClientState(GL_NORMAL_ARRAY)
        glDisableClientState(GL_VERTEX_ARRAY)
    def draw_arrays(self,shader=None,indices=[],withmaterials=True,withtexcoords=True,withnormals=True,withtangents=True):
        lst_amb=None;lst_dif=None;lst_spc=None;lst_shn=None
        if self.hasmaterial: glPushAttrib(GL_ENABLE_BIT|GL_LIGHTING_BIT)
        location = -1
        if shader != None:
            glLibUseShader(shader)
            location = glGetAttribLocation(shader.program,"vert_tangent")
        glEnableClientState(GL_VERTEX_ARRAY)
        if self.hasnormcoords and withnormals: glEnableClientState(GL_NORMAL_ARRAY)
        if self.hastexcoords and withtexcoords:
            glEnableClientState(GL_TEXTURE_COORD_ARRAY)
            if location != -1 and withtangents: glEnableVertexAttribArray(location)
        for sublist in range(self.number_of_lists):
            if self.hasmaterial and withmaterials:
                lst_amb,lst_dif,lst_spc,lst_shn = self.glLibInternal_set_mtl(sublist,indices, lst_amb,lst_dif,lst_spc,lst_shn)
            if self.vertices[sublist] != []:
                glVertexPointer(3,GL_FLOAT,0,self.vertices[sublist])
                if self.hasnormcoords and withnormals: glNormalPointer(GL_FLOAT,0,self.normals[sublist])
                if self.hastexcoords and withtexcoords: glTexCoordPointer(2,GL_FLOAT,0,self.texturecoords[sublist])
                if location != -1 and withtangents: glVertexAttribPointer(location,4,GL_FLOAT,GL_FALSE,0,self.tbnvectors[sublist])
                glDrawArrays(self.type,0,len(self.vertices[sublist]))
        if self.hastexcoords and withtexcoords:
            if location != -1 and withtangents: glDisableVertexAttribArray(location)
            glDisableClientState(GL_TEXTURE_COORD_ARRAY)
        if self.hasnormcoords and withnormals: glDisableClientState(GL_NORMAL_ARRAY)
        glDisableClientState(GL_VERTEX_ARRAY)
        if self.hasmaterial: glPopAttrib()
    def __del__(self):
        try:
            buffers = []
            for vbolist in [self.vertex_vbos,self.normal_vbos,self.texcoord_vbos,self.vertex_attrib_vbos]:
                for vbo in vbolist:
                    vbo.delete()
        except:pass
class glLibRectangularSolid():
    def glLibInternal_draw_faces(self,size,texcoord_type,normalflip,per_face_texture=None):
        if per_face_texture == None: glBegin(GL_QUADS)
        for face_ind in range(6):
            if per_face_texture != None:
                glLibSelectTexture(per_face_texture[face_ind])
                glBegin(GL_QUADS)
            if self.normals[0] != False: glNormal3f(*sc_vec(normalflip,self.normals[face_ind]))
            v_indices = [0,1,2,3]
            if normalflip == -1.0: v_indices = [1,0,3,2]
            for v_index in v_indices:
                if   texcoord_type ==   "2D": glTexCoord2f(*self.texcoords2d[face_ind][v_index])
                elif texcoord_type ==   "3D": glTexCoord3f(*sc_vec(0.5,vec_add(self.vertices[face_ind][v_index],[1.0]*3)))
                elif texcoord_type == "Cube": glTexCoord3f(*self.vertices[face_ind][v_index])
                glVertex3f(*vec_mult(size,self.vertices[face_ind][v_index]))
            if per_face_texture != None: glEnd()
        if per_face_texture == None: glEnd()
    def __init__(self,size,texture=False,normals=GLLIB_FACE_NORMALS,normalflip=False):
        self.box = glGenLists(1)
        glNewList(self.box,GL_COMPILE)
        #Right, Left, Top, Bottom, Front, Back
        if normals == GLLIB_FACE_NORMALS:
            self.normals = [[1,0,0],[-1,0,0],[0,1,0],[0,-1,0],[0,0,-1],[0,0,1]]
        else:
            self.normals = [False]*6
        self.texcoords2d = [[[1,0],[1,1],[0,1],[0,0]],
                            [[0,1],[0,0],[1,0],[1,1]],
                            [[0,1],[0,0],[1,0],[1,1]],
                            [[1,0],[1,1],[0,1],[0,0]],
                            [[1,0],[1,1],[0,1],[0,0]],
                            [[1,0],[1,1],[0,1],[0,0]]]
        self.vertices = [[[ 1, 1, 1],[ 1,-1, 1],[ 1,-1,-1],[ 1, 1,-1]],
                         [[-1,-1, 1],[-1, 1, 1],[-1, 1,-1],[-1,-1,-1]],
                         [[-1, 1,-1],[-1, 1, 1],[ 1, 1, 1],[ 1, 1,-1]],
                         [[ 1,-1,-1],[ 1,-1, 1],[-1,-1, 1],[-1,-1,-1]],
                         [[ 1, 1,-1],[ 1,-1,-1],[-1,-1,-1],[-1, 1,-1]],
                         [[-1, 1, 1],[-1,-1, 1],[ 1,-1, 1],[ 1, 1, 1]]]
        normalflip = ((1.0-int(normalflip))-0.5)*2.0
        if texture == False: #No coordinates
            self.glLibInternal_draw_faces(size,None,normalflip)
        elif texture != False: #There is texture data to be specified
            if type(texture) == type([]):
                self.glLibInternal_draw_faces(size,"2D",normalflip,texture)
            else:
                if texture == GLLIB_TEXTURE_2D: #2D placeholder
                    self.glLibInternal_draw_faces(size,"2D",normalflip)
                elif texture == GLLIB_TEXTURE_3D: #3D placeholder
                    self.glLibInternal_draw_faces(size,"3D",normalflip)
                elif texture.type == GLLIB_TEXTURE_3D: #3D texture was passed
                    glDisable(GL_TEXTURE_2D)
                    glEnable(GL_TEXTURE_3D)
                    glLibSelectTexture(texture)
                    self.glLibInternal_draw_faces(size,"3D",normalflip)
                    glDisable(GL_TEXTURE_3D)
                    glEnable(GL_TEXTURE_2D)
                elif texture.type == GLLIB_TEXTURE_CUBE: #Cube texture was passed
                    glDisable(GL_TEXTURE_2D)
                    glEnable(GL_TEXTURE_CUBE_MAP)
                    glLibSelectTexture(texture)
                    self.glLibInternal_draw_faces(size,"Cube",normalflip)
                    glDisable(GL_TEXTURE_CUBE_MAP)
                    glEnable(GL_TEXTURE_2D)
        glEndList()
    def draw(self):
        glCallList(self.box)
class glLibInternal_grid_obj:
    def __init__(self,size,order=None):
        if order != None:
            if type(size) in [type([]),type(())]: self.size = list(size)
            else:                                 self.size = [size]*order
            self.fsize = list(map(float,self.size))
    def draw(self):
        glEnableClientState(GL_VERTEX_ARRAY)
        self.vertex_vbo.bind()
        glVertexPointerf(self.vertex_vbo)
        glDrawArrays(self.type,0,self.arrsize)
        glBindBuffer(GL_ARRAY_BUFFER,0)
        glDisableClientState(GL_VERTEX_ARRAY)
    def __del__(self):
        self.vertex_vbo.delete()
class glLibGrid2D(glLibInternal_grid_obj):
    def __init__(self,size):
        glLibInternal_grid_obj.__init__(self,size,2)
        self.size_grid = self.size[0] * self.size[1]
        threedimensionalgrid = np.array(np.dstack(np.mgrid[0:self.size[0],0:self.size[1],0:1]),
                                             dtype="f")\
                                             /np.array([self.size[0]-1.0,self.size[1]-1.0,1.],dtype="f")
        twodimensionalgrid = threedimensionalgrid.reshape(self.size_grid,3)
        self.vertex_vbo = vbo.VBO(twodimensionalgrid)
        self.arrsize = len(self.vertex_vbo)
        self.type = GL_POINTS
class glLibGrid3DLines(glLibInternal_grid_obj):
    def __init__(self,size):
        glLibInternal_grid_obj.__init__(self,size)
        if type(size) in [type([]),type(())]: self.size = list(size);self.size.append(2)
        else:                                 self.size = [size,size,2]
        x_col = np.array(np.repeat(np.arange(self.size[0]),self.size[1]*self.size[2])         ,"f")
        y_col = np.array(np.tile(np.repeat(np.arange(self.size[1]),self.size[2]),self.size[0]),"f")
        z_col = np.array(np.tile(np.arange(self.size[2]),self.size[0]*self.size[1])           ,"f")
        x_col /= float(self.size[0]-1)
        y_col /= float(self.size[1]-1)
        vertex_array = np.transpose([x_col,y_col,z_col])
        self.vertex_vbo = vbo.VBO(vertex_array)
        self.arrsize = len(vertex_array)
        self.type = GL_LINES   
class glLibGrid2DMesh(glLibInternal_grid_obj):
    def __init__(self,size,loop=[False,False]):#,meshtype=GL_TRIANGLE_STRIP):
        glLibInternal_grid_obj.__init__(self,size,2)
        size = self.size
        self.loop = loop
        self.type = GL_TRIANGLE_STRIP#meshtype
        if self.type in [GL_TRIANGLE_STRIP,GL_QUAD_STRIP]:
            if self.loop[0]:
                zcol = np.zeros((size[0]+1)*(size[1]+1)*2)
                ypart = np.repeat(np.arange(size[1]+1.)/size[1], 2)
                ycol = np.array(list(ypart)*(size[0]+1))
                xbase = np.repeat(np.arange(size[0]+1) / self.fsize[0], 2*(size[1]+1))
                xadd = np.array([0., 1.]*(len(xbase)//2)) / self.fsize[0]
                xcol = xbase + xadd
                array = np.transpose([xcol, ycol, zcol])
            elif self.loop[1]: pass
            else:
                zcol = np.zeros(size[0]*(size[1]+1)*2)
                ypart = np.repeat(np.arange(size[1]+1.)/size[1], 2)
                ycol = np.array(list(ypart)*size[0])
                xbase = np.repeat(np.arange(size[0]) / self.fsize[0], 2*(size[1]+1))
                xadd = np.array([0., 1.]*(len(xbase)//2)) / self.fsize[0]
                xcol = xbase + xadd
                array = np.transpose([xcol, ycol, zcol])
            if self.type == GL_TRIANGLE_STRIP:
                #degenerate triangle addition
                step = 2*(self.size[1]+1)
                firstind = 2*(self.size[1]+1)-1
                first_insert = np.insert(array,        np.arange(firstind,   len(array       ), step  ), array.copy()[firstind  ::step], axis=0)
                array        = np.insert(first_insert, np.arange(firstind+2, len(first_insert), step+1), array.copy()[firstind+1::step], axis=0)
##            else:
##                #degenerate quadrilateral addition
##                step = 2*(self.size[1]+1)
##                firstind = 2*(self.size[1]+1)-1
##                first_insert  = np.insert(array,         np.arange(firstind,   len(array        ), step  ), array.copy()[firstind  ::step], axis=0)
##                second_insert = np.insert(first_insert,  np.arange(firstind+2, len(first_insert ), step+1), array.copy()[firstind+1::step], axis=0)
##                third_insert  = np.insert(second_insert, np.arange(firstind+4, len(second_insert), step+2), array.copy()[firstind+2::step], axis=0)
##                array         = np.insert(third_insert,  np.arange(firstind+6, len(third_insert ), step+3), array.copy()[firstind+3::step], axis=0)
##        if self.type == GL_QUADS:
##            array = []
##            for x in range(self.size[0]-1):
##                for y in range(self.size[1]-1):
##                    array.append([ x   /self.fsize[0], y   /self.fsize[1],0.0])
##                    array.append([(x+1)/self.fsize[0], y   /self.fsize[1],0.0])
##                    array.append([(x+1)/self.fsize[0],(y+1)/self.fsize[1],0.0])
##                    array.append([ x   /self.fsize[0],(y+1)/self.fsize[1],0.0])
        self.vertex_vbo = vbo.VBO(np.array(array,"f"))
        self.arrsize = len(array)
class glLibGrid3D(glLibInternal_grid_obj):
    def __init__(self,size):
        glLibInternal_grid_obj.__init__(self,size,3)
        #Rework to use grid3D?
        x_col = np.array(np.repeat(np.arange(self.size[0]),self.size[1]*self.size[2])         ,"f")/(self.size[0]-1.0)
        y_col = np.array(np.tile(np.repeat(np.arange(self.size[1]),self.size[2]),self.size[0]),"f")/(self.size[1]-1.0)
        z_col = np.array(np.tile(np.arange(self.size[2]),self.size[0]*self.size[1])           ,"f")/(self.size[2]-1.0)
        array = np.transpose([x_col,y_col,z_col])
        self.vertex_vbo = vbo.VBO(array)
        self.type = GL_POINTS
        self.arrsize = len(self.vertex_vbo)
class glLibDoubleGrid3DMesh(glLibInternal_grid_obj):
    def __init__(self,size):#,loop=[False,False]):#,meshtype=GL_TRIANGLE_STRIP):
        glLibInternal_grid_obj.__init__(self,size,3)#need to subtract 1 from size, like in 2d grid mesh?
        self.type = GL_TRIANGLE_STRIP

        x_col = np.repeat(np.repeat(np.arange(self.size[0]),self.size[1]*self.size[2]),         2)
        y_col = np.repeat(np.tile(np.repeat(np.arange(self.size[1]),self.size[2]),self.size[0]),2)
        z_col = np.repeat(np.tile(np.arange(self.size[2]),self.size[0]*self.size[1]),           2)
        vertex_array = np.transpose([x_col,y_col,z_col])
        raw_data_length = len(vertex_array) #sans degenerate triangles
        step = 2*(self.size[2])
        firstind = 2*(self.size[2])-1
        first_insert = np.insert(vertex_array, np.arange(firstind,   len(vertex_array), step  ), vertex_array.copy()[firstind  ::step], axis=0)
        vertex_array = np.insert(first_insert, np.arange(firstind+2, len(first_insert), step+1), vertex_array.copy()[firstind+1::step], axis=0)
        vertex_array = vertex_array[:-1]
        
##        vertex_attrib_array = np.tile([0,1],raw_data_length/2)
##        step = 2*(self.size[2])
##        firstind = 2*(self.size[2])
##        first_insert        = np.insert(vertex_attrib_array,np.arange(firstind,   len(vertex_attrib_array), step  ), 2, axis=0)
##        vertex_attrib_array = np.insert(first_insert,       np.arange(firstind+1, len(first_insert       ), step+1), 2, axis=0)
##        vertex_attrib_array = vertex_attrib_array.reshape((-1,1))
##        vertex_attrib_array = np.array(vertex_attrib_array,"f")
        vertex_attrib_array = np.concatenate(( np.tile([0,1],self.size[2]), np.tile([1,0],self.size[2]) ))
##        print len(vertex_attrib_array),self.size[2],raw_data_length
##        vertex_attrib_array = np.concatenate(( np.tile([0,1],self.size[2]), np.tile([1,0],raw_data_length/2-self.size[2]) ))
##        print len(vertex_attrib_array)
        tile = raw_data_length/(4.0*self.size[2])
        vertex_attrib_array = np.tile(vertex_attrib_array,floor(tile))
        if tile-float(floor(tile)) != 0.0: vertex_attrib_array = np.concatenate(( vertex_attrib_array, np.tile([0,1],self.size[2]) ))
        step = 2*(self.size[2])
        firstind = 2*(self.size[2])
##        first_insert        = np.insert(vertex_attrib_array,np.arange(firstind,   len(vertex_attrib_array), step  ), 2, axis=0)
##        vertex_attrib_array = np.insert(first_insert,       np.arange(firstind+1, len(first_insert       ), step+1), 2, axis=0)
        first_insert        = np.insert(vertex_attrib_array,np.arange(firstind,  len(vertex_attrib_array),step  ),vertex_attrib_array.copy()[firstind  ::step], axis=0)
        vertex_attrib_array = np.insert(first_insert,       np.arange(firstind+2,len(first_insert       ),step+1),vertex_attrib_array.copy()[firstind+2::step], axis=0)
        vertex_attrib_array = vertex_attrib_array.reshape((-1,1))
        vertex_attrib_array = np.array(vertex_attrib_array,"f")

##        vertex_array = np.concatenate((vertex_array,vertex_attrib_array.reshape((-1,1))),axis=1)
        vertex_array = vertex_array/np.array([self.size[0]-1.0,self.size[1]-1.0,self.size[2]-1.0])

        self.arrsize = len(vertex_array)

##        print vertex_array
##        print len(vertex_array), len(vertex_attrib_array)
##        print np.concatenate((vertex_array,vertex_attrib_array.reshape((-1,1))),axis=1)
        
        self.vertex_vbo = vbo.VBO(np.array(vertex_array,"f"))
        self.vertex_attrib_vbo = vbo.VBO(vertex_attrib_array)
        
    def draw(self,shader=None,var=None):
        if shader != None:
            try:location = glGetAttribLocation(shader.program,var)
            except:pass
        glEnableClientState(GL_VERTEX_ARRAY)
        if shader != None:
            try:glEnableVertexAttribArray(location)
            except:pass
        self.vertex_vbo.bind()
        glVertexPointerf(self.vertex_vbo)
        if shader != None:
            try:
                self.vertex_attrib_vbo.bind()
                glVertexAttribPointer(location,1,GL_FLOAT,GL_FALSE,0,None)
            except:pass
        glDrawArrays(self.type,0,self.arrsize)
        glBindBuffer(GL_ARRAY_BUFFER,0)
        if shader != None:
            try:glDisableVertexAttribArray(location)
            except:pass
        glDisableClientState(GL_VERTEX_ARRAY)
    def __del__(self):
        self.vertex_vbo.delete()
class glLibUnwrappedCubemap:
    def __init__(self,faces,size):
        correspondence = {GLLIB_LEFT:0,GLLIB_RIGHT:1,
                          GLLIB_BOTTOM:2,GLLIB_TOP:3,
                          GLLIB_BACK:4,GLLIB_FRONT:5}
        which = faces[0]
        which.reverse()
        rot = faces[1]
        rot.reverse()
        
        self.list = glGenLists(1)
        glNewList(self.list,GL_COMPILE)
        glDisable(GL_TEXTURE_2D)
        glEnable(GL_TEXTURE_CUBE_MAP)
        glBegin(GL_QUADS)
        y = 0
        for row in range(len(which)):
            x = 0
            for item_num in range(len(which[0])):
                w = which[row][item_num]
                r = rot[row][item_num]
                if w==r==None:pass
                elif w != None and r != None: self.glLibInternal_draw_face(correspondence[w],r,(x,y,size,size))
                else: raise glLibError("Error: faces do not correspond to rotations")
                x += size
            y += size
        glEnd()
        glDisable(GL_TEXTURE_CUBE_MAP)
        glEnable(GL_TEXTURE_2D)
        glEndList()
    def glLibInternal_draw_face(self,which,rot,rect):
        quad = [[[-1,-1, 1],[-1, 1, 1],[-1, 1,-1],[-1,-1,-1]],
                [[ 1, 1, 1],[ 1,-1, 1],[ 1,-1,-1],[ 1, 1,-1]],
                
                [[ 1,-1,-1],[ 1,-1, 1],[-1,-1, 1],[-1,-1,-1]],
                [[-1, 1,-1],[-1, 1, 1],[ 1, 1, 1],[ 1, 1,-1]],
                
                [[-1, 1, 1],[-1,-1, 1],[ 1,-1, 1],[ 1, 1, 1]],
                [[ 1, 1,-1],[ 1,-1,-1],[-1,-1,-1],[-1, 1,-1]]][which]
        rot = list(rot)
        rot[0] = rot[0]%4
        if   rot[0] == 0: quad = [quad[0],quad[1],quad[2],quad[3]]
        elif rot[0] == 1: quad = [quad[1],quad[2],quad[3],quad[0]]
        elif rot[0] == 2: quad = [quad[2],quad[3],quad[0],quad[1]]
        elif rot[0] == 3: quad = [quad[3],quad[0],quad[1],quad[2]]
        index = 0
        for texcoord in quad:
            glTexCoord3f(*texcoord)
            glVertex2f(*[[rect[0],        rect[1]        ],
                         [rect[0]+rect[2],rect[1]        ],
                         [rect[0]+rect[2],rect[1]+rect[3]],
                         [rect[0],        rect[1]+rect[3]]][index])
            index += 1
    def draw(self):
        glCallList(self.list)
