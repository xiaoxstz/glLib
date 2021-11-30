#Tutorial by Ian Mallett

#Controls:
#ESC           - Return to menu
#LCLICK + DRAG - Rotate camera
#SROLL WHEEL   - Zoom
#RCLICK + DRAG - Rotate object
#UP            - Rotate light up
#DOWN          - Rotate light down
#LEFT          - Rotate light left
#RIGHT         - Rotate light right
#v             - Switch among no light volume drawing, light volume outlines, and light volumes filled
#r             - Reset camera rotation/zoom, object rotation, light volume drawing mode, and light position

#Theory:
#Shadow volumes are the geometric representation of the areas of a
#scene that are shadowed.  These volumes can be found by extruding
#the edges of an object (as seen from the light's perspective) to
#a sufficiently faraway point, and then covering these extruded
#boundaries with "capping" geometry.  By using the stencil buffer
#to count the number of times a ray has passed through the volume,
#a point can be determined to be in light or in shadow.  The
#advantages to this technique are that it is pixel-perfect, unlike
#shadow-mapping, and, because the volume data is known, more
#complex effects, like true volumetric lighting, can be achieved.
#The disadvantage is that it is slow, especially in Python, and
#requires special attention to transformations.  In any case,
#as much built-in functionality as is reasonable is provided.
#Note that objects with smoothed normals do not extrude properly.
#The "SpaceshipFlat.obj" model is loaded instead.

import sys,os
sys.path.append(os.path.split(sys.path[0])[0])
from glLib import *

def init(Screen):
    global View3D, Spaceship, SpaceshipPosition, SpaceshipRotation, Light1, ShadowVolume, plane, camerarot, cameraradius, drawing_volumes, Shader
    View3D = glLibView3D((0,0,Screen[0],Screen[1]),45,0.1,500)

    Spaceship = glLibObject("data/objects/SpaceshipFlat.obj",GLLIB_FILTER,GLLIB_MIPMAP_BLEND)
    Spaceship.build_vbo()
    Spaceship.build_light_volume_data()

    plane = glLibPlane(5.0,[0.0,1.0,0.0])

    SpaceshipPosition = [0,1,0]
    SpaceshipRotation = [0,0]

    #Critical
    glDepthFunc(GL_LEQUAL)

    glEnable(GL_LIGHTING)
    Light1 = glLibLight(1)
    Light1.set_pos([0,3,1])
    Light1.set_ambient([0,0,0,1])
    Light1.set_diffuse([1.0,1.0,1.0,1])
    Light1.set_specular([1.0,1.0,1.0,1])
    Light1.set_type(GLLIB_POINT_LIGHT)
    Light1.enable()

    pygame.mouse.get_rel()

    camerarot = [90,10]
    cameraradius = 8.0

    drawing_volumes = 1

    TransformObjectData()
    ExtrudeVolume()

    Shader = glLibShader()
    Shader.render_equation("""
    color.rgb += ambient_color.rgb*light_ambient(light1).rgb;
    color.rgb += diffuse_color.rgb*light_diffuse(light1).rgb;
    color.rgb += specular_color.rgb*light_specular_ph(light1).rgb;
    color.rgb *= texture2D(tex2D_1,uv).rgb;""")
    errors = Shader.compile()
    print(errors)

def quit():
    global Light1, Spaceship
    glDisable(GL_LIGHTING)
    del Light1
    del Spaceship

def GetInput():
    global camerarot,cameraradius,SpaceshipRotation,drawing_volumes
    key = pygame.key.get_pressed()
    mrel = pygame.mouse.get_rel()
    mpress = pygame.mouse.get_pressed()
    for event in pygame.event.get():
        if   event.type == QUIT: quit(); pygame.quit(); sys.exit()
        elif event.type == KEYDOWN:
            if   event.key == K_ESCAPE: return False
            elif event.key == K_v:
                drawing_volumes += 1
                if drawing_volumes > 2: drawing_volumes = 0
            elif event.key == K_r:
                camerarot = [90,10]
                cameraradius = 8.0
                SpaceshipRotation = [0,0]
                TransformObjectData()
                ExtrudeVolume()
                Light1.set_pos([0,3,1])
                drawing_volumes = 1
        elif event.type == MOUSEBUTTONDOWN:
            if   event.button == 4: cameraradius -= 0.25
            elif event.button == 5: cameraradius += 0.25
    if mpress[0]:
        camerarot[0] += mrel[0]
        camerarot[1] += mrel[1]
    if mpress[2]:
        SpaceshipRotation[0] += mrel[1]
        SpaceshipRotation[1] += mrel[0]
        TransformObjectData()
        ExtrudeVolume()
    lightposition = Light1.get_pos()
    if key[K_UP]:
        Light1.set_pos(rotate_arbitrary_deg(lightposition,[1,0,0],2))
        ExtrudeVolume()
    if key[K_DOWN]:
        Light1.set_pos(rotate_arbitrary_deg(lightposition,[1,0,0],-2))
        ExtrudeVolume()
    if key[K_LEFT]:
        Light1.set_pos(rotate_arbitrary_deg(lightposition,[0,1,0],2))
        ExtrudeVolume()
    if key[K_RIGHT]:
        Light1.set_pos(rotate_arbitrary_deg(lightposition,[0,1,0],-2))
        ExtrudeVolume()
