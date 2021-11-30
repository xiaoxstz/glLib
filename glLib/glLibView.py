from glLibLocals import *
from glLibMath import *
class glLibInternal_glLibView():
    def __init__(self,rect):
        self.rect = list(rect)
        self.x = rect[0]
        self.y = rect[1]
        self.width = rect[2]
        self.height = rect[3]
        self.size = [rect[2],rect[3]]
        self.aspect_ratio = float(self.width)/float(self.height)
    def set_view(self):
        glViewport(*self.rect)
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        self.glLibInternal_set_proj()
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
        glScissor(*self.rect)
    def get_projection_matrix(self):
        glMatrixMode(GL_PROJECTION)
        glPushMatrix()
        glLoadIdentity()
        self.glLibInternal_set_proj()
        mat = glGetFloatv(GL_PROJECTION_MATRIX)
        glPopMatrix()
        glMatrixMode(GL_MODELVIEW)
        return mat
def glLibGetFrustumPoints(view,pos,center,up):
    #http://www.lighthouse3d.com/opengl/viewfrustum/index.php?gaplanes
    vec = vec_subt(center,pos)
    nvec = normalize(vec)
    right = normalize(cross(vec,up))
    up = normalize(cross(right,nvec))

    a = 2.0 * tan(radians(view.angle/2.0))
    Hnear = a * view.near
    Wnear = Hnear * view.aspect_ratio
    Hfar  = a * view.far
    Wfar  = Hfar * view.aspect_ratio

    nc = vec_add(pos,sc_vec(view.near,nvec))
    a = sc_vec(Hnear/2.0,up)
    b = sc_vec(Wnear/2.0,right)
    ntl = vec_subt(vec_add (nc,a),b)
    ntr = vec_add (vec_add (nc,a),b)
    nbl = vec_subt(vec_subt(nc,a),b)
    nbr = vec_add (vec_subt(nc,a),b)
    
    fc = vec_add(pos,sc_vec(view.far,nvec))
    a = sc_vec(Hfar/2.0,up)
    b = sc_vec(Wfar/2.0,right)
    ftl = vec_subt(vec_add (fc,a),b)
    ftr = vec_add (vec_add (fc,a),b)
    fbl = vec_subt(vec_subt(fc,a),b)
    fbr = vec_add (vec_subt(fc,a),b)

    return [[nbl,nbr,ntr,ntl],[fbl,fbr,ftr,ftl]]
	
class glLibView2D(glLibInternal_glLibView):
    def __init__(self,rect):
        glLibInternal_glLibView.__init__(self,rect)
        self.near = -1.0
        self.far = 1.0
    def glLibInternal_set_proj(self):
##        gluOrtho2D(self.rect[0],self.rect[0]+self.rect[2],self.rect[1],self.rect[1]+self.rect[3])
        gluOrtho2D(0,0+self.rect[2],0,0+self.rect[3])
class glLibViewISO(glLibInternal_glLibView):
    def __init__(self,rect,near=0.1,far=1000.0):
        glLibInternal_glLibView.__init__(self,rect)
        self.near = near
        self.far = far
        self.zoom = 1.0
    def set_near(self,value):
        self.near = value
    def set_far(self,value):
        self.far = value
    def set_zoom(self,value):
        self.zoom = value
    def glLibInternal_set_proj(self):
        angle = atan(1.0/self.aspect_ratio)
        x = cos(angle)
        y = sin(angle)
        glOrtho(-x/self.zoom,x/self.zoom,-y/self.zoom,y/self.zoom,\
                self.near,self.far)
class glLibView3D(glLibInternal_glLibView):
    def __init__(self,rect,angle,near=0.1,far=1000.0):
        glLibInternal_glLibView.__init__(self,rect)
        self.angle = angle
        self.near = near
        self.far = far
    def set_angle(self,angle):
        self.angle = angle
    def set_near(self,value):
        self.near = value
    def set_far(self,value):
        self.far = value
    def glLibInternal_set_proj(self):
        gluPerspective(self.angle,self.aspect_ratio,self.near,self.far)
