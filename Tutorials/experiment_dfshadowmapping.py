#Tutorial by Ian Mallett

#Controls:
#ESC           - Return to menu
#LCLICK + DRAG - Rotate camera
#RCLICK + DRAG - Rotate spaceship
#SROLL WHEEL   - Zoom

#Theory
#The screen is a "framebuffer" of types.  Scenes are rendered to
#the current framebuffer(s).  Normally, that's the screen, but
#by using off-screen renderbuffers, larger scenes can be
#rendered.  The accuracy (and hence usability) of shadowmapping
#depends to a large degree on the size of the depthmap--the
#larger, the more accurate it is.  Normally, the size of the
#shadowmap would be dependent on the size of the screen's
#framebuffer.  By rendering the depthmap in a separate
#framebuffer, a higher resolution, and hence higher accuracy,
#can be achieved.

import sys,os
sys.path.append(os.path.split(sys.path[0])[0])
from glLib import *

def init(Screen):
    global shadowmode, shadowoffset, shadowmapsize, blur_kernel, depth_conscious
    global View3D, LightView, LightView2D
    global Spaceship, Plane
    global SpaceshipPosition, SpaceshipRotation, CameraRotation, CameraRadius
    global Light1, fbo_occluders, fbo_receivers, fbo_blurx, fbo_blury, fbo_kernel
    global ShaderShadow, ShaderDFShadow, ShaderDepthConsciousBlurX, ShaderDepthConsciousBlurY, ShaderDepthConsciousKernelSize
    global DiffuseTexture, FloorTexture
    View3D = glLibView3D((0,0,Screen[0],Screen[1]),45,0.1,20)
    shadowmode = 2
    shadowoffset = 0.0
##    shadowmapsize = 64
##    shadowmapsize = 128
    shadowmapsize = 256
##    shadowmapsize = 512
##    shadowmapsize = 1024
##    shadowmapsize = 2048
##    shadowmapsize = 4096
    depth_conscious = False
    LightView   = glLibView3D((0,0,shadowmapsize,shadowmapsize),20,5,25)
    LightView2D = glLibView2D((0,0,shadowmapsize,shadowmapsize))

    Spaceship = glLibObject("data/objects/Spaceship.obj",GLLIB_FILTER,GLLIB_MIPMAP_BLEND)
    Spaceship.build_vbo()

    FloorTexture = glLibTexture2D("data/floor.jpg",[0,0,512,512],GLLIB_RGBA,GLLIB_FILTER,GLLIB_MIPMAP_BLEND)

    Plane = glLibPlane(5,(0,1,0),FloorTexture,10)

    DiffuseTexture = glLibTexture2D("data/plates.jpg",[0,0,512,512],GLLIB_RGBA,GLLIB_FILTER,GLLIB_MIPMAP_BLEND)

    SpaceshipPosition = [0.0,1.5,0.0]
    SpaceshipRotation = [0,0]
    CameraRotation = [90,23]
    CameraRadius = 10.0
##    CameraRotation = [115,13]
##    CameraRadius = 1.2

    #Make a framebuffer.  We want it to be
    #the same size as the light's view.  The
    #view can now be (way) larger than the
    #Screen (800,600)!
    fbo_occluders = glLibFBO((shadowmapsize,shadowmapsize))
    fbo_occluders.add_render_target(1,type=GLLIB_DEPTH)
    fbo_occluders.add_render_target(2,type=GLLIB_RGB,filtering=GLLIB_FILTER)

    fbo_receivers = glLibFBO((shadowmapsize,shadowmapsize))
    fbo_receivers.add_render_target(1,type=GLLIB_DEPTH)

    fbo_blurx = glLibFBO((shadowmapsize,shadowmapsize))
    fbo_blurx.add_render_target(1,type=GLLIB_RGB,filtering=GLLIB_FILTER)

    fbo_blury = glLibFBO((shadowmapsize,shadowmapsize))
    fbo_blury.add_render_target(1,type=GLLIB_RGB,filtering=GLLIB_FILTER)

    fbo_kernel = glLibFBO((shadowmapsize,shadowmapsize))
    fbo_kernel.add_render_target(1,type=GLLIB_RGB,filtering=GLLIB_FILTER)

    glEnable(GL_LIGHTING)
    Light1 = glLibLight(1)
    Light1.set_pos([5,8,5])
    Light1.set_type(GLLIB_POINT_LIGHT)
    Light1.enable()

    pygame.mouse.get_rel()

##    blur_kernel = range(-4,4+1,1)
    blur_kernel = range(-8,8+1,2)
##    blur_kernel = range(-16,16+1,4)
##    blur_kernel = range(-32,32+1,8)

