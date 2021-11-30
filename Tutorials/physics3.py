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

class glLibInternal_PhysMesh:
    def __init__(self,object):
        self.vertices = np.array(object.raw_vertices)
        self.extremes = np.array(object.get_extremes())
        self.vertex_indices = np.array(object.indexed_vertices[0])
class glLibCPUSoftPhysMesh(glLibInternal_PhysMesh):
    def __init__(self,object,gridres):
        glLibInternal_PhysMesh.__init__(self,object)
        self.gridres = list(gridres)
        self.grid = grid3D(self.gridres)
        self.grid_positions = (grid3D(self.gridres)\
                              /np.array([self.gridres[0]-1.0,self.gridres[1]-1.0,self.gridres[2]-1.0]))\
                              .reshape((self.gridres[0],self.gridres[1],self.gridres[2],3))
        self.grid_positions = (self.grid_positions*(self.extremes[:,1]-self.extremes[:,0]))+self.extremes[:,0]
        self.target_grid_lengths = ((self.extremes[:,1]-self.extremes[:,0])/(np.array(self.gridres)-1.0)).tolist()
##        self.grid_positions += np.random.normal(0.0,0.1,(gridres[0],gridres[1],gridres[2],3))
        self.grid_speeds = np.zeros((gridres[0],gridres[1],gridres[2],3))

        self.datatype = "f"
        self.grid_positions = self.grid_positions.astype(self.datatype)
        self.grid_positions *= 0.5
        self.grid_speeds = self.grid_speeds.astype(self.datatype)
    def add_force(self,force):
        self.grid_speeds[:,:,:] += np.array(force,self.datatype)
    def update(self):
        convergence = 0.1
        index = 0
        directions = [  [-1, 0, 0],  [ 1, 0, 0],  [ 0,-1, 0],  [ 0, 1, 0],  [ 0, 0,-1],  [ 0, 0, 1],
                        [-1,-1,-1],  [ 1,-1,-1],  [-1,-1, 1],  [ 1,-1, 1],  [-1, 1,-1],  [ 1, 1,-1],  [-1, 1, 1],  [ 1, 1, 1]]
##        directions = [[-1,0,0],[1,0,0],[0,0,-1],[0,0,1],[-1,0,-1],[1,0,-1],[-1,0,1],[1,0,1]]
        for direction in directions:
            target_length = length([direction[0]*self.target_grid_lengths[0],
                                    direction[1]*self.target_grid_lengths[1],
                                    direction[2]*self.target_grid_lengths[2]])
            adjacent_point_grid_indexes = [clamp(  [0+direction[0],self.gridres[0]+direction[0]],  0,  self.gridres[0]  ),
                                           clamp(  [0+direction[1],self.gridres[1]+direction[1]],  0,  self.gridres[1]  ),
                                           clamp(  [0+direction[2],self.gridres[2]+direction[2]],  0,  self.gridres[2]  )]
            grid_indices = [  [adjacent_point_grid_indexes[0][0]-direction[0],adjacent_point_grid_indexes[0][1]-direction[0]],
                              [adjacent_point_grid_indexes[1][0]-direction[1],adjacent_point_grid_indexes[1][1]-direction[1]],
                              [adjacent_point_grid_indexes[2][0]-direction[2],adjacent_point_grid_indexes[2][1]-direction[2]]  ]
##            if index == 0: print direction," ",adjacent_point_grid_indexes," ",grid_indices," ",self.grid_positions.shape
            delta_vec = self.grid_positions[grid_indices[0][0]:grid_indices[0][1],
                                            grid_indices[1][0]:grid_indices[1][1],
                                            grid_indices[2][0]:grid_indices[2][1]] - \
                        self.grid_positions[adjacent_point_grid_indexes[0][0]:adjacent_point_grid_indexes[0][1],
                                            adjacent_point_grid_indexes[1][0]:adjacent_point_grid_indexes[1][1],
                                            adjacent_point_grid_indexes[2][0]:adjacent_point_grid_indexes[2][1]]
            length_of_delta_vectors = np.sum(delta_vec**2.0,axis=3)**0.5
##            if direction == [0,1,0]: print length_of_delta_vectors
            delta_length = length_of_delta_vectors - target_length
