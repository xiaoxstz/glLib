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
#implement in OpenGL.  A common approach is to render the
#surrounding scene ("environment") in every direction, and then
#simply use the reflected ray or refracted ray's direction to
#look up the proper color from the stored map.  Each of 6
#directions is rendered and the result stored in a "cubemap".
#This isn't correct unless the environment is infinitely far
#away, the reflector is convex, and no inter-reflections occur,
#but in practice the result is visually fairly good.  

import sys,os
sys.path.append(os.path.split(sys.path[0])[0])
from glLib import *

def init(Screen):
    global InsetView2D, View3D, CubemapView
    global Spaceship, Plane, UnwrappedMap, EnvCube, Cubemap
    global SpaceshipRotation, CameraRotation, CameraRadius
    global Light1
    global Shader
    global Normalmap
    global using_normalmap, reflect_refract, eta
    InsetView2D = glLibView2D((0,0,256,192))
    View3D = glLibView3D((0,0,Screen[0],Screen[1]),45,0.1,200)
    #Cubemap view.  Angle must be 90 degrees.
    CubemapView = glLibView3D((0,0,512,512),90)

    Spaceship = glLibObject("data/objects/Spaceship.obj",GLLIB_FILTER,GLLIB_MIPMAP_BLEND)
    #give the spaceship a soft shininess, leave the other material parameters alone.  
    Spaceship.set_material([[-1,-1,-1,1.0],0,-1]) 
    Spaceship.build_vbo()

    FloorTexture = glLibTexture2D("data/floor.jpg",[0,0,512,512],GLLIB_RGBA,GLLIB_FILTER,GLLIB_MIPMAP_BLEND)

    Plane = glLibPlane(5,(0,1,0),FloorTexture,10)

    Normalmap = glLibTexture2D("data/rocknormal.png",[0,0,255,255],GLLIB_RGBA,GLLIB_FILTER,GLLIB_MIPMAP_BLEND)

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

    #Make a cubemap texture.  Pass None in for the texture data.  The
    #texture will be updated dynamically with glLibUpdateCubeMap(...)
    Cubemap = glLibTextureCube([None]*6,(0,0,512,512),GLLIB_RGB,GLLIB_FILTER)
    Cubemap.edge(GLLIB_CLAMP)

    #This will render an unwrapped version of contents of the cubemap
    #for our evaluation.
    faces = [[[       None,    GLLIB_TOP,        None,       None],
              [GLLIB_RIGHT,  GLLIB_FRONT,  GLLIB_LEFT, GLLIB_BACK],
              [       None, GLLIB_BOTTOM,        None,       None]],
             [[            None, [-1,False,False],             None,            None],
              [[ 1,False,False], [ 1,False,False], [-1,False,False], [ 1,False,False]],
              [            None, [ 1,False,False],             None,            None]]]
    size = 64
    UnwrappedMap = glLibUnwrappedCubemap(faces,size)

    SpaceshipRotation = [0,0]
    CameraRotation = [90,23]
    CameraRadius = 5.0
    eta = 1.0

    glEnable(GL_LIGHTING)
    Light1 = glLibLight(1)
    Light1.set_pos([0,10,0])
    Light1.set_type(GLLIB_POINT_LIGHT)
    Light1.enable()

    pygame.mouse.get_rel()

    #"cubenorm" is a normal, derived from the object's normal that can be
    #sampled in cubemap_reflect_sample(...) and/or cubemap_refract_sample(...).
    #cubemap_normal_from_normalmap(...) does the same, but from a normalmap.  
    Shader = glLibShader()
    #Custom variables
    Shader.user_variables("""
    uniform bool using_normalmap;
    uniform int reflect_refract;
    uniform float eta;""")
    Shader.render_equation("""
    vec3 cubenorm=vec3(0.0);
    if (!using_normalmap) { cubenorm = cubemap_normal(); }
    else                  { cubenorm = cubemap_normal_from_normalmap(texture2D(tex2D_2,uv).rgb); }
    
    vec4 reflectsample = cubemap_reflect_sample(texCube_1,cubenorm);
    vec4 refractsample = cubemap_refract_sample(texCube_1,cubenorm,eta);
    
    if      (reflect_refract==1) { color.rgb = reflectsample.rgb; }
    else if (reflect_refract==2) { color.rgb = refractsample.rgb; }
    else if (reflect_refract==3) {
        //light reflecting off the surface to eye
        float reflecting_light = fresnel_coefficient(1.33,1.0).x;
        //light from inside the surface to eye
        float refracting_light = fresnel_coefficient(1.33,1.0).y;
        color.rgb += 1.3*reflecting_light*reflectsample.rgb;
        color.rgb += 1.0*refracting_light*refractsample.rgb;
    }""")
    Shader.uv_transform("uv*=10.0;")
    #Because we have a cube map, we'll need to send it to texCube_1 in the shader.
    Shader.max_textures_cube(1)
    errors = Shader.compile()
    print(errors)