##    blur_kernel = range(-8,8+1,1)
##    blur_kernel = range(-16,16+1,2)
##    blur_kernel = range(-32,32+1,4)

    blur_sc = str(8.0)

    ShaderDepthConsciousBlurX = glLibShader()
    blur = ""
    for element in blur_kernel:
        blur += """color.rgb += """+str(1.0/float(len(blur_kernel)))+"*texture2D(tex2D_1,vec2(uv.x+depth_sc*("+str(float(element)/float(shadowmapsize))+"""),uv.y)).rgb;
        """
    ShaderDepthConsciousBlurX.render_equation("""
    float depth_sc = """+blur_sc+"""*texture2D(tex2D_2,uv).r;
    """+blur)#+"color.rgb=vec3(depth_sc);")
    errors = ShaderDepthConsciousBlurX.compile()
    print(errors)

    ShaderDepthConsciousBlurY = glLibShader()
    blur = ""
    for element in blur_kernel:
        blur += """color.rgb += """+str(1.0/float(len(blur_kernel)))+"*texture2D(tex2D_1,vec2(uv.x,uv.y+depth_sc*("+str(float(element)/float(shadowmapsize))+"""))).rgb;
        """
    ShaderDepthConsciousBlurY.render_equation("""
    float depth_sc = """+blur_sc+"""*texture2D(tex2D_2,uv).r;
    """+blur)#+"color.rgb=vec3(depth_sc);")
    errors = ShaderDepthConsciousBlurY.compile()
    print(errors)

    ShaderDepthConsciousKernelSize = glLibShader()
    ShaderDepthConsciousKernelSize.render_equation("""
    float depth_occluder = depth_from_depthbuffer(texture2D(tex2D_1,uv).r,"""+str(float(LightView.near))+","+str(float(LightView.far))+""");
    float depth_receiver = depth_from_depthbuffer(texture2D(tex2D_2,uv).r,"""+str(float(LightView.near))+","+str(float(LightView.far))+""");
    color.r = clamp(depth_receiver-depth_occluder,0.0,1.0);""")
    errors = ShaderDepthConsciousKernelSize.compile()
    print(errors)
    
##    light_eq = """
##    color.rgb = vec3(1.0);"""
    light_eq = """
    color.rgb += ambient_color.rgb*light_ambient(light1).rgb;
    color.rgb += diffuse_color.rgb*light_diffuse(light1).rgb;
    color.rgb += specular_color.rgb*light_specular_ph(light1).rgb;"""
    
    shadow_equation = "color.rgb *= clamp(shadowed_value,0.15,1.0);"

    ShaderShadow = glLibShader()
    ShaderShadow.render_equation(light_eq+"""
    float shadowed_value = shadowed(tex2D_2,depth_coord_1,false);
    color.rgb *= texture2D(tex2D_1,uv).rgb;
    """+shadow_equation)
    errors = ShaderShadow.compile()
    print(errors)

    ShaderDFShadow = glLibShader()
    ShaderDFShadow.fragment_extension_functions("""
    float dfshadowmap(sampler2D intentex, vec4 depth_coord) {
        vec2 testcoord = depth_coord.xy/depth_coord.w - vec2(0.5);
        if (abs(testcoord.x)>0.5) return 1.0;
        if (abs(testcoord.y)>0.5) return 1.0;
            
        return 1.0 - texture2DProj(intentex,depth_coord).r;
    }""")
    ShaderDFShadow.render_equation(light_eq+"""
    float shadowed_value = dfshadowmap(tex2D_2,depth_coord_1);
    color.rgb *= texture2D(tex2D_1,uv).rgb;
    """+shadow_equation)
    errors = ShaderDFShadow.compile()
    print(errors)

def quit():
    global Light1, Spaceship
    glDisable(GL_LIGHTING)
    del Light1
    del Spaceship

def GetInput():
    global shadowmode, shadowoffset, depth_conscious
    global CameraRadius
    mrel = pygame.mouse.get_rel()
    mpress = pygame.mouse.get_pressed()
    key = pygame.key.get_pressed()
    for event in pygame.event.get():
        if event.type == QUIT: quit(); pygame.quit(); sys.exit()
        if event.type == KEYDOWN:
            if event.key == K_ESCAPE: return False
            elif event.key == K_s:
                shadowmode = 3 - shadowmode
                print("Shadow mode is now %d" % (shadowmode))
            elif event.key == K_d:
                depth_conscious = not depth_conscious
                print("Depth conscious:",depth_conscious)
        if event.type == MOUSEBUTTONDOWN:
            if event.button == 5: CameraRadius += .2
            if event.button == 4: CameraRadius -= .2
    if mpress[0]:
        CameraRotation[0] += mrel[0]
        CameraRotation[1] += mrel[1]
    if mpress[2]:
        SpaceshipRotation[0] += mrel[0]
        SpaceshipRotation[1] += mrel[1]
    if key[K_o]:
        if key[K_UP]:
            shadowoffset += 0.01
            print("Shadow offset is now %f" % (shadowoffset))
        if key[K_DOWN]:
            shadowoffset -= 0.01
            print("Shadow offset is now %f" % (shadowoffset))

