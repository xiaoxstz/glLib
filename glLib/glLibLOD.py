class glLibLODTree:
    def __init__(self,levels):
        self.levels = float(levels)
    def set_clip(self):pass
    def get_rectangles(self,sample_point):
        rectangles = []
        collide_rectangles = []
        pos = map(lambda x:int(round(x)),[sample_point[0]*(2.0**(self.levels-2)),
                                          sample_point[1]*(2.0**(self.levels-2))])
        centers = [pos]
        for level in xrange(int(self.levels),0,-1):
            size = 1.0/(2.0**(level-1))
            
            newrects = []
            for center in centers:
                xpositions = [center[0]*2-2,center[0]*2-1,center[0]*2,center[0]*2+1]
                ypositions = [center[1]*2-2,center[1]*2-1,center[1]*2,center[1]*2+1]
                for xsquare in xpositions:
                    for ysquare in ypositions:
                        rect = [xsquare*size,ysquare*size,size]
                        if rect not in newrects:
                            newrects.append(rect)
            for newrect in newrects:
                adding = True
                if newrect[0]<0.0 or newrect[1]<0.0 or newrect[0]+newrect[2]>1.0 or newrect[1]+newrect[2]>1.0:
                    adding = False
                if adding:
                    for r in collide_rectangles:
                        if r[0]<=newrect[0]<=r[0]+r[2]-newrect[2] and \
                           r[1]<=newrect[1]<=r[1]+r[3]-newrect[2]:
                            adding = False
                            break
                if adding:
                    rectangles.append(newrect)
                    collide_rectangles.append([newrect[0],newrect[1],newrect[2],newrect[2]])
            
            lower = [collide_rectangles[0][0],collide_rectangles[0][1]]
            upper = [collide_rectangles[0][0]+collide_rectangles[0][2],collide_rectangles[0][1]+collide_rectangles[0][3]]
            for rect in collide_rectangles[1:]:
                lower[0] = min([lower[0],rect[0]])
                lower[1] = min([lower[1],rect[1]])
                upper[0] = max([upper[0],rect[0]+rect[2]])
                upper[1] = max([upper[1],rect[1]+rect[3]])
            collide_rectangles = [  [lower[0],lower[1],upper[0]-lower[0],upper[1]-lower[1]]  ]
            
            new_centers = []
            for center in centers:     
                x = center[0] / 2.0
                y = center[1] / 2.0
                fx = int(x); fy = int(y)
                cx = fx + 1; cy = fy + 1
                if x % 1.0 == 0.5:
                    if y % 1.0 == 0.5: to_add = [[fx,fy],[fx,cy],[cx,fy],[cx,cy]]
                    else:              to_add = [[fx,fy],        [cx,fy]        ]
                elif y % 1.0 == 0.5:   to_add = [[fx,fy],[fx,cy]                ]
                else:                  to_add = [[fx,fy]                        ]
                for add in to_add:
                    found = False
                    for added_center in new_centers:
                        if added_center[0] == add[0] and added_center[1] == add[1]:
                            found = True
                            break
                    if not found:
                        new_centers.append(add)
            centers = list(new_centers)
        return rectangles
