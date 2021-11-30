#Tutorial by Ian Mallett

#Controls:
#ESC           - Return to menu
#LCLICK + DRAG - Rotate camera
#RCLICK + DRAG - Rotate spaceship
#SROLL WHEEL   - Zoom
#UP            - Preturb the model's base normals more
#DOWN          - Preturb the model's base normals less

#Theory:
#As you should already know, normals are perpendicular vectors
#to a surface, and are the basis for lighting in OpenGL.  Normals
#must be specified at every vertex and/or at every face.  However,
#by storing normals in a texture, normals can be specified for
#many points on a polygon.  This allows for very detailed lighting
#with no extra geometry.  The direction of the normal depends on
#the direction of the texture.  Thus, vectors along the direction
#of the U and V directions of the texture as mapped onto the object,
#called tangent and bitangent (or T and B),  must be supplied.
#This is done automatically by glLibObject(...).  Other objects may
#not look correct because the T and B vectors are not specified.

import sys,os
sys.path.append(os.path.split(sys.path[0])[0])
from glLib import *

class glLibCPUSoftPhysMesh:
    def __init__(self,object):
        self.object = object
        
        self.original_vertices = np.array(object.raw_vertices)
        self.vertices = np.array(object.raw_vertices)
        self.vertex_indices = np.array(object.indexed_vertices[0])
        
        self.vertex_speeds = np.zeros((self.vertices.shape[0],3))
        
        self.delta_pos = np.zeros((self.vertices.shape[0],3))
        
        v1s = self.original_vertices[self.vertex_indices[0::3]]
        v2s = self.original_vertices[self.vertex_indices[1::3]]
        v3s = self.original_vertices[self.vertex_indices[2::3]]
        self.target_lengths1 = np.sum((v1s-v2s)**2.0,axis=1)**0.5
        self.target_lengths2 = np.sum((v2s-v3s)**2.0,axis=1)**0.5
        self.target_lengths3 = np.sum((v3s-v1s)**2.0,axis=1)**0.5

        self.dampening = 0.999
    def add_force(self,force):
        self.vertex_speeds += np.array(force)
    def add_position(self,pos):
        self.delta_pos += np.array(pos)
    def move(self):
        #Length tensors
        v1s = self.vertices[self.vertex_indices[0::3]]
        v2s = self.vertices[self.vertex_indices[1::3]]
        v3s = self.vertices[self.vertex_indices[2::3]]
        side1 = v2s - v1s
        side2 = v3s - v2s
        side3 = v1s - v3s
        delta_side1 = np.transpose( ((np.sum(side1**2.0,axis=1)**0.5)-self.target_lengths1,)*3 ) * side1
        delta_side2 = np.transpose( ((np.sum(side2**2.0,axis=1)**0.5)-self.target_lengths2,)*3 ) * side2
        delta_side3 = np.transpose( ((np.sum(side3**2.0,axis=1)**0.5)-self.target_lengths3,)*3 ) * side3
        tensor = 0.01
        self.vertex_speeds[self.vertex_indices[0::3]] += tensor*delta_side1
        self.vertex_speeds[self.vertex_indices[1::3]] -= tensor*delta_side1
        self.vertex_speeds[self.vertex_indices[1::3]] += tensor*delta_side2
        self.vertex_speeds[self.vertex_indices[2::3]] -= tensor*delta_side2
        self.vertex_speeds[self.vertex_indices[2::3]] += tensor*delta_side3
        self.vertex_speeds[self.vertex_indices[0::3]] -= tensor*delta_side3
        
        self.delta_pos += self.vertex_speeds
        self.vertex_speeds *= self.dampening
        self.vertices += self.delta_pos
        self.delta_pos.fill(0.0)
    def collision_detect(self):
        indices = np.where(self.vertices[:,1]<0.0001)
        self.vertices[indices,1] = 0.0001
        self.vertex_speeds[indices] *= -0.1
    def get_data(self):
        return [self.vertices[self.vertex_indices].tolist()]
