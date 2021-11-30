#Tutorial by Ian Mallett

#Controls:
#ESC           - Return to menu
#LCLICK + DRAG - Rotate camera
#RCLICK + DRAG - Rotate object
#SROLL WHEEL   - Zoom
#e + UP        - Increase eta (ratio of refractive indices, means refractive index of spaceship gets small)
#e + DOWN      - Decrease eta (ratio of refractive indices, means refractive index of spaceship gets larger)
#0             - Make object transparent
#1             - Make object red-transparent
#2             - Make object green-transparent
#3             - Make object blue-transparent

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
#WRONG THIS IS FOR NORMALMAPPING

import sys,os
sys.path.append(os.path.split(sys.path[0])[0])
from glLib import *

def init(Screen):
    global ShadowCausticLightView, LightView, View2D, View3D, CubemapView
    global Rays, Plane, MaterialPlane, Objects, CausticGrid
    global light_caustic_size, depth_peels, ray_light_intensity, eta, object_color, current_object, causticparticlesize, causticparticleintensity
    global ObjectRotation, CameraRotation, CameraRadius, objectposition, Cubemap, GlassTex, depthmap, causticmap
    global Light1
    global ObjectShader, PositionNormalShader, PlaneShader, AccumulationShader, CausticPositionNormalShader, CausticmapGeneratorShader
    global posnorm_fbo1, posnorm_fbo2, CausticMapFBO, SceneFBO
    scalar = 1
    light_caustic_size = 64*scalar
    shadowcaustic_size = 512
    ray_light_intensity = 0.01/(4*scalar)
    causticgridres = 512
    causticmapres = 512
    causticparticlesize = 3.0
    causticparticleintensity = 0.04
##    causticparticlesize = 6.0
##    causticparticleintensity = 0.01
##    causticparticlesize = 12.0
##    causticparticleintensity = 0.0025
    
    ShadowCausticLightView = glLibView3D((0,0,shadowcaustic_size,shadowcaustic_size),19,5.0,15.0)
    LightView = glLibView3D((0,0,light_caustic_size,light_caustic_size),19,5.0,15.0)
    View2D = glLibView2D((0,0,Screen[0],Screen[1]))
    View3D = glLibView3D((0,0,Screen[0],Screen[1]),45,0.1,250)
    
    CubemapView = glLibView3D((0,0,512,512),90)

##    GlassTex = glLibTexture2D("data/glass.png",GLLIB_ALL,GLLIB_RGB,GLLIB_FILTER,GLLIB_MIPMAP_BLEND)

    Objects = [glLibObject("data/objects/Spaceship.obj",GLLIB_FILTER,GLLIB_MIPMAP_BLEND),
               glLibObject("data/objects/sphere.obj",GLLIB_FILTER,GLLIB_MIPMAP_BLEND),
               glLibObject("data/objects/trisphere.obj",GLLIB_FILTER,GLLIB_MIPMAP_BLEND)]
    for object in Objects: object.build_vbo()
    object_color = [1.0,0.0,0.0]

    FloorTexture = glLibTexture2D("data/floor.jpg",[0,0,512,512],GLLIB_RGBA,GLLIB_FILTER,GLLIB_MIPMAP_BLEND)
    FloorTexture.anisotropy(GLLIB_MAX)
    Plane = glLibPlane(5,(0,1,0),False,10)
    MaterialPlane = glLibPlane(5,(0,1,0),FloorTexture,10)
    
    Cubemap = glLibTextureCube([None]*6,(0,0,512,512),GLLIB_RGB,GLLIB_FILTER)
    Cubemap.edge(GLLIB_CLAMP)

    Rays = glLibGrid3DLines([light_caustic_size+1,light_caustic_size+1,2])

    ObjectRotation = [0,0]
    CameraRotation = [90,23]
    CameraRadius = 10.0
    objectposition = [0.0,2.0,0.0]
    current_object = 1
    depth_peels = 2
    eta = 1.0/1.33

    glEnable(GL_LIGHTING)
    Light1 = glLibLight(1)
    Light1.set_diffuse([1.0,1.0,0.8])
