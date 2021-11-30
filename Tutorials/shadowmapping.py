#Tutorial by Ian Mallett

#Controls:
#ESC           - Return to menu
#f             - Toggle shadowmap filtering
#p             - Toggle projection of another texture
#LCLICK + DRAG - Rotate camera
#RCLICK + DRAG - Rotate spaceship
#SROLL WHEEL   - Zoom

#Theory:
#If you were a light source, everything you could see in any
#direction would be lit (i.e., not in shadow).  Shadowmapping
#draws the scene from the light's point of view, recording
#each fragment's depth.  Then, from the camera's perspective,
#for every fragment, if that fragment is further away from the
#light than the fragment it recorded in its depth map, the
#point is in shadow.  Otherwise, it is lit.
#
#Projective texture mapping is identical, except that the
#final result is then multiplied by a texture in the projected
#space (the same space that the shadowmap was sampled in).  

import sys,os
sys.path.append(os.path.split(sys.path[0])[0])
from glLib import *

def init(Screen):
    global View3D, LightView, filtering, use_projection_texture, draw_light_frustum
    global Spaceship, Plane, StainedGlassWindow
    global SpaceshipRotation, SpaceshipPosition, CameraRotation, CameraRadius
    global Light1
    global ShadowDrawingShader
    global DiffuseTexture, FloorTexture, ProjectionTexture
    View3D = glLibView3D((0,0,Screen[0],Screen[1]),45,0.1,20)
    #The light's viewpoint.  Try to keep the angle as small as
    #possible to efficiently use the texture's space.  This
    #corresponds to an extremely small shadowmap resolution; it
    #is only to show the general technique as well as the
    #advantages of filtering and distance field shadowmapping
    #more clearly.
    LightView = glLibView3D((0,0,128,128),35,3,6)

    Spaceship = glLibObject("data/objects/Spaceship.obj",GLLIB_FILTER,GLLIB_MIPMAP_BLEND)
    Spaceship.build_vbo()

    FloorTexture = glLibTexture2D("data/floor.jpg",[0,0,512,512],GLLIB_RGBA,GLLIB_FILTER,GLLIB_MIPMAP_BLEND)

    Plane = glLibPlane(5,(0,1,0),FloorTexture,10)

    DiffuseTexture = glLibTexture2D("data/plates.jpg",[0,0,512,512],GLLIB_RGBA,GLLIB_FILTER,GLLIB_MIPMAP_BLEND)
    
    ProjectionTexture = glLibTexture2D("data/glass.png",[0,0,500,500],GLLIB_RGB,GLLIB_FILTER,GLLIB_MIPMAP_BLEND)

    StainedGlassWindow = glLibPlane(0.5,(0,1,0),ProjectionTexture,1)

    SpaceshipRotation = [0,0]
    SpaceshipPosition = [0,1,0]
    CameraRotation = [90,23]
    CameraRadius = 5.0
    filtering = False
    use_projection_texture = False
    draw_light_frustum = False

    glEnable(GL_LIGHTING)
    Light1 = glLibLight(1)
    Light1.set_pos([0,5,1])
    #Make this light a point light type
    Light1.set_type(GLLIB_POINT_LIGHT)
    #Set the spot light's direction to aim at the spaceship.
    Light1.set_spot_dir(normalize(vec_subt(SpaceshipPosition,Light1.get_pos())))
    #Set the light's angle.  The light's cone
    #will have an apex angle of 35 degrees.
    Light1.set_spot_angle(35.0)
    #Set the light's exponent (the rate at which the intensity drops off
    #as distance increases from the center of the light's cone).  0.0 is
    #the default (no attenuation), but you can play with it.  
    Light1.set_spot_ex(0.0)
    Light1.enable()

    pygame.mouse.get_rel()

    #Add the shadowing calls.  We do .pass_shadow_texture(...,2)
    #below, so we must use shadtex2 here.  "tex2D_1" contains the
    #diffuse texture.  The "clamp" moves shadowed values (0.0) to
    #0.5, making the shadows not completely black; just darker.
    #light_spot(...) checks to see if the fragment is in the
    #light's spot--in this case, 1.0 if yes, 0.0 if no.  Because
    #there is only one depth map, and we're using it, we use
    #projcoord_1.
    
    #If the shadows do not look correct, try deleting (the
    #contents of, not the lines themselves!) lines 103 to 105.
    #If they still look wrong, change "false" on line 102 to
    #"true".
    ShadowDrawingShader = glLibShader()
    ShadowDrawingShader.user_variables("uniform bool use_proj_tex;")
    ShadowDrawingShader.render_equation("""
    color.rgb += ambient_color.rgb*light_ambient(light1).rgb;
    color.rgb += diffuse_color.rgb*light_diffuse(light1).rgb;
    color.rgb += specular_color.rgb*light_specular_ph(light1).rgb;
    color.rgb = clamp(color.rgb,0.2,1.0);
    color.rgb *= texture2D(tex2D_1,uv).rgb; //floor texture

    float light_intensity = shadowed(tex2D_3,depth_coord_1,0.0,false); //sample shadow texture
    //float light_intensity = df_shadowed(tex2D_3,vec2(128.0),depth_coord_1); //sample shadow texture
    if (use_proj_tex==false) {
        light_intensity *= light_spot(light1);
    }
    light_intensity = clamp(light_intensity,0.2,1.0);

    if (use_proj_tex==true) {
        color.rgb *= light_intensity;
        if (light_intensity!=0.2) {
            color.rgb += 0.3*texture2DProj(tex2D_2,depth_coord_1).rgb; //sample projection texture
        }
    }
    else {
        color.rgb *= light_intensity;
    }""")
    errors = ShadowDrawingShader.compile()
