#Tutorial by Ian Mallett

#Controls:
#ESC           - Return to menu
#n             - Toggles using/not using normalmap
#r             - Cycle among reflection, refraction, both
#LCLICK + DRAG - Rotate camera
#RCLICK + DRAG - Rotate spaceship
#SROLL WHEEL   - Zoom

#Theory:
#Reflections and refractions are really neat, but difficult to
#Shadowmaps are all very well and good, but they don't work in
#all directions.  A solution is to render the depth in each of
#the six cardinal directions to six depthmaps, and use these
#for tests.  Simple and effective.  

import sys,os
sys.path.append(os.path.split(sys.path[0])[0])
from glLib import *

def init(Screen):
    global InsetView2D, View3D, CubemapView
    global Objects, Plane, BoundingCube, UnwrappedMap, Cubemap
    global ObjectRotation, CameraRotation, CameraRadius
    global Light1
    global Shader
    cubemapsize = 512
    InsetView2D = glLibView2D((0,0,256,192))
    View3D = glLibView3D((0,0,Screen[0],Screen[1]),45,0.1,200)
    #Cubemap view.  Angle must be 90 degrees.
    CubemapView = glLibView3D((0,0,cubemapsize,cubemapsize),90,1.5,10.0)

    Objects = []
    for path in ["Spaceship.obj","trisphere.obj","cube.obj","icosahedron.obj","disco.obj","tetrahedron.obj"]:
        object = glLibObject("data/objects/"+path,GLLIB_FILTER,GLLIB_MIPMAP_BLEND)
##        object.set_material([[-1,-1,-1,1.0],0,-1]) #give the object a soft shininess, leave the other material parameters alone.
        object.build_list([1])
        Objects.append(object)

    box_tex = glLibTexture2D("data/floor.jpg",GLLIB_ALL,GLLIB_RGB,GLLIB_FILTER,GLLIB_MIPMAP_BLEND)
    if GLLIB_ANISOTROPY_AVAILABLE: box_tex.anisotropy(GLLIB_MAX)
    BoundingCube = glLibRectangularSolid([5.0,5.0,5.0],texture=[box_tex]*6,normalflip=True)

    Cubemap = glLibTextureCube([None]*6,(0,0,cubemapsize,cubemapsize),GLLIB_DEPTH)
    Cubemap.edge(GLLIB_CLAMP)

    #For the unwrapped version of the cubemap
    faces = [[[       None,    GLLIB_TOP,        None,       None],
              [GLLIB_RIGHT,  GLLIB_FRONT,  GLLIB_LEFT, GLLIB_BACK],
              [       None, GLLIB_BOTTOM,        None,       None]],
             [[            None, [-1,False,False],             None,            None],
              [[ 1,False,False], [ 1,False,False], [-1,False,False], [ 1,False,False]],
              [            None, [ 1,False,False],             None,            None]]]
    size = 64
    UnwrappedMap = glLibUnwrappedCubemap(faces,size)

    ObjectRotation = [0,0]
    CameraRotation = [90,23]
    CameraRadius = 15.0
##    CameraRadius = 35.0

    glEnable(GL_LIGHTING)
    Light1 = glLibLight(1)
    Light1.set_pos([0,0,0])
    Light1.set_type(GLLIB_POINT_LIGHT)
    Light1.enable()

    pygame.mouse.get_rel()

    Shader = glLibShader()
    Shader.render_equation("""
    color.rgb += ambient_color.rgb*light_ambient(light1).rgb;
    color.rgb += diffuse_color.rgb*light_diffuse(light1).rgb;
    color.rgb += specular_color.rgb*light_specular_ph(light1).rgb;
    
    color.rgb *= texture2D(tex2D_1,uv).rgb;
    float shadowed = cubemap_depthtest(texCube_2,vec3(0.0),"""+str(float(CubemapView.near))+","+str(float(CubemapView.far))+""");//light1.position.xyz
    color.rgb *= clamp(shadowed,0.5,1.0);""")
    Shader.max_textures_cube(2)
    errors = Shader.compile()
    print(errors)
