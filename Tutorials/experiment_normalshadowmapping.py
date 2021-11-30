#Tutorial by Ian Mallett

#Controls:
#ESC           - Return to menu
#LCLICK + DRAG - Rotate camera
#RCLICK + DRAG - Rotate spaceship
#SROLL WHEEL   - Zoom

import sys,os
sys.path.append(os.path.split(sys.path[0])[0])
from glLib import *

def init(Screen):
    global shadowmode, shadowoffset, shadervariable
    global View3D, LightView
    global Spaceship, Plane
    global SpaceshipPosition, SpaceshipRotation, CameraRotation, CameraRadius
    global Light1, fbo
    global ShaderShadow, ShaderNormal, ShaderNormalShadow
    global DiffuseTexture, FloorTexture
    View3D = glLibView3D((0,0,Screen[0],Screen[1]),45,0.1,20)
    shadowmode = 2
    shadowoffset = 0.0
##    shadowmapsize = 4
    shadowmapsize = 8
##    shadowmapsize = 16
##    shadowmapsize = 32
##    shadowmapsize = 64
##    shadowmapsize = 128
##    shadowmapsize = 256
##    shadowmapsize = 512
##    shadowmapsize = 1024
##    shadowmapsize = 2048
##    shadowmapsize = 4096
##    LightView = glLibView3D((0,0,shadowmapsize,shadowmapsize),20,7.8,9.5)
    LightView = glLibView3D((0,0,shadowmapsize,shadowmapsize),20,8.5,12.0)

    Spaceship = glLibObject("data/objects/Spaceship.obj",GLLIB_FILTER,GLLIB_MIPMAP_BLEND)
    Spaceship.build_vbo()

    FloorTexture = glLibTexture2D("data/floor.jpg",[0,0,512,512],GLLIB_RGBA,GLLIB_FILTER,GLLIB_MIPMAP_BLEND)

    Plane = glLibPlane(5,(0,1,0),FloorTexture,10)

    DiffuseTexture = glLibTexture2D("data/plates.jpg",[0,0,512,512],GLLIB_RGBA,GLLIB_FILTER,GLLIB_MIPMAP_BLEND)

    SpaceshipPosition = [0.0,1.0,0.0]
    SpaceshipRotation = [0,0]
    CameraRotation = [90,23]
    CameraRadius = 10.0

    fbo = glLibFBO((shadowmapsize,shadowmapsize)) #remember to change enable if these rendertargets change!
    fbo.add_render_target(1,type=GLLIB_DEPTH) #nonlinear depth
    fbo.add_render_target(2,type=GLLIB_RGB) #linear depth (1 float)
    fbo.add_render_target(3,type=GLLIB_RGB) #normal

    glEnable(GL_LIGHTING)
    Light1 = glLibLight(1)
    Light1.set_pos([2,8,5])
    Light1.set_type(GLLIB_POINT_LIGHT)
    Light1.enable()

    pygame.mouse.get_rel()

    pack_unpack_functions = """
    //http://www.gamedev.net/topic/442138-packing-a-float-into-a-a8r8g8b8-texture-shader/
    vec4 pack4_float(float input) {
        return mod( input*vec4(1.0,256.0,65536.0,16777216.0), 1.0 );
    }
    float unpack4_float(vec4 input) {
        return dot(input,vec4(1.0,0.00390625,0.0000152587890625,0.000000059604644775390625));
    }
    vec3 pack3_float(float input) {
        return mod( input*vec3(1.0,256.0,65536.0), 1.0 );
    }
    float unpack3_float(vec3 input) {
        return dot(input,vec3(1.0,0.00390625,0.0000152587890625));
    }"""
    color_with_diffuse_texture = """
    color.rgb += ambient_color.rgb*light_ambient(light1).rgb;
    color.rgb += diffuse_color.rgb*light_diffuse(light1).rgb;
    color.rgb += specular_color.rgb*light_specular_ph(light1).rgb;
    
    color.rgb *= texture2D(tex2D_1,uv).rgb;"""

    ShaderShadow = glLibShader()
    ShaderShadow.render_equation(color_with_diffuse_texture+"""
    float shadowed_value = shadowed(tex2D_2,depth_coord_1,false);
    color.rgb *= clamp(shadowed_value,0.5,1.0);""")
    errors = ShaderShadow.compile()
    print(errors)

    ShaderNormalShadow = glLibShader()
    ShaderNormalShadow.user_variables("""
    uniform int var;
    const vec2 tex_size = vec2("""+str(float(shadowmapsize))+","+str(float(shadowmapsize))+""");""")
    ShaderNormalShadow.fragment_extension_functions(pack_unpack_functions)
    ShaderNormalShadow.render_equation(color_with_diffuse_texture+"""
    vec3 eye_normal = 2.0*texture2DProj(tex2D_4,depth_coord_1).rgb - vec3(1.0);

    if (depth_coord_1.w>0.0) {
        vec2 testcoord = depth_coord_1.xy/depth_coord_1.w;
        
        color.rgb *= 0.1;
        if (testcoord.x>=0.0) { if (testcoord.x<=1.0) { if (testcoord.y>=0.0) { if (testcoord.y<=1.0) {
            color.rgb *= 10.0;

            //texture2DProj is the same as texture2D, with depth_coord_1.xy/depth_coord_1.w for coordinates
            float depth_sample;
            vec2 coords = depth_coord_1.xy / depth_coord_1.w;
            vec2 nearest_coords = (round(coords*tex_size+vec2(0.5))-vec2(0.5))/tex_size; //texel's exact center
            if (var==0) depth_sample =               texture2D(tex2D_2,nearest_coords).r ;
            else        depth_sample = unpack4_float(texture2D(tex2D_3,nearest_coords)  );

            //Light's eye space plane:
            //eye_normal.x*x + eye_normal.y*y + eye_normal.z*z = depth_sample

            //We will take the fragment's x,y coordinates and put them into the above equation.  
            //In this way, we can solve for z, the interpolated depth.
            float plane_interpolated_z = (depth_sample-dot(eye_normal.xy,coords)) / eye_normal.z;
            
            float depth_fragment = clamp(depth_coord_1.z/depth_coord_1.w,0.0,1.0);

            //vec2 offset = mod(coord*tex_size,vec2(1.0)) - vec2(0.5);
            
            if (depth_fragment>plane_interpolated_z) color.rgb *= 0.5;

            //color.rg = abs(offset);
            //color.b = 0.0;
            //color.rgb = vec3(depth_sample);
            //color.rg = nearest_coords;
            color.rgb = vec3(plane_interpolated_z);
        }}}}
    }""")
    errors = ShaderNormalShadow.compile()
    #Textures:
    #1st = diffuse
    #2nd = nonlinear light depth
    #3rd = encoded linear light depth
    #4th = normals from light view
    print(errors)

    shadervariable = 0 #using nonlinear encoded depthmap.  Hopefully shouldn't make much difference.

    ShaderNormal = glLibShader()
    ShaderNormal.user_variables("varying float linear_depth; uniform mat4 normals_model_matrix;")
