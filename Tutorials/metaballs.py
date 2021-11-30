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

def init(Screen):
    global View3D, LightView, CubemapView
    global Plane, Metaballs, BoundingBox, EnvCube, UnwrappedMap
    global CameraRotation, CameraRadius, Light1, Shader, viewing_wire, Cubemap, viewing_mode
    View3D = glLibView3D((0,0,Screen[0],Screen[1]),45,0.1,200)
    LightView = glLibView3D((0,0,512,512),25,0.1,25)
    CubemapView = glLibView3D((0,0,512,512),90,0.1,500.0)

    #Load the Floor
    FloorTexture = glLibTexture2D("data/floor.jpg",[0,0,512,512],GLLIB_RGBA,GLLIB_FILTER,GLLIB_MIPMAP_BLEND)
    try:FloorTexture.anisotropy(GLLIB_MAX)
    except:pass
    Plane = glLibPlane(5,(0,1,0),FloorTexture,10)

    #A bounding box of the metaballs for reference
    BoundingBox = glLibRectangularSolid([1.0,1.0,1.0],normals=GLLIB_NONE)

    #Load environment textures
    texturenames = []
    for texturename in ["xpos","xneg","ypos","yneg","zpos","zneg"]:
        texturenames.append("data/cubemaps/"+texturename+".jpg")
    textures = []
    for texturename in texturenames:
        texture = glLibTexture2D(texturename,(0,0,256,256),GLLIB_RGB,GLLIB_FILTER,GLLIB_MIPMAP_BLEND)
        texture.edge(GLLIB_CLAMP)
        textures.append(texture)
    #Make a 3D cube using these textures of size 100.0
    EnvCube = glLibRectangularSolid([100.0,100.0,100.0],textures)

    #Cubemap
    Cubemap = glLibTextureCube([None]*6,(0,0,512,512),GLLIB_RGB,GLLIB_FILTER)
    Cubemap.edge(GLLIB_CLAMP)

    SpaceshipRotation = [0,0]
    #Add variables for the camera's rotation and radius
    CameraRotation = [90,23]
    CameraRadius = 5.0
    viewing_wire = False
    viewing_mode = 1

    glEnable(GL_LIGHTING)
    Light1 = glLibLight(1)
    Light1.set_diffuse([1,1,1])
    Light1.set_pos([5,5,5])
    Light1.set_type(GLLIB_POINT_LIGHT)
    Light1.enable()

    glPointSize(5)

    Metaballs = glLibMetaSystem(20)
    Metaballs.add_point("0",[0.5,0.5,0.5],0.2)
    Metaballs.add_point("1",[0.3,0.8,0.4],0.1)
    Metaballs.add_point("2",[0.6,0.4,0.2],0.1)
    Metaballs.add_point("3",[0.2,0.2,0.8],0.2)
    Metaballs.add_point("4",[0.8,0.3,0.8],0.2)
    Metaballs.update()
##    Metaballs.build_vbo()

    faces = [[[       None,    GLLIB_TOP,        None,       None],
              [GLLIB_RIGHT,  GLLIB_FRONT,  GLLIB_LEFT, GLLIB_BACK],
              [       None, GLLIB_BOTTOM,        None,       None]],
             [[            None, [-1,False,False],             None,            None],
              [[ 1,False,False], [ 1,False,False], [-1,False,False], [ 1,False,False]],
              [            None, [ 1,False,False],             None,            None]]]
    size = 64
    UnwrappedMap = glLibUnwrappedCubemap(faces,size)

    pygame.mouse.get_rel()

    Shader = glLibShader()
    Shader.user_variables("uniform int stage; uniform int rendermode;")
    Shader.render_equation("""
    if (stage==1) {
        if (rendermode==1) {
            color.rgb += ambient_color.rgb*light_ambient(light1).rgb;
            color.rgb += diffuse_color.rgb*light_diffuse(light1).rgb;
            color.rgb += specular_color.rgb*light_specular_ph(light1).rgb;
            color.rgb *= clamp(shadowed(tex2D_2,depth_coord_1,1.0,false),0.5,1.0);
        }
        else if (rendermode==2) {
            color.rgb = cubemap_reflect_sample(texCube_1,cubemap_normal()).rgb;
        }
        else {
            color.rgb = cubemap_refract_sample(texCube_1,cubemap_normal(),1.33).rgb;
        }
    }
    else if (stage==2) {
        color.rgb = vec3(1.0,0.0,0.0);
    }
    else if (stage==3) {
        color.rgb = vec3(1.0,0.0,1.0);
    }
    else if (stage==4) {
        color.rgb = vec3(0.0,0.0,1.0);
    }
    else {
        color.rgb = texture2D(tex2D_1,uv).rgb * clamp(shadowed(tex2D_2,depth_coord_1,1.0,false),0.5,1.0);
    }""")
    Shader.max_textures_cube(1)
    errors = Shader.compile()
    print(errors)
def quit():
    global Light1, Spaceship
    glDisable(GL_LIGHTING)
    del Light1
    glPointSize(1)

def move_point(name,delta_vec):
    point = Metaballs.get_point(name)
    position = point[0]
    Metaballs.move_point(name,vec_add(position,delta_vec))
    Metaballs.update()