##    Light1.set_pos([5,5,5])
##    Light1.set_pos([5,1,5])
##    Light1.set_pos([0.0,1.0,8.124])
    Light1.set_pos([0.0,9.124,0.01])
    Light1.set_spot_dir([0.0,-1.0,0.0])
    Light1.set_spot_angle(19.0)
    Light1.set_spot_ex(0.5)
    Light1.set_type(GLLIB_POINT_LIGHT)
    Light1.enable()

    #Prepare the caustics
    glLibPrepareCaustics()
    #Create a grid so that the caustic effects are evenly distributed.  
    CausticGrid = glLibGrid2D(causticgridres)

    depthmap = None
    causticmap = None

    posnorm_fbo1 = glLibFBO((shadowcaustic_size,shadowcaustic_size))
    posnorm_fbo1.add_render_target(1,GLLIB_RGB)
    posnorm_fbo1.add_render_target(2,GLLIB_RGB)
    posnorm_fbo1.textures[1].edge(GLLIB_CLAMP)
    posnorm_fbo1.textures[2].edge(GLLIB_CLAMP)
    posnorm_fbo2 = glLibFBO((shadowcaustic_size,shadowcaustic_size))
    posnorm_fbo2.add_render_target(1,GLLIB_RGB)
    posnorm_fbo2.add_render_target(2,GLLIB_RGB)
    posnorm_fbo2.textures[1].edge(GLLIB_CLAMP)
    posnorm_fbo2.textures[2].edge(GLLIB_CLAMP)

    CausticMapFBO = glLibFBO((shadowcaustic_size,shadowcaustic_size))
    CausticMapFBO.add_render_target(1,GLLIB_RGB,GLLIB_FILTER,precision=32)

    SceneFBO = glLibFBO(Screen)
    SceneFBO.add_render_target(1,GLLIB_RGB,precision=16)

    pygame.mouse.get_rel()

    AccumulationShader = glLibShader()
    AccumulationShader.user_variables("""
    uniform vec3 lightpos;
    uniform vec3 object_color;
    uniform vec4 lightcolor;
    uniform mat4 inv_mat;
    uniform int stage;
    uniform float eta;
    varying float continuing;
    varying vec2 coord;
    uniform mat4 modelmatrix;""")
    AccumulationShader.vertex_extension_functions("""
    vec4 at_depth(vec2 location, float depth) {
        vec4 window_vec = vec4((2.0*location.x)-1.0,(2.0*location.y)-1.0,(2.0*depth)-1.0,1.0);
        return inv_mat*window_vec;
    }
    vec4 from_sample(sampler2D texture, vec2 location) {
        vec3 sample = texture2D(texture,location).rgb;
        float dist = 0.0;
        if      (sample.g==0.0) { dist = sample.r; } //receiver only
        else if (sample.g==1.0) { dist = sample.b; } //(reflective and receiver) or none
        else                    { dist = sample.b; } //(refractive and receiver) or none
        if (dist==0.0) { dist = 1.0; } //none, set to far clip
        vec4 window_vec = vec4((2.0*location.x)-1.0,(2.0*location.y)-1.0,(2.0*dist)-1.0,1.0);
        return inv_mat*window_vec;
    }
    vec4 from_sample_caster(sampler2D texture, vec2 location) {
        vec3 sample = texture2D(texture,location).rgb;
        float dist = 0.0;
        if      (sample.g==0.0) { dist = 1.0; } //receiver only
        else if (sample.g==1.0) { dist = sample.b; } //(reflective and receiver) or none
        else                    { dist = sample.b; } //(refractive and receiver) or none
        vec4 window_vec = vec4((2.0*location.x)-1.0,(2.0*location.y)-1.0,(2.0*dist)-1.0,1.0);
        return inv_mat*window_vec;
    }""")
    AccumulationShader.vertex_transform("""
    continuing = 2.0;
    coord = vertex.xy;
    if (length(vertex.xy-vec2(0.5,0.5))>0.5) {
        continuing = 0.0;
    }
    else if (stage==1) {
        if (vertex.z==1.0) { vertex.xyz = lightpos; }
        else { vertex = from_sample(tex2D_2,coord); }
    }
    else {
        if (vertex.z==1.0) { vertex = from_sample_caster(tex2D_2,coord); }
        else {
            vertex = from_sample_caster(tex2D_2,coord);
            vec3 normal_sample = texture2D(tex2D_3,coord).rgb;
            vec3 normal = (modelmatrix*vec4(normalize(normal_sample-vec3(0.5)),1.0)).xyz;
            if (normal_sample!=vec3(0.0)) {
                vertex.xyz = vertex.xyz/vertex.w;
                vertex.w = 1.0;
                vec3 refractedray = refract(normalize(vertex.xyz-lightpos),normal,eta);
                vertex.xyz += 10.0*refractedray;
            }
        }
    }""")
    AccumulationShader.render_equation("""
    if (continuing>1.0) { color = lightcolor; }
    else { discard; }
    if (stage==2) { color.rgb = object_color; }
    //color.rgb *= texture2D(tex2D_1,coord).rgb;""")
    errors = AccumulationShader.compile()
    print(errors)

    ObjectShader = glLibShader()
    #Custom variables
    ObjectShader.user_variables("uniform float eta;uniform vec3 object_color;")
    ObjectShader.render_equation("""
    vec3 cubenorm = cubemap_normal();
    vec4 refractsample = cubemap_refract_sample(texCube_1,cubenorm,eta);
    color.rgb = refractsample.rgb*0.5;
    color.rgb += specular_color.rgb*light_specular_ph(light1).rgb;
    color.rgb *= object_color;""")
    #Because we have a cube map, we'll need to send it to texCube_1 in the shader.
    ObjectShader.max_textures_cube(1)
    errors = ObjectShader.compile()
    print(errors)

    PlaneShader = glLibShader()
    #Custom variables
    PlaneShader.user_variables("")
    PlaneShader.render_equation("""
    color.rgb = vec3(1.0);
    
    float shadowed_value = shadowed(tex2D_2,depth_coord_1,false)*light_spot(light1);
    color.rgb *= clamp(shadowed_value,0.2,1.0);
    vec3 caustic_value = 10.0*add_caustics(tex2D_3,depth_coord_1);
    
    color.r +=       caustic_value.r;
    color.g += clamp(caustic_value.r-1.0,0.0,1.0);
    color.b += clamp(caustic_value.r-1.0,0.0,1.0);
    
    color.r += clamp(caustic_value.g-1.0,0.0,1.0);
    color.g +=       caustic_value.g;
    color.b += clamp(caustic_value.g-1.0,0.0,1.0);
    
    color.r += clamp(caustic_value.b-1.0,0.0,1.0);
    color.g += clamp(caustic_value.b-1.0,0.0,1.0);
    color.b +=       caustic_value.b;

    color.rgb *= texture2D(tex2D_1,uv).rgb;""")
    errors = PlaneShader.compile()
    print(errors)

    #Shader for depth peeling
    CausticPositionNormalShader = glLibShader()
    CausticPositionNormalShader.use_prebuilt(GLLIB_POSITION_NORMAL_MAP)

    #Renders the caustic map
    CausticmapGeneratorShader = glLibShader()
    CausticmapGeneratorShader.use_prebuilt(GLLIB_CAUSTIC_MAP)

