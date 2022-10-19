import glob
import tqdm
import os
import glob
import pandas as pd
import sys
import shutil

from concurrent.futures import ThreadPoolExecutor, as_completed

sys.path.append(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))
from utils import audio_to_flac

def convert_and_json_dump(df, overwrite:bool=False):
    if os.path.isfile(df['dest']) and os.path.isfile(df['dest']).replace('.wav', '.text') and overwrite==False:
        print(f"{df['dest']} already exists, skiping")
        return

    audio_to_flac(df['src'], df['dest'])
    with open(df['dest'].replace('.wav', '.txt'), 'w') as f:
        f.write(df['text'])
        # json.dump({'filename': os.path.join(*dest.split('/')[5:]), 'text':[df['text']], 'original_data':df['original_data']}, f)


def split_all_audio_files(df, max_workers=96):
    # if not os.path.exists(dest_root_path):
    #     raise FileNotFoundError(f'Please Check {dest_root_path} exists')

    l = len(df)
    with tqdm.tqdm(total=l, desc=f'Processing') as pbar:
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            threads = [executor.submit(convert_and_json_dump, row) for row in df.iloc()]
            for _ in as_completed(threads):
                pbar.update(1)

def main():
    emns_csv_path = '/home/knoriy/Documents/phd/dataset_collection_tool/django_dataset_collection_tool/audio_recorder_utterances.csv'
    emns_audio_path = '/home/knoriy/Documents/phd/EMNS/wavs/'
    root_dest_path = '/home/knoriy/Documents/phd/EMNS/processed_wavs/'

    raw_df = pd.read_csv(emns_csv_path, sep="|").dropna()
    # print("raw df", raw_df)

    new_df = []
    for row in tqdm.tqdm(raw_df.iloc(), total=len(raw_df), desc='Generating dataframe: '):
        new_df.append({
            'src':f'{os.path.join(emns_audio_path, row["audio_recording"].split ("/")[-1])}', 
            'dest':f'{os.path.join(root_dest_path, row["audio_recording"].split ("/")[-1].replace(".webm",".wav"))}', 
            'text': row['utterance'],
            })
    new_df = pd.DataFrame(new_df)

    split_all_audio_files(new_df)

if __name__ == '__main__':
    main()
