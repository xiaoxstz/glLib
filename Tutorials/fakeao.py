#Tutorial by Ian Mallett

#Controls:
#ESC           - Return to menu
#LCLICK + DRAG - Rotate camera
#RCLICK + DRAG - Rotate object
#r             - Reset all rotations
#a             - Turn ambient occlusion effect on/off

#Theory
#Ambient occlusion is an amazing effect.  It approximates global
#illumination by darkening areas that are surrounded by other objects.
#Thus, corners will be slightly shadowed, things under other things
#will be darker, and so on.  Though many ambient occlusion techniques
#are available, this method is a cheap and dirty way to simulate it.
#The depth buffer is blurred, subtracted from the original depth
#buffer, and then subtracted from the pixel's color.  It's not
#perfect, but it does well for its computational complexity.  A FBO is
#used to render the color and depth buffers.
#
#Because of the large fillrate required for the blur and subsequent
#operations, the effect is only operated over a 400x300 window.

import sys,os
sys.path.append(os.path.split(sys.path[0])[0])
from glLib import *

def init(Screen):
    global View2D, View3D, LightView
    global Object
    global ObjectPosition, ObjectRotation, CameraRotation, CameraRadius
    global Light1, fbo
    global ao
    global BoxShader, CompositingShader
    View2D = glLibView2D((0,0,Screen[0]//2,Screen[1]//2))
    View3D = glLibView3D((0,0,Screen[0]//2,Screen[1]//2),45,0.5,10)

    #Create the object
    BoxTexture = glLibTexture2D("data/floor.jpg",[0,0,512,512],GLLIB_RGBA,GLLIB_FILTER,GLLIB_MIPMAP_BLEND)
    Block = glLibRectangularSolid([0.3,0.3,0.3],[BoxTexture]*6)
    Object = glGenLists(1)
    glNewList(Object,GL_COMPILE)
    for block in [[[0.0,0.0,0.0],1.0],
                  [[0.2,-0.2,0.0],1.2],
                  [[0.6,0.0,0.1],0.6],
                  [[0.8,-0.1,0.0],0.5],
                  [[-0.3,0.4,0.3],0.7],
                  [[-0.3,0.6,0.4],0.5],
                  [[-0.2,0.3,0.6],0.5],
                  [[0.2,0.2,0.4],0.7],
                  [[0.3,0.1,0.3],0.6]]:
        glPushMatrix()
        glTranslatef(*block[0])
        glScalef(*[block[1]]*3)
        Block.draw()
        glPopMatrix()
    glEndList()

    ObjectPosition = [0.0,1.0,0.0]
    ObjectRotation = [0,0]
    CameraRotation = [90,23]
    CameraRadius = 2.0
    ao = False

    fbo = glLibFBO([Screen[0]//2,Screen[1]//2])
    fbo.add_render_target(1,type=GLLIB_RGB,filtering=GLLIB_FILTER)
    fbo.add_render_target(2,type=GLLIB_DEPTH,filtering=GLLIB_FILTER)

    glEnable(GL_LIGHTING)
    Light1 = glLibLight(1)
    Light1.set_pos([0,10,1])
    Light1.set_type(GLLIB_POINT_LIGHT)
    Light1.enable()

    pygame.mouse.get_rel()

    BoxShader = glLibShader()
    BoxShader.render_targets(2)
    BoxShader.render_equation("""
    color.rgb += ambient_color.rgb*light_ambient(light1).rgb;
    color.rgb += diffuse_color.rgb*light_diffuse(light1).rgb;""")
    errors = BoxShader.compile()
    print(errors)
##    if errors != "": pygame.quit();raw_input(errors);sys.exit()
##    print "No errors to report with box shader (fakeao.py)!"

    #Blurs the depth buffer with a simple box blur.  Better
    #results (aesthetically and computationally) could be
    #achieved with a hard-coded gaussian blur.  The blurred
    #depth buffer is subtracted from the original resulting
    #in a difference (delta).  This value is scaled and
    #subtracted from the color, giving the fake ambient
    #occlusion effect.
    CompositingShader = glLibShader()
    CompositingShader.user_variables("""
    uniform bool ao;
    uniform float radius, jump;
    uniform vec2 size;""")
    CompositingShader.render_equation("""
    color.rgb = texture2D(tex2D_2,uv).rgb;
    if (ao) {
        float value = 0.0;
        float number = 0.0;
        for (float x=-radius;x<radius+1.0;x+=1.0) {
            for (float y=-radius;y<radius+1.0;y+=1.0) {
                float texel = texture2D(tex2D_1,uv+jump*vec2(x,y)/size).r;
                if (texel!=1.0) {
                    value += texel;
                    number += 1.0;
                }
            }
        }
        value = value*(1.0/number);
        float mid = texture2D(tex2D_1,uv).r;
        float delta = clamp(mid-value,0.0,1.0);
        
        color.rgb -= 5.0*vec3(delta);
    }""")
    errors = CompositingShader.compile()
    print(errors)
##    if errors != "": pygame.quit();raw_input(errors);sys.exit()
##    print "No errors to report with compositing shader (fakeao.py)!"

def quit():
    global Light1
    glDisable(GL_LIGHTING)
    del Light1

def GetInput():
    global ObjectRotation, CameraRotation, ao
    mrel = pygame.mouse.get_rel()
    mpress = pygame.mouse.get_pressed()
    for event in pygame.event.get():
        if event.type == QUIT: quit(); pygame.quit(); sys.exit()
        elif event.type == KEYDOWN:
            if event.key == K_ESCAPE: return False
            elif event.key == K_r:
                ObjectRotation = [0,0]
                CameraRotation = [90,23]
            elif event.key == K_a:
                ao = not ao
    if mpress[0]:
        CameraRotation[0] += mrel[0]
        CameraRotation[1] += mrel[1]
    if mpress[2]:
        ObjectRotation[0] += mrel[0]
        ObjectRotation[1] += mrel[1]

def Draw(Window):
    #First pass: render the scene.  Output the colors to
    #rendertarget 1 and the depth to rendertarget 2.
    fbo.enable([1,2])
    
    Window.clear()
    View3D.set_view()
    camerapos = [0 + CameraRadius*cos(radians(CameraRotation[0]))*cos((radians(CameraRotation[1]))),
                 1 + CameraRadius*sin((radians(CameraRotation[1]))),
                 0 + CameraRadius*sin(radians(CameraRotation[0]))*cos((radians(CameraRotation[1])))]
    gluLookAt(camerapos[0],camerapos[1],camerapos[2], 0,1,0, 0,1,0)
    
    Light1.set()
    Light1.draw_as_sphere()

    glLibUseShader(BoxShader)

    glPushMatrix()
    glTranslatef(*ObjectPosition)
    glRotatef(ObjectRotation[0],0,1,0)
    glRotatef(ObjectRotation[1],1,0,0)
    glCallList(Object)
    glPopMatrix()

    fbo.disable()

    #Second pass: composite the depth information and color
    #information into a final, post-processed result.
    Window.clear()
    View2D.set_view()
    glLibUseShader(CompositingShader)
    CompositingShader.pass_texture(fbo.get_texture(2),1)
    CompositingShader.pass_texture(fbo.get_texture(1),2)
    CompositingShader.pass_float("radius",6.0)
    CompositingShader.pass_float("jump",2.0)
    CompositingShader.pass_vec2("size",View2D.rect[2:])
    CompositingShader.pass_bool("ao",ao)
    glLibDrawScreenQuad(texture=True)
    glBlendFunc(GL_SRC_ALPHA,GL_ONE_MINUS_SRC_ALPHA)

    glLibUseShader(None)

    Window.flip()