def init(Screen):
    global View3D, Object, PhysObject, Plane, CameraRotation, CameraRadius, Light1, view_type
    View3D = glLibView3D((0,0,Screen[0],Screen[1]),45,0.1,20)

##    Object = glLibObject("data/objects/tetrarot.obj")
##    Object = glLibObject("data/objects/tetrahedron.obj")
    Object = glLibObject("data/objects/cube.obj")
##    Object = glLibObject("data/objects/Spaceship.obj")
##    Object = glLibObject("Fokker Dr.1.obj")
    PhysObject = glLibCPUSoftPhysMesh(Object)
    PhysObject.add_position([0.0,0.3,0.0])

    FloorTexture = glLibTexture2D("data/floor.jpg",[0,0,512,512],GLLIB_RGBA,GLLIB_FILTER,GLLIB_MIPMAP_BLEND)
    try:FloorTexture.anisotropy(GLLIB_MAX)
    except:pass

    Plane = glLibPlane(5,(0,1,0),FloorTexture,10)

    #Add variables for the camera's rotation and radius
    CameraRotation = [90,23]
    CameraRadius = 5.0

    glEnable(GL_LIGHTING)
    Light1 = glLibLight(1)
    Light1.set_pos([0,10,0])
    Light1.set_type(GLLIB_POINT_LIGHT)
    Light1.enable()

    view_type = 1

    pygame.mouse.get_rel()

def quit():
    global Light1, Object
    glDisable(GL_LIGHTING)
    del Light1
    del Object

def GetInput():
    global CameraRadius, view_type
    mrel = pygame.mouse.get_rel()
    mpress = pygame.mouse.get_pressed()
    key = pygame.key.get_pressed()
    for event in pygame.event.get():
        if   event.type == QUIT: quit(); pygame.quit(); sys.exit()
        elif event.type == KEYDOWN:
            if   event.key == K_ESCAPE: return False
            elif event.key == K_v: view_type = 3 - view_type
        elif event.type == MOUSEBUTTONDOWN:
            if   event.button == 5: CameraRadius += .2
            elif event.button == 4: CameraRadius -= .2
    #If the left mouse button is clicked,
    #rotate the camera.  
    if mpress[0]:
        CameraRotation[0] += mrel[0]
        CameraRotation[1] += mrel[1]
def Draw(Window):
    Window.clear()
    View3D.set_view()
    #Calculate the camera's position using CameraRotation.
    #Basically just spherical coordinates.
    camerapos = [0.0 + CameraRadius*cos(radians(CameraRotation[0]))*cos(radians(CameraRotation[1])),
                 0.5 + CameraRadius                                *sin(radians(CameraRotation[1])),
                 0.0 + CameraRadius*sin(radians(CameraRotation[0]))*cos(radians(CameraRotation[1]))]
    gluLookAt(camerapos[0],camerapos[1],camerapos[2], 0,0.5,0, 0,1,0)
    Light1.set()

    #Draw the floor
    Plane.draw()

    #Update the physics object.  Normally this wouldn't happen in the draw code
    #but it's harmless to do it here
    for x in xrange(1):
        PhysObject.add_force([0.0,-0.000001,0.0000001])
        PhysObject.move()
    PhysObject.collision_detect()
    
    #Use the physics object's data
    Object.use_data(PhysObject.get_data()) #doesn't work with shadow volumes
    #Draw the object
    glDisable(GL_LIGHTING)
    #   Draw as lines
    glLineWidth(4)
    glColor3f(0,0,0)
    glPolygonMode(GL_FRONT_AND_BACK,GL_LINE)
    Object.draw_direct()
    glPolygonMode(GL_FRONT_AND_BACK,GL_FILL)
    glColor3f(1,1,1)
    #   Draw polygons
    glLineWidth(1)
    glDepthMask(False)
    glLibAlpha(0.1)
    Object.draw_direct()
    glLibAlpha(1.0)
    glDepthMask(True)
    glEnable(GL_LIGHTING)

    Window.flip()
