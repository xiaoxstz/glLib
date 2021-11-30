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
import ode

class glLibInternal_PhysMesh:
    def __init__(self,object):
        self.original_vertices = np.array(object.raw_vertices)
        self.vertices = np.array(object.raw_vertices)
        self.vertex_indices = np.array(object.indexed_vertices[0])
        
        self.world = ode.World()
        self.world.setGravity((0,-0.6,0))
        self.world.setERP(0.8)
        self.world.setCFM(1E-5)
        
        self.space = ode.Space()

        self.contactgroup = ode.JointGroup()
    def glLibInternal_near_callback(self, args, geom1, geom2):
        # Check if the objects do collide
        contacts = ode.collide(geom1, geom2)
        # Create contact joints
        world,contactgroup = args
        for c in contacts:
            c.setBounce(0.2)
            c.setMu(5000)
            j = ode.ContactJoint(world, contactgroup, c)
            j.attach(geom1.getBody(), geom2.getBody())
    def update(self,dt):
        self.space.collide((self.world,self.contactgroup),self.glLibInternal_near_callback)
        self.world.step(dt)
        self.contactgroup.empty()
class glLibCPURigidPhysMesh(glLibInternal_PhysMesh):
    def __init__(self,object):
        glLibInternal_PhysMesh.__init__(self,object)

        ode.GeomPlane(self.space,(0,1,0),0)

        triMeshData = ode.TriMeshData()
        vert_data = self.vertices
        
##        vert_data[:] = np.transpose((vert_data[:,0],vert_data[:,1],vert_data[:,2]))
##        triMeshData.build(  vert_data.tolist(),  [self.vertex_indices]  )
        triMeshData.build(self.original_vertices.tolist(),
                          np.array(self.vertex_indices).reshape((-1,3)).tolist())
        self.body = ode.Body(self.world)
        self.mass = ode.Mass()
        self.mass.setSphere(1,0.05)
        self.body.setMass(self.mass)
        self.mesh_geom = ode.GeomTriMesh(triMeshData,self.space)
        self.mesh_geom.setBody(self.body)
    def add_position(self,pos):
        self.mesh_geom.setPosition(vec_add(self.mesh_geom.getPosition(),pos))
        self.body.setPosition(vec_add(self.body.getPosition(),pos))
    def get_data(self):
        mesh_data = np.array(self.original_vertices)[self.vertex_indices]
        R = self.mesh_geom.getRotation()
        rot_mat = np.array([[R[0],R[3],R[6]],
                            [R[1],R[4],R[7]],
                            [R[2],R[5],R[8]]])
        mesh_data = np.dot(mesh_data,rot_mat)
        mesh_data += np.array(self.mesh_geom.getPosition())
        return [mesh_data.tolist()]
class glLibCPUSoftPhysMesh(glLibInternal_PhysMesh):
    def __init__(self,object):
        glLibInternal_PhysMesh.__init__(self,object)
        
        ode.GeomPlane(self.space,(0,1,0),0)

        self.vertex_bodies = []
        for vertex in self.vertices:
            body = ode.Body(self.world)
            M = ode.Mass()
            M.setSphere(1,0.05)
            body.setMass(M)
            body.setPosition(vertex)
            geom = ode.GeomBox(self.space, lengths=[0.01,0.01,0.01])
            geom.setBody(body)
            self.vertex_bodies.append(body)
        self.connections = []
        for vertex_body in self.vertex_bodies:
            vertex_body.used = False
        self.joints = []
        for vertex_body1 in self.vertex_bodies:
            for vertex_body2 in self.vertex_bodies:
                if vertex_body1 != vertex_body2 and vertex_body1.used == False:
##                    joints.append(ode.BallJoint(self.world))
                    self.joints.append(ode.FixedJoint(self.world))
                    self.joints[-1].attach(vertex_body1,vertex_body2)
                    vertex_body1.used = True
        for joint in self.joints:
            joint.setFixed()
##    def add_force(self,force):
##        self.vertex_speeds += np.array(force)
    def add_position(self,pos):
        for vertex in self.vertex_bodies:
            vertex.setPosition(vec_add(vertex.getPosition(),pos))
    def get_data(self):
        vertices = []
        for body in self.vertex_bodies:
            vertices.append(body.getPosition())
        return [np.array(vertices)[self.vertex_indices].tolist()]
def init(Screen):
    global View3D, Object, PhysObject, Plane, CameraRotation, CameraRadius, Light1, view_type
    View3D = glLibView3D((0,0,Screen[0],Screen[1]),45,0.1,20)

    Object = glLibObject("data/objects/tetrarot.obj")
##    Object = glLibObject("data/objects/tetrahedron.obj")
##    Object = glLibObject("data/objects/cube.obj")
##    Object = glLibObject("data/objects/Spaceship.obj")
##    Object = glLibObject("Fokker Dr.1.obj")
    PhysObject = glLibCPURigidPhysMesh(Object)
##    PhysObject = glLibCPUSoftPhysMesh(Object)
    PhysObject.add_position([0.0,0.6,0.0])

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
    PhysObject.update(1.0/60.0)
    
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
