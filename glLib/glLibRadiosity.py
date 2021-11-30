from glLibLocals import *
from glLibFBO import *
from glLibView import *
from glLibMath import *
from glLibShader import *

from glLibMisc import *

class glLibInternal_vertex:
    def __init__(self,pos,norm):
        self.pos = list(pos)
        self.norm = list(norm)
        self.data = []
class glLibRadiosityMesh:
    def __init__(self,meshes):
        self.gamma = 1.0
        self.iteration = 0
        
        self.vertices = {}
        patches_count = 0
        for mesh_data in meshes:
            obj = mesh_data[0]
            for sublist in range(obj.number_of_lists):
                for index in range(0,len(obj.vertices[sublist]),4):
                    patches_count += 1
        self.original_patches = np.empty(  (patches_count),  [("number",np.int16),
                                                              ("polygon",np.float32,(4,3)),
                                                              ("center",np.float32,(3)),
                                                              ("tangent",np.float32,(3)),
                                                              ("norm",np.float32,(3)),
                                                              ("area",np.float32),
                                                              ("accumulated radiance",np.float32,(3)),
                                                              ("residual radiance",np.float32,(3)),
                                                              ("residual power",np.float32),
                                                              ("color",np.float32,(3)),
                                                              ("reflectance",np.float32,(3))]  )
        polynum = 0
        vertex_number = 0
        for mesh_data in meshes:
            obj         = mesh_data[0]
            emission    = mesh_data[2]
            if emission == GLLIB_NONE: emission = [0.0,0.0,0.0]
            reflectance = mesh_data[3]
            for sublist in range(obj.number_of_lists):
                color = mesh_data[1]
                if   color ==  GLLIB_MATERIAL_AMBIENT: color = obj.materials[sublist]["Ka"][:3]
                elif color ==  GLLIB_MATERIAL_DIFFUSE: color = obj.materials[sublist]["Kd"][:3]
                elif color == GLLIB_MATERIAL_SPECULAR: color = obj.materials[sublist]["Ks"][:3]
                for index in range(0,len(obj.vertices[sublist]),4):
                    v1 = obj.vertices[sublist][index  ]; v2 = obj.vertices[sublist][index+1]; v3 = obj.vertices[sublist][index+2]; v4 = obj.vertices[sublist][index+3]
                    n1 = obj.normals [sublist][index  ]; n2 = obj.normals [sublist][index+1]; n3 = obj.normals [sublist][index+2]; n4 = obj.normals [sublist][index+3]
                    self.vertices[tuple(v1)] = glLibInternal_vertex(v1,n1); self.vertices[tuple(v2)] = glLibInternal_vertex(v2,n2); self.vertices[tuple(v3)] = glLibInternal_vertex(v3,n3); self.vertices[tuple(v4)] = glLibInternal_vertex(v4,n4)
                    area = polygon_area([v1,v2,v3,v4])
                    self.original_patches[polynum]["number"              ]       = polynum
                    self.original_patches[polynum]["polygon"             ][0][:] = np.array( v1 )
                    self.original_patches[polynum]["polygon"             ][1][:] = np.array( v2 )
                    self.original_patches[polynum]["polygon"             ][2][:] = np.array( v3 )
                    self.original_patches[polynum]["polygon"             ][3][:] = np.array( v4 )
                    self.original_patches[polynum]["center"              ][:]    = np.array( sc_vec(0.25,vec_add(vec_add(v1,v2),vec_add(v3,v4))) )
                    self.original_patches[polynum]["tangent"             ][:]    = np.array( normalize(vec_add(vec_subt(v1,v2),vec_subt(v3,v4))) )
                    self.original_patches[polynum]["norm"                ][:]    = np.array( normalize(vec_add(vec_add(n1,n2),vec_add(n3,n4))) )
                    self.original_patches[polynum]["area"                ]       = area
                    self.original_patches[polynum]["color"               ][:]    = np.array( color )
                    self.original_patches[polynum]["accumulated radiance"][:]    = np.array( emission )
                    self.original_patches[polynum]["residual radiance"   ][:]    = np.array( emission )
                    self.original_patches[polynum]["residual power"      ]       = sum(emission)*area
                    self.original_patches[polynum]["reflectance"         ][:]    = reflectance
                    polynum += 1
        self.reset()

        self.visibility_shader = glLibShader()
        self.visibility_shader.user_variables("""
        uniform vec3 patch_center;
        uniform vec3 current_patch_center;
        uniform vec3 patch_normal;
        uniform vec3 indices;
        varying float depth;
        varying vec3 vertex_vector;""")
        self.visibility_shader.post_vertex("""
        vec3 axis_vector = normalize(   cross( patch_normal, vec3(0.0,0.0,-1.0) )   );
        float angle = acos(   dot( patch_normal, vec3(0.0,0.0,-1.0) )   );
        mat3 rot_matrix = rotation_matrix_arbitrary(axis_vector,-angle);
        
        vertex_vector = vertex.xyz - patch_center;
        vertex_vector = rot_matrix*vertex_vector;

        depth = length(vertex_vector)/1000.0;

        vertex_vector = normalize(vertex_vector);
        
        //http://en.wikipedia.org/wiki/Lambert_azimuthal_equal-area_projection
        float z_term = pow( 2.0/(1.0-vertex_vector.z), 0.5 );
        // in range (-2,2)
        //however, we discard vertex_vector.z>=-0.01, to get a hemisphere so in range (-sqrt(2),sqrt(2))
        vec2 coord = z_term*vertex_vector.xy;

        coord = coord/pow(2.0,0.5); //in range (-1,1)
        
        vertex.xy = coord;
        vertex.z = 0.0;
        vertex.w = 1.0;

        gl_Position = vertex;""")
        self.visibility_shader.render_equation("""
        if (patch_center==current_patch_center) { discard; }
        if (vertex_vector.z>=-0.01) { discard; }
        color.rgb = indices;
        gl_FragDepth = depth;""")
        errors = self.visibility_shader.compile()
        print(errors)

        self.index_list = glGenLists(1)
        glNewList(self.index_list,GL_COMPILE)
        color = [0.0,0.0,1.0]
        for polynum in range(len(self.patches)):
            c_index = vec_div(color,[255.0]*3)
            self.visibility_shader.pass_vec3("indices",c_index)
            self.visibility_shader.pass_vec3("current_patch_center",self.patches[polynum]["center"])
            glNormal3f(*self.patches[polynum]["norm"])
            glColor3f(*c_index)
            glBegin(GL_QUADS)
            for vert in self.patches[polynum]["polygon"]:
                glVertex3f(*vert)
            glEnd()
            color[2] += 1.0
            if color[2] == 256.0:
                color[2] = 1.0
                color[1] += 1.0
                if color[1] == 256.0:
                    color[1] = 0.0
                    color[0] += 1.0
        glEndList()
    def compute_visibility(self,resolution):
        glDisable(GL_LIGHTING)
        glDisable(GL_TEXTURE_2D)
        glEnable(GL_SCISSOR_TEST)

        patch_view = glLibView2D([0,0,resolution,resolution])
        total_circle_pixels = pi*((resolution/2.0)**2.0)

        distances = np.abs(np.arange(0,resolution,1)+0.5-(resolution/2.0))
        x_gradient = np.tile(distances,(resolution,1))
        y_gradient = np.copy(x_gradient)
        y_gradient = np.swapaxes(y_gradient,0,1)
        distances_to_center = np.hypot(x_gradient,y_gradient)
        angles = np.radians(   (distances_to_center/((resolution/2.0)-0.5)) * 90.0   )
        lambert_weights = np.cos(angles)
        lambert_weights[np.where(lambert_weights<0.0)] = 0.0
        total_height = np.sum(np.sum(lambert_weights))
        lambert_weights *= total_circle_pixels / total_height