##    Metaballs.build_vbo()
def GetInput():
    global CameraRadius, viewing_wire, viewing_mode
    mrel = pygame.mouse.get_rel()
    mpress = pygame.mouse.get_pressed()
    key = pygame.key.get_pressed()
    for event in pygame.event.get():
        if   event.type == QUIT: quit(); pygame.quit(); sys.exit()
        elif event.type == KEYDOWN:
            if   event.key == K_ESCAPE: return False
            elif event.key == K_m: viewing_wire = not viewing_wire
            elif event.key == K_v:
                viewing_mode += 1
                if viewing_mode == 4:
                    viewing_mode = 1
        elif event.type == MOUSEBUTTONDOWN:
            if   event.button == 5: CameraRadius += .2
            elif event.button == 4: CameraRadius -= .2
    if mpress[0]:
        CameraRotation[0] += mrel[0]
        CameraRotation[1] += mrel[1]
    if mpress[2]:
        SpaceshipRotation[0] += mrel[0]
    if key[K_UP   ]: move_point("4",[ 0.00, 0.01, 0.00])
    if key[K_DOWN ]: move_point("4",[ 0.00,-0.01, 0.00])
    if key[K_LEFT ]: move_point("4",[-0.01, 0.00, 0.00])
    if key[K_RIGHT]: move_point("4",[ 0.01, 0.00, 0.00])

def transform_to_metaballs():
    glScalef(2.0,2.0,2.0)
    glTranslatef(-0.5,0.0,-0.5)
def draw_metaballs(shader=None):
    glPushMatrix()
    transform_to_metaballs()
##    Metaballs.draw_vbo(shader)
    Metaballs.draw_direct()
    glPopMatrix()
def draw_env_cube():
    glDisable(GL_LIGHTING)
    EnvCube.draw()
    glEnable(GL_LIGHTING)
def draw_reflectees():
    draw_floor()
    draw_env_cube()
def draw_floor():
    glLibUseShader(Shader)
    Shader.pass_int("stage",5)
    if depthmap != None:
        glLibUseDepthMaps([[depthmap,proj,view]],1,2,Shader,lambda:0)
    Plane.draw()
depthmap = None
def Draw(Window):
    global depthmap,proj,view

    #Update cubemap
    glLibUpdateCubeMap(Cubemap,CubemapView,[0.0,1.0,0.0],draw_reflectees,update=GLLIB_ALL)
    
    #Update the Depthmap
    depthmap,proj,view = glLibMakeDepthMap(Light1,LightView,[0.0,1.0,0.0],depthmap,draw_metaballs,offset=1.0,filtering=GLLIB_FILTER)

    #Main pass
    Window.clear()
    View3D.set_view()
    camerapos = [0 + CameraRadius*cos(radians(CameraRotation[0]))*cos((radians(CameraRotation[1]))),
                 1 + CameraRadius*sin((radians(CameraRotation[1]))),
                 0 + CameraRadius*sin(radians(CameraRotation[0]))*cos((radians(CameraRotation[1])))]
    gluLookAt(camerapos[0],camerapos[1],camerapos[2], 0,1,0, 0,1,0)
    Light1.set()
    Light1.draw_as_point(10)

    #Draw Environment Box
    draw_env_cube()

    #Draw with the shader
    glLibUseShader(Shader)
    Shader.pass_int("rendermode",viewing_mode)
    glPushMatrix();glLoadIdentity();Shader.pass_mat4("transform_matrix",glGetFloatv(GL_MODELVIEW_MATRIX));glPopMatrix()
    glLibUseDepthMaps([[depthmap,proj,view]],1,2,Shader,transform_to_metaballs)
    
    #Draw Metaballs
    Shader.pass_int("stage",1)
    Shader.pass_texture(Cubemap,1)
    #   offset so that, if we draw the mesh, the lines' fragments
    #   will not interfere with the metaballs' fragments
    glEnable(GL_POLYGON_OFFSET_FILL)
    glPolygonOffset(1.0,1.0)
    draw_metaballs()
    glPolygonOffset(0.0,0.0)
    glDisable(GL_POLYGON_OFFSET_FILL)

    if viewing_wire:
        glPolygonMode(GL_FRONT_AND_BACK,GL_LINE)
        Shader.pass_int("stage",2)
        draw_metaballs()
        glPolygonMode(GL_FRONT_AND_BACK,GL_FILL)

    glPushMatrix()
    transform_to_metaballs()
    glDisable(GL_DEPTH_TEST)
    Shader.pass_int("stage",3)
    glBegin(GL_POINTS)
    for name in ["0","1","2","3","4"]: glVertex3f(*Metaballs.get_point(name)[0])
    glEnd()
    glEnable(GL_DEPTH_TEST)
    glPopMatrix()

    #Draw Bounding Box
    glPushMatrix()
    glTranslatef(0.0,1.0,0.0)
    glPolygonMode(GL_FRONT_AND_BACK,GL_LINE)
    Shader.pass_int("stage",4)
    glLineWidth(2)
    BoundingBox.draw()
    glLineWidth(1)
    glPolygonMode(GL_FRONT_AND_BACK,GL_FILL)
    glPopMatrix()

    #Draw the floor
    draw_floor()

    glLibUseShader(None)

    InsetView2D = glLibView2D((0,0,256,192))
    InsetView2D.set_view()
    glEnable(GL_SCISSOR_TEST)
    glScissor(0,0,InsetView2D.width,InsetView2D.height)
    Window.clear()
    glDisable(GL_LIGHTING)
    UnwrappedMap.draw()
    glEnable(GL_LIGHTING)
    glDisable(GL_SCISSOR_TEST)

    Window.flip()