##    if errors != "": pygame.quit();raw_input(errors);sys.exit()
##    print("No errors to report with shadowmapping shader (shadowmapping.py)!")
    print(errors)
    
def quit():
    global Light1, Spaceship
    glDisable(GL_LIGHTING)
    del Light1
    del Spaceship

def GetInput():
    global CameraRadius, filtering, use_projection_texture, draw_light_frustum
    mrel = pygame.mouse.get_rel()
    mpress = pygame.mouse.get_pressed()
    for event in pygame.event.get():
        if   event.type == QUIT: quit(); pygame.quit(); sys.exit()
        elif event.type == KEYDOWN:
            if   event.key == K_ESCAPE: return False
            elif event.key == K_f: filtering = not filtering
            elif event.key == K_p: use_projection_texture = not use_projection_texture
            elif event.key == K_v: draw_light_frustum = not draw_light_frustum
        elif event.type == MOUSEBUTTONDOWN:
            if   event.button == 5: CameraRadius += .2
            elif event.button == 4: CameraRadius -= .2
    if mpress[0]:
        CameraRotation[0] += mrel[0]
        CameraRotation[1] += mrel[1]
    if mpress[2]:
        SpaceshipRotation[0] += mrel[0]
        SpaceshipRotation[1] += mrel[1]

#depthmap here is None.  Note that the first
#time glLibMakeShadowMap(...) is called, it is
#still None, but after the first frame, it is
#updated, not recreated, saving time.  
depthmap=None
def TransformOccluders():
    glTranslatef(*SpaceshipPosition)
    glRotatef(SpaceshipRotation[0],0,1,0)
    glRotatef(SpaceshipRotation[1],1,0,0)
def DrawOccluders():
    TransformOccluders()
    Spaceship.draw_vbo()
def SetCamera():
    gluLookAt(camerapos[0],camerapos[1],camerapos[2],\
              SpaceshipPosition[0],SpaceshipPosition[1],SpaceshipPosition[2],\
              0,1,0)