##            print delta_length.shape
            delta_length = np.tile(delta_length.reshape((delta_length.shape[0],delta_length.shape[1],delta_length.shape[2],1)),3)
##            print delta_length.shape
##            print
##            print self.grid_positions
            self.grid_positions[grid_indices[0][0]:grid_indices[0][1],
                                grid_indices[1][0]:grid_indices[1][1],
                                grid_indices[2][0]:grid_indices[2][1]] -= delta_vec*delta_length*convergence
            index += 1
##        #Move nodes surrounded on all sides
##        target_pos = np.zeros((self.gridres[0]-2,self.gridres[1]-2,self.gridres[2]-2,3))
##        #[1:self.gridres[0]-1,1:self.gridres[1]-1,1:self.gridres[2]-1]
##        target_pos += self.grid_positions[0:self.gridres[0]-2,1:self.gridres[1]-1,1:self.gridres[2]-1]
##        target_pos += self.grid_positions[2:self.gridres[0]+0,1:self.gridres[1]-1,1:self.gridres[2]-1]
##        target_pos += self.grid_positions[1:self.gridres[0]-1,0:self.gridres[1]-2,1:self.gridres[2]-1]
##        target_pos += self.grid_positions[1:self.gridres[0]-1,2:self.gridres[1]+0,1:self.gridres[2]-1]
##        target_pos += self.grid_positions[1:self.gridres[0]-1,1:self.gridres[1]-1,0:self.gridres[2]-2]
##        target_pos += self.grid_positions[1:self.gridres[0]-1,1:self.gridres[1]-1,2:self.gridres[2]+0]
##        target_pos *= 1.0 / 6.0
##        delta = self.grid_positions[1:-1,1:-1,1:-1] - target_pos
##        self.grid_positions[1:-1,1:-1,1:-1] -= delta*convergence
##        #Move left/right face nodes (not including edges/corners)
##        for x_ind in [0,-1]:
##            target_pos = np.zeros((1,self.gridres[1]-2,self.gridres[2]-2,3))
##            target_pos += self.grid_positions[x_ind::self.gridres[0],0:self.gridres[1]-2,1:self.gridres[2]-1]
##            target_pos += self.grid_positions[x_ind::self.gridres[0],2:self.gridres[1]+0,1:self.gridres[2]-1]
##            target_pos += self.grid_positions[x_ind::self.gridres[0],1:self.gridres[1]-1,0:self.gridres[2]-2]
##            target_pos += self.grid_positions[x_ind::self.gridres[0],1:self.gridres[1]-1,2:self.gridres[2]+0]
##            target_pos *= 1.0 / 4.0
##            delta = self.grid_positions[x_ind::self.gridres[0],1:-1,1:-1] - target_pos
##            self.grid_positions[x_ind::self.gridres[0],1:-1,1:-1] -= delta*convergence
##        #Move up/down face nodes (not including edges/corners)
##        for y_ind in [0,-1]:
##            target_pos = np.zeros((self.gridres[0]-2,1,self.gridres[2]-2,3))
##            target_pos += self.grid_positions[0:self.gridres[0]-2,y_ind::self.gridres[1],1:self.gridres[2]-1]
##            target_pos += self.grid_positions[2:self.gridres[0]+0,y_ind::self.gridres[1],1:self.gridres[2]-1]
##            target_pos += self.grid_positions[1:self.gridres[0]-1,y_ind::self.gridres[1],0:self.gridres[2]-2]
##            target_pos += self.grid_positions[1:self.gridres[0]-1,y_ind::self.gridres[1],2:self.gridres[2]+0]
##            target_pos *= 1.0 / 4.0
##            delta = self.grid_positions[1:-1,y_ind::self.gridres[1],1:-1] - target_pos
##            self.grid_positions[1:-1,y_ind::self.gridres[1],1:-1] -= delta*convergence
##        #Move front/back face nodes (not including edges/corners)
##        for z_ind in [0,-1]:
##            target_pos = np.zeros((self.gridres[0]-2,self.gridres[1]-2,1,3))
##            target_pos += self.grid_positions[0:self.gridres[0]-2,1:self.gridres[1]-1,z_ind::self.gridres[2]]
##            target_pos += self.grid_positions[2:self.gridres[0]+0,1:self.gridres[1]-1,z_ind::self.gridres[2]]
##            target_pos += self.grid_positions[1:self.gridres[0]-1,0:self.gridres[1]-2,z_ind::self.gridres[2]]
##            target_pos += self.grid_positions[1:self.gridres[0]-1,2:self.gridres[1]+0,z_ind::self.gridres[2]]
##            target_pos *= 1.0 / 4.0
##            delta = self.grid_positions[1:-1,1:-1,z_ind::self.gridres[2]] - target_pos
##            self.grid_positions[1:-1,1:-1,z_ind::self.gridres[2]] -= delta*convergence
        #Move grid positions according to speed
        self.grid_positions += self.grid_speeds
    def collision_detect(self):
        self.grid_positions = self.grid_positions.reshape((-1,3))
        self.grid_speeds = self.grid_speeds.reshape((-1,3))
        indices = np.where(self.grid_positions[:,1]<0.0)[0]
        self.grid_positions[indices,:,1] = 0.0
        self.grid_speeds[indices] *= -1.0
        self.grid_positions = self.grid_positions.reshape((self.gridres[0],self.gridres[1],self.gridres[2],3))
        self.grid_speeds = self.grid_speeds.reshape((self.gridres[0],self.gridres[1],self.gridres[2],3))
    def add_position(self,pos):
        self.grid_positions[:,:,:] += np.array(pos)
    def draw_grid(self):
        glEnableClientState(GL_VERTEX_ARRAY)
        data = self.grid_positions.reshape((-1,3))
        glVertexPointer(  3,  GL_FLOAT,  0,  data  )
        glDrawArrays(GL_POINTS,0,len(data))
        glDisableClientState(GL_VERTEX_ARRAY)
    def get_data(self):
        raw_voxel_pos = np.transpose([(self.vertices[:,0]-self.extremes[0][0])/float(self.extremes[0][1]-self.extremes[0][0]),
                                      (self.vertices[:,1]-self.extremes[1][0])/float(self.extremes[1][1]-self.extremes[1][0]),
                                      (self.vertices[:,2]-self.extremes[2][0])/float(self.extremes[2][1]-self.extremes[2][0])])\
                                    .reshape((-1,3))\
                                    *np.array([self.gridres[0]-1.0,self.gridres[1]-1.0,self.gridres[2]-1.0])
        lower_voxel_indices = np.floor(raw_voxel_pos).astype("int")
        upper_voxel_indices = np.ceil(raw_voxel_pos).astype("int")
        voxel_part = raw_voxel_pos - lower_voxel_indices
        vertex_positions = self.grid_positions[upper_voxel_indices[:,0],upper_voxel_indices[:,1],upper_voxel_indices[:,2]]*voxel_part + \
                           self.grid_positions[lower_voxel_indices[:,0],lower_voxel_indices[:,1],lower_voxel_indices[:,2]]*(1.0-voxel_part)
        return [vertex_positions[self.vertex_indices].tolist()]
