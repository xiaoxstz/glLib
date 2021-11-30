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
    global view_size, View2D, View3D, LightPassView3D
    global splat_grid, Spaceship
    global SpaceshipPosition, SpaceshipRotation, CameraRotation, CameraRadius
    global Light1
    global light_fbo, view_fbo, accumulation_fbo
    global LightPassShader, ViewPassShader, AccumulationPassShader, DrawPassShader
    global GLLIB_CAUSTIC_POINT
    light_pass_size = 128
    point_size = 128.0
    view_size = list(Screen)
    View2D = glLibView2D((0,0,view_size[0],view_size[1]))
    View3D = glLibView3D((0,0,view_size[0],view_size[1]),45,0.5,200.0)
    LightPassView3D = glLibView3D((0,0,light_pass_size,light_pass_size),28,3.0,8.0)

    Spaceship = glLibObject("data/objects/Spaceship.obj",GLLIB_FILTER,GLLIB_MIPMAP_BLEND)
##    Spaceship = glLibObject("spikeyball.obj",GLLIB_FILTER,GLLIB_MIPMAP_BLEND)
    Spaceship.build_vbo()

    SpaceshipPosition = [0.0,0.0,0.0]
    SpaceshipRotation = [0,0]
    CameraRotation = [90,23]
    CameraRadius = 5.0

    #Uses the same point splatting technique as
    #caustic mapping; prepare light transport
    GLLIB_CAUSTIC_POINT = glLibPrepareCaustics()
    splat_grid = glLibGrid2D([light_pass_size,light_pass_size])

    light_fbo = glLibFBO([light_pass_size,light_pass_size])
    light_fbo.add_render_target(1,GLLIB_RGB,filtering=False,mipmapping=False,precision=32) #position texture
    light_fbo.add_render_target(2,GLLIB_RGB,filtering=False,mipmapping=False,precision= 8) #normal texture

    view_fbo = glLibFBO(view_size)
    view_fbo.add_render_target(1,GLLIB_DEPTH,filtering=False,mipmapping=False,precision=8) #depth texture

    accumulation_fbo = glLibFBO(view_size)
    accumulation_fbo.add_render_target(1,GLLIB_RGB,filtering=False,mipmapping=False,precision=8) #accumulation texture

    LightPassShader = glLibShader()
    LightPassShader.user_variables("uniform vec3 center; uniform float radius;")
    LightPassShader.render_equation("""
    color.rgb = vec3(vertex.xyz-center)/(2.0*radius) + vec3(0.5);
    color2.rgb = vec3(realnorm+vec3(1.0))/2.0;""")
    LightPassShader.render_targets(2)
    errors = LightPassShader.compile()
##    if errors != "": pygame.quit();raw_input(errors);sys.exit()
##    print("No errors to report with light pass shader (sss.py)!")
    print(errors)

    ViewPassShader = glLibShader()
    errors = ViewPassShader.compile()
##    if errors != "": pygame.quit();raw_input(errors);sys.exit()
##    print("No errors to report with view pass shader (sss.py)!")
    print(errors)

    #TODO: THIS SHOULD USE THE DIPOLE MODEL!!!
    AccumulationPassShader = glLibShader()
    AccumulationPassShader.user_variables("uniform vec2 size; uniform vec3 center; uniform float radius, near, far; varying float normcoeff;")
    AccumulationPassShader.vertex_transform("""
    vec2 coordinate = vertex.xy;
    vertex.xyz = vec3(texture2D(tex2D_1,coordinate).rgb-vec3(0.5))*2.0*radius + center;""")
    AccumulationPassShader.post_vertex("""
    //normcoeff = dot(  gl_NormalMatrix*(texture2D(tex2D_2,coordinate).rgb*2.0-vec3(1.0)),  normalize(vVertex));
    //normcoeff = abs(normcoeff);
    gl_PointSize = """+str(point_size)+"""/length(gl_Position);""")
    AccumulationPassShader.render_equation("""
    float depth = texture2D(tex2D_3,gl_FragCoord.xy/size).r;
    if (depth!=1.0) {
        vec4 point = texture2D(tex2D_4,gl_PointCoord.xy);
        float delta_depth = depth_from_depthbuffer(gl_FragCoord.z,near,far)-depth_from_depthbuffer(depth,near,far);
        color.rgb = vec3(1.0 - 3000.0*delta_depth);
        color.rgb *= point.rgb*point.a*0.032*"""+str(10.0**(4.8164-2.0*log(point_size,10.0)))+""";//*clamp(normcoeff,0.0,1.0);
    }
    else { discard; }
    //color.rgb = vec3(normcoeff*0.1);""")
    errors = AccumulationPassShader.compile()
