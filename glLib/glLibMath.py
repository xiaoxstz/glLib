from glLibLocals import np
from math import *
import random
def random_sphere_vec():
    return normalize([random.gauss(0.0,1.0),random.gauss(0.0,1.0),random.gauss(0.0,1.0)])
def sign(num):
    if num < 0: return -1
    return 1
def clamp(value,low,high):
    if type(value)in [type([]),type(())]:
        result = []
        for element in value:
            result.append(clamp(element,low,high))
        return result
    else:
        return min([high,max([low,value])])
def grid3D(size):
    x_col = np.array(np.repeat(np.arange(size[0]),size[1]*size[2])         ,"f")
    y_col = np.array(np.tile(np.repeat(np.arange(size[1]),size[2]),size[0]),"f")
    z_col = np.array(np.tile(np.arange(size[2]),size[0]*size[1])           ,"f")
    array = np.transpose([x_col,y_col,z_col])
    return array
def const_vec(const,vec): return [const+vec[i] for i in range(len(vec))]
def sc_vec   (   sc,vec): return [sc*vec[i] for i in range(len(vec))]
def vec_add  ( vec1,vec2): return [vec1[i]+vec2[i] for i in range(len(vec1))]
def vec_subt ( vec1,vec2): return [vec1[i]-vec2[i] for i in range(len(vec1))]
def vec_div  ( vec1,vec2): return [vec1[i]/vec2[i] for i in range(len(vec1))]
def vec_mult ( vec1,vec2): return [vec1[i]*vec2[i] for i in range(len(vec1))]
def vec_negate(vec): return map(lambda x:-x,vec)
def same_vec(v1,v2):
    if length(vec_subt(v1,v2))==0.0: return True
    return False
def min_vec(vecs):
    min_vec = [length(vecs[0]),vecs[0]]
    for vec in vecs[1:]:
        min_vec = min([ [length(vecs[0]),vecs[0]], min_vec ])
    return min_vec[1]
def rndint(num):
    try:return int(round(num))
    except:return map(rndint,num)
def length(vec):
    length_sq = 0.0
    for element in vec: length_sq += element*element
    return length_sq**0.5
def normalize(vec):
    vec_length = length(vec)
    if vec_length != 0.0:
        result = []
        for element in vec: result.append(element/vec_length)
        return result
    return [0]*len(vec)
def scale_to_one(vec):
    size = float(sum(vec))
    if size != 0.0:
        result = []
        for element in vec: result.append(element/size)
        return result
    return [0]*len(vec)
def cross(vec1,vec2):
    return [vec1[1]*vec2[2]-vec1[2]*vec2[1],
            vec1[2]*vec2[0]-vec1[0]*vec2[2],
            vec1[0]*vec2[1]-vec1[1]*vec2[0]]
def dot(vec1,vec2):
    result = 0.0
    for index in range(len(vec1)):
        result += vec1[index]*vec2[index]
    return result
def sort_with(l1,l2):
    #Sorts l1 using l2
    pairs = zip(l2,l1)
    pairs.sort()
    return [v[1] for v in pairs]
def abs_angle_between_rad(vec1,vec2):
    return acos(dot(vec1,vec2)/(length(vec1)*length(vec2)))
def abs_angle_between_deg(vec1,vec2):
    return degrees(abs_angle_between_rad(vec1,vec2))
def abs_angle_between_norm_rad(vec1,vec2):
    return acos(dot(vec1,vec2))
def abs_angle_between_norm_deg(vec1,vec2):
    return degrees(abs_angle_between_rad(vec1,vec2))
def angle_between_deg(vec1,vec2,perpendicular=[0,1,0]):
    return degrees(angle_between_rad(vec1,vec2,perpendicular))
def angle_between_rad(vec1,vec2,perpendicular=[0,1,0]):
    return atan2(dot(perpendicular,cross(vec1,vec2)),dot(vec1,vec2))
