from glLibLocals import *
from glLibFBO import *
from glLibMath import *
from glLibMisc import *
from glLibObjects import *
from glLibView import *
from glLibShader import *
import time
class glLibFluidGasGPU:
    def __init__(self,res):
        #heavily based on http://http.developer.nvidia.com/GPUGems/gpugems_ch38.html
        
        self.res = list(res)
        self.diff = 0.0
        self.visc = 0.0

        self.new_forces = []
        self.new_densities = []

        self.view2D = glLibView2D((0,0,self.res[0],self.res[1]))

        self.precis = 32

        self.texture_captions = {}
        self.font = pygame.font.SysFont("Times New Roman",10)

        self.gas_fbo1 = glLibFBO((self.res[0],self.res[1]))
        self.gas_fbo2 = glLibFBO((self.res[0],self.res[1]))
        self.prs_fbo1 = glLibFBO((self.res[0],self.res[1]))
        self.prs_fbo2 = glLibFBO((self.res[0],self.res[1]))
        self.vel_fbo1 = glLibFBO((self.res[0],self.res[1]))
        self.vel_fbo2 = glLibFBO((self.res[0],self.res[1]))
        self.div_fbo1 = glLibFBO((self.res[0],self.res[1]))
        self.div_fbo2 = glLibFBO((self.res[0],self.res[1]))
        for fbo in [self.gas_fbo1,self.gas_fbo2,self.prs_fbo1,self.prs_fbo2,self.vel_fbo1,self.vel_fbo2,self.div_fbo1,self.div_fbo2]:
            fbo.add_render_target(1,GLLIB_RGB,filtering=GLLIB_FILTER,precision=self.precis)
            fbo.textures[1].edge(GLLIB_CLAMP)

        self.gas_ping_pong = 1
        self.prs_ping_pong = 1
        self.vel_ping_pong = 1
        self.div_ping_pong = 1

        self.zero_value = np.empty((self.res[0],self.res[1],3))
        self.zero_value.fill(0.5)
        self.reset()

        self.advection_shader = glLibShader()
        self.advection_shader.user_variables("""
        uniform float dt;
        const vec2 gridsize = vec2("""+str(self.res[0])+","+str(self.res[1])+""");
        const vec2 griddelta = 1.0/gridsize;""")
        self.advection_shader.render_equation("""
        //follow the velocity field "back in time"
        vec2 pos = uv - dt*griddelta*(texture2D(tex2D_1,uv).rg-vec2(0.5));
        //sample the data texture there, and write to the current fragment
        color = texture2D(tex2D_2,pos);""")
        print "Advection Shader:"
        errors = self.advection_shader.compile()
        if errors != "": print errors

        self.vec_zero_shader = glLibShader()
        self.vec_zero_shader.render_equation("""
        color.rgb = vec3(0.5);""")
        print "Vector Zero Shader:"
        errors = self.vec_zero_shader.compile()
        if errors != "": print errors

        self.add_shader = glLibShader()
        self.add_shader.user_variables("uniform vec3 quantity;")
        self.add_shader.render_equation("""
        //tex2D_1 contains the obstacles.  tex2D_2 contains the data field.
        color.rgb = texture2D(tex2D_2,uv).rgb;
        if (texture2D(tex2D_1,uv).r==0.0) { color.rgb += quantity; }""")
        print "Add Shader:"
        errors = self.add_shader.compile()
        if errors != "": print errors

        self.diffuse_shader = glLibShader()
        self.diffuse_shader.user_variables("""
        const vec2 gridsize = vec2("""+str(self.res[0])+","+str(self.res[1])+""");
        const vec2 griddelta = 1.0/gridsize;""")
        self.diffuse_shader.render_equation("""
        //tex2D_1 contains the obstacles texture.  tex2D_2 contains the data texture
        vec3 q01 = texture2D(tex2D_2,uv-vec2(griddelta.x,0.0)).rgb;
        vec3 q21 = texture2D(tex2D_2,uv+vec2(griddelta.x,0.0)).rgb;
        vec3 q10 = texture2D(tex2D_2,uv-vec2(0.0,griddelta.y)).rgb;
        vec3 q12 = texture2D(tex2D_2,uv+vec2(0.0,griddelta.y)).rgb;
        vec3 q11 = texture2D(tex2D_2,uv                      ).rgb;
        color.rgb = q11;
        float total = 1.0;
        if (texture2D(tex2D_1,uv-vec2(griddelta.x,0.0)).r==0.0) { color.rgb += q01; total += 1.0; }
        if (texture2D(tex2D_1,uv+vec2(griddelta.x,0.0)).r==0.0) { color.rgb += q21; total += 1.0; }
        if (texture2D(tex2D_1,uv-vec2(0.0,griddelta.y)).r==0.0) { color.rgb += q10; total += 1.0; }
        if (texture2D(tex2D_1,uv+vec2(0.0,griddelta.y)).r==0.0) { color.rgb += q12; total += 1.0; }
        color.rgb /= total;
        //color.rgb = vec3(0.5) + -4.0*(q11-vec3(0.5)) + q01+q21 + q10+q12 - 4.0*vec3(0.5);""")
        print "Diffuse Shader:"
        errors = self.diffuse_shader.compile()
        if errors != "": print errors

        self.div_shader = glLibShader()
        self.div_shader.user_variables("""
        const vec2 gridsize = vec2("""+str(self.res[0])+","+str(self.res[1])+""");
        const vec2 griddelta = 1.0/gridsize;""")
        self.div_shader.render_equation("""
        //tex2D_1 contains velocity.  tex2D_2 contains the obstacles texture
        vec3 wL = texture2D(tex2D_1,uv-vec2(griddelta.x,0.0)).rgb;
        vec3 wR = texture2D(tex2D_1,uv+vec2(griddelta.x,0.0)).rgb;
        vec3 wB = texture2D(tex2D_1,uv-vec2(0.0,griddelta.y)).rgb;
        vec3 wT = texture2D(tex2D_1,uv+vec2(0.0,griddelta.y)).rgb;

        if (texture2D(tex2D_2,uv-vec2(griddelta.x,0.0)).r==1.0) { wL = vec3(0.5); }
        if (texture2D(tex2D_2,uv+vec2(griddelta.x,0.0)).r==1.0) { wR = vec3(0.5); }
        if (texture2D(tex2D_2,uv-vec2(0.0,griddelta.y)).r==1.0) { wB = vec3(0.5); }
        if (texture2D(tex2D_2,uv+vec2(0.0,griddelta.y)).r==1.0) { wT = vec3(0.5); }
        
        color.r = 0.5 + 0.5 * ((wR.x-wL.x)+(wT.y-wB.y));""")
        print "Divergence Shader:"
        errors = self.div_shader.compile()
        if errors != "": print errors

        self.prs_jacobi_shader = glLibShader()
        self.prs_jacobi_shader.user_variables("""
        const vec2 gridsize = vec2("""+str(self.res[0])+","+str(self.res[1])+""");
        const vec2 griddelta = 1.0/gridsize;
        const float alpha = 1.0;//-pow(griddelta.x,2.0);
        const float beta = 4.0;""")
        self.prs_jacobi_shader.render_equation("""
        //tex2D_1 contains x, the pressure.  tex2D_2 contains b, the divergence.  tex2D_3 contains the obstacles.
        float xC = texture2D(tex2D_1,uv                      ).r - 0.5;
        float xL = texture2D(tex2D_1,uv-vec2(griddelta.x,0.0)).r - 0.5;
        float xR = texture2D(tex2D_1,uv+vec2(griddelta.x,0.0)).r - 0.5;
        float xB = texture2D(tex2D_1,uv-vec2(0.0,griddelta.y)).r - 0.5;
        float xT = texture2D(tex2D_1,uv+vec2(0.0,griddelta.y)).r - 0.5;
        float bC = texture2D(tex2D_2,uv                      ).r - 0.5;
        
        if (texture2D(tex2D_3,uv-vec2(griddelta.x,0.0)).r==1.0) { xL = xC; }
        if (texture2D(tex2D_3,uv+vec2(griddelta.x,0.0)).r==1.0) { xR = xC; }
        if (texture2D(tex2D_3,uv-vec2(0.0,griddelta.y)).r==1.0) { xB = xC; }
        if (texture2D(tex2D_3,uv+vec2(0.0,griddelta.y)).r==1.0) { xT = xC; }

        //color.r = 0.5 + ((xL+xR+xB+xT+(alpha*bC))/beta);
        color.r = 0.5 + ((xL+xR+xB+xT-bC)/4.0);""")
        print "Pressure Jacobi Shader:"
        errors = self.prs_jacobi_shader.compile()
        if errors != "": print errors

        self.velprs_proj_shader = glLibShader()
        self.velprs_proj_shader.user_variables("""
        const vec2 gridsize = vec2("""+str(self.res[0])+","+str(self.res[1])+""");
        const vec2 griddelta = 1.0/gridsize;""")
        self.velprs_proj_shader.render_equation("""
        //tex2D_1 contains the velocities.  tex2D_2 contains the pressure.  tex2D_3 contains the obstacles.
        float pC = texture2D(tex2D_2,uv                      ).r;
        float pL = texture2D(tex2D_2,uv-vec2(griddelta.x,0.0)).r;
        float pR = texture2D(tex2D_2,uv+vec2(griddelta.x,0.0)).r;
        float pB = texture2D(tex2D_2,uv-vec2(0.0,griddelta.y)).r;
        float pT = texture2D(tex2D_2,uv+vec2(0.0,griddelta.y)).r;

        if (texture2D(tex2D_3,uv-vec2(griddelta.x,0.0)).r==1.0) { pL = pC; }
        if (texture2D(tex2D_3,uv+vec2(griddelta.x,0.0)).r==1.0) { pR = pC; }
        if (texture2D(tex2D_3,uv-vec2(0.0,griddelta.y)).r==1.0) { pB = pC; }
        if (texture2D(tex2D_3,uv+vec2(0.0,griddelta.y)).r==1.0) { pT = pC; }

        color.xyz = texture2D(tex2D_1,uv).xyz;
        //subtract the gradient of the pressure from the velocity
        color.xy -= 0.5*vec2(pR-pL,pT-pB);""")
        print "Velocity-Pressure Projection Shader:"
        errors = self.velprs_proj_shader.compile()
        if errors != "": print errors
        
    def glLibInternal_add(self, data_tex, to_add, fbo1,fbo2, ping_pong):
        glLibUseShader(self.add_shader)
        self.add_shader.pass_texture(self.obs_tex,1)
        for addition in to_add:
            if ping_pong == 1: fbo1.enable([1])
            else:              fbo2.enable([1])
            self.view2D.set_view()
            glClear(GL_COLOR_BUFFER_BIT|GL_DEPTH_BUFFER_BIT);glLoadIdentity()
            self.add_shader.pass_texture(data_tex,2)
            self.add_shader.pass_vec3("quantity",[0.0,0.0,0.0])
            glLibDrawScreenQuad(texture=True)
            self.add_shader.pass_vec3("quantity",addition[1])
            glBegin(GL_QUADS)
            for delta in [[-1,-1],[1,-1],[1,1],[-1,1]]:
                coord = vec_add(addition[0][0:2],sc_vec(5.0,delta))
                coord[0] = clamp(coord[0],1,self.res[0]-1)
                coord[1] = clamp(coord[1],1,self.res[1]-1)
                glTexCoord2f(float(coord[0])/self.res[0],
                             float(coord[1])/self.res[1]);
                glVertex3f(coord[0],coord[1],0)
            glEnd()
            if ping_pong == 1: fbo1.disable(); data_tex = fbo1.get_texture(1)
            else:              fbo2.disable(); data_tex = fbo2.get_texture(1)
            ping_pong = 3 - ping_pong
        return data_tex, ping_pong
    def glLibInternal_diffuse(self, data_tex, fbo1,fbo2, ping_pong):
        glLibUseShader(self.diffuse_shader)
        self.diffuse_shader.pass_texture(self.obs_tex,1)
        self.diffuse_shader.pass_texture(data_tex,2)
        if ping_pong == 1: fbo1.enable([1])
        else:              fbo2.enable([1])
        self.view2D.set_view()
        glClear(GL_COLOR_BUFFER_BIT|GL_DEPTH_BUFFER_BIT);glLoadIdentity()
        glLibDrawScreenQuad(texture=True)
        if ping_pong == 1: fbo1.disable(); data_tex = fbo1.get_texture(1)
        else:              fbo2.disable(); data_tex = fbo2.get_texture(1)
        ping_pong = 3 - ping_pong
        return data_tex, ping_pong
    def glLibInternal_velprs(self,n,dt):
        #So you calculate pressure in each cell each timestep by first calculating divergence
        #(the difference between the flow out of a cell and the flow into the cell, which in a
        #real incompressible fluid must be zero), and then by calculating what pressures will
        #exactly counteract all of those divergences simultaneously.
        #-Sneftel, http://www.gamedev.net/community/forums/topic.asp?topic_id=577826

        #Calculate Divergence
        glLibUseShader(self.div_shader)
        self.div_shader.pass_texture(self.vel_tex,1)
        self.div_shader.pass_texture(self.obs_tex,2)
        if self.div_ping_pong == 1: self.div_fbo1.enable([1])
        else:                       self.div_fbo2.enable([1])
        self.view2D.set_view()
        glClear(GL_COLOR_BUFFER_BIT|GL_DEPTH_BUFFER_BIT);glLoadIdentity()
        glLibDrawScreenQuad(texture=True)
        if self.div_ping_pong == 1: self.div_fbo1.disable(); self.div_tex = self.div_fbo1.get_texture(1)
        else:                       self.div_fbo2.disable(); self.div_tex = self.div_fbo2.get_texture(1)
        self.div_ping_pong = 3 - self.div_ping_pong

        #Solve the matrix equation A*x = b with Jacobi iteration to find x, the forces that counter all the divergences simultaneously
        #   Initialize pressure texture to 0.0 - our initial "guess"
        glLibUseShader(self.vec_zero_shader)
        if self.prs_ping_pong == 1: self.prs_fbo1.enable([1])
        else:                       self.prs_fbo2.enable([1])
        self.view2D.set_view()
        glClear(GL_COLOR_BUFFER_BIT|GL_DEPTH_BUFFER_BIT);glLoadIdentity()
        glLibDrawScreenQuad(texture=True)
        if self.prs_ping_pong == 1: self.prs_fbo1.disable(); self.prs_tex = self.prs_fbo1.get_texture(1)
        else:                       self.prs_fbo2.disable(); self.prs_tex = self.prs_fbo2.get_texture(1)
        self.prs_ping_pong = 3 - self.prs_ping_pong
        #   Jacobi iterate
        glLibUseShader(self.prs_jacobi_shader)
        self.prs_jacobi_shader.pass_texture(self.div_tex,2) #b, which is constant here
        self.prs_jacobi_shader.pass_texture(self.obs_tex,3) #obstacles, which are constant here
        for iter in xrange(n):
            if self.prs_ping_pong == 1: self.prs_fbo1.enable([1])
            else:                       self.prs_fbo2.enable([1])
            self.view2D.set_view()
            glClear(GL_COLOR_BUFFER_BIT|GL_DEPTH_BUFFER_BIT);glLoadIdentity()
            self.prs_jacobi_shader.pass_texture(self.prs_tex,1) #x, which changes each time
            glLibDrawScreenQuad(texture=True)
            if self.prs_ping_pong == 1: self.prs_fbo1.disable(); self.prs_tex = self.prs_fbo1.get_texture(1)
            else:                       self.prs_fbo2.disable(); self.prs_tex = self.prs_fbo2.get_texture(1)
            self.prs_ping_pong = 3 - self.prs_ping_pong
            
        #Add these forces back into the forces (velocity) texture
        glLibUseShader(self.velprs_proj_shader)
        self.velprs_proj_shader.pass_texture(self.vel_tex,1)
        self.velprs_proj_shader.pass_texture(self.prs_tex,2)
        self.velprs_proj_shader.pass_texture(self.obs_tex,3)
        if self.vel_ping_pong == 1: self.vel_fbo1.enable([1])
        else:                       self.vel_fbo2.enable([1])
        self.view2D.set_view()
        glClear(GL_COLOR_BUFFER_BIT|GL_DEPTH_BUFFER_BIT);glLoadIdentity()
        glLibDrawScreenQuad(texture=True)
        if self.vel_ping_pong == 1: self.vel_fbo1.disable(); self.vel_tex = self.vel_fbo1.get_texture(1)
        else:                       self.vel_fbo2.disable(); self.vel_tex = self.vel_fbo2.get_texture(1)
        self.vel_ping_pong = 3 - self.vel_ping_pong
    def glLibInternal_advect(self, data_tex, fbo1,fbo2, ping_pong, dt, type):
        glLibUseShader(self.advection_shader)
        self.advection_shader.pass_float("dt",dt)
        self.advection_shader.pass_texture(self.vel_tex,1)
        self.advection_shader.pass_texture(data_tex,2)
        if ping_pong == 1: fbo1.enable([1])
        else:              fbo2.enable([1])
        self.view2D.set_view()
        glClear(GL_COLOR_BUFFER_BIT|GL_DEPTH_BUFFER_BIT);glLoadIdentity()
        glLibDrawScreenQuad(texture=True)
        if ping_pong == 1: fbo1.disable(); data_tex = fbo1.get_texture(1)
        else:              fbo2.disable(); data_tex = fbo2.get_texture(1)
        ping_pong = 3 - ping_pong
        
        return data_tex, ping_pong
    def add_density_at(self,coord,density):
        self.new_densities.append([coord,density])
    def add_force_at(self,coord,force):
        self.new_forces.append([coord,force])
    def reset(self):
        self.gas_tex = glLibTexture2D(pygame.Surface(self.res),GLLIB_ALL,GLLIB_RGB,filtering=GLLIB_FILTER,precision=self.precis)
        self.prs_tex = glLibTexture2D(         self.zero_value,GLLIB_ALL,GLLIB_RGB,filtering=GLLIB_FILTER,precision=self.precis)
        self.vel_tex = glLibTexture2D(         self.zero_value,GLLIB_ALL,GLLIB_RGB,                       precision=self.precis)
        self.div_tex = glLibTexture2D(         self.zero_value,GLLIB_ALL,GLLIB_RGB,                       precision=self.precis)
        self.obs_tex = glLibTexture2D(    "data/obstacles.png",GLLIB_ALL,GLLIB_RGB)
    def step(self,n,dt):
        t1 = time.time()
        glLibPushView()
        glDisable(GL_DEPTH_TEST)

        #Add densities to gas texture and add forces to velocity texture
        self.gas_tex, self.gas_ping_pong = self.glLibInternal_add(self.gas_tex,self.new_densities,self.gas_fbo1,self.gas_fbo2,self.gas_ping_pong)
        self.vel_tex, self.vel_ping_pong = self.glLibInternal_add(self.vel_tex,self.new_forces,   self.vel_fbo1,self.vel_fbo2,self.vel_ping_pong)
        self.new_densities = []
        self.new_forces = []
        t2 = time.time()

        #Pressure affecting velocity
        self.glLibInternal_velprs(n,dt)
        t3 = time.time()
        
        #Advect the gas texture and self-advect velocity texture (self-advection must come last!)
        self.gas_tex, self.gas_ping_pong = self.glLibInternal_advect(self.gas_tex, self.gas_fbo1,self.gas_fbo2, self.gas_ping_pong, dt,"gas")
        self.vel_tex, self.vel_ping_pong = self.glLibInternal_advect(self.vel_tex, self.vel_fbo1,self.vel_fbo2, self.vel_ping_pong, dt,"vel")
        t4 = time.time()

        #Diffuse gas texture (blur it)
        self.gas_tex, self.gas_ping_pong = self.glLibInternal_diffuse(self.gas_tex, self.gas_fbo1,self.gas_fbo2, self.gas_ping_pong)

        glEnable(GL_DEPTH_TEST)
        glLibPopView()
        glLibUseShader(None)
        t5 = time.time()
