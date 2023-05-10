from pteros import *
import numpy as np

class Analysis(TaskBase):

    def pre_process(self):
        #Selection for the membrane COM
        self.membr = self.system('resname POPC and noh')
        # Number of lipids
        self.Nlipids = self.membr('name P').size()
        # Selections for density distributions
        self.head = self.membr('name N "C1[12345]"')
        self.head_masses = self.head.get_mass()
        #self.po4 = self.membr('name P "O[1234]')
        # Histograms for density
        self.head_hist = Histogram(0,3.5,200)
        # area 
        self.xy_area = 0.0
        # pbc
        self.pbcZ = np.array([0,0,1])
        # Head tilt
        self.head_NP = self.membr('name N P').split_by_residue()
        self.head_tilt = 0.0


    def process_frame(self,info):
        box = self.system.getBox()
        # Get membrane center
        cm = self.membr.center(mass_weighted=True,pbc=self.pbcZ)
        # Density
        z = [box.shortest_vector(v,cm,pbc=self.pbcZ)[2] for v in self.head.get_xyz()]
        self.head_hist.add(z,self.head_masses)
        # Area
        self.xy_area += box.extent(0)*box.extent(1)
        # Head group tilt
        for sel in self.head_NP:
            v = box.shortest_vector(sel[0].xyz,sel[1].xyz)
            z = box.shortest_vector(sel[0].xyz,cm)[2]
            # Invert for lower monolayer
            if z<0:
                v*=-1
            self.head_tilt += np.degrees(angle_between_vectors(v,self.pbcZ))
            

    def post_process(self,info):
        # Head density
        self.head_hist.normalize()
        self.head_hist.save_to_file('head_density.dat')
        # Get membrane thikness
        i=np.argmax(self.head_hist.values)
        head_head_d = 2.0*self.head_hist.positions[i]
        # Area per lipid
        area_per_lipid = self.xy_area/info.valid_frame/(self.Nlipids/2)
        # Head tils
        head_tilt = self.head_tilt/info.valid_frame/self.Nlipids
        
        # Output properties
        with open('properties.dat','w') as out:
            out.write(f'head_head_d = {head_head_d:.3f}\n')
            out.write(f'area_per_lipid = {area_per_lipid:.3f}\n')
            out.write(f'head_tilt = {head_tilt:.3f}\n')
        
