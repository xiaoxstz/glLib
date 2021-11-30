#Tutorial by Ian Mallett

#Controls:
#ESC           - Return to menu
#LCLICK + DRAG - Rotate camera
#RCLICK + DRAG - Rotate spaceship
#SROLL WHEEL   - Zoom
#UP            - Preturb the model's base normals more
#DOWN          - Preturb the model's base normals less

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

import sys,os
sys.path.append(os.path.split(sys.path[0])[0])
from glLib import *

def init(Screen):
    global View2D, View3D, Spaceship, Plane, SpaceshipRotation, CameraRotation, CameraRadius, Light1, Shader, screen_fbo
    View2D = glLibView2D((0,0,Screen[0],Screen[1]))
    View3D = glLibView3D((0,0,Screen[0],Screen[1]),45,0.1,20)

    Spaceship = glLibObject("data/objects/Spaceship.obj",GLLIB_FILTER,GLLIB_MIPMAP_BLEND)
    Spaceship.build_vbo()

    ambient,diffuse,specular,shininess = [0.24725,0.1995,0.0745,1.0],[0.75164,0.60648,0.22648,1.0],[0.628281,0.555802,0.366065,1.0],51.2
    
    #Objects loaded from .obj files have their own materials
    #that will overwrite the current material when they are
    #drawn.  Simply calling glLibUseMaterial(GLLIB_MATERIAL_GOLD)
    #before drawing won't work; the spaceship's material itself
    #must be changed.  Any of the following methods will work.
    Spaceship.set_material(GLLIB_MATERIAL_GOLD)
##    Spaceship.set_material([GLLIB_MATERIAL_GOLD,0])
##    Spaceship.set_material([ambient,diffuse,specular,shininess])
##    Spaceship.set_material([[ambient,diffuse,specular,shininess],0])

    FloorTexture = glLibTexture2D("data/floor.jpg",[0,0,512,512],GLLIB_RGBA,GLLIB_FILTER,GLLIB_MIPMAP_BLEND)
    try:FloorTexture.anisotropy(GLLIB_MAX)
    except:pass

    Plane = glLibPlane(5,(0,1,0),FloorTexture,10)

    SpaceshipRotation = [0,0]
    #Add variables for the camera's rotation and radius
    CameraRotation = [90,23]
    CameraRadius = 5.0
    pertubation_level = 1.0

    glEnable(GL_LIGHTING)
    Light1 = glLibLight(1)
    Light1.set_pos([0,10,0])
    Light1.set_type(GLLIB_POINT_LIGHT)
    Light1.enable()

    pygame.mouse.get_rel()

    Shader = glLibShader()
    Shader.render_equation("""
    color.rgb += ambient_color.rgb*light_ambient(light1).rgb;
    color.rgb += diffuse_color.rgb*light_diffuse(light1).rgb;
    color.rgb += specular_color.rgb*light_specular_ph(light1).rgb;""")
    errors = Shader.compile()
    print errors

    screen_fbo = glLibFBO(Screen,samples=1)
    print screen_fbo.check_status()
    screen_fbo.add_render_target(1,GLLIB_RGB)
    print screen_fbo.check_status()

def quit():
    global Light1, Spaceship
    glDisable(GL_LIGHTING)
    del Light1
    del Spaceship

def GetInput():
    global CameraRadius
    mrel = pygame.mouse.get_rel()
    mpress = pygame.mouse.get_pressed()
    key = pygame.key.get_pressed()
    for event in pygame.event.get():
        if event.type == QUIT: quit(); pygame.quit(); sys.exit()
        if event.type == KEYDOWN and event.key == K_ESCAPE: return False
        if event.type == MOUSEBUTTONDOWN:
            if event.button == 5: CameraRadius += .2
            if event.button == 4: CameraRadius -= .2
    #If the left mouse button is clicked,
    #rotate the camera.  Rotate the spaceship
    #if the right mouse button is pressed.
    if mpress[0]:
        CameraRotation[0] += mrel[0]
        CameraRotation[1] += mrel[1]
    if mpress[2]:
        SpaceshipRotation[0] += mrel[0]
        SpaceshipRotation[1] += mrel[1]

def Draw(Window):
    screen_fbo.enable([1])
    
    Window.clear()
    View3D.set_view()
    #Calculate the camera's position using CameraRotation.
    #Basically just spherical coordinates.
    camerapos = [0 + CameraRadius*cos(radians(CameraRotation[0]))*cos((radians(CameraRotation[1]))),
                 1 + CameraRadius*sin((radians(CameraRotation[1]))),
                 0 + CameraRadius*sin(radians(CameraRotation[0]))*cos((radians(CameraRotation[1])))]
    gluLookAt(camerapos[0],camerapos[1],camerapos[2], 0,1,0, 0,1,0)
    Light1.set()

    glLibUseShader(Shader)
    glPushMatrix()
    glTranslatef(0.0,1.0,0.0)
    glRotatef(SpaceshipRotation[0],0,1,0)
    glRotatef(SpaceshipRotation[1],1,0,0)
    Spaceship.draw_vbo()
    glPopMatrix()

    glLibUseShader(None)
    Plane.draw()

    screen_fbo.disable()

    glDisable(GL_LIGHTING)
    Window.clear()
    View2D.set_view()
    glLibSelectTexture(screen_fbo.get_texture(1))
    glLibTexFullScreenQuad()
    Window.flip()
    glEnable(GL_LIGHTING)
