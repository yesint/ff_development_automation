from common import Config
from glob import glob
import os

finished_list = []

for db_dir in glob(f'{Config.cluster_root_dir}/db/*'):
    db_hash = os.path.basename(db_dir)
    for test_dir in glob(f'{db_dir}/tests/*'):
        test = os.path.basename(test_dir)
        try:
            status = open(f'{test_dir}/STATUS').read().strip()
            prop_present = os.path.isfile(f'{test_dir}/properties.dat')
            print(f'Status of {db_hash}:{test} is "{status}", properties: {prop_present} ')
            if status == "analysis finished" and prop_present:
                finished_list.append((db_hash,test))
        except:
            print(f'No status file in {db_hash}:{test}!')
            
print('Writing list of finished tests')
with open(f'{Config.cluster_root_dir}/db/finished_list','w') as f:
    for el in finished_list:
        f.write(f'{el[0]} {el[1]}\n')
