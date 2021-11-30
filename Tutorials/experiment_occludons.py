#Tutorial by Ian Mallett

#Controls:
#ESC           - Return to menu
#LCLICK + DRAG - Rotate camera
#RCLICK + DRAG - Rotate spaceship
#SROLL WHEEL   - Zoom

#Theory

import sys,os
sys.path.append(os.path.split(sys.path[0])[0])
from glLib import *

def init(Screen):
    global view_size, View2D, View3D, LightView3D, InsetView2D
    global splat_grid, Spaceship, Plane
    global SpaceshipPosition, SpaceshipRotation, CameraRotation, CameraRadius
    global Light1
    global fbo_light, fbos_depth_peel
    global LightPassShader, ViewPassShader, AccumulationPassShader, DrawPassShader, ShaderDepthPeel
    global GLLIB_CAUSTIC_POINT
    global num_depth_layers

    num_depth_layers = 4
    light_pass_size = 128
    point_size = 128.0
    view_size = list(Screen)
    
    View2D = glLibView2D((0,0,view_size[0],view_size[1]))
    View3D = glLibView3D((0,0,view_size[0],view_size[1]),45,0.5,200.0)
    LightView3D = glLibView3D((0,0,light_pass_size,light_pass_size),35,3.0,8.0)
    InsetView2D = glLibView2D((0,0,128,128))

    Spaceship = glLibObject("data/objects/Spaceship.obj",GLLIB_FILTER,GLLIB_MIPMAP_BLEND)
##    Spaceship = glLibObject("spikeyball.obj",GLLIB_FILTER,GLLIB_MIPMAP_BLEND)
    Spaceship.build_vbo()

    FloorTexture = glLibTexture2D("data/floor.jpg",[0,0,512,512],GLLIB_RGBA,GLLIB_FILTER,GLLIB_MIPMAP_BLEND)
    Plane = glLibPlane(5,(0,1,0),FloorTexture,10)

    SpaceshipPosition = [0.0,1.0,0.0]
    SpaceshipRotation = [0,0]
    CameraRotation = [90,23]
    CameraRadius = 5.0

    #Uses the same point splatting technique as
    #caustic mapping; prepare light transport
    GLLIB_CAUSTIC_POINT = glLibPrepareCaustics()
    splat_grid = glLibGrid2D([light_pass_size,light_pass_size])

    fbos_depth_peel = []
    for x in range(1,num_depth_layers+1,1):
        fbo = glLibFBO([light_pass_size,light_pass_size])
        fbo.add_render_target(x,GLLIB_DEPTH,filtering=False,mipmapping=False,precision=8)
        fbos_depth_peel.append(fbo)

    fbo_light = glLibFBO([light_pass_size,light_pass_size])
    fbo_light.add_render_target(1,GLLIB_RGB,filtering=False,mipmapping=False,precision=32) #position texture
    fbo_light.add_render_target(2,GLLIB_RGB,filtering=False,mipmapping=False,precision= 8) #normal texture

    LightPassShader = glLibShader()
    LightPassShader.user_variables("uniform vec3 center;")
    LightPassShader.render_equation("""
    color.rgb = vertex.xyz;
    color2.rgb = realnorm;
    clamp_color = false;
    clamp_color2 = false;""")
    LightPassShader.render_targets(2)
    errors = LightPassShader.compile()
##    if errors != "": pygame.quit();raw_input(errors);sys.exit()
##    print("No errors to report with light pass shader (sss.py)!")
    print(errors)

    #Shader for depth peeling
    ShaderDepthPeel = glLibShader()
    ShaderDepthPeel.use_prebuilt(GLLIB_DEPTH_PEEL)

    DrawPassShader = glLibShader()
    DrawPassShader.user_variables("uniform vec2 size;")
    DrawPassShader.render_equation("""
    color.rgb += ambient_color.rgb*light_ambient(light1).rgb;
    color.rgb += diffuse_color.rgb*light_diffuse(light1).rgb;
    //color.rgb += texture2D(tex2D_2,gl_FragCoord.xy/size).rgb;
    color.rgb += specular_color.rgb*light_specular_ph(light1).rgb;

    color.rgb *= texture2D(tex2D_1,uv).rgb;""")
    errors = DrawPassShader.compile()
