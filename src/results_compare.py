from common import Config
from glob import glob
import os
import numpy as np

class TestResults:
    def __init__(self,test):
        self.test = test
        self.prop = {}
        self.ref = {}
        with open(f'{Config.root_dir}/tests/{self.test}/reference/properties.dat') as f:
            for line in f:
                key,dum,val = line.split()
                self.ref[key] = float(val)
                
                
    def load_result(self,hashsum):
        with open(f'{Config.root_dir}/db/{hashsum}/tests/{self.test}/properties.dat') as f:
            for line in f:
                key,dum,val = line.split()
                self.prop[key] = float(val)
                
        stats = []        
        for pr in self.ref:
            delta=self.prop[pr]-self.ref[pr]
            rel_delta=delta/self.ref[pr]
            print(f'\t{pr:15s}\t{self.prop[pr]:8.3f} ({self.ref[pr]:8.3f})\tΔ: {delta:8.3f}\t({rel_delta*100:8.3f}%)')
            stats.append(abs(rel_delta))
        
        mean = np.mean(stats)
        std = np.std(stats)
        print(f'\t------------\n\t{100*mean:.3f}±{100*std:.3f}%')
        
        return (mean,std)
            