def get_rotation_matrix_deg(vec,theta):
    return get_rotation_matrix_rad(vec,radians(theta))
def get_rotation_matrix_rad(vec,theta):
    c = cos(theta)
    s = sin(theta)
    C = 1-c
    x,y,z = vec
    xs = x*s;   ys = y*s;   zs = z*s
    xC = x*C;   yC = y*C;   zC = z*C
    xyC = x*yC; yzC = y*zC; zxC = z*xC
    matrix = [[x*xC+c,xyC-zs,zxC+ys],
              [xyC+zs,y*yC+c,yzC-xs],
              [zxC-ys,yzC+xs,z*zC+c]]
    return matrix
def rotate_arbitrary_deg(point,vec,theta):
    theta = radians(theta)
    return rotate_arbitrary_rad(point,vec,theta)
def rotate_arbitrary_rad(point,vec,theta):
    matrix = get_rotation_matrix_rad(vec,theta)
    return glLibMathMultMatrices([[point[0],point[1],point[2]]],matrix)[0]
def glLibMathAugmentMatrix(M,B):
    for r in range(0, len(M)):
        for s in range(0, len(B[r])):
            M[r].append(B[r][s])
    return M
def glLibMathSwapRowMatrix(M,i,j):
    B = M[i]
    M[i] = M[j]
    M[j] = B
    return M
def glLibMathMultMatrices(a,b):
    return [[sum(i*j for i, j in zip(row, col)) for col in zip(*b)] for row in a]
def glLibMathMultRowMatrix(k, M, row):
    for j in range(0, len(M[0])): M[row][j] *= k
    return M
def glLibMathMultRowAddMatrix(k, M, source, dest):
    for j in range(0, len(M[0])): M[dest][j] += M[source][j] * k
    return M
def glLibMathRRefMatrix(M, n = 0):
    if n >= len(M) or n > len(M): return M
    col = -1
    for i in range(n, len(M)):
        raise "WHAT DOES THE BELOW LINE DO?"
        #if M[i][n] <> 0: col = i
        if col != -1:    break
    if col != n: glLibMathSwapRowMatrix(M, col, n)
    if M[n][n] != 1:
        #M[n][n] = int(M[n][n] * (1. / M[n][n]))
        glLibMathMultRowMatrix(1. / M[n][n], M, n)
    for i in range(0, len(M)):
        if i == n: continue
        if M[i][n] != 0: glLibMathMultRowAddMatrix(-M[i][n], M, n, i)
    glLibMathRRefMatrix(M, n + 1)
    return M
def glLibMathDelColMatrix(B, j):
    for r in range(0,len(B)):
        B[r].pop(j)
    return B
def glLibMathIdentMatrix(size):
    C = []
    for r in range(0, size):
        C.append([])
        for c in range(0, size):
            if c == r: C[r].append(1)
            else:      C[r].append(0)
    return C
def glLibMathGetListMatrix(A):
    A = [[A[0][0],A[0][1],A[0][2],A[0][3]],
         [A[1][0],A[1][1],A[1][2],A[1][3]],
         [A[2][0],A[2][1],A[2][2],A[2][3]],
         [A[3][0],A[3][1],A[3][2],A[3][3]]]
    return A
def glLibMathRotateMatrix(A):
    A = [[A[0][0],A[1][0],A[2][0],A[3][0]],
         [A[0][1],A[1][1],A[2][1],A[3][1]],
         [A[0][2],A[1][2],A[2][2],A[3][2]],
         [A[0][3],A[1][3],A[2][3],A[3][3]]]
    return A
def glLibMathTruncate4x4to3x3(A):
    A = [[A[0][0],A[0][1],A[0][2]],
         [A[1][0],A[1][1],A[1][2]],
         [A[2][0],A[2][1],A[2][2]]]
    return A