##        zero = np.zeros((resolution,resolution))
##        pygame.image.save(pygame.surfarray.make_surface(np.transpose([lambert_weights*255.0,zero,zero])),"test.png")
        #reshape
        lambert_weights = lambert_weights.reshape((resolution*resolution))
        
        num_patches = len(self.patches)
        
        self.visibility = np.zeros((num_patches,num_patches),dtype=np.float32)
        glLibUseShader(self.visibility_shader)
        patch_view.set_view()
        t_start = time.time()
        for poly1num in range(num_patches):
            t1 = time.time()
            glClear(GL_COLOR_BUFFER_BIT|GL_DEPTH_BUFFER_BIT)
            glLoadIdentity()
            
            camera_pos = list(self.patches[poly1num]["center"])
            center = vec_add(self.patches[poly1num]["norm"],camera_pos)
            up = list(self.patches[poly1num]["tangent"])
            gluLookAt(camera_pos[0],camera_pos[1],camera_pos[2],center[0],center[1],center[2],up[0],up[1],up[2])
            
            self.visibility_shader.pass_vec3("patch_center",self.patches[poly1num]["center"])
            self.visibility_shader.pass_vec3("patch_normal",self.patches[poly1num]["norm"])

            glCallList(self.index_list)

            pixel_data = np.cast['int16'](255.0*glReadPixels(0,0,patch_view.width,patch_view.height,GL_RGB,GL_FLOAT)).reshape((-1,3))
            pixel_data = np.dot(pixel_data,np.array([65025,255,1]))
            count = np.bincount(pixel_data,lambert_weights)[1:]
            self.visibility[poly1num][0:count.shape[0]] += count
            self.visibility[poly1num] /= total_circle_pixels
            
                    
            t2 = time.time()
            seconds,minutes,hours = glLibGetTimeElements((num_patches-poly1num)*(t2-t1))
            message = ""
            message += "Visibility found for patch "+str(poly1num+1)+"/"+str(num_patches)+" "
            message += "("
            message += str(rndint(100.0*float(poly1num)/float(num_patches+1)))+"%"
            if poly1num!=num_patches-1:
                message += ", E.T.C.: ~"
                if hours   > 0: message += str(hours  )+"H "
                if minutes > 0: message += str(minutes)+"M "
                if seconds > 0: message += str(rndint(seconds))+"S"
            message += ")"
            message += (79-len(message))*" " + "\r"
            sys.stdout.write(message)
            sys.stdout.flush()
        print()
        t_final = time.time()
        seconds,minutes,hours = glLibGetTimeElements(t_final-t_start)
        message = ""
        message += "Total time to calculate visibility coefficients: "
        if hours   > 0: message += str(hours  )+"H "
        if minutes > 0: message += str(minutes)+"M "
        if seconds > 0: message += str(rndint(seconds))+"S"
        print(message)
        
        glLibUseShader(None)
        glDisable(GL_SCISSOR_TEST)
        glEnable(GL_TEXTURE_2D)
        glEnable(GL_LIGHTING)

    def save_visibility(self,name):
        file = open(name,"wb")
        np.save(file,self.visibility)
        file.close()
    def use_visibility(self,name):
        file = open(name,"rb")
        self.visibility = np.load(file)
        file.close()
    def visibility_factor(self,i,j):
        return self.visibility[i.number][j.number]
    def reset(self):
        self.patches = np.copy(self.original_patches)
        self.iteration = 0
    def calculate(self,termination_type,value):
        termination_ratio = None
        termination_iteration = None
        if   termination_type == GLLIB_RADIOSITY_RATIO:      termination_ratio = value
        elif termination_type == GLLIB_RADIOSITY_ITERATIONS: termination_iteration = value
        #Iterate shooting steps
        while True:
            self.patches[:]["residual power"] = np.sum(self.patches[:]["residual radiance"],1)*self.patches[:]["area"]
            self.patches.sort(order="residual power")
            if self.iteration == 0:
                first_power = np.copy(self.patches[-1]["residual power"])
            message = ""
            message += "Iteration: "+((5-len(str(self.iteration)))*" ")+str(self.iteration)+"; "
            if   termination_ratio     != None: ratio = (self.patches[-1]["residual power"]-(first_power*termination_ratio)) / (first_power-first_power*termination_ratio)
            elif termination_iteration != None: ratio = float(termination_iteration-self.iteration) / float(termination_iteration)
            percent = round(100.0-(100.0*ratio),6)
            print_percent = list(map(str,[int(percent),percent-int(percent)])); print_percent[0] = print_percent[0][0:3]; print_percent[0] = ((3-len(print_percent[0]))*" ")+"~"+print_percent[0]; print_percent[1] = print_percent[1][2:8]; print_percent[1] = print_percent[1] = print_percent[1]+((6-len(print_percent[1]))*"0")
            message += print_percent[0] + "." + print_percent[1]
            message += "% converged to tolerance"
            message += "      \r"
            sys.stdout.write(message);sys.stdout.flush()
            if percent >= 100.0: break
            #Shoot from patch i to patch j
            azimuthal_area = self.visibility[self.patches[-1]["number"]][self.patches[:-1]["number"]]
            per_channel_transport = self.patches[-1]["residual radiance"]*self.patches[:-1]["color"]
            energy_transferred = per_channel_transport[:] * np.transpose([azimuthal_area,azimuthal_area,azimuthal_area])

            delta_positions = self.patches[-1]["center"] - self.patches[:-1]["center"]
            lengths = np.power(  np.sum(delta_positions*delta_positions,1),  0.5  )
            delta_vectors = delta_positions / np.transpose([lengths,lengths,lengths])
            cos_theta_2s = np.sum(  delta_vectors*self.patches[:-1]["norm"],  1  )
            energy_transferred *= np.transpose([cos_theta_2s]*3)
            
            reflected = energy_transferred[:]*self.patches[:-1]["reflectance"]
            self.patches[:-1]["accumulated radiance"][:] += reflected
            self.patches[:-1]["residual radiance"   ][:] += reflected
            #   http://en.wikipedia.org/wiki/View_factor
