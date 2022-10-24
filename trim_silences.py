import sys
import argparse
from pathlib import Path
import multiprocessing as mp
from dataclasses import dataclass

import ffmpeg
from tqdm import tqdm
from textgrids import TextGrid



NUM_CORES = mp.cpu_count()
DEBUG = False
ACODEC = "opus"


@dataclass
class WavFile:
    raw_path: str
    textgrid_path: str
    out_path: str



def get_speech_bounds(filename: str) -> (str, str):
    grid = TextGrid(filename)
    grid_items = grid.items()
    word_intervals = []
    for item in grid_items:
        _, word_intervals = item
        break # only need one of the grid items. odict preserves insert order so this is guaranteed to be word intervals, not phones
    
    start_interval = word_intervals[0]
    end_interval = word_intervals[-1]

    speech_start_time = start_interval.xmax if start_interval.text == "" else start_interval.xmin
    speech_end_time = end_interval.xmin if end_interval.text == "" else end_interval.xmax
    return (float(speech_start_time), float(speech_end_time )) # seconds
     

def trim_audio(in_filename: str, out_filename: str, start: float, end: float) -> bool:
    if DEBUG: print(start, end, in_filename)
    try:
        (
            ffmpeg
            .input(in_filename)
            .audio
            .filter('atrim', start=start, end=end+0.5)
            .output(out_filename, strict='-2', acodec=ACODEC)
            .run(quiet=not DEBUG, overwrite_output=True)
        )

        return True
    except ffmpeg.Error as e:
        print(f"ffmpeg could not process file {in_filename}: {e}")
        exit()
        return False


def get_field_index(header: [str], to_find: str) -> int:
    idx = 0
    for item in header:
        if item == to_find:
            return idx
        idx += 1

    assert False, f"{to_find} does not exist in the header: {header}"


def get_filenames_to_process(root_dir: str, filelist: str, outdir: str, criterion="Complete") -> [(str, str, str)]:
    outdir_abs = Path(outdir).resolve()
    rd = Path(root_dir).resolve()
    filenames = [] # list of tuples of absolute filepaths (in_filename, textgrid_filename, out_filename)
    with open(filelist, "r") as fh:
        idx = 0
        filepath_idx = 0
        status_idx = 0
        skipped = 0
        for line in fh:
            line = line.strip()
            line = line.split("\t")
            if idx == 0:
                # in the header
                filepath_idx = get_field_index(line, "audio_recording")
                status_idx = get_field_index(line, "status")
            else:
                # rest of file
                if line[status_idx] == criterion:
                    wav_path_abs = rd / line[filepath_idx]
                    stem = wav_path_abs.stem
                    name = wav_path_abs.name
                    ext = name.split(".")[-1]
                    textgrid_path_abs = rd / "emns_aligned" / f"{stem}.TextGrid"
                    outfile_abs = outdir_abs / name
                    filenames.append(WavFile(str(wav_path_abs), str(textgrid_path_abs), str(outfile_abs)))
                else:
                    skipped += 1
            idx += 1

    return filenames, skipped


def process_file(wavfile):
    s, e = get_speech_bounds(wavfile.textgrid_path)
    return (trim_audio(wavfile.raw_path, wavfile.out_path, s, e), wavfile.raw_path)
    

def parse_args(args):
    parser = argparse.ArgumentParser()
    parser.add_argument('media_root', type=str, help="root directory of the raw audio and textgrid files")
    parser.add_argument('flist', type=str, help="CSV file containing a list of paths to raw audio files. These paths will be interpreted as relative to MEDIA_ROOT")
    parser.add_argument('out_dir', type=str, help="Output directory to store trimmed audio - files will have the same name as in the filelist")
    parser.add_argument('-c', '--criterion', default="Complete", choices=["Complete", "Pending", "Awaiting Review", "Needs Updating"], help="only gather files that have been marked according to the supplied criterion")
    parser.add_argument('-ac', '--acodec', default="opus", help="Codec to use when encoding and decoding audio")
    parser.add_argument('-d', '--debug', action="store_true", default=False, help="disables ffmpeg quiet mode")
    return parser.parse_args(args)

if __name__=="__main__":
    args = parse_args(sys.argv[1:])
    print("Gathering filenames to process...")
    files, skipped = get_filenames_to_process(args.media_root, args.flist, args.out_dir, args.criterion)
    print(f"Will process {len(files)} files (skipped {skipped} based on criterion `{args.criterion}`)")
    DEBUG = args.debug
    ACODEC = args.acodec



    pool = mp.Pool(NUM_CORES)
    results = pool.map(process_file, tqdm(files))
    pool.close()
    pool.join()
    failed_files = [r[1] for r in results if not r[0]]
    if len(failed_files) > 0:
        print(f"{len(failed_files)} failed to trim:")
        for f in failed_files:
            print (f[0])