def glLibMathInvertMatrix(A):
    l = len(A)
    A = glLibMathAugmentMatrix(A,glLibMathIdentMatrix(l))
    A = glLibMathRRefMatrix(A)
    for i in range(0, l):
        A = glLibMathDelColMatrix(A, 0)
    return A
def determinant(M):
    #http://stackoverflow.com/questions/462500/can-i-get-the-matrix-determinant-by-numpy
    return np.linalg.det(np.array(M))
def glLibMathPlanarProjectionMatrix(plane,light_position):
    #http://www.ia.hiof.no/~borres/cgraph/explain/shadow/p-shadow.html
    shadow_mat = [0,0,0,0,
                  0,0,0,0,
                  0,0,0,0,
                  0,0,0,0]
    
    d = dot(plane[:3],light_position)

    light_position = light_position+[0]

    shadow_mat[0]  = d - light_position[0] * plane[0];
    shadow_mat[4]  = -light_position[0] * plane[1];
    shadow_mat[8]  = -light_position[0] * plane[2];
    shadow_mat[12] = -light_position[0] * plane[3];

    shadow_mat[1]  = -light_position[1] * plane[0];
    shadow_mat[5]  = d - light_position[1] * plane[1];
    shadow_mat[9]  = -light_position[1] * plane[2];
    shadow_mat[13] = -light_position[1] * plane[3];

    shadow_mat[2]  = -light_position[2] * plane[0];
    shadow_mat[6]  = -light_position[2] * plane[1];
    shadow_mat[10] = d - light_position[2] * plane[2];
    shadow_mat[14] = -light_position[2] * plane[3];

    shadow_mat[3]  = -light_position[3] * plane[0];
    shadow_mat[7]  = -light_position[3] * plane[1];
    shadow_mat[11] = -light_position[3] * plane[2];
    shadow_mat[15] = d - light_position[3] * plane[3];

    return shadow_mat;