##    if errors != "":
##        pygame.quit()
##        raw_input(errors)
##        sys.exit()
##    else:
##        print("No errors to report with cubemapping shader (cubemapping.py)!")

    #variables for uniforms that determine whether the shader uses
    #a normalmap, and whether it uses reflection, refraction, or both.
    using_normalmap, reflect_refract = False, 1
        
def quit():
    global Light1, Spaceship
    glDisable(GL_LIGHTING)
    del Light1
    del Spaceship

def GetInput():
    global CameraRadius
    global using_normalmap, reflect_refract, eta
    mrel = pygame.mouse.get_rel()
    mpress = pygame.mouse.get_pressed()
    key = pygame.key.get_pressed()
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
        SpaceshipRotation[0] += mrel[0]
        SpaceshipRotation[1] += mrel[1]
    if key[K_e]:
        if key[K_UP]: eta += 0.01
        if key[K_DOWN]: eta -= 0.01
        #clamp the refractive index to 1/1 and 1/4, meaning the
        #object can have a refractive index of any number 1 to 4
        eta = clamp(eta,0.25,1.0)

def draw_env_cube():
    glDisable(GL_LIGHTING)
    EnvCube.draw()
    glEnable(GL_LIGHTING)
def draw_reflectees():
    Light1.set()
    draw_env_cube()
    Plane.draw()
def spaceship_rotate():
    glRotatef(SpaceshipRotation[0],0,1,0)
    glRotatef(SpaceshipRotation[1],1,0,0)
def pass_rotations(shader):
    glPushMatrix()
    glLoadIdentity()
    spaceship_rotate()
    #Pass the cubemap matrix (contains the rotations only
    #of the reflective and/or refractive object).
    shader.pass_mat4("transform_matrix",glGetFloatv(GL_MODELVIEW_MATRIX))
    glPopMatrix()
def pass_variables(shader):
    #Pass the cubemap
    shader.pass_texture(Cubemap,1)
    shader.pass_texture(Normalmap,2)
    shader.pass_bool("using_normalmap",using_normalmap)
    shader.pass_int("reflect_refract",reflect_refract)
    shader.pass_float("eta",eta)
def Draw(Window):
    #Update the cubemap.  Draws the environment with
    #draw_reflectees() 6 times.
    glLibUpdateCubeMap(Cubemap,CubemapView,[0,1,0],draw_reflectees,update=GLLIB_ALL)
    
    Window.clear()
    View3D.set_view()
    camerapos = [0 + CameraRadius*cos(radians(CameraRotation[0]))*cos((radians(CameraRotation[1]))),
                 1 + CameraRadius*sin((radians(CameraRotation[1]))),
                 0 + CameraRadius*sin(radians(CameraRotation[0]))*cos((radians(CameraRotation[1])))]
    gluLookAt(camerapos[0],camerapos[1],camerapos[2], 0,1,0, 0,1,0)
    Light1.set()

    glLibUseShader(Shader)
    pass_rotations(Shader)
    pass_variables(Shader)
    glPushMatrix()
    glTranslatef(0.0,1.0,0.0)
    spaceship_rotate()
    Spaceship.draw_vbo(Shader)
    glPopMatrix()

    glLibUseShader(None)
    Plane.draw()
    draw_env_cube()

    InsetView2D.set_view()
    glEnable(GL_SCISSOR_TEST)
    glScissor(0,0,InsetView2D.width,InsetView2D.height)
    Window.clear()
    glDisable(GL_LIGHTING)
    UnwrappedMap.draw()
    glEnable(GL_LIGHTING)
    glDisable(GL_SCISSOR_TEST)

    Window.flip()
