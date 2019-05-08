import scaper
import numpy as np
import os
import wave
import random
import csv
import re
from datetime import datetime
import jams
import sys
import pandas as pd

# from multiprocessing import cpu_count
# from concurrent.futures import ProcessPoolExecutor
# from concurrent.futures import as_completed


# Bird	Start_times	End_times	Freq_low	Freq_high	Full_clip_length

def build_scapes(outdir, scape_dur, scapecount, sourcedir, bg_label, junk_label):
	ratscapes = pd.DataFrame(columns = ["Scape", "Rat File", "Start Time", "End Time", "Low Freq", "High Freq"])

	rats = pd.read_csv("../fieldData/ratspecs.csv")
	rats.columns = ["Filename", "Length", "Low Freq", "High Freq"]

	bg_folder = "../fieldData/background"
	fg_folder = "../fieldData/foreground"

################################################################################################# RAT AND MAYBE FARINOSA
	for i in range(scapecount):
		sc = scaper.Scaper(scape_dur, fg_folder, bg_folder)
		sc.ref_db = -40 #TODO

		fname = f"1min_yolorat_scape{str(i)}" #f"yolorat_scape{str(i)}" 		##TODO
		audiofile = f"{outdir}/{fname}.wav"
		jamsfile = f"{outdir}/{fname}.jams"
					
		sc.add_background(label = ("const", "some-farinosas"),
						source_file = ("choose", []),
						source_time = ("uniform", 0, 60-scape_dur))

		thisrat = rats.sample() #grab a random rat call
		start = round(random.uniform(0,scape_dur-.5), 3)

		eventdur = thisrat["Length"].iloc[0]
		end = start + eventdur

		if (scape_dur-start < eventdur):
			eventdur = scape_dur-start
			end = scape_dur

		fname = thisrat["Filename"].iloc[0]

		ratrow = [audiofile, fname, start, end, thisrat["Low Freq"].iloc[0], thisrat["High Freq"].iloc[0]]
		ratscapes.loc[i] = ratrow

		# print(f"start: {start}, end: {end}, dur: {eventdur}")

		sc.add_event(label=('const', "clean-rats"), #one rat per file
					 source_file = ('const', f"{fg_folder}/clean-rats/{fname}"),
					 source_time = ('const', 0),
					 event_time = ('const', start),
					 event_duration = ('const', eventdur), #duration of event in synthesized soundscape - you will get warnings
					 snr=('uniform', -10, 2), #TODO - decide
					 pitch_shift=None, #number of semitones (can be fractional) to shift sound up/down
					 time_stretch=None ) #factor to stretch sound by (<1 = shorter, >1 = longer)

		num_junk = random.randint(0,10) #4 for 15s, 10 for 1min  			##TODO
		for j in range(num_junk):
			sc.add_event(label=('const', junk_label),
						source_file = ('choose', []),
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
			   no_audio=False)

		print(f"Scape {i} generated.")

	ratscapes.to_csv("1min_rat_scapes_yolo.csv", index=False) #"15s_rat_scapes_yolo.csv", index=False)

start = datetime.now()
scape_dur = 60 #15													 		##TODO
scapecount = 10000
outdir = "yoloscapes_1min" #"yoloscapes_15s"		 						##TODO
sourcedir = "."
bg_label = "empty"
junk_label = "junk"

build_scapes(outdir, scape_dur, scapecount, sourcedir, bg_label, junk_label)
print("Done! Completed in " + str(datetime.now()-start) + " seconds.\n")
