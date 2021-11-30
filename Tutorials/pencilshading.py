#Tutorial by Ian Mallett

#Controls:
#ESC           - Return to menu
#LCLICK + DRAG - Rotate spaceship

#Theory:

import sys,os
sys.path.append(os.path.split(sys.path[0])[0])
from glLib import *

def init(Screen):
    global View2D, View3D, object, ObjectRotation, Light1, line_size, PaperTex
    global BinormalShader, PencilShader, DrawingShader
    global BinormalFBO, PencilAccumulationFBO, PencilLines
    View2D = glLibView2D((0,0,Screen[0],Screen[1]))
    View3D = glLibView3D((0,0,Screen[0],Screen[1]),45,0.1,20)

    object = glLibObject("data/objects/Spaceship.obj",GLLIB_FILTER,GLLIB_MIPMAP_BLEND)
    object.build_vbo()

    ObjectRotation = [0,0]

    glEnable(GL_LIGHTING)
    Light1 = glLibLight(1)
    Light1.set_pos([0,100,0])
    Light1.set_type(GLLIB_POINT_LIGHT)
    Light1.enable()

    BinormalFBO = glLibFBO(Screen)
    BinormalFBO.add_render_target(1,GLLIB_RGBA,precision=32)

    PencilAccumulationFBO = glLibFBO(Screen)
    PencilAccumulationFBO.add_render_target(1,GLLIB_RGB,precision=32)

    PaperTex = glLibTexture2D("data/paper.jpg",GLLIB_ALL,GLLIB_RGB,GLLIB_FILTER,GLLIB_MIPMAP_BLEND)

    sampling_div = 4
    line_length = 50
    line_size = 4
    PencilLines = glLibGrid3DLines(vec_div(Screen,[sampling_div,sampling_div]))

    pygame.mouse.get_rel()

    BinormalShader = glLibShader()
    BinormalShader.render_equation("""
    color = vec4( 0.5*b+vec3(0.5), light_diffuse(light1).r);""")
    errors = BinormalShader.compile()

    PencilShader = glLibShader()
    PencilShader.user_variables("""
    const vec2 screen_size = vec2("""+str(Screen[0])+","+str(Screen[1])+""");
    const float line_length = """+str(float(line_length))+""";
    varying float intensity;""")
    PencilShader.vertex_transform("""
    vertex.xy *= vec2(1.0) - vec2(1.0)/screen_size;
    vertex.xy += vec2(0.5)/screen_size;
    
    gl_TexCoord[0].st = vertex.xy;
    vec4 sample = texture2D(tex2D_1,gl_TexCoord[0].st);
    vec3 binorm = 2.0 * (sample.rgb-vec3(0.5));

    intensity = 1.0 - sample.w;
    if (length(binorm) < 0.1) { intensity = -1.0; }
    else {
        vertex.xy *= screen_size;

        float length_sc = 0.5*line_length * 2.0*pow(intensity,1.0);
        vec2 direction = normalize(binorm.xy);
        if      (vertex.z==0.0) { vertex.xy += length_sc*direction; }
        else if (vertex.z==1.0) { vertex.xy -= length_sc*direction; }
        vertex.z = 0.0;
    }""")
    PencilShader.render_equation("""
    if (intensity==-1.0) { discard; }
    float value = 4.0*intensity;
    value = clamp(value,0.1,0.8);
    color.rgb = vec3(value);""")
    errors = PencilShader.compile()
    print(errors)

    DrawingShader = glLibShader()
    DrawingShader.render_equation("""
    float value = pow(0.3*texture2D(tex2D_2,uv).r,1.5);
    color.rgb = texture2D(tex2D_1,uv).rgb - vec3( value );""")
    errors = DrawingShader.compile()
    print(errors)
    
##    if errors != "":
##        pygame.quit()
##        raw_input(errors)
##        sys.exit()
##    else:
##        print("No errors to report with red shader (shaderdrawing.py)!")

def quit():
    global Light1, object
    glDisable(GL_LIGHTING)

    del Light1
    del object

def GetInput():
    mrel = pygame.mouse.get_rel()
    mpress = pygame.mouse.get_pressed()
    for event in pygame.event.get():
        if event.type == QUIT: quit(); pygame.quit(); sys.exit()
        if event.type == KEYDOWN and event.key == K_ESCAPE: return False
    if mpress[0]:
        ObjectRotation[0] += mrel[0]
        ObjectRotation[1] += mrel[1]

def Draw(Window):
    BinormalFBO.enable(GLLIB_ALL)
    glClearColor(0.5,0.5,0.5,1.0);Window.clear();glClearColor(0.0,0.0,0.0,1.0)
    View3D.set_view()
    gluLookAt(0,3,3, 0,0,0, 0,1,0)
    Light1.set()
    
    glLibUseShader(BinormalShader)
    glRotatef(ObjectRotation[0],0,1,0)
    glRotatef(ObjectRotation[1],1,0,0)
    object.draw_vbo(BinormalShader)

    BinormalFBO.disable()

    PencilAccumulationFBO.enable([1])
    Window.clear();
    View2D.set_view()
    
    glLibUseShader(PencilShader)
    PencilShader.pass_texture(BinormalFBO.get_texture(1),1)

    glEnable(GL_LINE_SMOOTH)
    glBlendFunc(GL_ONE,GL_ONE)
    glDisable(GL_DEPTH_TEST)
    glLineWidth(line_size)
    PencilLines.draw()
    glLineWidth(1)
    glEnable(GL_DEPTH_TEST)
    glBlendFunc(GL_SRC_ALPHA,GL_ONE_MINUS_SRC_ALPHA)
    glDisable(GL_LINE_SMOOTH);

    PencilAccumulationFBO.disable()

    Window.clear();
    View2D.set_view()
    glLibUseShader(DrawingShader)
    DrawingShader.pass_texture(PaperTex,1)
    DrawingShader.pass_texture(PencilAccumulationFBO.get_texture(1),2)
    glLibDrawScreenQuad(texture=True)
    glLibUseShader(None)

    Window.flip()
