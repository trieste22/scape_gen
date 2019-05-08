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
	


def build_scapes(outdir, scape_dur, sourcedir, bg_label, junk_label):
	csvfile = "ratfiles_inception.csv"

	with open(csvfile, 'w', newline='') as csvfile:

		writer = csv.writer(csvfile, delimiter=',')
		header = ['File', 'Rat', 'A Farinosa']
		writer.writerow(header)

		ratcount = 1000 #1000
		parrotcount = 3000 #3000
		emptycount = 4000 #4000
		ratparrotcount = 2000 #2000

		total = ratcount + parrotcount + emptycount + ratparrotcount

############################################################################################### RATS
		for i in range(ratcount):
			sc = scaper.Scaper(scape_dur, f"{sourcedir}/foreground", f"{sourcedir}/background")
			sc.ref_db = -40 #TODO

			fname = f"rat_scape{str(i)}"
			audiofile = f"{outdir}/{fname}.wav"
			jamsfile = f"{outdir}/{fname}.jams"

			writer.writerow([f"{audiofile}", 1, 0])
						
			sc.add_background(label = ("const", bg_label),
							source_file = ("choose", []),
							source_time = ("const", 0))
			
			sc.add_event(label=('const', "clean-rats"), #one rat per file
						 source_file = ('choose', []),
						 source_time = ('const', 0),
						 event_time = ('uniform', 0, 59),
						 event_duration = ('const', 25), #duration of event in synthesized soundscape - you will get warnings
						 snr=('uniform', -10, 2), #TODO - decide
						 pitch_shift=None, #number of semitones (can be fractional) to shift sound up/down
						 time_stretch=None ) #factor to stretch sound by (<1 = shorter, >1 = longer)		
				
			num_junk = random.randint(0,10) #10 for just rats
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

			print(f"Rat scape {i} generated.")

################################################################################################# EMPTY
		for i in range(emptycount):
			sc = scaper.Scaper(scape_dur, f"{sourcedir}/foreground", f"{sourcedir}/background")
			sc.ref_db = -40 #TODO

			fname = f"empty_scape{str(i)}"
			audiofile = f"{outdir}/{fname}.wav"
			jamsfile = f"{outdir}/{fname}.jams"

			writer.writerow([f"{audiofile}", 0, 0])
						
			sc.add_background(label = ("const", bg_label),
							source_file = ("choose", []),
							source_time = ("const", 0))
		
			num_junk = random.randint(0,10)
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

			print(f"Empty scape {i} generated.")
################################################################################################# A. FARINOSA
		for i in range(parrotcount):
			sc = scaper.Scaper(scape_dur, f"{sourcedir}/foreground", f"{sourcedir}/background")
			sc.ref_db = -40 #TODO

			fname = f"farinosa_scape{str(i)}"
			audiofile = f"{outdir}/{fname}.wav"
			jamsfile = f"{outdir}/{fname}.jams"

			writer.writerow([f"{audiofile}", 0, 1])
						
			sc.add_background(label = ("const", "farinosa-minutes"),
							source_file = ("choose", []),
							source_time = ("const", 0))
		
			num_junk = random.randint(0,10)
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

			print(f"Farinosa scape {i} generated.")

################################################################################################# A. FARINOSA AND RAT
		for i in range(ratparrotcount):
			sc = scaper.Scaper(scape_dur, f"{sourcedir}/foreground", f"{sourcedir}/background")
			sc.ref_db = -40 #TODO

			fname = f"rat_and_farinosa_scape{str(i)}"
			audiofile = f"{outdir}/{fname}.wav"
			jamsfile = f"{outdir}/{fname}.jams"

			writer.writerow([f"{audiofile}", 1, 1])
						
			sc.add_background(label = ("const", "farinosa-minutes"),
							source_file = ("choose", []),
							source_time = ("const", 0))

			sc.add_event(label=('const', "clean-rats"), #one rat per file
						 source_file = ('choose', []),
						 source_time = ('const', 0),
						 event_time = ('uniform', 0, 58),
						 event_duration = ('const', 40), #duration of event in synthesized soundscape - you will get warnings
						 snr=('uniform', -10, 2), #TODO - decide
						 pitch_shift=None, #number of semitones (can be fractional) to shift sound up/down
						 time_stretch=None ) #factor to stretch sound by (<1 = shorter, >1 = longer)

			num_junk = random.randint(0,10) #10 for farinosas and rat
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

			print(f"Rat and farinosa scape {i} generated.")

# 0 fname, 1 start times, 2 end times, 3 lo freq, 4 hi freq, 5 total clip length
start = datetime.now()
scape_dur = 60
outdir = "scapes"
sourcedir = "."
bg_label = "empty"
junk_label = "junk"

build_scapes(outdir, scape_dur, sourcedir, bg_label, junk_label)
print("Done! Completed in " + str(datetime.now()-start) + " seconds.\n")