##def cone_ray(ray_origin,ray_direction, cone_vertex,cone_axis,cone_angle):
##    #http://www.geometrictools.com/LibFoundation/Intersection/Wm4IntrLine3Cone3.cpp
##    #Set up the quadratic Q(t) = c2*t^2 + 2*c1*t + c0 that corresponds to
##    #the cone.  Let the vertex be V, the unit-length direction vector be A,
##    #and the angle measured from the cone axis to the cone wall be Theta,
##    #and define g = cos(Theta).  A point X is on the cone wall whenever
##    #Dot(A,(X-V)/|X-V|) = g.  Square this equation and factor to obtain
##    #  (X-V)^T * (A*A^T - g^2*I) * (X-V) = 0
##    #where the superscript T denotes the transpose operator.  This defines
##    #a double-sided cone.  The line is L(t) = P + t*D, where P is the line
##    #origin and D is a unit-length direction vector.  Substituting
##    #X = L(t) into the cone equation above leads to Q(t) = 0.  Since we
##    #want only intersection points on the single-sided cone that lives in
##    #the half-space pointed to by A, any point L(t) generated by a root of
##    #Q(t) = 0 must be tested for Dot(A,L(t)-V) >= 0.
##    fAdD = dot(cone_axis,line_direction)
##    fCosSqr = cos(radians(cone_angle))**2.0
##    kE = vec_subt(line_origin,cone_vertex)
##    fAdE = dot(cone_axis,kE)
##    fDdE = dot(line_direction,kE)
##    fEdE = dot(kE,kE)
##    fC2 = fAdD*fAdD - fCosSqr
##    fC1 = fAdD*fAdE - fCosSqr*fDdE
##    fC0 = fAdE*fAdE - fCosSqr*fEdE
##
##    #Solve the quadratic.  Keep only those X for which Dot(A,X-V) >= 0.
##    if fC2 != 0.0: #c2 != 0
##        fDiscr = fC1*fC1 - fC0*fC2
##        if fDiscr < 0.0: #Q(t) = 0 has no real-valued roots.  The line does not intersect the double-sided cone.
##            return None
##        elif fDiscr > 0.0:
##            #Q(t) = 0 has two distinct real-valued roots.  However, one or
##            #both of them might intersect the portion of the double-sided
##            #cone "behind" the vertex.  We are interested only in those
##            #intersections "in front" of the vertex.
##            fRoot = fDiscr ** 0.5
##            fInvC2 = 1.0 / fC2
##            m_iQuantity = 0
##
##            fT = (-fC1-fRoot)*fInvC2
##            m_akPoint[m_iQuantity] = vec_add(line_origin,sc_vec(fT,line_direction))
##            kE = vec_subt(m_akPoint[m_iQuantity],cone_vertex)
##            fDot = dot(kE,cone_axis)
##            if fDot > 0.0: m_iQuantity += 1
##
##            fT = (-fC1+fRoot)*fInvC2
##            m_akPoint[m_iQuantity] = vec_add(line_origin,sc_vec(fT,line_direction))
##            kE = vec_subt(m_akPoint[m_iQuantity],cone_vertex)
##            fDot = dot(kE,cone_axis)
##            if fDot > 0.0: m_iQuantity += 1
##            
##            if m_iQuantity == 2: #The line intersects the single-sided cone in front of the vertex twice.
##                m_iIntersectionType = IT_SEGMENT
##            elif m_iQuantity == 1:
##                #The line intersects the single-sided cone in front of the
##                #vertex once.  The other intersection is with the
##                #single-sided cone behind the vertex.
##                m_iIntersectionType = IT_RAY
##                m_akPoint[m_iQuantity+1] = line_direction
##            else: #The line intersects the single-sided cone behind the vertex twice.
##                return None
##        else: #one repeated real root (line is tangent to the cone)
##            m_akPoint[0] = line_origin - (fC1/fC2)*line_direction
##            kE = vec_subt(m_akPoint[0],cone_vertex)
##            if dot(kE,cone_axis) > 0.0:
##                m_iIntersectionType = IT_POINT
##                m_iQuantity = 1
##                return [m_akPoint[0]]
##            else:
##                return None
##    elif fC1 != 0.0:
##        #c2 = 0, c1 != 0 (D is a direction vector on the cone boundary)
##        m_akPoint[0] = line_origin - sc_vec(0.5*fC0/fC1,line_direction)
##        kE = vec_subt(m_akPoint[0],cone_vertex)
##        fDot = dot(kE,cone_axis)
##        if fDot > 0.0:
##            m_iIntersectionType = IT_RAY
##            m_iQuantity = 2
##            m_akPoint[1] = line_direction
##        else:
##            return None
##    elif fC0 != 0.0: #c2 = c1 = 0, c0 != 0
##        return None
##    else: #c2 = c1 = c0 = 0, cone contains ray V+t*D where V is cone vertex and D is the line direction.
##        return [cone_vertex]
def triangle_area(v1,v2,v3):
    a = length(vec_subt(v2,v1))
    b = length(vec_subt(v3,v2))
    c = length(vec_subt(v1,v3))
    s = (a+b+c)/2.0
    try: return (s*(s-a)*(s-b)*(s-c))**0.5
    except: return 0.0
def quadrilateral_area(v1,v2,v3,v4):
    #http://www.wikihow.com/Find-the-Area-of-a-Quadrilateral
    a = length(vec_subt(v2,v1))
    b = length(vec_subt(v3,v2))
    c = length(vec_subt(v4,v3))
    d = length(vec_subt(v1,v4))
    p = length(vec_subt(v1,v3))
    q = length(vec_subt(v2,v4))
    s = (a+b+c+d)/2.0
    return ( (s-a)*(s-b)*(s-c)*(s-d) - 0.25*(a*c+b*d+p*q)*(a*c+b*d-p*q) )**0.5