def quit():
    global Light1, Objects, posnorm_fbo1, posnorm_fbo2
    glDisable(GL_LIGHTING)
    del Light1
    for object in Objects: del object
to_update = ["pos/norm maps","shadowmap","causticmap","cubemap",
             "pos/norm maps","shadowmap","causticmap","cubemap",
             "pos/norm maps","shadowmap","causticmap","cubemap"]
def GetInput():
    global CameraRadius, eta, to_update, object_color, current_object
    mrel = pygame.mouse.get_rel()
    mpress = pygame.mouse.get_pressed()
    key = pygame.key.get_pressed()
    for event in pygame.event.get():
        if   event.type == QUIT: quit(); pygame.quit(); sys.exit()
        elif event.type == KEYDOWN:
            if   event.key == K_ESCAPE: return False
            elif event.key in [K_0 or K_KP0]: object_color = [1.0,1.0,1.0]; to_update.append("causticmap"); to_update.append("cubemap")
            elif event.key in [K_1 or K_KP1]: object_color = [1.0,0.0,0.0]; to_update.append("causticmap"); to_update.append("cubemap")
            elif event.key in [K_2 or K_KP2]: object_color = [0.0,1.0,0.0]; to_update.append("causticmap"); to_update.append("cubemap")
            elif event.key in [K_3 or K_KP3]: object_color = [0.0,0.0,1.0]; to_update.append("causticmap"); to_update.append("cubemap")
            elif event.key == K_o:
                current_object += 1
                if current_object == len(Objects)+1: current_object = 1
                to_update.append("pos/norm maps")
                to_update.append("shadowmap")
                to_update.append("causticmap")
                to_update.append("cubemap")
        elif event.type == MOUSEBUTTONDOWN:
            if   event.button == 5: CameraRadius += 1.0
            elif event.button == 4: CameraRadius -= 1.0
    #If the left mouse button is clicked,
    #rotate the camera.  Rotate the Object
    #if the right mouse button is pressed.
    if mpress[0]:
        CameraRotation[0] += mrel[0]
        CameraRotation[1] += mrel[1]
    if mpress[2]:
        ObjectRotation[0] += mrel[0]
        ObjectRotation[1] += mrel[1]
        to_update.append("pos/norm maps")
        to_update.append("shadowmap")
        to_update.append("causticmap")
        to_update.append("cubemap")
    if key[K_e]:
        if key[K_UP]: eta += 0.01
        if key[K_DOWN]: eta -= 0.01
        #clamp the refractive index to 1/1 and 1/4, meaning the
        #ship can have a refractive index of any number 1 to 4
        eta = clamp(eta,0.25,1.0)
        to_update.append("causticmap")
        to_update.append("cubemap") #'cause of what the difference in teh caustic map does

