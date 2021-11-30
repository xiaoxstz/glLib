#Tutorial by Ian Mallett

#Controls:
#ESC           - Return to menu
#LCLICK + DRAG - Rotate camera
#RCLICK + DRAG - Rotate spaceship
#SROLL WHEEL   - Zoom
#UP            - Preturb the model's base normals more
#DOWN          - Preturb the model's base normals less

#Theory:


import sys,os
sys.path.append(os.path.split(sys.path[0])[0])
from glLib import *

def init(Screen):
    global View3D, Plane, Glass
    global CameraRotation, CameraRadius, Light1
    View3D = glLibView3D((0,0,Screen[0],Screen[1]),45,0.1,200)

    #Load the Glass
    GlassTexture = glLibTexture2D("data/glass.png",[0,0,500,500],GLLIB_RGBA,GLLIB_FILTER,GLLIB_MIPMAP_BLEND)
    try:GlassTexture.anisotropy(GLLIB_MAX)
    except:pass
    Glass = glLibPlane(1,(0,1,0),GlassTexture,1)

    #Load the Floor
    FloorTexture = glLibTexture2D("data/floor.jpg",[0,0,512,512],GLLIB_RGBA,GLLIB_FILTER,GLLIB_MIPMAP_BLEND)
    try:FloorTexture.anisotropy(GLLIB_MAX)
    except:pass
    Plane = glLibPlane(5,(0,1,0),FloorTexture,10)

    ObjectRotation = [0,0]
    #Add variables for the camera's rotation and radius
    CameraRotation = [90,23]
    CameraRadius = 15.0

    glEnable(GL_LIGHTING)
    Light1 = glLibLight(1)
    Light1.set_pos([0,5,0])
    Light1.set_type(GLLIB_POINT_LIGHT)
    Light1.enable()

    pygame.mouse.get_rel()

    Shader = glLibShader()
    Shader.user_variables("uniform float pertubation_level;")
    Shader.render_equation("""
    vec3 normalmapsample = texture2D(tex2D_1,uv).rgb;
    
    //normal = normal_from_normalmap(normalmapsample,pertubation_level);
    
    //normal = normal_from_normalmap(normalmapsample); //same as "normal_from_normalmap(normalmapsample,1.0)"
    
    color.rgb += ambient_color.rgb*light_ambient(light1).rgb;
    color.rgb += diffuse_color.rgb*light_diffuse(light1).rgb;
    color.rgb += specular_color.rgb*light_specular_ph(light1).rgb;""")
    #The normalmap is tileable.  Let's tile it.
    Shader.uv_transform("uv *= vec2(5.0,4.0);")
    errors = Shader.compile()
    print(errors)
##    if errors != "":
##        pygame.quit()
##        raw_input(errors)
##        sys.exit()
##    else:
##        print("No errors to report with normalmapping shader (normalmapping.py)!")
def quit():
    global Light1
    glDisable(GL_LIGHTING)
    del Light1

def GetInput():
    global CameraRadius
    mrel = pygame.mouse.get_rel()
    mpress = pygame.mouse.get_pressed()
    key = pygame.key.get_pressed()
    for event in pygame.event.get():
        if   event.type == QUIT: quit(); pygame.quit(); sys.exit()
        elif event.type == KEYDOWN:
            if event.key == K_ESCAPE: return False
        elif event.type == MOUSEBUTTONDOWN:
            if   event.button == 5: CameraRadius += .2
            elif event.button == 4: CameraRadius -= .2
    if mpress[0]:
        CameraRotation[0] += mrel[0]
        CameraRotation[1] += mrel[1]

def Draw(Window):
    Window.clear()
    View3D.set_view()
    #Calculate the camera's position using CameraRotation.
    #Basically just spherical coordinates.
    camerapos = [0 + CameraRadius*cos(radians(CameraRotation[0]))*cos((radians(CameraRotation[1]))),
                 1 + CameraRadius*sin((radians(CameraRotation[1]))),
                 0 + CameraRadius*sin(radians(CameraRotation[0]))*cos((radians(CameraRotation[1])))]
    gluLookAt(camerapos[0],camerapos[1],camerapos[2], 0,1,0, 0,1,0)
    Light1.set()
    Light1.draw_as_point(10)

##    glLibUseShader()
##    
##    glLibUseShader(None)

    #Draw the glass
    glPushMatrix()
    glTranslatef(0.0,2.0,0.0)
    Glass.draw()
    glPopMatrix()
    
    #Draw the floor
    Plane.draw()

    Window.flip()