##    ShaderNormal.vertex_transform("linear_depth = -vVertex.z;")
    ShaderNormal.post_vertex("linear_depth = (-vVertex.z-"+str(LightView.near)+")/("+str(LightView.far)+"-"+str(LightView.near)+");")
    ShaderNormal.fragment_extension_functions(pack_unpack_functions)
    ShaderNormal.render_equation("""
    //color is the nonlinear depth
    color2 = pack4_float(linear_depth);

    //vec3 world_normal = vec4( normals_model_matrix * vec4(realnorm,1.0) ).rgb;
    //color3.rgb = 0.5 * (world_normal+vec3(1.0));
    color3.rgb = 0.5 * (normal+vec3(1.0));""") #realnorm is object space
    ShaderNormal.render_targets(3)
    errors = ShaderNormal.compile()
    print(errors)

def quit():
    global Light1, Spaceship
    glDisable(GL_LIGHTING)
    del Light1
    del Spaceship

printed_shadowmode = False
def GetInput():
    global shadowmode, shadowoffset, shadervariable, printed_shadowmode
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
                printed_shadowmode = False
            elif event.key == K_v:
                if shadervariable == 0:
                    shadervariable = 1
                    print("Using linear depth texture")
                elif shadervariable == 1:
                    shadervariable = 0
                    print("Using nonlinear depth texture")
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
def DrawOccluders():
    TransformOccluders()