def TransformObjectData():
    glLibTransformLightVolumeData(Spaceship,translate_points,rotate_points)
def ExtrudeVolume():
    global ShadowVolume
    ShadowVolume = glLibExtrudeLightVolumes(Light1,Spaceship,0.01,10.0)
#When determining how the original data (as loaded from the file)
#is to be transformed, a point is considered transformed and then
#rotated.  Scaling can be applied in the translation stage.  In
#this way, most any data configuration can be achieved.  
def translate_points(points):
    points += np.array(SpaceshipPosition)
    return points
def rotate_points(points):
    m1 = get_rotation_matrix_deg([1,0,0],-SpaceshipRotation[0])
    m2 = get_rotation_matrix_deg([0,1,0],-SpaceshipRotation[1])
    points = np.dot(points,glLibMathMultMatrices(m1,m2))
    return points
def DrawScene(diff,spec):
    Light1.set_diffuse(diff)
    Light1.set_specular(spec)
    #Occluder
    glPushMatrix()
    glTranslatef(*SpaceshipPosition)
    glRotatef(SpaceshipRotation[1],0,1,0)
    glRotatef(SpaceshipRotation[0],1,0,0)
    glLibUseShader(Shader)
    Spaceship.draw_vbo()
    glLibUseShader(None)
    glPopMatrix()
    #receiver
    glDisable(GL_TEXTURE_2D); plane.draw(); glEnable(GL_TEXTURE_2D)
def Draw(Window):
    #Clear the Window
    Window.clear()
    
    #Set View, Camera, and Light
    View3D.set_view()
    camerapos = [SpaceshipPosition[0]+cameraradius*cos(radians(camerarot[0]))*cos(radians(camerarot[1])),
                 SpaceshipPosition[1]+cameraradius*sin(radians(camerarot[1])),
                 SpaceshipPosition[2]+cameraradius*sin(radians(camerarot[0]))*cos(radians(camerarot[1]))]
    gluLookAt(camerapos[0],camerapos[1],camerapos[2],
              SpaceshipPosition[0],SpaceshipPosition[1],SpaceshipPosition[2],
              0,1,0)
    Light1.set()
    Light1.draw_as_point()

    #Draws the scene with shadow volumes.  The second
    #argument draws the whole scene in light, the first
    #argument draws the whole scene "in shadow".  The
    #third argument is the shadow volume created eariler
    #by glLibExtrudeLightVolumes(...).
    glLibDrawWithShadowVolumes(lambda:DrawScene([0.2,0.2,0.2],[0.0,0.0,0.0]),
                               lambda:DrawScene([1.0,1.0,0.9],[1.0,1.0,0.9]),
                               lambda:glCallList(ShadowVolume))

    if drawing_volumes != 0:
        #Draw the shadow volume geometry for the user as
        #a series of faintly yellow lines.
        glDepthMask(False)
        glDisable(GL_LIGHTING)
        glDisable(GL_TEXTURE_2D)
        glColor4f(1.0,1.0,0.6,0.1)
        if drawing_volumes == 1:
            glPolygonMode(GL_FRONT_AND_BACK,GL_LINE)
        glCallList(ShadowVolume)
        if drawing_volumes == 1:
             glPolygonMode(GL_FRONT_AND_BACK,GL_FILL)
        glColor4f(1.0,1.0,1.0,1.0)
        glEnable(GL_TEXTURE_2D)
        glEnable(GL_LIGHTING)
        glDepthMask(True)
    
    #Flip
    Window.flip()