##            delta_positions = self.patches[:-1]["center"] - self.patches[-1]["center"]
##            lengths = np.power(  np.sum(delta_positions*delta_positions,1),  0.5  )
##            delta_vectors = delta_positions / np.transpose([lengths,lengths,lengths])
##            cos_theta_1s = np.dot(delta_vectors,self.patches[-1]["norm"])
##            cos_theta_2s = np.sum(  -delta_vectors*self.patches[:-1]["norm"],  1  )
##            factors = ((cos_theta_1s*cos_theta_2s)/(pi*(lengths*lengths)))*self.patches[:-1]["area"]
##            delta_e = np.transpose([factors]*3)*self.patches[-1]["residual radiance"]
##            reflected = delta_e*self.patches[:-1]["color"]
##            self.patches[:-1]["accumulated radiance"][:] += reflected
##            self.patches[:-1]["residual radiance"][:] += reflected
            
            self.patches[-1]["residual radiance"][:] = np.array([0.0,0.0,0.0])
            self.iteration += 1;
            print(self.patches[-1]["residual power"])
        print()
        print("Satisfactorily converged.")

    def set_gamma(self,new_gamma):
        self.gamma = new_gamma
            
    def build_list_patches(self):
        self.patches_list = glGenLists(1)
        glNewList(self.patches_list,GL_COMPILE)
        self.draw_direct_patches()
        glEndList()
    def build_list_vertices(self):
        self.list_vertices = glGenLists(1)
        glNewList(self.list_vertices,GL_COMPILE)
        self.draw_direct_vertices()
        glEndList()
        
    def draw_list_patches(self):
        glCallList(self.patches_list)
    def draw_list_vertices(self):
        glCallList(self.list_vertices)
        
    def draw_direct_patches(self):
        glDisable(GL_TEXTURE_2D)
        glDisable(GL_LIGHTING)
        glBegin(GL_QUADS)
        for patch in self.patches:
            color = np.power(patch["accumulated radiance"],self.gamma).tolist()
            color = map(lambda x:clamp(x,0.0,1.0),color)
            glColor3f(*color)
            for vert in patch["polygon"]:
                glVertex3f(*vert)
        glEnd()
        glColor3f(1,1,1)
        glEnable(GL_LIGHTING)
        glEnable(GL_TEXTURE_2D)
    def draw_direct_vertices(self):
        pass