def SetCamera():
    camerapos = [objectposition[0] + CameraRadius*cos(radians(CameraRotation[0]))*cos((radians(CameraRotation[1]))),
                 objectposition[1] + CameraRadius*sin((radians(CameraRotation[1]))),
                 objectposition[2] + CameraRadius*sin(radians(CameraRotation[0]))*cos((radians(CameraRotation[1])))]
    gluLookAt(camerapos[0],camerapos[1],camerapos[2], objectposition[0],objectposition[1],objectposition[2], 0,1,0)
def RotateObject():
    glRotatef(ObjectRotation[0],0,1,0)
    glRotatef(ObjectRotation[1],1,0,0)
def TransformObject():
    glTranslatef(*objectposition)
    RotateObject()
    if current_object == 3: glScalef(0.5,0.5,0.5)
def DrawObject(withmaterial=False):
    glPushMatrix()
    TransformObject()
    if withmaterial: Objects[current_object-1].draw_vbo(indices=[1])
    else: Objects[current_object-1].draw_vbo()
    glPopMatrix()
sm_perspective_proj_mat, sm_perspective_view_mat = None, None
def DrawPlane():
    glLibUseShader(PlaneShader)
    if sm_perspective_proj_mat != None and sm_perspective_view_mat != None:
        glLibUseDepthMaps([[depthmap,sm_perspective_proj_mat,sm_perspective_view_mat]],1,2,PlaneShader,lambda:0)
    PlaneShader.pass_texture(causticmap,3)
    MaterialPlane.draw()
    glLibUseShader(None)
