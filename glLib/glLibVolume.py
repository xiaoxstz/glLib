from glLibLocals import *
from glLibFBO import *
from glLibObjects import *
from glLibShader import *
from glLibMisc import *
class glLibVolume:
    def __init__(self,render_size):
        global glLibInternal_ray_shader, glLibInternal_draw_volume_shader
        self.render_size = list(render_size)
        self.ray_fbo = glLibFBO(self.render_size)
        self.ray_fbo.add_render_target(1,GLLIB_RGBA)
        self.ray_fbo.add_render_target(2,GLLIB_RGBA)
        try:
            glLibInternal_ray_shader
            glLibInternal_draw_volume_shader
        except:
            glLibInternal_ray_shader = glLibShader()
            glLibInternal_ray_shader.use_prebuilt(GLLIB_INTERNAL_VOLUME_RAY)

            glLibInternal_draw_volume_shader = glLibShader()
            glLibInternal_draw_volume_shader.use_prebuilt(GLLIB_INTERNAL_VOLUME_DRAW)
        self.box = glLibRectangularSolid([0.5,0.5,0.5],texture=GLLIB_TEXTURE_3D,normals=GLLIB_FACE_NORMALS)
    def draw(self,view,data_tex,volume_size,step,max_steps):
##        self.ray_fbo.enable([1,2])
##        glClear(GL_COLOR_BUFFER_BIT|GL_DEPTH_BUFFER_BIT)
##        
##        glLibUseShader(glLibInternal_ray_shader)
##        
##        glDisable(GL_DEPTH_TEST)
##        glEnable(GL_CULL_FACE)
##        glPushMatrix()
##        glScalef(*volume_size)
##        glCullFace(GL_BACK );glLibInternal_ray_shader.pass_int("stage",1);self.box.draw()
##        glCullFace(GL_FRONT);glLibInternal_ray_shader.pass_int("stage",2);self.box.draw()
##        glPopMatrix()
##        glDisable(GL_CULL_FACE)
##        glEnable(GL_DEPTH_TEST)
##        
##        self.ray_fbo.disable()
        
        glLibPushView()
        glLibView2D(view.rect).set_view()
        glLibUseShader(glLibInternal_draw_volume_shader)
        glLibInternal_draw_volume_shader.pass_float("near",view.near)
        glLibInternal_draw_volume_shader.pass_float("far",view.far)
        glLibInternal_draw_volume_shader.pass_float("step",step)
        glLibInternal_draw_volume_shader.pass_int("max_steps",max_steps)
        glLibInternal_draw_volume_shader.pass_texture(data_tex,1)
        glLibInternal_draw_volume_shader.pass_texture(self.ray_fbo.get_texture(1),2)
        glLibInternal_draw_volume_shader.pass_texture(self.ray_fbo.get_texture(2),3)
        glLibDrawScreenQuad(texture=True)
        glLibPopView()
        
        glLibUseShader(None)