class spline:
    def __init__(self,control_values,loop=False):
        self.control_values = list(control_values)
        if not loop:
            self.control_values = [self.control_values[0]]+self.control_values+[self.control_values[-1]]
        else:
            self.control_values = [self.control_values[-2]]+self.control_values+[self.control_values[1]]
        t=b=c=0
        self.tans = []
        self.tand = []
        for x in range(len(self.control_values)-2):
            self.tans.append([])
            self.tand.append([])
        cona = (1-t)*(1+b)*(1-c)*0.5
        conb = (1-t)*(1-b)*(1+c)*0.5
        conc = (1-t)*(1+b)*(1+c)*0.5
        cond = (1-t)*(1-b)*(1-c)*0.5
        i = 1
        while i < len(self.control_values)-1:
            pa = self.control_values[i-1]
            pb = self.control_values[i]
            pc = self.control_values[i+1]
            x1 = pb - pa
            x2 = pc - pb
            self.tans[i-1] = cona*x1+conb*x2
            self.tand[i-1] = conc*x1+cond*x2
            i += 1
    def get_at(self,value):
        num_sections = len(self.control_values) - 3
        index = 1.0 + value*(len(self.control_values)-3.0)
        value = index - int(index)
        index = int(index)
        p0 = self.control_values[index]
        p1 = self.control_values[index+1]
        m0 = self.tand[index-1]
        m1 = self.tans[index]
        h00 = ( 2*(value**3)) - ( 3*(value**2)) + 1
        h10 = ( 1*(value**3)) - ( 2*(value**2)) + value
        h01 = (-2*(value**3)) + ( 3*(value**2))
        h11 = ( 1*(value**3)) - ( 1*(value**2))
        return h00*p0 + h10*m0 + h01*p1 + h11*m1
def distance_to_line_segment(point,p0,p1):
    #http://softsurfer.com/Archive/algorithm_0102/algorithm_0102.htm#Distance%20to%20Ray%20or%20Segment
    v = vec_subt(p1,p0)
    w = vec_subt(point,p0)
    c1 = dot(w,v)
    if c1 <= 0.0: return length(vec_subt(point,p0))
    c2 = dot(v,v)
    if c2 <= c1: return length(vec_subt(point,p1))
    b = c1 / c2
    pb = vec_add(p0,sc_vec(b,v))
    return length(vec_subt(point,pb))
def polygon_area(points):
    if len(points[0]) == 2: #2D
        #http://www.mathwords.com/a/area_convex_polygon.htm
        points = points + [points[0]]
        area = 0
        for index in range(len(points)-1):
            matrix = [[points[index  ][0],points[index  ][1]],
                      [points[index+1][0],points[index+1][1]]]
            det_matrix = determinant(matrix)
            area += det_matrix
        area = 0.5*area
    elif len(points[0]) == 3: #3D
        #http://softsurfer.com/Archive/algorithm_0101/algorithm_0101.htm
        points = points + [points[0]]
        result = [0.0,0.0,0.0]
        for index in range(len(points)-1):
            result = vec_add(result,cross(points[index],points[index+1]))
        normal = normalize(cross(vec_subt(points[0],points[1]),vec_subt(points[1],points[2])))
        area = dot(normal,result)/2.0
    return abs(area)
def reflect_point(point, normal,plane_point):
    #http://en.wikipedia.org/wiki/Reflection_%28mathematics%29
    #eliminates 1/dot(normal,normal) term by assuming that the normal is normalized
    point = vec_subt(point,plane_point)
    point = vec_subt( point, sc_vec(2.0*dot(point,normal),normal) )
    point = vec_add(point,plane_point)
    return point
def is_between(x,a,b):
##    print "is_between(...)"
##    print "  x =",x
##    print "  a =",a
##    print "  b =",b
    a_b_diff = normalize(vec_subt(a,b))