def Draw(Window):
    global camerapos
    #====FIRST PASS====
    
    #Global.  This setup prevents depthmap from
    #being made repeatedly--just updated.  This
    #is vastly more efficent.  
    global depthmap
    #Render the light's view of the occluders to a texture.
    depthmap,proj,view = glLibMakeDepthMap(Light1,LightView,SpaceshipPosition,depthmap,DrawOccluders,offset=1.0,filtering=False)
    if filtering: depthmap.filtering(GLLIB_FILTER,False)
    else: depthmap.filtering(False,False)
    
    #====SECOND PASS====
    
    #The screen must now be cleared again
    Window.clear()
    View3D.set_view()
    camerapos = [SpaceshipPosition[0] + CameraRadius*cos(radians(CameraRotation[0]))*cos((radians(CameraRotation[1]))),
                 SpaceshipPosition[1] + CameraRadius*sin(radians(CameraRotation[1])),
                 SpaceshipPosition[2] + CameraRadius*sin(radians(CameraRotation[0]))*cos((radians(CameraRotation[1])))]
    SetCamera()
    
    Light1.set()
    #Draw a sphere at the light's location just for
    #reference
    Light1.draw_as_point(10)

    #Draw a view frustum for the light for reference
    if draw_light_frustum:
        nearfrust,farfrust = glLibGetFrustumPoints(LightView,Light1.get_pos(),SpaceshipPosition,[0.0,1.0,0.0])
        glDisable(GL_TEXTURE_2D)
        glDisable(GL_LIGHTING)
        glBegin(GL_LINES)
        #draw view direction ray
        glColor3f(1.0, 1.0, 0.0)
        glVertex3f(*Light1.get_pos()); glVertex3f(*sc_vec(-9999.0,normalize(vec_subt(Light1.get_pos(),SpaceshipPosition))))
        #draw corner rays of frustum
        glColor4f(1.0, 1.0, 0.0, 0.2)
        #draw lines to near clipping plane
        glVertex3f(*Light1.get_pos()); glVertex3f(*nearfrust[0])
        glVertex3f(*Light1.get_pos()); glVertex3f(*nearfrust[1])
        glVertex3f(*Light1.get_pos()); glVertex3f(*nearfrust[2])
        glVertex3f(*Light1.get_pos()); glVertex3f(*nearfrust[3])
        #draw lines from far clipping plane to effective infinity
        glVertex3f(*farfrust[0]); glVertex3f(*sc_vec(-9999.0,normalize(vec_subt(Light1.get_pos(),farfrust[0]))))
        glVertex3f(*farfrust[1]); glVertex3f(*sc_vec(-9999.0,normalize(vec_subt(Light1.get_pos(),farfrust[1]))))
        glVertex3f(*farfrust[2]); glVertex3f(*sc_vec(-9999.0,normalize(vec_subt(Light1.get_pos(),farfrust[2]))))
        glVertex3f(*farfrust[3]); glVertex3f(*sc_vec(-9999.0,normalize(vec_subt(Light1.get_pos(),farfrust[3]))))
        #draw corner lines of frustum
        glColor4f(1.0, 1.0, 0.0, 1.0)
        glVertex3f(*nearfrust[0]);glVertex3f(*farfrust[0])
        glVertex3f(*nearfrust[1]);glVertex3f(*farfrust[1])
        glVertex3f(*nearfrust[2]);glVertex3f(*farfrust[2])
        glVertex3f(*nearfrust[3]);glVertex3f(*farfrust[3])
        #draw near clipping plane
        glVertex3f(*nearfrust[0]);glVertex3f(*nearfrust[1])
        glVertex3f(*nearfrust[1]);glVertex3f(*nearfrust[2])
        glVertex3f(*nearfrust[2]);glVertex3f(*nearfrust[3])
        glVertex3f(*nearfrust[3]);glVertex3f(*nearfrust[0])
        #draw far clipping plane
        glVertex3f(*farfrust[0]);glVertex3f(*farfrust[1])
        glVertex3f(*farfrust[1]);glVertex3f(*farfrust[2])
        glVertex3f(*farfrust[2]);glVertex3f(*farfrust[3])
        glVertex3f(*farfrust[3]);glVertex3f(*farfrust[0])
        glEnd()
        glColor3f(1.0, 1.0, 1.0)
        glEnable(GL_LIGHTING)
        glEnable(GL_TEXTURE_2D)

    #Draw the objects with shadows
    glLibUseShader(ShadowDrawingShader)
    ShadowDrawingShader.pass_texture(DiffuseTexture,1)
    #This texture is the "projected" texture that's
    #cast on the object.  In the shader, of course,
    #it's tex2D_2.  It's not necessary for simple
    #shadowing (as in mode 1).  Press "p" to engage.
    if use_projection_texture:
        ShadowDrawingShader.pass_texture(ProjectionTexture,2)
        ShadowDrawingShader.pass_bool("use_proj_tex",True)
    else:
        ShadowDrawingShader.pass_bool("use_proj_tex",False)
    #Send the shadow textures to "Shader" starting
    #with shadtex2.  "TransformOccluders" rotates the
    #shadow matrix so that the spaceship can be rotated
    #and the shadows still be correct.  Pass "1",
    #because this is the first depth effect (i.e., the
    #the first shadowmap.
    glPushMatrix()
    glLibUseDepthMaps([[depthmap,proj,view]],1,3,ShadowDrawingShader,TransformOccluders)
    DrawOccluders()
    glPopMatrix()
    
    ShadowDrawingShader.pass_texture(FloorTexture,1)
    #Send the shadow textures to "Shader" starting
    #with shadtex2.  Because the floor does not get
    #transformed, lambda:0 (null function) is passed.
    glLibUseDepthMaps([[depthmap,proj,view]],1,3,ShadowDrawingShader,lambda:0)
    Plane.draw()

    glLibUseShader(None)

    #Draw a quad showing a piece of "stained glass"
    #through which the light will be shining.  Has
    #no function to the algorithm whatsoever.  Just
    #helps you imagine how to use the effect.
    if use_projection_texture:
        vec = normalize(vec_subt(Light1.get_pos(),SpaceshipPosition))
        #The "window" object is 1.0 (2*0.5) on a side.
        #Therefore, because the light's viewing angle
        #is 35 degrees, a convincing distance must be:
        distance = 0.5/tan(radians(35.0/2.0))
        pos = vec_add(Light1.get_pos(),sc_vec(-distance,vec))
        glPushMatrix()
        glTranslatef(*pos)
        glRotatef(90.0-degrees(atan2(vec[1],length([vec[0],vec[2]]))),1,0,0)
        glBlendFunc(GL_ONE,GL_ONE)
        glDisable(GL_LIGHTING)
        glLibAlpha(0.3)
        StainedGlassWindow.draw()
        glLibAlpha(1.0)
        glEnable(GL_LIGHTING)
        glBlendFunc(GL_SRC_ALPHA,GL_ONE_MINUS_SRC_ALPHA)
        glPopMatrix()

    #Draw a little inset frame showing the contents of the light's view depth buffer
    View2D = glLibView2D((0,0,128,128))
    View2D.set_view()
    glDisable(GL_LIGHTING)
    glLibDrawScreenQuad(texture=depthmap)
    glEnable(GL_LIGHTING)

    Window.flip()