def TransformOccluders():
    glTranslatef(*SpaceshipPosition)
    glRotatef(SpaceshipRotation[0],0,1,0)
    glRotatef(SpaceshipRotation[1],1,0,0)
##    glScalef(0.2,0.2,0.2)
def DrawOccluders():
    TransformOccluders()
    Spaceship.draw_vbo()
def DrawBlurTexture(texture,kernel,shaderx=None,shadery=None,kerneltex=None):
    glDisable(GL_DEPTH_TEST); glDisable(GL_LIGHTING)
    glBlendFunc(GL_SRC_ALPHA,GL_ONE)
    glColor3fv( [1.0/len(kernel)]*3 )
    
    fbo_blurx.enable(GLLIB_ALL)
    glClear(GL_COLOR_BUFFER_BIT|GL_DEPTH_BUFFER_BIT)
    LightView2D.set_view()
    glLibSelectTexture( texture )
    if shaderx:
        glLibUseShader(shaderx)
        shaderx.pass_texture(kerneltex,2)
        glBegin(GL_QUADS)
        glTexCoord2f(0,0); glVertex2f(0,              0              )
        glTexCoord2f(1,0); glVertex2f(0+shadowmapsize,0              )
        glTexCoord2f(1,1); glVertex2f(0+shadowmapsize,0+shadowmapsize)
        glTexCoord2f(0,1); glVertex2f(0,              0+shadowmapsize)
        glEnd()
    else:
        glBegin(GL_QUADS)
        for x in kernel:
            glTexCoord2f(0,0); glVertex2f(x,              0              )
            glTexCoord2f(1,0); glVertex2f(x+shadowmapsize,0              )
            glTexCoord2f(1,1); glVertex2f(x+shadowmapsize,0+shadowmapsize)
            glTexCoord2f(0,1); glVertex2f(x,              0+shadowmapsize)
        glEnd()
    fbo_blurx.disable()
    
    fbo_blury.enable(GLLIB_ALL)
    glClear(GL_COLOR_BUFFER_BIT|GL_DEPTH_BUFFER_BIT)
    LightView2D.set_view()
    glLibSelectTexture( fbo_blurx.get_texture(1) )
    if shadery:
        glLibUseShader(shadery)
        shadery.pass_texture(kerneltex,2)
        glBegin(GL_QUADS)
        glTexCoord2f(0,0); glVertex2f(0,              0              )
        glTexCoord2f(1,0); glVertex2f(0+shadowmapsize,0              )
        glTexCoord2f(1,1); glVertex2f(0+shadowmapsize,0+shadowmapsize)
        glTexCoord2f(0,1); glVertex2f(0,              0+shadowmapsize)
        glEnd()
    else:
        glBegin(GL_QUADS)
        for y in kernel:
            glTexCoord2f(0,0); glVertex2f(0,              y              )
            glTexCoord2f(1,0); glVertex2f(0+shadowmapsize,y              )
            glTexCoord2f(1,1); glVertex2f(0+shadowmapsize,y+shadowmapsize)
            glTexCoord2f(0,1); glVertex2f(0,              y+shadowmapsize)
        glEnd()
    fbo_blury.disable()

    glColor3f(1,1,1)
    glBlendFunc(GL_SRC_ALPHA,GL_ONE_MINUS_SRC_ALPHA)
    glEnable(GL_DEPTH_TEST); glEnable(GL_LIGHTING)

    return fbo_blury.get_texture(1)