##    if errors != "": pygame.quit();raw_input(errors);sys.exit()
##    print("No errors to report with draw pass shader (sss.py)!")
    print(errors)

    pygame.mouse.get_rel()

    glEnable(GL_LIGHTING)
    Light1 = glLibLight(1)
    Light1.set_pos([0,5,0.1])
    Light1.set_type(GLLIB_POINT_LIGHT)
    Light1.enable()

def quit():
    global Light1, Spaceship, splat_grid
    glDisable(GL_LIGHTING)
    del Light1
    del Spaceship
    del splat_grid

def GetInput():
    global CameraRadius
    mrel = pygame.mouse.get_rel()
    mpress = pygame.mouse.get_pressed()
    for event in pygame.event.get():
        if event.type == QUIT: quit(); pygame.quit(); sys.exit()
        if event.type == KEYDOWN:
            if event.key == K_ESCAPE: return False
        if event.type == MOUSEBUTTONDOWN:
            if event.button == 5: CameraRadius += .2
            if event.button == 4: CameraRadius -= .2
    if mpress[0]:
        CameraRotation[0] += mrel[0]
        CameraRotation[1] += mrel[1]
    if mpress[2]:
        SpaceshipRotation[0] += mrel[0]
        SpaceshipRotation[1] += mrel[1]

def TranformObject():
    glTranslatef(*SpaceshipPosition)
    glRotatef(SpaceshipRotation[0],0,1,0)
    glRotatef(SpaceshipRotation[1],1,0,0)
def DrawOccluder():
    glPushMatrix()
    TranformObject()
    Spaceship.draw_vbo()
    glPopMatrix()
def DrawObjects():
    DrawOccluder()
    Plane.draw()
def Draw(Window):
    center = list(SpaceshipPosition)
    lightpos = Light1.get_pos()
    camerapos = [center[0] + CameraRadius*cos(radians(CameraRotation[0]))*cos(radians(CameraRotation[1])),
                 center[1] + CameraRadius*sin(radians(CameraRotation[1])),
                 center[2] + CameraRadius*sin(radians(CameraRotation[0]))*cos(radians(CameraRotation[1]))]

    #Pass 1: Render position and normal textures from light's perspective
    fbo_light.enable([1,2])
    Window.clear()
    LightView3D.set_view()
    gluLookAt(lightpos[0],lightpos[1],lightpos[2],center[0],center[1],center[2],0,1,0)
    glLibUseShader(LightPassShader)
    LightPassShader.pass_vec3("center",center)
    DrawOccluder()
    fbo_light.disable()

    #Passes 2: Depth peel
    textures,proj,view = glLibDepthPeelFBO(fbos_depth_peel,lightpos,LightView3D,center,\
                                           num_depth_layers,ShaderDepthPeel,DrawObjects)

    #Pass 4: Draw pass
    Window.clear()
    View3D.set_view()
    gluLookAt(camerapos[0],camerapos[1],camerapos[2],center[0],center[1],center[2],0,1,0)
    Light1.set()
    
    glLibUseShader(DrawPassShader)
    DrawPassShader.pass_vec2("size",view_size)
    DrawPassShader.pass_texture(Spaceship.materials[0]["texture_Kd"],1)
    #DrawPassShader.pass_texture(accumulation_fbo.get_texture(1),2)
    
    DrawObjects()
    
    glLibUseShader(None)

    glDisable(GL_LIGHTING)
    InsetView2D.set_view()
    glLibDrawScreenQuad(texture=textures[0])
    glEnable(GL_LIGHTING)

    Window.flip()
