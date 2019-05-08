import scaper
import numpy as np
import os
import wave
import contextlib
import random
import csv
import re
from datetime import datetime
import jams
import sys
import pandas as pd

# 0 ["fname", 1 [start, times], 2 call length, 3 # hits in annotated data, 4 low freq, 5 high freq, 6 full clip length, 7 prob (appended by get_probs)
PNRE_calls = [  ["EATO_call.wav", [0], .723, 1069, 838, 4275, .723], # eastern towhee
                ["EATO_song.wav", [0], 1.512, 1069, 2210, 6903, 1.512],
                ["NOCA_song_1.wav", [0], 4.126, 742, 737, 4088, 4.126],
                ["NOCA_song_2.wav", [0], 3.126, 742, 1340, 3753, 3.126],
                ["SCTA_song.wav", [0], 2.144, 286, 1675, 3887, 2.144],
                ["WOTH_call.wav", [0], .770, 531, 402, 8177, .770],
                ["AMRO_call.wav", [0], .932, 224, 1732, 3485, .932],
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


# choose start times as per geometric distribution for each call in call_list
# fill csv file with data for reference, output list of list with specs to build scape
def build_scapeData(call_list, n, t, outdir, curr_scape): #call_list without probs yet, n = max calls/file, t = length of file in seconds. Build data for single scapered file
    get_probs(call_list) #append probs to call_list
    rows = []

    if not os.path.exists(outdir):
        os.makedirs(outdir)
    csvfile = 'scape' + str(curr_scape) + '.csv'

    with open(outdir+ '/' + csvfile, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile, delimiter=',')

        header = ['Bird', 'Start_times', 'End_times', 'Freq_low', 'Freq_high', 'Full_clip_length']
        writer.writerow(header)

        for call in call_list:
            tmp = []
            tmp.append(call[0])
            start_times, end_times = call_times_in_file(call, n, t)
            tmp.append(start_times)
            tmp.append(end_times)
            tmp.append(call[4])
            tmp.append(call[5])
            tmp.append(call[6])
            rows.append(tmp)
            writer.writerow(tmp)
            # print(tmp)
    return rows

# build_scapeData(PNRE_calls, 10, 60)

def get_audio_info(filepath):
    files = sorted(os.listdir(path=filepath))
    clips = []
    for file in files:
        if not (bool(re.match("^\.",file))): # ignore hidden files
            clips.append(file)
    return clips



def build_scapes(outdir, scape_dur, scapecount, birdcount, sourcedir, bg_label, fg_label, call_list):  # outfile = path/to/and/filename.
    back_list = get_audio_info(sourcedir + '/background/' + bg_label)
    junk_list = get_audio_info(sourcedir + '/foreground/easy_junk')

    # for i in range(scapecount):
    #         sc = scaper.Scaper(scape_dur, sourcedir + '/foreground', sourcedir + '/background')
    #         sc.ref_db = -30 #TODO

    #         fname = 'scape' + str(i)
    #         audiofile = outdir + '/' + fname + '.wav'
    #         jamsfile = outdir + '/' + fname + '.jams'

    #         bg = random.choice(back_list) # random choice from background list
    #         sc.add_background(label = ('const', bg_label),
    #                         source_file = ('const', sourcedir + '/background/' + bg_label + '/' + bg),
    #                         source_time = ('const', 0))

    #         birds = build_scapeData(PNRE_calls, birdcount, scape_dur, outdir, i) # build data and populate csv
            for bird in birds:
                if len(bird[1]) > 0:
                    for t in bird[1]: # for each start time
                        dur = bird[5]
                        sc.add_event(label=('const', fg_label),
                                 source_file = ('const', sourcedir +'/foreground/' + fg_label +'/' + bird[0]),
                                 source_time = ('const', 0),
                                 event_time = ('const', t),
                                 event_duration = ('const', dur), #duration of event in synthesized soundscape - you will get warnings
                                 snr=('uniform', -15, 20), #TODO - decide
                                 pitch_shift=None, #number of semitones (can be fractional) to shift sound up/down
                                 time_stretch=None ) #factor to stretch sound by (<1 = shorter, >1 = longer)

            num_junk = random.randint(0,5) #10 for easyjunk, 5 for shortjunk
            for j in range(num_junk):
                sound = random.choice(junk_list)
                noiseindex = junk_list.index(sound)

                sc.add_event(label=('const', 'easy_junk'),
                            source_file = ('const', sourcedir + '/foreground/easy_junk/' + sound),
                            source_time = ('const', 0),
                            event_time = ('uniform', 0, scape_dur-.25),
                            event_duration = ('const', 5),
                            snr = ('normal',4,0),
                            pitch_shift=('normal', -.5,.5),
                            time_stretch=('uniform',.2,2))

            sc.generate(audiofile,jamsfile,
                   allow_repeated_label=True,
                   allow_repeated_source=True,
                   reverb=0,
                   disable_sox_warnings=True,
                   no_audio=False,
                   txt_path=None)

            print("Scape" + str(i) + " generated.")
# 0 fname, 1 start times, 2 end times, 3 lo freq, 4 hi freq, 5 total clip length


# outdir = sourcedir + '/scapes'
start = datetime.now()
sourcedir = os.getcwd()
# sourcedir = os.path.expanduser('/Volumes/MSD-0016')
# print(sys.argv[0])

#running from robin/../Trieste-Devlin: python3 PNRE_scape.py PNRE_scapes_noisy_nojunk 10000
outdir = sys.argv[1]
scapecount = int(sys.argv[2])

df = pd.DataFrame()

for i in range(scapecount):
    fname = 'scape' + str(i)
    audiofile = outdir + '/' + fname + '.wav'
    jamsfile = outdir + '/' + fname + '.jams'

    bg = random.choice(back_list) # random choice from background list
    sc.add_background(label = ('const', bg_label),
                    source_file = ('const', sourcedir + '/background/' + bg_label + '/' + bg),
                    source_time = ('const', 0))

    birds = build_scapeData(PNRE_calls, birdcount, scape_dur, outdir, i) # build data and populate csv



sc = scaper.Scaper(scape_dur, sourcedir + '/foreground', sourcedir + '/background')
    sc.ref_db = -30 #TODO


#build_scapes(outdir, 60, count, 30, sourcedir, 'noisy_clean', 'PNRE_birdcalls', PNRE_calls)

build_scapes(outdir, 15, count, 4, sourcedir, 'noisy_clean', 'PNRE_birdcalls', PNRE_calls) #birdcount = 30 for easyjunk
print("Done! Completed in " + str(datetime.now()-start) + " seconds.\n")
#def build_scapes(outdir, scape_dur, scapecount, birdcount (max calls per file), sourcedir, bg_label, fg_label, call_list):  # outfile = path/to/and/filename.

# # note: birdcount = max number of each call to happen per scape file