def Draw(Window):
    global depthmap, causticmap, to_update, causticposmaps, causticnormmaps, sm_perspective_proj_mat, sm_perspective_view_mat
    lightpos = Light1.get_pos()

    #Compute an inverse matrix for later use
    Window.clear()
    LightView.set_view()
    gluLookAt(lightpos[0],lightpos[1],lightpos[2],0,0,0,0,1,0)
    first_pass_view_data = list(map(glLibMathRotateMatrix,[glGetFloatv(GL_PROJECTION_MATRIX),glGetFloatv(GL_MODELVIEW_MATRIX)]))
    mp_mat = np.matrix(first_pass_view_data[0]) * np.matrix(first_pass_view_data[1])
    inv_mat = mp_mat.I

    while len(to_update) > 0:
        
        #First pass
        #Update cubemap, if the rest of the scene has been rendered
        if to_update[0] == "cubemap":
            if "shadowmap" not in to_update and "causticmap" not in to_update:
                glDisable(GL_LIGHTING)
                glClearColor(0.3,0.3,0.3,1.0)
                glLibUpdateCubeMap(Cubemap,CubemapView,objectposition,DrawPlane,update=GLLIB_ALL)
                glClearColor(0.0,0.0,0.0,1.0)
                glEnable(GL_LIGHTING)
                to_update = to_update[1:]
            else:
                to_update = to_update[1:]
                to_update.append("cubemap") #update this last

        #Second pass
        #Gets a shadowmap.  With some effort, a positionmap from the next pass could be repurposed
        #to save a pass.  Here, the extra pass is just done for clarity.
        elif to_update[0] == "shadowmap":
            depthmap,sm_perspective_proj_mat,sm_perspective_view_mat = glLibMakeDepthMap(Light1,ShadowCausticLightView,objectposition,depthmap,DrawObject,offset=1.0,filtering=GLLIB_FILTER)
            to_update = to_update[1:]

        #Second pass
        #The result of these passes are positionmaps and normalmaps of geometry from the light's perspective.
        elif to_update[0] == "pos/norm maps":
            glLibUseShader(None)
            causticposmaps,causticnormmaps = glLibCausticPositionNormalMapFBO(posnorm_fbo1,posnorm_fbo2,Light1,ShadowCausticLightView,[0,0,0],
                                                                              depth_peels,CausticPositionNormalShader,\
                                                                              lambda:Plane.draw(),DrawObject,lambda:0)
            to_update = to_update[1:]

        #Third pass
        elif to_update[0] == "causticmap":
            causticmap = glLibCausticMapFBO(CausticMapFBO,Light1,ShadowCausticLightView,objectposition,TransformObject,\
                                            CausticmapGeneratorShader,CausticGrid,1.0,\
                                            causticparticlesize,[ [sc_vec(causticparticleintensity,object_color),eta] ],\
                                            causticposmaps[:1],causticnormmaps[:1])
            to_update = to_update[1:]

    #Fourth pass
    #Draws the scene.  We do this in an FBO so that we can use a larger
    #color bit precision.  This allows faint rays (intensity < 0.5/255.0)
    #to show up, instead of disappearing entirely.  Larger precision of
    #course makes the drawing slower, as does the extra pass.  16-bit was
    #used here because it offers a good compromise.  
    SceneFBO.enable([1])
    Window.clear()
    View3D.set_view()
    SetCamera()
    Light1.set()
    Light1.draw_as_point(10)
    #   Draw caster
    glLibUseShader(ObjectShader)
    ObjectShader.pass_vec3("object_color",object_color)
    glPushMatrix()
    glLoadIdentity()
    RotateObject()
    #       Pass the cubemap matrix (contains the rotations only
    #       of the reflective and/or refractive object).
    ObjectShader.pass_mat4("transform_matrix",glGetFloatv(GL_MODELVIEW_MATRIX))
    ObjectShader.pass_texture(Cubemap,1)
    glPopMatrix()
    ObjectShader.pass_float("eta",eta)
    DrawObject()
    glLibUseShader(None)
    #   Draw receiver
    DrawPlane()
    #   Draws the scattered light
    glLineWidth(4)
    glDepthMask(False)
    glBlendFunc(GL_SRC_ALPHA,GL_ONE)
    glLibUseShader(AccumulationShader)
    glLibSendTransform(AccumulationShader,TransformObject,"modelmatrix")
    AccumulationShader.pass_float("eta",eta)
    AccumulationShader.pass_vec3("lightpos",lightpos)
    AccumulationShader.pass_vec3("object_color",object_color)
    AccumulationShader.pass_vec4("lightcolor",Light1.get_diffuse_color()+[ray_light_intensity])
    AccumulationShader.pass_mat4("inv_mat",inv_mat)
##    AccumulationShader.pass_texture(GlassTex,1)
    AccumulationShader.pass_int("stage",1)
    AccumulationShader.pass_texture(causticposmaps[0],2)
    Rays.draw()
    AccumulationShader.pass_int("stage",2)
    AccumulationShader.pass_texture(causticposmaps[0],2)
    AccumulationShader.pass_texture(causticnormmaps[0],3)
##    AccumulationShader.pass_texture(causticposmaps[1],4)
##    AccumulationShader.pass_texture(causticnormmaps[1],5)
    Rays.draw()
    glLibUseShader(None)
    glBlendFunc(GL_SRC_ALPHA,GL_ONE_MINUS_SRC_ALPHA)
    glDepthMask(True)
    glLineWidth(1)
    SceneFBO.disable()

    #Fifth pass
    #Draws the scene
    Window.clear()
    glDisable(GL_LIGHTING)
    glLibUseShader(None)
    View2D.set_view()
    glLibDrawScreenQuad(texture=SceneFBO.get_texture(1))
    glEnable(GL_LIGHTING)

    #Flip to screen
    Window.flip()
