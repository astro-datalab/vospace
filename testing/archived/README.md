- [TESTING](#testing)
  - [Contents:](#contents)
    - [test_vospace_API.py](#test_vospace_apipy)
      - [Testing Levels](#testing-levels)
        - [Levels](#levels)
          - [Level 0](#level-0)
          - [Level 1](#level-1)
          - [Level 2](#level-2)
          - [Level 3](#level-3)
          - [Level 4](#level-4)
          - [Level 5](#level-5)
          - [Level 6](#level-6)
    - [runlots](#runlots)
    - [stats](#stats)
  - [QA Testing](#qa-testing)
    - [Results](#results)
      - [12 UWSGI and 48 concurrent scripts](#12-uwsgi-and-48-concurrent-scripts)
      - [Comparison between new version vs old production version](#comparison-between-new-version-vs-old-production-version)
        - [Only one script running](#only-one-script-running)
        - [Four scripts running concurrently](#four-scripts-running-concurrently)
        - [Ten scripts running concurrently](#ten-scripts-running-concurrently)


# TESTING
The testing provided here is not an automated unit testing that exclusively focuses on VOSpace programming logic, 
but rather a manual dependency test that goes all the way from the python client side, to the storagemanager, 
to the VOSpace and back.\
It also provides a crude way to perform batch or load testing.\
The python script was mostly drawn from the `storagemanager` `test_client.py` script.

## Contents:
There are just three scripts:

* ``test_vospace_API.py`` :\
  python scripts, requires the datalab storeClient library, really, only the storeClient.py
* ``runlots`` :\
  bash script, runs a batch of test_vospace_API.py
* ``stats`` :\
  runs crude stats on the log file output of the python script.
 
### test_vospace_API.py
Python script, very similar to the `storagemanager` `test_client.py` script. In this script we've added a number 
of difficulty **_Levels_**, ranging from 0 (the easiest) to 6 (the most difficult) but only 0 to 5 available 
from the command line.

####Testing Levels
We provide 7 testing levels from 0 to 6, although only 0 to 5 available via arguments.
Each level has a specific focus, and higher levels mean bigger load to the system in general, but particularly 
to the VOSpace.

#####Levels
######Level 0
#######Purpose:
This is a pipe cleaning level. Deletes the directory if already there, initializes the test directory system and
cleans up before leaving.
#######Steps:
* Initialization steps:\
  * Remove previous parent test directory\
  * Create parent and children test directories
    * &lt;parent dir&gt;/Z
    * &lt;parent dir&gt;/Z/Y
    * &lt;parent dir&gt;/Z/W
    * &lt;parent dir&gt;/R
* Cleanup\
.- Remove parent test directory and all children.
  
**All other levels also contain the Level 0 logic, which we will not repeat below**

######Level 1
#######Purpose:
Touches most APIs in the VOSpace but with a light touch.
#######Steps:
* Level 0
* LIST List archive container [vos://datalab.noao!vospace/ls_dr8/south/tractor/275]
* UPLOAD 1 random file to &lt;parent dir&gt;/R
* DOWNLOAD and md5sum uploaded file
* MOVE uploaded files from &lt;parent dir&gt;/R to &lt;parent_dir&gt;/Z
* LINK &lt;parent dir&gt;/Z/R to &lt;parent dir&gt;/L

######Level 2
#######Purpose:
Similar to Level 1 with one more Upload/Download and a link to the archive directory.
#######Steps:
* Level 0
* LIST archive container [vos://datalab.noao!vospace/ls_dr8/south/tractor/275]
* UPLOAD 2 random files to &lt;parent dir&gt;/R
* DOWNLOAD and md5sum uploaded file
* MOVE uploaded files from &lt;parent dir&gt;/R to &lt;parent_dir&gt;/Z
* LINK vos://datalab.noao!vospace/ls_dr8/south/tractor/275 to &lt;parent dir&gt;/L

######Level 3
#######Purpose:
It adds to the level 2 one more upload and download plus the copy to your local space of a 1GB of archive data.
Running more than 48 processes will be a heavy I/O load in the system.

#######Steps:
* Level 0
* LIST archive container [vos://datalab.noao!vospace/ls_dr8/south/tractor/275]
* COPY archive container from [vos://datalab.noao!vospace/ls_dr8/south/tractor/275] to [&lt;parent dir&gt;/Z/Y]
* UPLOAD 3 random files to &lt;parent dir&gt;/R
* DOWNLOAD and md5sum uploaded file
* MOVE uploaded files from &lt;parent dir&gt;/R to &lt;parent_dir&gt;/Z
* LINK &lt;parent dir&gt;/Z/R to &lt;parent dir&gt;/L

######Level 4
#######Purpose:
Very similar to Level 3 but with one more upload and a creation of a symlink to the archive directory instead of 
the local directory.
#######Steps:
* Level 0
* LIST archive container [vos://datalab.noao!vospace/ls_dr8/south/tractor/275]
* COPY vos://datalab.noao!vospace/ls_dr8/south/tractor/275 to test &lt;parent dir&gt;/Z/Y test directory
* UPLOAD 4 random files to &lt;parent dir&gt;/R
* DOWNLOAD and md5sum uploaded files
* MOVE uploaded files from &lt;parent dir&gt;/R to &lt;parent_dir&gt;/Z
* LINK vos://datalab.noao!vospace/ls_dr8/south/tractor/275 to &lt;parent dir&gt;/L

######Level 5
#######Purpose:
Similar to Level 1 and 2, with a little bit more of IO but with an important database load as it
performs a heavy subquery in archive directory containing >36K children/files.
This level is heavy in database and network

#######Steps:
* Level 0
* LIST archive container [vos://datalab.noao!vospace/ls_dr8/calib/wise/modelsky]
* UPLOAD 5 random files to &lt;parent dir&gt;/R
* DOWNLOAD and md5sum uploaded files
* MOVE uploaded files from &lt;parent dir&gt;/R to &lt;parent_dir&gt;/Z
* LINK vos://datalab.noao!vospace/ls_dr8/calib/wise/modelsky to &lt;parent dir&gt;/L

######Level 6
#######Purpose:
This level is massive in IO. Running one script will lock two or three threads on the VOSpace for a long time.
It is like adding a steady load to the system. Then you could stress test the system with a Level 1, 2 or 5 
and see how it responds.

#######Steps:
* Level 0
* LIST archive container [vos://datalab.noao!vospace/ls_dr8/calib/wise/modelsky]
* COPY vos://datalab.noao!vospace/ls_dr8/calib/wise/modelsky to test &lt;parent dir&gt;/Z/Y test directory [484 GB]
* UPLOAD 6 random files to &lt;parent dir&gt;/R
* MOVE archive copy from &lt;parent dir&gt;/Z/Y to &lt;parent_dir&gt;/Z/W
* LINK vos://datalab.noao!vospace/ls_dr8/south/tractor/275 to &lt;parent dir&gt;/L

###runlots
It's a script that allows batching.\
The below example spawns 10 concurrent scripts

**E.g.**\
```./runlots -n 10 -l 5 -sm http://vostest.datalab.noirlab.edu:3031 -t testuser.3666.3666./ABCDEFG/ZWUVPRST/% -s qa_gp05_test```

###stats
Runs crude stats on the log file output.\
**E.g.**\
```./stats qa_gp05_test```
```
FAILS:0
FAILED scripts: 0
Finalized scripts: 10
avg in secs per script = 25.185
```

## QA testing
We performed the tests mostly from gp05, gp04 and sometimes gp03 against a VM (vostest) with 4 CPUs, 16GB of RAM 
and 8GB of free disk space.\
* We pointed the system to a test database, copy of the production database, running in gp05.
* In this VM we also run the UWSGI `storagemanger` daemons.
* We tested against disk and NFS mounted directories for reading and writing.
* We run several test with different batches and `storemanager` UWSGI daemons:

### Results
We performed several test under different loads (levels and number of concurrent scripts) with different sets of UWSGI
`storagemanager` daemons running.

The best results came with 12 `storemanager` processes, that acted as a throttle to the VOSpace server for
large and numerous I/O requests. IO bottlenecks at the NFS client side and database were noticeable when many intensive 
IO or DB requests were performed at the same time.

### 12 UWSGI and 48 concurrent scripts
`E.g.`\

| Level | seconds per script | No of Fails | Scripts Not Finished |
| ----- | ------------------ | ----------- | -------------------- |
| 1 | 13.55 | 0 | 0 |
| 2 | 20.2 | 0 | 0 |
| 3* | 129.8 | 0 | 6 |
| 3* | 128.9 | 0 | 0 |
| 4* | 131.55 | 0 | 0 |
| 4* | 126.25 | 0 | 0 |
| 5** | 117.4 | 0 | 0 |
| 5**  | 115.1 | 0 | 0 |

(&ast;) with a pre-cache of the archive directory to be copied.\
(&ast;&ast;) 1/2 second delay between scripts. Otherwise DB gets swamped\
**Note**: Time of the day, depending how busy are the machines running the DB, NFS



####Comparison between new version vs old production version
The following tests were conducted with the VOSpace using a locally mounted disk (not NFS)
#####Only one script running
Only one test script running.
Production version can not execute the level 5, which is DB intensive.

| Level | QA(s) | PROD(s) |
| ----- | ----- | ------- |
| 1 | 3.83 | 6.81 |
| 2 | 5.94 | 7.52 |
| 3 | 10.82 | 14.94 |
| 4 | 12.57 | 17.02 |
| 5 | 17.5 | FAILED |
#####Four scripts running concurrently
The production version, as expected, failed in level 5

| Level | QA(s) | No of Fails | Scripts Not Finished | PROD(s) | No of Fails | Scripts Not Finished |
| ----- | ----- | ----------- | -------------------- | ------- | ----------- | -------------------- |
| 1 | 3.84 | 0 | 0 | 6.04 | 0 | 0 |
| 2 | 6.01 | 0 | 0 | 9.3 | 0 | 0 |
| 3 | 11.48 | 0 | 0 | 19.84 | 0 | 0 |
| 4 | 13.81 | 0 | 0 | 22.77 | 0 | 0 |
| 5 | 18.19 | 0 | 0 | --- | --- | 4 |
#####Ten scripts running concurrently
With 10 concurrent scripts the production version failed in all of the levels.
The QA version varied on IO and database access. In particular level 5, there is an important difference
between hitting the database at once and staggering the scripts with just one second delay between them.

| Level | QA(s) | No of Fails | Scripts Not Finished | PROD(s) | No of Fails | Scripts Not Finished |
| ----- | ----- | ----------- | -------------------- | ------- | ----------- | -------------------- |
| 1 | 4.01 | 0 | 0 | --- | --- | 10 |
| 2 | 6.83 | 0 | 0 | --- | --- | 10 |
| 3 | 17.4 | 0 | 0 | --- | --- | 10 |
| 4 | 18.5  | 0 | 0 | --- | --- | 10 |
| 5 | 40.55 | 0 | 0 | --- | --- | 10 |
| 5* | 25.18 | 0 | 0 | --- | --- | 10 |
(&ast;) one second delay between scripts