##    print "  a_b_diff =",a_b_diff
    d1 = dot(normalize(vec_subt(x,b)),            a_b_diff)
    d2 = dot(normalize(vec_subt(x,a)),sc_vec(-1.0,a_b_diff))
    if d1>0.0 and d2>0.0: return 1
    if d1>=0.0 and d2>=0.0: return 2
    return 0
def ray_sphere(raypos,raydir,spherepos,sphereradius):
    p = vec_subt(raypos,spherepos)
    b = -dot(p,raydir)
    det = b*b - dot(p,p) + sphereradius*sphereradius
    if det < 0.0: return False
    det = det ** 0.5
    i1 = b - det
    i2 = b + det
    if i2 < 0.0: return False
    if i1 < 0.0: return False
    return min(i1,i2)
def line_line_3D(p1,p2, p3,p4, eps):
    #adapted from
    #http://local.wasp.uwa.edu.au/~pbourke/geometry/lineline3d/
    p43 = vec_subt(p4,p3); p43n = normalize(p43)
    if length(p43)<eps: return False
    p21 = vec_subt(p2,p1); p21n = normalize(p21)
    if length(p21)<eps: return False
    p13 = vec_subt(p1,p3)
    p24 = vec_subt(p2,p4)
##    print abs(abs(dot(p43n,p21n))-1.0),"?<",eps
    if abs(abs(dot(p43n,p21n))-1.0)<eps:
##        print "yes; lines are parallel!"
##        print "",abs(abs(dot(normalize(p13),p21n))-1.0)
        #lines are parallel
        if abs(abs(dot(normalize(p13),p21n))-1.0)<eps:
##            print "lines overlap!"
##            raw_input()
            #lines overlap
            return True
##        print "lines do not overlap"
##        raw_input()
        return False
##    print "no; lines not parallel"
##    raw_input()

    d1343 = dot(p13,p43)
    d4321 = dot(p43,p21)
    d1321 = dot(p13,p21)
    d4343 = dot(p43,p43)
    d2121 = dot(p21,p21)

    denom = d2121 * d4343 - d4321 * d4321
    if denom==0.0: return False
    numer = d1343 * d4321 - d1321 * d4343

    mua = numer / denom
    mub = (d1343 + d4321*mua) / d4343

    pa = vec_add(p1,sc_vec(mua,p21))
    pb = vec_add(p3,sc_vec(mub,p43))
    return pa,pb

def point_triangle_3D(point,triangle,eps):
    #Adapted from http://www.blackpawn.com/texts/pointinpoly/default.html
    #Assumes point is known to be coplanar with triangle
    #Implicitly projects to 2D by ignoring the y coordinate
    #but rotates the whole problem if this would cause a degenerate case.
    #Returns 1 (inside), 2, (on edge or corner), 0 (neither)
    if length(vec_subt(point,triangle[0]))<eps: return 2
    if length(vec_subt(point,triangle[1]))<eps: return 2
    if length(vec_subt(point,triangle[2]))<eps: return 2
    if cross(vec_subt(triangle[2],triangle[0]),vec_subt(triangle[2],triangle[1]))[1] == 0.0:
##        print "rotating!"
        axis = normalize([1.0,1.0,1.0])
        A = rotate_arbitrary_deg(triangle[0],axis,30.0)
        B = rotate_arbitrary_deg(triangle[1],axis,30.0)
        C = rotate_arbitrary_deg(triangle[2],axis,30.0)
        P = rotate_arbitrary_deg(      point,axis,30.0)
        A = [A[0],A[2]]
        B = [B[0],B[2]]
        C = [C[0],C[2]]
        P = [P[0],P[2]]
    else:
        P = [point[0],point[2]]
        A = [triangle[0][0],triangle[0][2]]
        B = [triangle[1][0],triangle[1][2]]
        C = [triangle[2][0],triangle[2][2]]
    v0 = vec_subt(C,A)
    v1 = vec_subt(B,A)
    v2 = vec_subt(P,A)
    dot00 = dot(v0,v0)
    dot01 = dot(v0,v1)
    dot02 = dot(v0,v2)
    dot11 = dot(v1,v1)
    dot12 = dot(v1,v2)
    invDenom = 1.0 / (dot00*dot11-dot01*dot01)
    u = (dot11*dot02-dot01*dot12) * invDenom
    v = (dot00*dot12-dot01*dot02) * invDenom
    if u>eps and v>eps and u+v<1.0+eps:
        return 1
    elif u>-eps and v>-eps and u+v<1.0+eps:
        return 2
    else:
        return 0