##    if errors != "":
##        pygame.quit()
##        raw_input(errors)
##        sys.exit()
##    else:
##        print("No errors to report with cubeshadowmapping shader (cubeshadowmapping.py)!")
        
def quit():
    global Light1, Objects
    glDisable(GL_LIGHTING)
    del Light1
    del Objects

def GetInput():
    global CameraRadius
    global using_normalmap, reflect_refract
    mrel = pygame.mouse.get_rel()
    mpress = pygame.mouse.get_pressed()
    for event in pygame.event.get():
        if event.type == QUIT: quit(); pygame.quit(); sys.exit()
        elif event.type == KEYDOWN:
            if event.key == K_ESCAPE: return False
            elif event.key == K_n: using_normalmap = not using_normalmap
            elif event.key == K_r:
                reflect_refract += 1
                if reflect_refract == 4: reflect_refract = 1
        elif event.type == MOUSEBUTTONDOWN:
            if event.button == 5: CameraRadius += .2
            if event.button == 4: CameraRadius -= .2
    if mpress[0]:
        CameraRotation[0] += mrel[0]
        CameraRotation[1] += mrel[1]
    if mpress[2]:
        ObjectRotation[0] += mrel[0]
        ObjectRotation[1] += mrel[1]

def send_matrix_transform(shader,func):
    glPushMatrix()
    glLoadIdentity()
    func()
    shader.pass_mat4("transform_matrix",glGetFloatv(GL_MODELVIEW_MATRIX))
    glPopMatrix()
def draw_occluders(shader=False):
    Light1.set()
    def transform(pos):
        glTranslatef(*pos)
        glRotatef(ObjectRotation[0],0,1,0)
        glRotatef(ObjectRotation[1],1,0,0)
    index = 0
    for pos in [[0,0,3],[0,0,-3],[3,0,0],[-3,0,0],[0,3,0],[0,-3,0]]:
        glPushMatrix()
        transform(pos)
        #if the cube shadowmap drawing shader is supplied,
        #send the necessary transforms to it.
        if shader != False:
            send_matrix_transform(shader,lambda:transform(pos))
        Objects[index].draw_list()
        glPopMatrix()
        index += 1
    if shader == False:
        BoundingCube.draw()
    else:
        glEnable(GL_CULL_FACE)
        send_matrix_transform(Shader,lambda:0)
        BoundingCube.draw()
        glDisable(GL_CULL_FACE)
def Draw(Window):
    #Update the cubemap.  Draws the environment with
    #draw_occluders() 6 times.
    glEnable(GL_POLYGON_OFFSET_FILL);glPolygonOffset(1.0,1.0)
    glLibUpdateCubeMap(Cubemap,CubemapView,Light1.get_pos(),draw_occluders,format=GLLIB_DEPTH,update=GLLIB_ALL)
    glPolygonOffset(0.0,0.0);glDisable(GL_POLYGON_OFFSET_FILL)
    
    Window.clear()
    View3D.set_view()
    camerapos = [0 + CameraRadius*cos(radians(CameraRotation[0]))*cos((radians(CameraRotation[1]))),
                 0 + CameraRadius*sin((radians(CameraRotation[1]))),
                 0 + CameraRadius*sin(radians(CameraRotation[0]))*cos((radians(CameraRotation[1])))]
    gluLookAt(camerapos[0],camerapos[1],camerapos[2], 0,0,0, 0,1,0)
    Light1.set()
    Light1.draw_as_point(10)

    glLibUseShader(Shader)
    Shader.pass_texture(Cubemap,2)
    draw_occluders(Shader)
    glLibUseShader(None)

    InsetView2D.set_view()
    glEnable(GL_SCISSOR_TEST)
    glScissor(0,0,InsetView2D.width,InsetView2D.height)
    Window.clear()
    glDisable(GL_LIGHTING)
    UnwrappedMap.draw()
    glEnable(GL_LIGHTING)
    glDisable(GL_SCISSOR_TEST)

    Window.flip()