def Draw(Window):
    lightpos = Light1.get_pos()
    
    #====RENDER OCCLUDERS====

    fbo_occluders.enable(GLLIB_ALL)
    Window.clear()
    
    glLibPushView()
    
    proj,view = glLibInternal_set_proj_and_view_matrices(LightView,lightpos,SpaceshipPosition)

    glEnable(GL_POLYGON_OFFSET_FILL)
    glPolygonOffset(1.5,1.5)
        
    glDisable(GL_LIGHTING); glDisable(GL_TEXTURE_2D)
    glPushMatrix();DrawOccluders();glPopMatrix()
    glEnable(GL_LIGHTING); glEnable(GL_TEXTURE_2D)
    
    glPolygonOffset(0.0,0.0)
    glDisable(GL_POLYGON_OFFSET_FILL)
    
    glLibPopView()

    fbo_occluders.disable()

    #====RENDER RECEIVERS====

    if depth_conscious:
        fbo_receivers.enable(GLLIB_ALL)

        Window.clear()
        LightView.set_view()
        gluLookAt(lightpos[0],lightpos[1],lightpos[2], SpaceshipPosition[0],SpaceshipPosition[1],SpaceshipPosition[2], 0,1,0)
        
        glDisable(GL_LIGHTING); glDisable(GL_TEXTURE_2D)
        Plane.draw()
        glEnable(GL_LIGHTING); glEnable(GL_TEXTURE_2D)
    
        fbo_receivers.disable()

    #====GET KERNEL TEXTURE====
        
        fbo_kernel.enable(GLLIB_ALL)

        Window.clear()
        LightView2D.set_view()

        glLibUseShader(ShaderDepthConsciousKernelSize)
        ShaderDepthConsciousKernelSize.pass_texture(fbo_receivers.get_texture(1),2)
        ShaderDepthConsciousKernelSize.pass_texture(fbo_occluders.get_texture(1),1)
        
        glBegin(GL_QUADS)
        glTexCoord2f(0,0); glVertex2f(0,              0              )
        glTexCoord2f(1,0); glVertex2f(0+shadowmapsize,0              )
        glTexCoord2f(1,1); glVertex2f(0+shadowmapsize,0+shadowmapsize)
        glTexCoord2f(0,1); glVertex2f(0,              0+shadowmapsize)
        glEnd()
        
        fbo_kernel.disable()
        
    #====BLUR KERNEL TEXTURE====

        glLibUseShader(None)

##        kerneltex = fbo_kernel.get_texture(1)
##        kerneltex = DrawBlurTexture( fbo_kernel.get_texture(1), [0] )
        kerneltex = DrawBlurTexture( fbo_kernel.get_texture(1), range(-7,7+1,1) )

    #====BLUR LIGHT TEXTURE====
        
        shadowtex = DrawBlurTexture( fbo_occluders.get_texture(2), blur_kernel, ShaderDepthConsciousBlurX, ShaderDepthConsciousBlurY, kerneltex=kerneltex )
    else:
        shadowtex = DrawBlurTexture( fbo_occluders.get_texture(2), blur_kernel )
        
    #====DRAW SCENE====

    Window.clear()
    View3D.set_view()
    camerapos = [0 + CameraRadius*cos(radians(CameraRotation[0]))*cos((radians(CameraRotation[1]))),
                 1 + CameraRadius*sin((radians(CameraRotation[1]))),
                 0 + CameraRadius*sin(radians(CameraRotation[0]))*cos((radians(CameraRotation[1])))]
    gluLookAt(camerapos[0],camerapos[1],camerapos[2], 0,1,0, 0,1,0)
    
    Light1.set()
    Light1.draw_as_sphere()

    if shadowmode == 1:
        glLibUseShader(ShaderShadow)
        ShaderShadow.pass_texture(FloorTexture,1)
        glLibUseDepthMaps([[fbo_occluders.get_texture(1),proj,view]],1,2,ShaderShadow,lambda:0)
    elif shadowmode == 2:
        glLibUseShader(ShaderDFShadow)
        ShaderDFShadow.pass_texture(FloorTexture,1)
        glLibUseDepthMaps([[shadowtex,proj,view]],1,2,ShaderDFShadow,lambda:0)
    Plane.draw()

    glLibUseShader(ShaderShadow)
    ShaderShadow.pass_texture(DiffuseTexture,1)
    glPushMatrix()
    glLibUseDepthMaps([[fbo_occluders.get_texture(1),proj,view]],1,2,ShaderShadow,TransformOccluders)
    DrawOccluders()
    glPopMatrix()

    glLibUseShader(None)

    #====DRAW INSET====

    #Draw a little inset frame showing the contents of the light's view depth buffer
    View2D = glLibView2D((0,0,128,128))
    View2D.set_view()
    glDisable(GL_LIGHTING)
##    glLibDrawScreenQuad(texture=fbo_occluders.get_texture(1))
##    glLibDrawScreenQuad(texture=fbo_occluders.get_texture(2))
    glLibDrawScreenQuad(texture=fbo_blury.get_texture(1))
##    glLibDrawScreenQuad(texture=fbo_receivers.get_texture(1))
##    glLibDrawScreenQuad(texture=kerneltex)
    glEnable(GL_LIGHTING)

    Window.flip()
