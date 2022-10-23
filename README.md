# EMNS processing pipeline

## MFA

```bash
mfa models download acoustic english_mfa
mfa models download dictionary english_mfa
mfa align --clean ./processed_wavs/ english_mfa english_mfa ./emns_aligned
```

## Silence trimmer
Requires ffmpeg. 
```bash
usage: trim_silences.py [-h] [-c {Complete,Pending,Awaiting Review,Needs Updating}] [-d] media_root flist out_dir

positional arguments:
  media_root            root directory of the raw audio and textgrid files
  flist                 CSV file containing a list of paths to raw audio files. These paths will be interpreted as relative to MEDIA_ROOT
  out_dir               Output directory to store trimmed audio - files will have the same name as in the filelist

optional arguments:
  -h, --help            show this help message and exit
  -c {Complete,Pending,Awaiting Review,Needs Updating}, --criterion {Complete,Pending,Awaiting Review,Needs Updating}
                        only gather files that have been marked according to the supplied criterion
  -d, --debug           disables ffmpeg quiet mode
```