#=======================================================================================
#=======================================================================================
#=======================================================================================
#=======================================================================================
#=======================================================================================
class glLibGPUSoftPhysMesh(glLibInternal_PhysMesh):
    def __init__(self,object,bounding_box_size,data_scalar,gridres,rectres):
        glLibInternal_PhysMesh.__init__(self,object)
        self.gridres = gridres
        self.rectres = list(rectres)
        self.target_grid_lengths = (  (1.0/(np.array(self.gridres)-1.0))  *  data_scalar).tolist()
        #(  ((self.extremes[:,1]-self.extremes[:,0])/(np.array(self.gridres)-1.0))  *  data_scalar).tolist()
        #Mesh Parameters
        self.dampening = 0.98
        self.steps = 1
        self.time_step = 1.0
        self.numerical_data = None
        self.add_pos_to = [0.0,0.0,0.0] #trans added to object at next frame.
        self.scalar = bounding_box_size
        self.gravity = [0.0,0.0,0.0]
        self.bounce = 1.0
        #Misc.
        self.view_2d = glLibView2D((0,0,self.rectres[0],self.rectres[1]))
        #Geometry
        self.particles = glLibGrid2D(self.rectres)
        #Textures
        pos_data = (grid3D(self.gridres)\
                    /np.array([self.gridres[0]-1.0,self.gridres[1]-1.0,self.gridres[2]-1.0]))\
                   .reshape((self.gridres[0],self.gridres[1],self.gridres[2],3))
        tempx = pos_data[:,:,:,0]; tempy = pos_data[:,:,:,1]; tempz = pos_data[:,:,:,2]
        pos_data2 = np.transpose([tempx,tempy,tempz,np.ones(tempx.shape)])
        pos_data3 = np.zeros((self.rectres[0],self.rectres[1],4))
        for y in xrange(self.gridres[1]):
            z,x = y%rndint(self.gridres[0]**0.5),y/rndint(self.gridres[2]**0.5) #doesn't work for non-cubic things
            pos_data3[x*self.gridres[0]:(x+1)*self.gridres[0],
                      z*self.gridres[2]:(z+1)*self.gridres[2]] = pos_data2[:,y,:]
        pos_data3 -= 0.5
        pos_data3 *= data_scalar
        pos_data3 += 0.5
        self.original_numerical_data = pos_data3
        vel_data = np.zeros((self.original_numerical_data.shape[0],\
                             self.original_numerical_data.shape[1],\
                             3)).astype(self.original_numerical_data.dtype)
        vel_data.fill(0.5)
        self.pos_restrained_tex = glLibTexture2D(pos_data3,(0,0,self.rectres[0],self.rectres[1]),GL_RGBA,precision=32)
        self.velocity_tex       = glLibTexture2D(vel_data, (0,0,self.rectres[0],self.rectres[1]),GL_RGB, precision=32)
        #FBOs
        self.update_framebuffer = glLibFBO(self.rectres)
        self.update_framebuffer.add_render_target(1,precision=32,type=GLLIB_RGBA)
        self.update_framebuffer.add_render_target(2,precision=32,type=GLLIB_RGB )
        self.collision_framebuffer = glLibFBO(self.rectres)
        self.collision_framebuffer.add_render_target(1,precision=32,type=GLLIB_RGBA)
        self.collision_framebuffer.add_render_target(2,precision=32,type=GLLIB_RGB )
        self.add_force_framebuffer1 = glLibFBO(self.rectres)
        self.add_force_framebuffer1.add_render_target(1,precision=32,type=GLLIB_RGB)
        self.add_force_framebuffer2 = glLibFBO(self.rectres)
        self.add_force_framebuffer2.add_render_target(1,precision=32,type=GLLIB_RGB)
        self.flipflop = 1
        #Shaders
        print "Update Shader:"
        self.update_shader = glLibShader()
        self.update_shader.use_prebuilt(GLLIB_SOFTPHYS_UPDATE)
        print "Collide Shader:"
        self.collision_shader = glLibShader()
        self.collision_shader.use_prebuilt(GLLIB_SOFTPHYS_COLLIDE)
        print "Add Force Shader:"
        self.add_force_shader = glLibShader()
        self.add_force_shader.use_prebuilt(GLLIB_SOFTPHYS_ADDFORCE)
    def update(self):
        self.glLibInternal_push()
        for step in xrange(self.steps):
            self.update_framebuffer.enable(GLLIB_ALL)
            self.glLibInternal_set_2D_view()
            glLibUseShader(self.update_shader)
            self.update_shader.pass_vec2("size",self.rectres)
            self.update_shader.pass_vec3("level_size",map(lambda x:(self.gridres[0]**0.5)/x,self.gridres))
            self.update_shader.pass_vec3("trans",sc_vec(2.0,self.add_pos_to))
            self.add_pos_to = [0.0,0.0,0.0]
            self.update_shader.pass_vec3("new_forces",sc_vec(2.0,self.gravity))
            self.update_shader.pass_vec3("target_lengths",map(lambda x:2.0*x,self.target_grid_lengths))
            self.update_shader.pass_texture(self.pos_restrained_tex,1)
            self.update_shader.pass_texture(self.velocity_tex,2)
            self.particles.draw()
            self.update_framebuffer.disable()
            
            self.pos_restrained_tex = self.update_framebuffer.get_texture(1)
            self.velocity_tex = self.update_framebuffer.get_texture(2)
            
            self.collision_framebuffer.enable(GLLIB_ALL)
            self.glLibInternal_set_2D_view()
            glLibUseShader(self.collision_shader)
            self.collision_shader.pass_vec2("size",self.rectres)
            self.collision_shader.pass_float("bounce",-self.bounce)
            self.collision_shader.pass_texture(self.pos_restrained_tex,1)
            self.collision_shader.pass_texture(self.velocity_tex,2)
            self.particles.draw()
            self.collision_framebuffer.disable()

            self.pos_restrained_tex = self.collision_framebuffer.get_texture(1)
            self.velocity_tex = self.collision_framebuffer.get_texture(2)
        glLibUseShader(None)
        self.glLibInternal_pop()
        self.forces = [0.0,0.0,0.0]
    def add_position(self,position):
        self.add_pos_to = vec_add(self.add_pos_to,position)
    def add_force(self,point,force):
        if self.flipflop == 1: self.add_force_framebuffer1.enable(GLLIB_ALL)
        else:                  self.add_force_framebuffer2.enable(GLLIB_ALL)
        self.glLibInternal_set_2D_view()
        
        glLibUseShader(None)
        glLibSelectTexture(self.velocity_tex)
        glLibTexFullScreenQuad()
        
        glLibUseShader(self.add_force_shader)
        self.add_force_shader.pass_vec3("force",force)
        pixel = [point[0]-1,point[2]-1]
        pixel[0] += self.gridres[0]*(point[1]-1)
        while pixel[0] > self.rectres[0]:
            pixel[0] -= self.rectres[0]
            pixel[1] += self.gridres[2]
        glBegin(GL_POINTS)
        glVertex3f(pixel[0],pixel[1],0.1)
        glEnd()
        glLibUseShader(None)
        
        if self.flipflop == 1:
            self.add_force_framebuffer1.disable()
            self.velocity_tex = self.add_force_framebuffer1.get_texture(1)
        else:
            self.add_force_framebuffer2.disable()
            self.velocity_tex = self.add_force_framebuffer2.get_texture(1)
        self.flipflop = 3 - self.flipflop
    def set_gravity(self,gravity):
        self.gravity = list(gravity)
    def set_bounce(self,bounce):
        self.bounce = float(bounce)
    def set_steps(self,steps):
        self.steps = steps
    def glLibInternal_set_2D_view(self):
        glClear(GL_COLOR_BUFFER_BIT|GL_DEPTH_BUFFER_BIT)
        glLoadIdentity()
        self.view_2d.set_view()
    def glLibInternal_push(self):
        glLibPushView()
        glDisable(GL_BLEND)
    def glLibInternal_pop(self):
        glEnable(GL_BLEND)
        glLibPopView()
    def get_data(self):
        self.numerical_data = (self.pos_restrained_tex.get_texture_data()-0.5)*2.0*self.scalar
        return self.numerical_data
    def draw_data(self):
        glLibUseShader(None)
        glDisable(GL_LIGHTING)
        glLibPushView()
        self.view_2d.set_view()
        glDisable(GL_BLEND)
        glLibSelectTexture(self.pos_restrained_tex)
        glLibTexFullScreenQuad()
        glEnable(GL_BLEND)
        glLibPopView()
        glEnable(GL_LIGHTING)
    def draw_grid(self):
        glLibUseShader(None)
        glDisable(GL_LIGHTING)
        glEnableClientState(GL_VERTEX_ARRAY)
        if self.numerical_data == None:
            raise glLibError.glLibError("Numerical data is not available!  Be sure to call .get_data() first.")
        else:
            data = self.numerical_data.reshape((-1,4))
            glVertexPointer(  3,  GL_FLOAT,  0,  data[:,0:3]  )
            glDrawArrays(GL_POINTS,0,len(data))
            glDisableClientState(GL_VERTEX_ARRAY)
        glEnable(GL_LIGHTING)
    def __del__(self):
        try: self.particles.__del__()
        except:pass
