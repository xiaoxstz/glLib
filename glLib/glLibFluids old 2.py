from glLibLocals import *
from glLibFBO import *
from glLibMath import *
from glLibMisc import *
from glLibObjects import *
from glLibView import *
from glLibShader import *
class glLibFluidGasGPU:
    def __init__(self,res):
        #heavily based on http://http.developer.nvidia.com/GPUGems/gpugems_ch38.html
        
        self.res = list(res)
        self.diff = 0.0
        self.visc = 0.0

        self.new_forces = []
        self.new_densities = []

        self.view2D = glLibView2D((0,0,self.res[0],self.res[1]))

        self.particles = glLibGrid3D([self.res[0],self.res[1],4])
##        self.particles = glLibGrid3D([self.res[0]/4,self.res[1]/4,4])

##        print glLibGrid3D([2,2,4]).vertex_vbo.data

        self.precis = 32

        self.texture_captions = {}
        self.font = pygame.font.SysFont("Times New Roman",10)

        self.gas_fbo1 = glLibFBO((self.res[0],self.res[1]))
        self.gas_fbo2 = glLibFBO((self.res[0],self.res[1]))
        self.gas_fbo1.add_render_target(1,GLLIB_RGB,filtering=GLLIB_FILTER,precision=self.precis)
        self.gas_fbo2.add_render_target(1,GLLIB_RGB,filtering=GLLIB_FILTER,precision=self.precis)
        self.gas_fbo1.textures[1].edge(GLLIB_CLAMP)
        self.gas_fbo2.textures[1].edge(GLLIB_CLAMP)

        self.prs_fbo1 = glLibFBO((self.res[0],self.res[1]))
        self.prs_fbo2 = glLibFBO((self.res[0],self.res[1]))
        self.prs_fbo1.add_render_target(1,GLLIB_RGB,filtering=GLLIB_FILTER,precision=self.precis)
        self.prs_fbo2.add_render_target(1,GLLIB_RGB,filtering=GLLIB_FILTER,precision=self.precis)
        self.prs_fbo1.textures[1].edge(GLLIB_CLAMP)
        self.prs_fbo2.textures[1].edge(GLLIB_CLAMP)

        self.vel_fbo1 = glLibFBO((self.res[0],self.res[1]))
        self.vel_fbo2 = glLibFBO((self.res[0],self.res[1]))
        self.vel_fbo1.add_render_target(1,GLLIB_RGB,precision=self.precis)
        self.vel_fbo2.add_render_target(1,GLLIB_RGB,precision=self.precis)
        self.vel_fbo1.textures[1].edge(GLLIB_CLAMP)
        self.vel_fbo2.textures[1].edge(GLLIB_CLAMP)

        self.div_fbo1 = glLibFBO((self.res[0],self.res[1]))
        self.div_fbo2 = glLibFBO((self.res[0],self.res[1]))
        self.div_fbo1.add_render_target(1,GLLIB_RGB,precision=self.precis)
        self.div_fbo2.add_render_target(1,GLLIB_RGB,precision=self.precis)
        self.div_fbo1.textures[1].edge(GLLIB_CLAMP)
        self.div_fbo2.textures[1].edge(GLLIB_CLAMP)

        self.gas_ping_pong = 1
        self.prs_ping_pong = 1
        self.vel_ping_pong = 1
        self.div_ping_pong = 1

        zero_value = np.empty((self.res[0],self.res[1],3))
        zero_value.fill(0.5)
        
        self.vel_tex = glLibTexture2D(              zero_value,GLLIB_ALL,GLLIB_RGB,                       precision=self.precis)
        self.gas_tex = glLibTexture2D(pygame.Surface(self.res),GLLIB_ALL,GLLIB_RGB,filtering=GLLIB_FILTER,precision=self.precis)
        self.prs_tex = glLibTexture2D(              zero_value,GLLIB_ALL,GLLIB_RGB,filtering=GLLIB_FILTER,precision=self.precis)

        self.advection_shader = glLibShader()
        self.advection_shader.user_variables("""
        //tex2D_1 contains the velocities; tex2D_2 contains the quantity to be advected
        uniform float dt;
        uniform float pos_neg;
        varying vec3 sc;
        const vec2 gridsize = vec2("""+str(self.res[0])+","+str(self.res[1])+""");
        const vec2 griddelta = 1.0/gridsize;""")
        self.advection_shader.vertex_extension_functions("""
        vec2 refl(float component, float low, float high) {
            if (component>high) { return vec2(2.0*high-component,-1.0); }
            if (component<low) { return vec2(2.0*low-component,-1.0); }
            return vec2(component,1.0);
        }""")
        self.advection_shader.vertex_transform("""
        vertex.xy *= vec2(1.0) - griddelta;
        vertex.xy += 0.5 * griddelta;
        gl_TexCoord[0].st = vertex.xy;
        vertex.xy *= vec2("""+str(self.res[0])+","+str(self.res[1])+""");
        vec2 delta = dt * vec3(texture2D(tex2D_1,gl_TexCoord[0].st).rgb-vec3(0.5)).rg;
        
        vec2 bottom = floor(delta);
        vec2 top = bottom + vec2(1.0);
        vec2 part = delta - bottom;
        sc = vec3(0.0);
        if      (vertex.z==0.0) { sc=vec3((1.0-part.x)*(1.0-part.y)); vertex.x+=bottom.x; vertex.y+=bottom.y; } //vertex.z == 0.0
        else if (vertex.z==1.0) { sc=vec3(     part.x *(1.0-part.y)); vertex.x+=   top.x; vertex.y+=bottom.y; } //vertex.z == 1.0
        else if (vertex.z <0.5) { sc=vec3((1.0-part.x)*     part.y ); vertex.x+=bottom.x; vertex.y+=   top.y; } //vertex.z == 1/3
        else if (vertex.z >0.5) { sc=vec3(     part.x *     part.y ); vertex.x+=   top.x; vertex.y+=   top.y; } //vertex.z == 2/3
        //vec2 x_refl = refl(vertex.x,0.0,"""+str(float(self.res[0]))+""");
        //vec2 y_refl = refl(vertex.y,0.0,"""+str(float(self.res[1]))+""");
        //vec2 z_refl = refl(vertex.z,0.0,"""+str(1.0)+""");
        //vertex.xyz = vec3(x_refl.x,y_refl.x,z_refl.x);
        //sc        *= vec3(x_refl.y,y_refl.y,z_refl.y);""")
        self.advection_shader.render_equation("""
        color.rgb = texture2D(tex2D_2,uv).rgb;
        if (pos_neg!=0.0) {
            color.rgb = pos_neg * (color.rgb-vec3(0.5));
        }
        color.rgb *= sc;""")
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
        color.rgb = texture2D(tex2D_1,uv).rgb + quantity;""")
        print "Add Shader:"
        errors = self.add_shader.compile()
        if errors != "": print errors

        self.diffuse_shader = glLibShader()
        self.diffuse_shader.user_variables("""
        const vec2 gridsize = vec2("""+str(self.res[0])+","+str(self.res[1])+""");
        const vec2 griddelta = 1.0/gridsize;""")
        self.diffuse_shader.render_equation("""
        vec3 q01 = texture2D(tex2D_1,uv-vec2(griddelta.x,0.0)).rgb;
        vec3 q21 = texture2D(tex2D_1,uv+vec2(griddelta.x,0.0)).rgb;
        vec3 q10 = texture2D(tex2D_1,uv-vec2(0.0,griddelta.y)).rgb;
        vec3 q12 = texture2D(tex2D_1,uv+vec2(0.0,griddelta.y)).rgb;
        vec3 q11 = texture2D(tex2D_1,uv                      ).rgb;
        color.rgb = q11 + q01+q21 + q10+q12;
        color.rgb /= 5.0;
        //color.rgb = -4.0*q11 + q01+q21 + q10+q12;""")
        print "Diffuse Shader:"
        errors = self.diffuse_shader.compile()
        if errors != "": print errors

        self.div_shader = glLibShader()
        self.div_shader.user_variables("""
        const vec2 gridsize = vec2("""+str(self.res[0])+","+str(self.res[1])+""");
        const vec2 griddelta = 1.0/gridsize;
        const float halfrdx = 1.0;//0.5 * griddelta.x;""")
        self.div_shader.render_equation("""
        vec3 wL = texture2D(tex2D_1,uv-vec2(griddelta.x,0.0)).rgb;
        vec3 wR = texture2D(tex2D_1,uv+vec2(griddelta.x,0.0)).rgb;
        vec3 wB = texture2D(tex2D_1,uv-vec2(0.0,griddelta.y)).rgb;
        vec3 wT = texture2D(tex2D_1,uv+vec2(0.0,griddelta.y)).rgb;
        color.rgb = vec3(  0.5 + halfrdx * ((wR.x-wL.x)+(wT.y-wB.y))  );
        //color.rgb = vec3( (wR.x-wL.x), (wT.y-wB.y), 0.0 );""")
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
        //tex2D_1 contains x, the pressure.  tex2D_2 contains b, the divergence
        float xL = texture2D(tex2D_1,uv-vec2(griddelta.x,0.0)).r - 0.5;
        float xR = texture2D(tex2D_1,uv+vec2(griddelta.x,0.0)).r - 0.5;
        float xB = texture2D(tex2D_1,uv-vec2(0.0,griddelta.y)).r - 0.5;
        float xT = texture2D(tex2D_1,uv+vec2(0.0,griddelta.y)).r - 0.5;
        float bC = texture2D(tex2D_2,uv                      ).r - 0.5;

        //Evaluate Jacobi iteration
        color.rgb = vec3(  0.5 + ((xL+xR+xB+xT+(alpha*bC))/beta)  );""")
        print "Pressure Jacobi Shader:"
        errors = self.prs_jacobi_shader.compile()
        if errors != "": print errors

        self.velprs_proj_shader = glLibShader()
        self.velprs_proj_shader.user_variables("""
        const vec2 gridsize = vec2("""+str(self.res[0])+","+str(self.res[1])+""");
        const vec2 griddelta = 1.0/gridsize;""")
        self.velprs_proj_shader.render_equation("""
        //tex2D_1 contains the velocities.  tex2D_2 contains the pressure
        float pL = texture2D(tex2D_2,uv-vec2(griddelta.x,0.0)).x;
        float pR = texture2D(tex2D_2,uv+vec2(griddelta.x,0.0)).x;
        float pB = texture2D(tex2D_2,uv-vec2(0.0,griddelta.y)).x;
        float pT = texture2D(tex2D_2,uv+vec2(0.0,griddelta.y)).x;
        color.xyz = texture2D(tex2D_1,uv).xyz;
        color.xy += 0.5*vec2(pR-pL,pT-pB);""")
        print "Velocity-Pressure Projection Shader:"
        errors = self.velprs_proj_shader.compile()
        if errors != "": print errors

        self.boundary_condition_shader = glLibShader()
        self.boundary_condition_shader.user_variables("""
        const vec2 gridsize = vec2("""+str(self.res[0])+","+str(self.res[1])+""");
        const vec2 griddelta = 1.0/gridsize;
        uniform vec3 offset;
        uniform float scale;""")
        self.boundary_condition_shader.render_equation("""
        //tex2D_1 is the state field (the field to set boundary conditions on)
        color.rgb = vec3(0.5) + scale*(texture2D(tex2D_1,uv+offset.xy*griddelta).rgb-vec3(0.5));""")
        print "Boundary Condition Shader:"
        errors = self.boundary_condition_shader.compile()
        if errors != "": print errors
        
    def glLibInternal_set_boundary_conditions(self, scale, data_tex):
        glBlendFunc(GL_ONE,GL_ZERO)
        glLibUseShader(self.boundary_condition_shader)
        self.boundary_condition_shader.pass_texture(data_tex,1)
        self.boundary_condition_shader.pass_float("scale",scale)
        for l1,l2,offset in [  [[            0.5,            1.5],[            0.5,self.res[1]-0.5],[ 1, 0, 0]],
                               [[self.res[0]-0.5,            1.5],[self.res[0]-0.5,self.res[1]-0.5],[-1, 0, 0]],
                               [[            1.5,            0.5],[self.res[0]-0.5,            0.5],[ 0, 1, 0]],
                               [[            1.5,self.res[1]-0.5],[self.res[0]-0.5,self.res[1]-0.5],[ 0,-1, 0]]  ]:
            self.boundary_condition_shader.pass_vec3("offset",offset)
            glBegin(GL_LINES); glVertex2f(*l1);glVertex2f(*l2); glEnd()
        for p,offset in [  [[            0.5,            0.5],[ 1, 1, 0]],
                           [[self.res[0]-0.5,            0.5],[-1, 1, 0]],
                           [[            0.5,self.res[1]-0.5],[ 1,-1, 0]],
                           [[self.res[0]-0.5,self.res[1]-0.5],[-1,-1, 0]]  ]:
            self.boundary_condition_shader.pass_vec3("offset",offset)
            glBegin(GL_POINTS); glVertex2f(*p); glEnd()
        glBlendFunc(GL_SRC_ALPHA,GL_ONE_MINUS_SRC_ALPHA)
    def glLibInternal_add(self, data_tex, to_add, fbo1,fbo2, ping_pong):
        glLibUseShader(self.add_shader)
        for addition in to_add:
            if ping_pong == 1: fbo1.enable([1])
            else:              fbo2.enable([1])
            self.view2D.set_view()
            glClear(GL_COLOR_BUFFER_BIT|GL_DEPTH_BUFFER_BIT);glLoadIdentity()
            self.add_shader.pass_texture(data_tex,1)
            self.add_shader.pass_vec3("quantity",[0.0,0.0,0.0])
            glLibDrawScreenQuad(texture=True)
            self.add_shader.pass_vec3("quantity",addition[1])
            glBegin(GL_QUADS)
            for delta in [[-1,-1],[1,-1],[1,1],[-1,1]]:
                coord = vec_add(addition[0][0:2],sc_vec(5.0,delta))
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
        self.diffuse_shader.pass_texture(data_tex,1)
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
        if self.div_ping_pong == 1: self.div_fbo1.enable([1])
        else:                       self.div_fbo2.enable([1])
        self.view2D.set_view()
        glClear(GL_COLOR_BUFFER_BIT|GL_DEPTH_BUFFER_BIT);glLoadIdentity()
        glLibDrawScreenQuad(texture=True)
        if self.div_ping_pong == 1: self.div_fbo1.disable(); self.div_tex = self.div_fbo1.get_texture(1)
        else:                       self.div_fbo2.disable(); self.div_tex = self.div_fbo2.get_texture(1)
        self.div_ping_pong = 3 - self.div_ping_pong
##        #   Make a vector field of 0
##        glLibUseShader(self.vec_zero_shader)
##        if self.div_ping_pong == 1: self.div_fbo1.enable([1])
##        else:                       self.div_fbo2.enable([1])
##        self.view2D.set_view()
##        glClear(GL_COLOR_BUFFER_BIT|GL_DEPTH_BUFFER_BIT);glLoadIdentity()
##        glLibDrawScreenQuad(texture=True)
##        if self.div_ping_pong == 1: self.div_fbo1.disable(); self.div_tex = self.div_fbo1.get_texture(1)
##        else:                       self.div_fbo2.disable(); self.div_tex = self.div_fbo2.get_texture(1)
##        self.div_ping_pong = 3 - self.div_ping_pong
##        #   Advect this vector field with the velocity
##        self.div_tex, self.div_ping_pong = self.glLibInternal_advect(self.vel_tex, self.div_fbo1,self.div_fbo2, self.div_ping_pong, dt,"vec")

        #Solve the matrix equation A*x = b with Jacobi iteration to find x, the forces that counter all the divergences simultaneously
        #   Initialize pressure texture to 0.0 - our initial "guess"
        glLibUseShader(self.vec_zero_shader)
        if self.prs_ping_pong == 1: self.prs_fbo1.enable([1])
        else:                       self.prs_fbo2.enable([1])
        self.view2D.set_view()
        glClear(GL_COLOR_BUFFER_BIT|GL_DEPTH_BUFFER_BIT);glLoadIdentity()
        glLibDrawScreenQuad(texture=True)
##        self.glLibInternal_set_boundary_conditions(1.0, self.prs_tex)
        if self.prs_ping_pong == 1: self.prs_fbo1.disable(); self.prs_tex = self.prs_fbo1.get_texture(1)
        else:                       self.prs_fbo2.disable(); self.prs_tex = self.prs_fbo2.get_texture(1)
        self.prs_ping_pong = 3 - self.prs_ping_pong
        #   Jacobi iterate
        for iter in xrange(n):
            if self.prs_ping_pong == 1: self.prs_fbo1.enable([1])
            else:                       self.prs_fbo2.enable([1])
            self.view2D.set_view()
            glClear(GL_COLOR_BUFFER_BIT|GL_DEPTH_BUFFER_BIT);glLoadIdentity()
            glLibUseShader(self.prs_jacobi_shader)
            self.prs_jacobi_shader.pass_texture(self.prs_tex,1) #x
            self.prs_jacobi_shader.pass_texture(self.div_tex,2) #b
            glLibDrawScreenQuad(texture=True)
            self.glLibInternal_set_boundary_conditions(1.0, self.prs_tex)
            if self.prs_ping_pong == 1: self.prs_fbo1.disable(); self.prs_tex = self.prs_fbo1.get_texture(1)
            else:                       self.prs_fbo2.disable(); self.prs_tex = self.prs_fbo2.get_texture(1)
            self.prs_ping_pong = 3 - self.prs_ping_pong
            
        #Add these forces back into the forces (velocity) texture
        if self.vel_ping_pong == 1: self.vel_fbo1.enable([1])
        else:                       self.vel_fbo2.enable([1])
        self.view2D.set_view()
        glClear(GL_COLOR_BUFFER_BIT|GL_DEPTH_BUFFER_BIT);glLoadIdentity()
        glLibUseShader(self.velprs_proj_shader)
        self.velprs_proj_shader.pass_texture(self.vel_tex,1)
        self.velprs_proj_shader.pass_texture(self.prs_tex,2)
        glLibDrawScreenQuad(texture=True)
        self.glLibInternal_set_boundary_conditions(-1.0, self.vel_tex)
        if self.vel_ping_pong == 1: self.vel_fbo1.disable(); self.vel_tex = self.vel_fbo1.get_texture(1)
        else:                       self.vel_fbo2.disable(); self.vel_tex = self.vel_fbo2.get_texture(1)
        self.vel_ping_pong = 3 - self.vel_ping_pong
    def glLibInternal_advect(self, data_tex, fbo1,fbo2, ping_pong, dt, type):
        if ping_pong == 1: fbo1.enable([1])
        else:              fbo2.enable([1])
        self.view2D.set_view()
        glClear(GL_COLOR_BUFFER_BIT|GL_DEPTH_BUFFER_BIT);glLoadIdentity()
        if type=="vec":
            #Draw a vec3(0.5) == vec_RGB=0 background
            glLibUseShader(self.vec_zero_shader)
            glLibDrawScreenQuad()
        glBlendFunc(GL_ONE,GL_ONE)
        glLibUseShader(self.advection_shader)
        self.advection_shader.pass_texture(self.vel_tex,1)
        self.advection_shader.pass_texture(data_tex,2)
        if type=="vec":
            self.advection_shader.pass_float("dt",dt)
            self.advection_shader.pass_float("pos_neg",1.0)
            self.particles.draw()
            glBlendEquationSeparate(GL_FUNC_REVERSE_SUBTRACT,GL_MAX)
            self.advection_shader.pass_float("pos_neg",-1.0)
            self.particles.draw()
            glBlendEquationSeparate(GL_FUNC_ADD,GL_FUNC_ADD)
        else:
            self.advection_shader.pass_float("dt",dt)
            self.advection_shader.pass_float("pos_neg",0.0)
            self.particles.draw()
        glBlendFunc(GL_SRC_ALPHA,GL_ONE_MINUS_SRC_ALPHA)
        if ping_pong == 1: fbo1.disable(); data_tex = fbo1.get_texture(1)
        else:              fbo2.disable(); data_tex = fbo2.get_texture(1)
        ping_pong = 3 - ping_pong
        
        return data_tex, ping_pong
    def add_density_at(self,coord,density):
        self.new_densities.append([coord,density])
    def add_force_at(self,coord,force):
        self.new_forces.append([coord,force])
    def reset(self):pass
    def step(self,dt):
        glLibPushView()
        glDisable(GL_DEPTH_TEST)

        #Add densities to gas texture and add forces to velocity texture
        self.gas_tex, self.gas_ping_pong = self.glLibInternal_add(self.gas_tex,self.new_densities,self.gas_fbo1,self.gas_fbo2,self.gas_ping_pong)
        self.vel_tex, self.vel_ping_pong = self.glLibInternal_add(self.vel_tex,self.new_forces,   self.vel_fbo1,self.vel_fbo2,self.vel_ping_pong)
        self.new_densities = []
        self.new_forces = []

        #Pressure affecting velocity
        self.glLibInternal_velprs(20,dt)
        
        #Advect the gas texture and self-advect velocity texture (self-advection must come last!)
        self.gas_tex, self.gas_ping_pong = self.glLibInternal_advect(self.gas_tex, self.gas_fbo1,self.gas_fbo2, self.gas_ping_pong, dt,"gas")
        self.vel_tex, self.vel_ping_pong = self.glLibInternal_advect(self.vel_tex, self.vel_fbo1,self.vel_fbo2, self.vel_ping_pong, dt,"vec")

        #Diffuse velocity texture (blur it)
        self.vel_tex, self.vel_ping_pong = self.glLibInternal_diffuse(self.vel_tex, self.vel_fbo1,self.vel_fbo2, self.vel_ping_pong)

        glEnable(GL_DEPTH_TEST)
        glLibPopView()
        glLibUseShader(None)
    def draw(self):
        glDisable(GL_LIGHTING)
        glLibSelectTexture(self.gas_tex)
        glBegin(GL_QUADS)
        glTexCoord2f(0,0); glVertex3f(-0.5,0,0.5)
        glTexCoord2f(1,0); glVertex3f( 0.5,0,0.5)
        glTexCoord2f(1,1); glVertex3f( 0.5,0,-0.5)
        glTexCoord2f(0,1); glVertex3f(-0.5,0,-0.5)
        glEnd()
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
