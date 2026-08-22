# Surrogate source management

The curated public corpus is described in
[`../../research/SURROGATE_PACK.md`](../../research/SURROGATE_PACK.md) and
[`../../research/source-manifest.yaml`](../../research/source-manifest.yaml).

Raw third-party PDFs are **not canonical project evidence** and are not committed by
default. Public availability does not guarantee redistribution rights, and remote
sources can change. The repository therefore preserves:

- stable source URLs and access date;
- suggested local filenames;
- source-by-source derived research notes;
- a small downloader for reproducible private research copies.

Run from this directory:

```bash
python3 fetch_surrogate_pack.py
```

It downloads PDF sources into `documents/` and writes SHA-256 hashes to
`documents/SHA256SUMS`. Review the source's applicable terms before retaining or
redistributing any downloaded file.

If a source later becomes load-bearing for a frozen experiment, the experiment should
pin the exact bytes/hash it actually used; an unversioned web URL is not sufficient
scientific identity.