##        precis = 3
##        add_time    = round(t2-t1,precis)
##        velprs_time = round(t3-t2,precis)
##        adv_time    = round(t4-t3,precis)
##        diff_time   = round(t5-t4,precis)
##        total_time  = round(add_time+velprs_time+adv_time+diff_time,precis)
##        exp_fps     = round(1.0/total_time,precis)
##        def pad(num,l):
##            snum=str(num)
##            return snum+(l-len(snum))*"0"
##        l = precis + 3
##        print pad(add_time,l),pad(velprs_time,l),pad(adv_time,l),\
##              pad(diff_time,l),pad(total_time,l),pad(exp_fps,l)
    def draw(self):
        glDisable(GL_LIGHTING)

        glLibSelectTexture(self.gas_tex)
        glBegin(GL_QUADS)
        glTexCoord2f(0,0); glVertex3f(-0.5,0,0.5)
        glTexCoord2f(1,0); glVertex3f( 0.5,0,0.5)
        glTexCoord2f(1,1); glVertex3f( 0.5,0,-0.5)
        glTexCoord2f(0,1); glVertex3f(-0.5,0,-0.5)
        glEnd()

        glBlendFunc(GL_SRC_ALPHA,GL_ONE)
        glLibSelectTexture(self.obs_tex)
        glColor3f(0.0,0.5,0.0)
        glBegin(GL_QUADS)
        glTexCoord2f(0,0); glVertex3f(-0.5,0.01,0.5)
        glTexCoord2f(1,0); glVertex3f( 0.5,0.01,0.5)
        glTexCoord2f(1,1); glVertex3f( 0.5,0.01,-0.5)
        glTexCoord2f(0,1); glVertex3f(-0.5,0.01,-0.5)
        glEnd()
        glColor3f(1.0,1.0,1.0)
        glBlendFunc(GL_SRC_ALPHA,GL_ONE_MINUS_SRC_ALPHA)
        
        glEnable(GL_LIGHTING)
        
        glLibPushView()
        glEnable(GL_SCISSOR_TEST)
        glDisable(GL_LIGHTING)

        spacing = 4
        res = 64
        textures = []
        if hasattr(self,"gas_tex"): textures.append([self.gas_tex,"Density"])
        if hasattr(self,"vel_tex"): textures.append([self.vel_tex,"Velocity"])
        if hasattr(self,"div_tex"): textures.append([self.div_tex,"Divergence"])
        if hasattr(self,"prs_tex"): textures.append([self.prs_tex,"Pressure"])
        if hasattr(self,"obs_tex"): textures.append([self.obs_tex,"Obstacles"])
        x = spacing
        for tex in textures:
            glLibView2D((x,spacing,res,res)).set_view()
            glClear(GL_COLOR_BUFFER_BIT|GL_DEPTH_BUFFER_BIT);glLoadIdentity()
            glLibDrawScreenQuad(texture=tex[0])
            try:self.texture_captions[tex[1]]
            except:
                surf = self.font.render(tex[1],True,(255,255,255))
                self.texture_captions[tex[1]] = [surf.get_size(),glLibTexture2D(surf,GLLIB_ALL,GLLIB_RGBA)]
            size = self.texture_captions[tex[1]][0]
            glLibView2D((x,spacing+res+spacing,size[0],size[1])).set_view()
            glLibDrawScreenQuad(texture=self.texture_captions[tex[1]][1])
            x += res + spacing
        
        glEnable(GL_LIGHTING)
        glDisable(GL_SCISSOR_TEST)
        glLibPopView()
