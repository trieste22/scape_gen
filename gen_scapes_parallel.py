import scaper
import numpy as np
import os
import wave
# import contextlib
import random
import csv
import re
from datetime import datetime
import jams
import sys
import pandas as pd

from multiprocessing import cpu_count
from concurrent.futures import ProcessPoolExecutor
from concurrent.futures import as_completed

# 0 ["fname", 1 [start, times], 2 call length, 3 # hits in annotated data, 4 low freq, 5 high freq, 6 full clip length, 7 prob (appended by get_probs)
PNRE_calls = [  ["EATO_call.wav", [0], .723,500, 838, 4275, .723], # eastern towhee
                ["EATO_song.wav", [0], 1.512, 600, 2210, 6903, 1.512],
                ["NOCA_song_1.wav", [0], 4.126, 200, 737, 4088, 4.126],
                ["NOCA_song_2.wav", [0], 3.126, 500, 1340, 3753, 3.126],
                ["SCTA_song.wav", [0], 2.144, 300, 1675, 3887, 2.144],
                ["WOTH_call.wav", [0], .770, 531, 402, 8177, .770],
                ["AMRO_call.wav", [0], .932, 300, 1732, 3485, .932],
                ["DOWO_song.wav", [0], 1.955, 286, 1072, 7197, 1.955]
            ]

def rand(a,b): # return a random float in range [a,b)
    return (b - a) * np.random.random_sample() + a

def get_probs(call_list): #pass list of calls + metadata
    total = 0
    dist_list = []
    for call in call_list:
        total = total + call[3]
    # print('total = ' + str(total))

    for call in call_list:
        call.append(float(call[3]/total))
        # print(call)

def call_times_in_file(birdcall, n, t): #create list of 0-n times in a t-second file to play a given call, given probability
    #ie n = 10 possible calls/file, t = 60 second file length
    start_times = []
    end_times = []
    prob = birdcall[7]
    probs = np.random.geometric(prob, n) # list of 10 trial results: 1 = there was a birdcall
    for p in range(len(probs)):
        # print('probs['+str(p)+'] = ' + str(probs[p]))
        if probs[p] == 1:
            time = round(p*(t/n)+rand(0,(t/n)),3)
            start_times.append(time)
            end_times.append(round(time + birdcall[2],3))
    return start_times, end_times

    #return starts, ends
    
def get_audio_info(filepath):
    files = sorted(os.listdir(path=filepath))
    clips = []
    for file in files:
        if not (bool(re.match("^\.",file))): # ignore hidden files
            clips.append(file)
    return clips
    


# choose start times as per geometric distribution for each call in call_list
# fill csv file with data for reference, output list of list with specs to build scape
def build_scapeData(call_list, n, file_len, curr_scape, outdir): #call_list without probs yet, n = max calls/file, Build data for single scapered file
    get_probs(call_list) #append probs to call_list
    rows = []

    if not os.path.exists(outdir):
        os.makedirs(outdir)
    csvfile = f"scape{curr_scape}.csv"

    with open(outdir+ '/' + csvfile, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile, delimiter=',')

        header = ['Bird', 'Start_times', 'End_times', 'Freq_low', 'Freq_high', 'Full_clip_length']
        writer.writerow(header)

        for call in call_list:
            tmp = []
            tmp.append(call[0])
            start_times, end_times = call_times_in_file(call, n, file_len)
            tmp.append(start_times)
            tmp.append(end_times)
            tmp.append(call[4])
            tmp.append(call[5])
            tmp.append(call[6])
            rows.append(tmp)
            writer.writerow(tmp)
            # print(tmp)
    return rows

# build_scapeData(PNRE_calls, 10, 60, 0, ".") #call_list, max calls/file, file_len, curr_scape, outdir

def build_scape(birds, curr, outdir, scape_dur, sourcedir, bg_label, fg_label, junk_label):
    # birds = df with info about this scape. curr = which scape. outfile = path/to/and/filename.
    back_list = get_audio_info(f"{sourcedir}/background/{bg_label}")
    junk_list = get_audio_info(f"{sourcedir}/foreground/{junk_label}")
    sc = scaper.Scaper(scape_dur, f"{sourcedir}/foreground", f"{sourcedir}/background")
    sc.ref_db = -30 #TODO

    fname = f"scape{str(curr)}"
    audiofile = f"{outdir}/{fname}.wav"
    jamsfile = f"{outdir}/{fname}.jams"
    
    # print(f"fname: {fname}, audiofile: {audiofile}, jamsfile: {jamsfile}")

    
    bg = random.choice(back_list) # random choice from background list    
    sc.add_background(label = ("const", bg_label),
                    source_file = ("const", f"{sourcedir}/background/{bg_label}/{bg}"),
                    source_time = ("const", 0))
    
    # print(f"background: {bg}")
    # print(f"junk_list: {junk_list}")

    for bird in birds: # bird = row in birds, containing list of call times (if any, else empty list []) in file and boxing info
       
        # print(f"for bird: {bird[0]}")
        
        if len(bird[1]) > 0: #if bird calls in this scape
            for t in bird[1]: # for each start time
                dur = bird[5] #length of call
                sc.add_event(label=('const', fg_label),
                         source_file = ('const', f"{sourcedir}/foreground/{fg_label}/{bird[0]}"),
                         source_time = ('const', 0),
                         event_time = ('const', t),
                         event_duration = ('const', dur), #duration of event in synthesized soundscape - you will get warnings
                         snr=('uniform', -15, 6), #TODO - decide
                         pitch_shift=None, #number of semitones (can be fractional) to shift sound up/down
                         time_stretch=None ) #factor to stretch sound by (<1 = shorter, >1 = longer)
         
                # print(f"   added a {bird[0]}")
                
            num_junk = random.randint(0,5) #10 for easyjunk, 5 for shortjunk
            for j in range(num_junk):
                sound = random.choice(junk_list)
                noiseindex = junk_list.index(sound)

                sc.add_event(label=('const', junk_label),
                            source_file = ('const', f"{sourcedir}/foreground/{junk_label}/{sound}"),
                            source_time = ('const', 0),
                            event_time = ('uniform', 0, scape_dur-.5),
                            event_duration = ('const', 5),
                            snr = ('uniform',-5,2),
                            pitch_shift=('normal', -.5,.5),
                            time_stretch=('uniform',.5,2))

            sc.generate(audiofile,jamsfile,
                   allow_repeated_label=True,
                   allow_repeated_source=True,
                   reverb=0,
                   disable_sox_warnings=True,
                   no_audio=False)#,
#                    txt_path=None)
    print(f"Scape {curr} generated.")

# 0 fname, 1 start times, 2 end times, 3 lo freq, 4 hi freq, 5 total clip length
start = datetime.now()
scape_count = 5000
max_calls_perfile = 10
scape_dur = 15
outdir = "./scapes"
sourcedir = "."
fg_label = "PNRE_fromRecordings"
bg_label = "noisy_clean"
junk_label = "junk"

df = pd.DataFrame()
for i in range(scape_count):
    df = df.append(pd.Series(build_scapeData(PNRE_calls, max_calls_perfile, scape_dur, i, outdir)),ignore_index=True)

nprocs = cpu_count()
executor = ProcessPoolExecutor(nprocs)
futs = [executor.submit(build_scape, row, idx, outdir, scape_dur, sourcedir, bg_label, fg_label, junk_label) for idx, row in df.iterrows()]
for fut in as_completed(futs):
    _ = fut.result()

print("Done! Completed in " + str(datetime.now()-start) + " seconds.\n")