##    if errors != "": pygame.quit();raw_input(errors);sys.exit()
##    print("No errors to report with accumulation pass shader (sss.py)!")
    print(errors)

    DrawPassShader = glLibShader()
    DrawPassShader.user_variables("uniform vec2 size;")
    DrawPassShader.render_equation("""
    color.rgb += ambient_color.rgb*light_ambient(light1).rgb;
    color.rgb += diffuse_color.rgb*light_diffuse(light1).rgb;
    color.rgb += texture2D(tex2D_2,gl_FragCoord.xy/size).rgb;
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
def DrawObjects(shader=None):
    glPushMatrix()
    TranformObject()
    Spaceship.draw_vbo(shader)
    glPopMatrix()
def Draw(Window):
    center = list(SpaceshipPosition)
    lightpos = Light1.get_pos()
    camerapos = [center[0] + CameraRadius*cos(radians(CameraRotation[0]))*cos(radians(CameraRotation[1])),
                 center[1] + CameraRadius*sin(radians(CameraRotation[1])),
                 center[2] + CameraRadius*sin(radians(CameraRotation[0]))*cos(radians(CameraRotation[1]))]
    bounding_sphere_radius = 10.0

    #Pass 1: Render position and normal textures from light's perspective
    light_fbo.enable([1,2])
    Window.clear()
    LightPassView3D.set_view()
    gluLookAt(lightpos[0],lightpos[1],lightpos[2],center[0],center[1],center[2],0,1,0)
    glLibUseShader(LightPassShader)
    LightPassShader.pass_vec3("center",center)
    LightPassShader.pass_float("radius",bounding_sphere_radius)
    DrawObjects(LightPassShader)
    light_fbo.disable()

    #Pass 2: Render depth texture from view perspective
    view_fbo.enable([1])
    Window.clear()
    View3D.set_view()
    gluLookAt(camerapos[0],camerapos[1],camerapos[2],center[0],center[1],center[2],0,1,0)
    glLibUseShader(ViewPassShader)
    DrawObjects(ViewPassShader)
    view_fbo.disable()

    #Pass 3: Render accumulation texture from view perspective
    accumulation_fbo.enable([1])
    Window.clear()
    View3D.set_view()
    gluLookAt(camerapos[0],camerapos[1],camerapos[2],center[0],center[1],center[2],0,1,0)
    glLibUseShader(AccumulationPassShader)
    AccumulationPassShader.pass_vec2("size",view_size)
    AccumulationPassShader.pass_vec3("center",center)
    AccumulationPassShader.pass_float("radius",bounding_sphere_radius)
    AccumulationPassShader.pass_float("near",View3D.near)
    AccumulationPassShader.pass_float("far",View3D.far)
    AccumulationPassShader.pass_texture(light_fbo.get_texture(1),1)
##    AccumulationPassShader.pass_texture(light_fbo.get_texture(2),2)
    AccumulationPassShader.pass_texture(view_fbo.get_texture(1),3)
    AccumulationPassShader.pass_texture(GLLIB_CAUSTIC_POINT,4)
        
    glEnable(GL_POINT_SPRITE)
    glBlendFunc(GL_ONE,GL_ONE)
    glDisable(GL_DEPTH_TEST)
    glEnable(GL_VERTEX_PROGRAM_POINT_SIZE)
    glPushMatrix()
    TranformObject()
    splat_grid.draw()
    glPopMatrix()
    glDisable(GL_VERTEX_PROGRAM_POINT_SIZE)
    glEnable(GL_DEPTH_TEST)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
    glDisable(GL_POINT_SPRITE)

##    glLibUseShader(None)
##    glDisable(GL_LIGHTING)
##    glDisable(GL_TEXTURE_2D)
##    glColor4f(1.0,1.0,1.0,0.2)
##    glPolygonMode(GL_FRONT_AND_BACK,GL_LINE)
##    DrawObjects()
##    Light1.draw_as_sphere()
##    glPolygonMode(GL_FRONT_AND_BACK,GL_FILL)
##    glColor4f(1.0,1.0,1.0,1.0)
##    glEnable(GL_TEXTURE_2D)
##    glEnable(GL_LIGHTING)
    
    accumulation_fbo.disable()

    #Pass 4: Draw pass
    Window.clear()
    View3D.set_view()
    gluLookAt(camerapos[0],camerapos[1],camerapos[2],center[0],center[1],center[2],0,1,0)
    glLibUseShader(DrawPassShader)
    DrawPassShader.pass_vec2("size",view_size)
    DrawPassShader.pass_texture(Spaceship.materials[0]["texture_Kd"],1)
    DrawPassShader.pass_texture(accumulation_fbo.get_texture(1),2)
    DrawObjects(DrawPassShader)
    
    glLibUseShader(None)

##    glDisable(GL_LIGHTING)
##    Window.clear()
##    View2D.set_view()
##    glLibSelectTexture(accumulation_fbo.get_texture(1))
##    glLibTexFullScreenQuad()
##    glEnable(GL_LIGHTING)

    Window.flip()