def ray_triangle(raypos,raydir,triangle):
    #http://geometryalgorithms.com/Archive/algorithm_0105/algorithm_0105.htm#intersect_RayTriangle()
    p1,p2,p3 = triangle
    u = vec_subt(p2,p1)
    v = vec_subt(p3,p1)
    n = normalize(cross(u,v))

    v1 = vec_subt(p1,raypos)

    a = -dot(n,vec_negate(v1))
    b = dot(n,raydir)
    if abs(b) <= 0.0: #ray is parallel to triangle plane
        return False #=> no intersect

    #get intersect point of ray with triangle plane
    r = a / b
    if r < 0.0: #ray goes away from triangle
        return False #=> no intersect

    #for a segment, also test if (r > 1.0) => no intersect
    I = sc_vec(r,raydir)#intersect point of ray and plane

    #is I inside the triangle?
    uu = dot(u,u)
    uv = dot(u,v)
    vv = dot(v,v)
    w = vec_subt(I,v1)
    wu = dot(w,u)
    wv = dot(w,v)
    D = uv * uv - uu * vv

    #get and test parametric coords
    s = (uv * wv - vv * wu) / D
    if s < 0.0 or s > 1.0: #I is outside the triangle
        return False #=> no intersect
    t = (uv * wu - uu * wv) / D
    if t < 0.0 or (s + t) > 1.0: #I is outside the triangle
        return False #=> no intersect
 
    return vec_add(I,raypos) #I is in the triangle
def glLibInternal_CalculateTangentArray(triangle):#[[v1,v2,v3],[t1,t2,t3],[n1,n2,n3]]
    vertex1 = triangle[0][0]
    vertex2 = triangle[0][1]
    vertex3 = triangle[0][2]
    texcoord1 = triangle[1][0]
    texcoord2 = triangle[1][1]
    texcoord3 = triangle[1][2]
    x1 = vertex2[0]-vertex1[0]
    x2 = vertex3[0]-vertex1[0]
    y1 = vertex2[1]-vertex1[1]
    y2 = vertex3[1]-vertex1[1]
    z1 = vertex2[2]-vertex1[2]
    z2 = vertex3[2]-vertex1[2]
    s1 = texcoord2[0]-texcoord1[0]
    s2 = texcoord3[0]-texcoord1[0]
    t1 = texcoord2[1]-texcoord1[1]
    t2 = texcoord3[1]-texcoord1[1]
    divisor = ((s1*t2)-(s2*t1))
    if divisor == 0:
        divisor = 0.01
    r = 1.0/divisor
    sdir = ((t2*x1-t1*x2)*r,(t2*y1-t1*y2)*r,(t2*z1-t1*z2)*r)
    tdir = ((s1*x2-s2*x1)*r,(s1*y2-s2*y1)*r,(s1*z2-s2*z1)*r)
    tangents = []
    for i in range(3):
        n = triangle[2][i]
        t = sdir
        tangent = normalize(vec_subt(t,sc_vec(dot(n,t),n)))
        if dot(cross(n,t),tdir) < 0.0: tangent.append(-1.0)
        else:                          tangent.append( 1.0)
        tangents.append(list(map(float,tangent)))
##    print "Vertices:",[vertex1,vertex2,vertex3]
##    print "Tangents:",tangents
    return tangents