##        for patch in self.patches:
##            for vertex in patch.polygon:
##                self.vertices[vertex].data.append([patch.accumulated_radiance,patch.norm])
##        for vertex in self.vertices.values():
##            avg_normal = [0.0,0.0,0.0]
##            for patch_data in vertex.data:
##                avg_normal = vec_add(avg_normal,patch_data[1])
##            avg_normal = normalize(avg_normal)
##            colors = []
##            scalars = []
##            for patch_data in vertex.data:
##                scalars.append( dot(avg_normal,patch_data[1]) )
##                colors.append( patch_data[0] )
##            color = [0.0,0.0,0.0]
##            if sum(scalars) == 0.0:
##                for color_num in range(len(colors)):
##                    color = vec_add(color,colors[color_num])
##                for element in color:
##                    color = sc_vec(1.0/len(scalars),color)
##            else:
##                for color_num in range(len(colors)):
##                    color = vec_add(color,sc_vec(scalars[color_num],colors[color_num]))
##            vertex.color = color
##            vertex.data = []
##        glDisable(GL_TEXTURE_2D)
##        glDisable(GL_LIGHTING)
##        glBegin(GL_QUADS)
##        for patch in self.patches:
##            for index in range(4):
##                vertex = self.vertices[patch.polygon[index]]
##                glColor3f(*vertex.color)
##                glVertex3f(*vertex.pos)
##        glEnd()
##        glColor3f(1,1,1)
##        glEnable(GL_LIGHTING)
##        glEnable(GL_TEXTURE_2D)













            