##    Spaceship.draw_vbo()
def Draw(Window):
    global printed_shadowmode
    #====FIRST PASS====

    fbo.enable([1]) #nonlinear depth
    glClear(GL_DEPTH_BUFFER_BIT)
    
    fbo.enable([2]) #linear depth
    glClearColor(1,1,1,1)
    glClear(GL_COLOR_BUFFER_BIT|GL_DEPTH_BUFFER_BIT)
    glClearColor(0,0,0,1)
    
    fbo.enable([3]) #normals
    glClear(GL_COLOR_BUFFER_BIT|GL_DEPTH_BUFFER_BIT)
    
    fbo.enable([1,2,3])
    
    glLibPushView()
    
    proj,view = glLibInternal_set_proj_and_view_matrices(LightView,Light1.get_pos(),[0,1,0])

    glDisable(GL_BLEND)
    if shadowmode==1:
        glEnable(GL_POLYGON_OFFSET_FILL);glPolygonOffset(shadowoffset,shadowoffset);
        
    glLibUseShader(ShaderNormal)

    glMatrixMode(GL_TEXTURE); glPushMatrix(); glLoadIdentity()
    ShaderNormal.pass_mat4("normals_model_matrix",glLibMathGetListMatrix(glGetFloatv(GL_TEXTURE_MATRIX)))
    glPopMatrix(); glMatrixMode(GL_MODELVIEW)
    Plane.draw()
    
    glMatrixMode(GL_TEXTURE); glPushMatrix(); glLoadIdentity(); TransformOccluders()
    ShaderNormal.pass_mat4("normals_model_matrix",glLibMathGetListMatrix(glGetFloatv(GL_TEXTURE_MATRIX)))
    glPopMatrix(); glMatrixMode(GL_MODELVIEW)
    DrawOccluders()
    
    glLibUseShader(None)
    
    if shadowmode==1:
        glPolygonOffset(0.0,0.0);glDisable(GL_POLYGON_OFFSET_FILL)
    glEnable(GL_BLEND)
    
    glLibPopView()

    fbo.disable()
    
    #====SECOND PASS====

    Window.clear()
    View3D.set_view()
    camerapos = [0 + CameraRadius*cos(radians(CameraRotation[0]))*cos((radians(CameraRotation[1]))),
                 1 + CameraRadius*sin((radians(CameraRotation[1]))),
                 0 + CameraRadius*sin(radians(CameraRotation[0]))*cos((radians(CameraRotation[1])))]
    gluLookAt(camerapos[0],camerapos[1],camerapos[2], 0,1,0, 0,1,0)
    
    Light1.set()
    Light1.draw_as_sphere()

    if shadowmode == 1:
        if not printed_shadowmode:
            print("Using conventional SM algorithm (%d)!" % (shadowmode))
            printed_shadowmode = True
        glLibUseShader(ShaderShadow)
        
        ShaderShadow.pass_texture(DiffuseTexture,1)
        glPushMatrix()
        glLibUseDepthMaps([[fbo.get_texture(1),proj,view]],1,2,ShaderShadow,TransformOccluders)
        DrawOccluders()
        glPopMatrix()
        
        ShaderShadow.pass_texture(FloorTexture,1)
        glLibUseDepthMaps([[fbo.get_texture(1),proj,view]],1,2,ShaderShadow,lambda:0)
        Plane.draw()
    elif shadowmode == 2:
        if not printed_shadowmode:
            print("Using normal-SM algorithm (%d)!" % (shadowmode))
            printed_shadowmode = True
        glLibUseShader(ShaderNormalShadow)
        ShaderNormalShadow.pass_int("var",shadervariable);
        ShaderNormalShadow.pass_texture(fbo.get_texture(3),4) #normals
        
        shadowmap_data = [   [ [fbo.get_texture(1),fbo.get_texture(2)], proj, view ]   ] #nonlinear depth, encoded linear depth
        
        ShaderNormalShadow.pass_texture(DiffuseTexture,1)
        glPushMatrix()
        glLibUseDepthMaps(shadowmap_data,1,2,ShaderNormalShadow,TransformOccluders)
        DrawOccluders()
        glPopMatrix()
        
        ShaderNormalShadow.pass_texture(FloorTexture,1)
        glLibUseDepthMaps(shadowmap_data,1,2,ShaderNormalShadow,lambda:0)
        Plane.draw()

    glLibUseShader(None)

    #Draw a little inset frame showing the contents of the light's view depth buffer
    View2D = glLibView2D((0,0,128,128))
    View2D.set_view()
    glDisable(GL_LIGHTING)
    if   shadervariable==0 or shadowmode == 1:
        glLibDrawScreenQuad(texture=fbo.get_texture(1))
    elif shadervariable==1:
        glDisable(GL_BLEND)
        glLibDrawScreenQuad(texture=fbo.get_texture(2))
        glEnable(GL_BLEND)
    glEnable(GL_LIGHTING)

    Window.flip()
