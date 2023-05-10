from common import Config
from glob import glob
import os

for db_dir in glob(f'{Config.cluster_root_dir}/db/*'):
    db_hash = os.path.basename(db_dir)
    for test_dir in glob(f'{db_dir}/tests/*'):
        test = os.path.basename(test_dir)
        try:
            status = open(f'{test_dir}/STATUS').read().strip()
            print(f'Status of {db_hash}:{test} is "{status}"')
        except:
            print(f'No status file in {db_hash}:{test}!')