def init(Screen):
    global View3D, Object, PhysObject, Plane, BoundingBox, CameraRotation, CameraRadius, Light1, view_type
    View3D = glLibView3D((0,0,Screen[0],Screen[1]),45,0.1,200)

##    Object = glLibObject("data/objects/tetrarot.obj")
##    Object = glLibObject("data/objects/icosahedron.obj")
##    Object = glLibObject("data/objects/tetrahedron.obj")
##    Object = glLibObject("data/objects/cube.obj")
    Object = glLibObject("data/objects/Spaceship.obj")
##    Object = glLibObject("Fokker Dr.1.obj")
    
    scalar = 1.0
    data_size = 1.0/4.0
##    PhysObject = glLibGPUSoftPhysMesh(Object,scalar,data_size,[1]*3,[1]*2)
##    PhysObject = glLibGPUSoftPhysMesh(Object,scalar,data_size,[4]*3,[8]*2)
    PhysObject = glLibGPUSoftPhysMesh(Object,scalar,data_size,[9]*3,[27]*2)
##    PhysObject = glLibGPUSoftPhysMesh(Object,scalar,data_size,[16]*3,[64]*2)
##    PhysObject = glLibGPUSoftPhysMesh(Object,scalar,data_size,[25]*3,[125]*2)
##    PhysObject = glLibGPUSoftPhysMesh(Object,scalar,data_size,[36]*3,[216]*2)
##    PhysObject = glLibGPUSoftPhysMesh(Object,scalar,data_size,[49]*3,[343]*2)
##    PhysObject = glLibGPUSoftPhysMesh(Object,scalar,data_size,[64]*3,[512]*2)
##    PhysObject.add_position([0.75,0.5,0.0])
    PhysObject.add_position([0.0,0.25,0.0])
    PhysObject.set_bounce(0.9)
    PhysObject.set_steps(10)
