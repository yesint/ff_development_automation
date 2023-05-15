#!/bin/env python3

from subprocess import call, check_output
from results_compare import TestResults
import argparse
from pathlib import Path
from glob import glob
import os
import shutil

#--------------
from common import Config, CRC32_from_file
#--------------

def update_tests(db_dir):
    hashsum = os.path.basename(db_dir)
    print(f'Updating tests for {hashsum}')
    # Retrieve list of tests
    for test_name in open(f'{db_dir}/tests.lst').readlines():
        test_name = test_name.strip('\n\r\t ')
        # See if we have a template for this test
        if os.path.isdir(f'{Config.root_dir}/tests/{test_name}'):
            # Copy content of the test template folder
            call(f'mkdir -p {db_dir}/tests/{test_name}', shell=True)
            call(f'cp -rL {Config.root_dir}/tests/{test_name}/template/* {db_dir}/tests/{test_name}', shell=True)
            # copy params.itp to a toppar of the test folder
            call(f'cp {db_dir}/params.itp {db_dir}/tests/{test_name}/toppar/', shell=True)
            # Set hash in job file
            call(f'sed -i s/%HASH%/{hashsum}/  {db_dir}/tests/{test_name}/job', shell=True)
            print(f'\tUpdated test {test_name}')
        else:
            print(f'\tNo template for test {test_name}, skipping')


#--------------

parser = argparse.ArgumentParser(prog="ff-manage")
parser.add_argument('-a','--add',
                    nargs='*',
                    required=False,
                    metavar='path',
                    help='Add new sets of parameters')
parser.add_argument('-c','--check',
                    nargs='+',
                    required=False,
                    metavar='hash',
                    help='Check the status of given sets of parameters')
parser.add_argument('--check-all',
                    action='store_true',
                    required=False,
                    help='Check the status of all parameters')
parser.add_argument('--get-results',
                    action='store_true',
                    required=False,
                    help='Check status of cluster jobs and retrieve the results')
parser.add_argument('--send-db',
                    action='store_true',
                    required=False,
                    help='Send whole db to cluster')
parser.add_argument('--update-tests',
                    action='store_true',
                    required=False,
                    help='Update test rules for all db entries locally')
parser.add_argument('--compare-results',
                    action='store_true',
                    required=False,
                    help='Compare results of tests with reference')


args = parser.parse_args()


if args.add!=None:
    if len(args.add)==0:
        args.add.append(f'{Config.root_dir}/current_params')
        
    print(f'Adding {len(args.add)} sets parameters')
    
    for par_dir in args.add:
        print(f'Adding parameter set from "{par_dir}"')
        # See if we have any .par files
        par_files = glob(f'{par_dir}/*.par')
        nf = len(list(par_files))
        if nf==0:
            print(f'Directory contains no .par files!')
        else:
            print(f'Directory contains {nf} .par files')
            
            call("""
            cat %s/*.par \
            | grep -vP "#" | sed -r 's/\s+//g' \
            | sed '/^$/d' | sort  \
            | awk -F '=' '{print "#define",$1,$2}' > %s/params.itp
            """ % (par_dir,par_dir) ,shell=True)
            
            hash = CRC32_from_file(f"{par_dir}/params.itp")
            
            print(f'Generated params.itp, hash={hash}')
            
            # Checking the database
            db_dir = f'{Config.root_dir}/db/{hash}'
            if not os.path.isdir(db_dir):
                print(f'Creating new DB directory {hash}')
                os.mkdir(db_dir)
            else:
                print(f'DB directory for {hash} already exists')
            
            print(f'Copying .par files to {hash}')
            # Move processed parameters file
            call(f'mv {par_dir}/params.itp {db_dir}', shell=True)
            # Copy raw .par files to a dedicated directory
            call(f'mkdir -p {db_dir}/par_files', shell=True)
            call(f'cp {par_dir}/*.par {db_dir}/par_files', shell=True)

            # Copy tests list
            print('Processing tests')
            call(f'cp {par_dir}/tests.lst {db_dir}', shell=True)

            # Create tests directory in db
            call(f'mkdir -p {db_dir}/tests', shell=True)

            update_tests(db_dir)

            # Transfer db entry to a cluster
            print(f'Sending {hash} to cluster...')
            call(f'rsync -aPr -e "ssh" {db_dir} {Config.ssh_host}:{Config.cluster_root_dir}/db >/dev/null', shell=True)
            print(f'Done adding {hash}\n')


if args.send_db:
    print(f'Sending db to cluster...')
    call(f'rsync -aPr -e "ssh" {Config.root_dir}/db {Config.ssh_host}:{Config.cluster_root_dir} >/dev/null', shell=True)
    print(f'Done sending db.\n')


if args.update_tests:
    # Update tests for all db entries
    for db_dir in glob(f'{Config.root_dir}/db/*'):
        update_tests(db_dir)


if args.check:
    for hash in args.check:
        print(f'Checking status of {hash}:')

        # See if such db entry exists
        db_dir = f'{Config.root_dir}/db/{hash}'
        if not os.path.isdir(db_dir):
            print(f'{hash} DOES NOT exists locally')
        else:
            print(f'{hash} exists locally')

            # Check if db entry exists on cluster
            remote_dir = f'{cluster_root_dir}/db/{hash}'
            ret = call(f'ssh {ssh_host} [ -d {remote_dir} ]', shell=True)
            if ret!=0:
                print(f'{hash} DOES NOT exists on cluster')
            else: # 0 return code
                print(f'{hash} exists on cluster')
                # Check the execution status for all tests
                # Get sttaus of all tests
                cmd = f'ssh {Config.ssh_host} "cd {remote_dir}/tests; for d in *; do [ -f \$d/STATUS ] && echo -n \$d: && cat \$d/STATUS; done"'
                #print(cmd)
                try:
                    res = check_output(cmd,shell=True,encoding='UTF8').strip()
                    print(f'Test status:\n{res}')
                except:
                    print('No tests results')


if args.get_results:
    print(f'Sending scripts to cluster...')
    call(f'rsync -aPr -e "ssh" {Config.root_dir}/src {Config.ssh_host}:{Config.cluster_root_dir} >/dev/null', shell=True)

    # Run cluster side script
    print(f'Running cluster-side script...')
    call(f'ssh {Config.ssh_host} "python3 {Config.cluster_root_dir}/src/check_status_on_cluster.py"', shell=True)
    
    print('Getting results of finished tests...')
    call(f'rsync -aPr -e "ssh" {Config.ssh_host}:{Config.cluster_root_dir}/db/finished_list {Config.root_dir}/tmp >/dev/null', shell=True)
    
    # Make list of files to download
    with open(f'{Config.root_dir}/tmp/download_list','w') as f:
        for line in open(f'{Config.root_dir}/tmp/finished_list'):
            hashsum,test = line.split()
            f.write(f'db/{hashsum}/tests/{test}/properties.dat\n')
            print(f'\t{hashsum}:{test}')

    # Perform download
    call(f'rsync -aPr -e "ssh" --no-dirs --files-from={Config.root_dir}/tmp/download_list {Config.ssh_host}:{Config.cluster_root_dir} {Config.root_dir} > /dev/null', shell=True)
    

if args.compare_results:
    db_dirs = glob(f'{Config.root_dir}/db/*')
    # Cycle over tests
    for test in glob(f'{Config.root_dir}/tests/*'):
        test = os.path.basename(test)
        tr = TestResults(test)
        print(f'Test {test}:')
        # Cycle over db entries
        for db_dir in db_dirs:
            db_dir = os.path.basename(db_dir)
            print(f'{db_dir}:')
            tr.load_result(db_dir)
    
