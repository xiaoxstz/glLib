#Tutorial by Ian Mallett

#Controls:
#ESC           - Return to menu
#LCLICK + DRAG - Rotate camera
#RCLICK + DRAG - Rotate object
#SROLL WHEEL   - Zoom

#Theory:
#Depth of field can make any 3D scene look more realistic.
#To do this in realtime, we base the approach on the
#observation that objects out of focus are blurry--that
#is, objects of a different depth than the focal length
#are blurred.  In real life, this blurriness comes from a
#scene convolution with the camera's lens area.  To fake
#this, we'll just blur everything that's not in focus.
#To prevent color bleeding, the post process additively
#blends a matrix of pixels together as point sprites.

import sys,os
sys.path.append(os.path.split(sys.path[0])[0])
from glLib import *

def init(Screen):
    global View2D, View3D, Light1, ShaderObject, ShaderDOF
    global Object, Plane
    global ObjectRotation
    global CameraRotation, CameraRadius
    global fbo
    global points

    View2D = glLibView2D((0,0,Screen[0],Screen[1]))
    View3D = glLibView3D((0,0,Screen[0],Screen[1]),45,0.1,20)

    Object = glLibObject("data/objects/Spaceship.obj",GLLIB_FILTER,GLLIB_MIPMAP_BLEND)
    Object.build_vbo()

    FloorTexture = glLibTexture2D("data/floor.jpg",[0,0,512,512],GLLIB_RGBA,GLLIB_FILTER,GLLIB_MIPMAP_BLEND)
    Plane = glLibPlane(5,(0,1,0),FloorTexture,10)

    ObjectRotation = [0,0]
    CameraRotation = [90,23]
    CameraRadius = 5.0

    glEnable(GL_LIGHTING)
    Light1 = glLibLight(1)
    Light1.set_pos([0,10,0])
    Light1.set_type(GLLIB_POINT_LIGHT)
    Light1.enable()

    fbo = glLibFBO(Screen)
    fbo.add_render_target(1,GLLIB_RGB)
    fbo.add_render_target(2,GLLIB_DEPTH)

##    points = glLibGrid2D([Screen[0]/16,Screen[1]/16])
    points = glLibGrid2D(Screen)

    pygame.mouse.get_rel()

    ShaderObject = glLibShader()
    ShaderObject.render_equation("""
    color.rgb += ambient_color.rgb*light_ambient(light1).rgb;
    color.rgb += diffuse_color.rgb*light_diffuse(light1).rgb;
    color.rgb += specular_color.rgb*light_specular_ph(light1).rgb;
    color.rgb *= texture2D(tex2D_1,uv).rgb;""")
    ShaderObject.render_targets(2)
    errors = ShaderObject.compile()
##    ShaderObject.print_fragment()
    print(errors)
##    if errors != "":
##        pygame.quit()
##        raw_input(errors)
##        sys.exit()
##    else:
##        print("No errors to report with object shader (fakedepthoffield.py)!")

    ShaderDOF = glLibShader()
    ShaderDOF.user_variables("""
    varying vec2 scene_pos;
    varying float pi_r_sq;
    const vec2 screen = vec2("""+str(float(Screen[0]))+","+str(float(Screen[1]))+""");
    const float size = 1.0;
    const float pi = 3.14159265358979323846264;
    float focal_depth = 0.5;""")
    ShaderDOF.vertex_transform("""
    scene_pos = vertex.xy;
    vertex.xy *= screen-vec2(1.0,1.0);
    vertex.xy += 0.5;
    scene_pos *= 1.0 - 1.0/screen;
    scene_pos += 0.5 / screen;""")
    ShaderDOF.vertex_extension_functions("float depth_from_depthbuffer(float depth,float near,float far) { return ((-(far*near)/((depth*(far-near))-far))-near)/(far-near); }")
    ShaderDOF.post_vertex("""
    float depth = depth_from_depthbuffer(texture2D(tex2D_2,scene_pos).r,"""+str(float(View3D.near))+","+str(float(View3D.far))+""");
    float diameter = 1.0 + 10.0*abs(depth-focal_depth);
    gl_PointSize = diameter;
    pi_r_sq = pi * (diameter/2.0) * (diameter/2.0);""")
    ShaderDOF.render_equation("""
    vec2 v_rot = normalize(vertex.zw);
    vec4 l_uv = vec4(0.0,0.0,gl_PointCoord.xy);
    l_uv.zw-=vec2(0.5,0.5);l_uv.x=l_uv.z*v_rot.x;l_uv.y=l_uv.w*v_rot.x;l_uv.x-=l_uv.w*v_rot.y;l_uv.y+=l_uv.z*v_rot.y;
    if (length(l_uv.xy)>0.5) discard;
    
    color.rgb = texture2D(tex2D_1,scene_pos).rgb / pi_r_sq;""")
    errors = ShaderDOF.compile()