##    PhysObject.set_gravity([-0.00001,0.00001,-0.00001])
##    PhysObject.set_gravity([0.000001,0.0,0.0])
##    PhysObject.set_gravity([0.0,0.00001,0.0])
##    PhysObject.set_gravity([0.0,-0.00001,0.0])

    FloorTexture = glLibTexture2D("data/floor.jpg",[0,0,512,512],GLLIB_RGBA,GLLIB_FILTER,GLLIB_MIPMAP_BLEND)
    try:FloorTexture.anisotropy(GLLIB_MAX)
    except:pass

    BoundingBox = glLibRectangularSolid([1]*3)

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
    if key[K_UP]:
        PhysObject.add_force([1,1,1],[0.0,0.0,0.0001])
def Draw(Window):
    glClearColor(0.2,0.2,0.2,0.0)
    Window.clear()
    glClearColor(0.0,0.0,0.0,0.0)
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
    PhysObject.update()
    
    #Use the physics object's data
    Object.use_data(PhysObject.get_data()) #doesn't work with shadow volumes

    #   Draw PhysObject grid
    glPointSize(2)
    glDisable(GL_TEXTURE_2D)
    PhysObject.draw_grid()
    glEnable(GL_TEXTURE_2D)
    glPointSize(1)

    #   Draw Bounding Box
    glColor3f(0,0,0)
    glDisable(GL_LIGHTING)
    glPolygonMode(GL_FRONT_AND_BACK,GL_LINE)
    glDisable(GL_TEXTURE_2D)
    BoundingBox.draw()
    glEnable(GL_TEXTURE_2D)
    glPolygonMode(GL_FRONT_AND_BACK,GL_FILL)
    glEnable(GL_LIGHTING)
    glColor3f(1,1,1)

    #   Draw data textures
##    PhysObject.draw_data()
    
    #Draw the object
    glDisable(GL_LIGHTING)
    glDisable(GL_TEXTURE_2D)
    #   Draw as lines
    glLineWidth(2)
    glColor3f(0,0,0)
    glPolygonMode(GL_FRONT_AND_BACK,GL_LINE)
##    Object.draw_arrays()
    glPolygonMode(GL_FRONT_AND_BACK,GL_FILL)
    glColor3f(1,1,1)
    glLineWidth(1)
    #   Draw polygons
    glDepthMask(False)
    glLibAlpha(0.3)
##    Object.draw_arrays()
    glLibAlpha(1.0)
    glDepthMask(True)
    #   Finish drawing object
    glEnable(GL_LIGHTING)
    glEnable(GL_TEXTURE_2D)

    glDisable(GL_LIGHTING)
    PhysObject.add_force([1,1,1],[0.0,0.0,-0.0001])
    glEnable(GL_LIGHTING)

    Window.flip()
