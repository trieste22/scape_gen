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

# Trieste Devlin, 03/2019
# TODO: clean up generate_files() inputs for broader use with other data
# class Call:
#   def __init__(self, src, hits, prob, start_times, dur, freq_low, freq_high):
#     self.src = src
#     self.hits = hits
#     self.prob = prob
#     self.start_times = start_times
#     self.dur = dur
#     self.freq_low = freq_low
#     self.freq_high = freq_high

# 0 ["fname", 1 [start, times], 2 call length, 3 # hits in annotated data, 4 low freq, 5 high freq, 6 full clip length, 7 prob (appended by get_probs)
PNRE_calls = [   ["EATO.wav", [0], 1.464, 1069, 1070, 15625, 1.464], # eastern towhee
            ["OVEN.wav", [0], 2.548, 784, 2606, 15625, 2.548], # ovenbird
            ["NOCA.wav", [0,.538,.761,.938], .128, 742, 1071, 16939, 1.066], # northern cardinal
            ["AMCR.wav", [0, .416], .197, 637, 400, 8527, .613], # american crow
            ["WOTH.wav", [0], 1.512, 531, 1265, 15479, 1.512], # wood thrush
            ["BTNW.wav", [0], 1.438, 510, 3164, 14262, 1.438], # black-throated green warbler
            ["BCCH.wav", [0], 1.566, 508, 2385, 10660, 1.566], # black-capped chickadee
            ["REVI.wav", [0], .423, 495, 1898, 5500, .423], # red-eyed vireo
            ["TUTI.wav", [0,.324], .207, 424, 2044, 13824, .531], # tufted titmouse
            ["RBWO.wav", [0,.265], .093, 390, 584, 14213, .391], # red-bellied woodpecker
            ["RWBL.wav", [0],.932, 327, 584, 15820, .932], # red-winged blackbird
            ["COYE.wav", [0,.558], .515, 321, 2726, 15917, 1.073], # common yellowthroat
            ["HOWA.wav", [0], 1.002, 312, 2580, 14019, 1.002], # hooded warbler
            ["SCTA.wav", [0], 1.790, 286, 1925, 10784, 1.790], # scarlet tanager
            ["BWWA.wav", [0], 1.613, 263, 2086, 19033, 1.613], # Blue-winged warbler
            ["SOSP.wav", [0], 2.285, 248, 1348, 15856, 2.285], # Song sparrow
            ["SWSP.wav", [0], 2.436,  226, 2632, 6805, 2.436], # Swamp sparrow
            ["AMRO.wav", [0, .583], .277 , 224, 1637, 14764, .860], # American robin
            ["BHCO.wav", [0], .932, 192, 867, 17621, .932], # Brown-headed cowbird
            ["ACFL.wav", [0], .630, 191, 1541, 15856, .630], # Acadian flycatcher
            ["GRCA.wav", [0], 3.076, 190, 899, 16048, 3.076], # Gray catbird
            ["BAWW.wav", [0, .411, .817, 1.222], .380 , 187, 3980, 15856, 1.605] # black-and-white warbler
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

    for i in range(scapecount):
            sc = scaper.Scaper(scape_dur, sourcedir + '/foreground', sourcedir + '/background')
            sc.ref_db = -30 #TODO

            fname = 'scape' + str(i)
            audiofile = outdir + '/' + fname + '.wav'
            jamsfile = outdir + '/' + fname + '.jams'

            bg = random.choice(back_list) # random choice from background list
            sc.add_background(label = ('const', bg_label),
                            source_file = ('const', sourcedir + '/background/' + bg_label + '/' + bg),
                            source_time = ('const', 0))

            birds = build_scapeData(PNRE_calls, birdcount, scape_dur, outdir, i) # build data and populate csv
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
count = int(sys.argv[2])
#build_scapes(outdir, 60, count, 30, sourcedir, 'noisy_clean', 'PNRE_birdcalls', PNRE_calls)

build_scapes(outdir, 15, count, 4, sourcedir, 'noisy_clean', 'PNRE_birdcalls', PNRE_calls) #birdcount = 30 for easyjunk
print("Done! Completed in " + str(datetime.now()-start) + " seconds.\n")
#def build_scapes(outdir, scape_dur, scapecount, birdcount (max calls per file), sourcedir, bg_label, fg_label, call_list):  # outfile = path/to/and/filename.

# # note: birdcount = max number of each call to happen per scape file
