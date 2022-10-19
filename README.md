# EMNS processing pipeline

## MFA

```bash
mfa models download acoustic english_mfa
mfa models download dictionary english_mfa
mfa align --clean ./processed_wavs/ english_mfa english_mfa ./emns_aligned
```