##    ShaderDOF.print_fragment()
    print(errors)
##    if errors != "":
##        pygame.quit()
##        raw_input(errors)
##        sys.exit()
##    else:
##        print("No errors to report with DOF shader (fakedepthoffield.py)!")

def quit():
    global Light1, Object
    glDisable(GL_LIGHTING)
    del Light1
    del Object

def GetInput():
    global CameraRadius
    mrel = pygame.mouse.get_rel()
    mpress = pygame.mouse.get_pressed()
    for event in pygame.event.get():
        if event.type == QUIT: quit(); pygame.quit(); sys.exit()
        if event.type == KEYDOWN and event.key == K_ESCAPE: return False
        if event.type == MOUSEBUTTONDOWN:
            if event.button == 5: CameraRadius += .2
            if event.button == 4: CameraRadius -= .2
    if mpress[0]:
        CameraRotation[0] += mrel[0]
        CameraRotation[1] += mrel[1]
    if mpress[2]:
        ObjectRotation[0] += mrel[0]
        ObjectRotation[1] += mrel[1]

def Draw(Window):
    fbo.enable(GLLIB_ALL)
    
    Window.clear()
    View3D.set_view()
    camerapos = [0 + CameraRadius*cos(radians(CameraRotation[0]))*cos((radians(CameraRotation[1]))),
                 1 + CameraRadius*sin((radians(CameraRotation[1]))),
                 0 + CameraRadius*sin(radians(CameraRotation[0]))*cos((radians(CameraRotation[1])))]
    gluLookAt(camerapos[0],camerapos[1],camerapos[2], 0,1,0, 0,1,0)
    Light1.set()

    glLibUseShader(ShaderObject)
    glPushMatrix()
    glTranslatef(0.0,1.0,0.0)
    glRotatef(ObjectRotation[0],0,1,0)
    glRotatef(ObjectRotation[1],1,0,0)
    Object.draw_vbo(shader=ShaderObject,indices=[1])
    glPopMatrix()
    
    Plane.draw()

    fbo.disable()

    Window.clear()
    View2D.set_view()

    glEnable(GL_POINT_SPRITE)
    glDisable(GL_DEPTH_TEST)
    glBlendFunc(GL_SRC_ALPHA,GL_ONE)
    glEnable(GL_VERTEX_PROGRAM_POINT_SIZE)
    glLibUseShader(ShaderDOF)
    ShaderDOF.pass_texture(fbo.get_texture(1),1)
    ShaderDOF.pass_texture(fbo.get_texture(2),2)
    points.draw()
    glLibUseShader(None)
    glDisable(GL_VERTEX_PROGRAM_POINT_SIZE)
    glBlendFunc(GL_SRC_ALPHA,GL_ONE_MINUS_SRC_ALPHA)
    glEnable(GL_DEPTH_TEST)
    glDisable(GL_POINT_SPRITE)

    Window.flip()

