# Windows 11 migration: November 2026

This document describes the migration of the independent bim-markup-bench
research experiment. It does not authorize paid LLM calls or official scoring.

## Destination and exact version

- Windows: D:\Projects\2026-11_bim-markup-bench
- Mac source: /Users/pikaybh/Projects/bim-markup-bench, plus its 21 issue worktrees
- Original GitHub main: 679ecb372fc1a91a9059b83fa1a7dd4e2b6eb12c
- Windows Git 2.43, Python 3.12.2, uv 0.6.17
- Frozen Python dependency version: IfcOpenShell 0.8.4.post1
- The pinned public 324-record tasks.jsonl SHA-256 is
  9bdf9536b94096a06e0e43bd4c59314d6427d3b939517576c7d4c13e1084ef83
- Thirteen tiny public IFC assets (1,573,389 bytes) were downloaded at
  the pinned official model repo revision, with hashes/sizes checked.
  Six input/GT pairs cover seven of the fixed 36 candidate tasks.
  The other 29 cases remain unverified.

## Portability findings and fixes

IMPORTANT: Windows Git was initially using core.autocrlf=true, which
corrupted byte-for-byte scientific fixture identity during checkout.
The tracked synthetic input.ifc file became 6,812 bytes instead of
the original 6,665 bytes. The canonical Git blob SHA-256 is
10d57d3eeb6e50fb51493b03d7cb508d57eadeb76719afaeb71fa6658c3ecf58.
This patch adds .gitattributes with *.ifc -text, restores the exact
tracked IFC bytes, and uses local Git core.autocrlf=false. IFC must
never be normalized as ordinary CRLF text: changing bytes alters
source integrity, experiment IDs and rights ledger checksums.

The compiler previously fsynced a read-only staged IFC file descriptor.
Windows rejects this with EBADF. The validated *new staging file*
now opens as r+b for fsync, before an exclusive hard-link publication.
Original input IFC remains immutable and source overwrite is refused.

The independent scorer computed a macOS/arm64 calibration report.
On Windows/x64 the same version of IfcOpenShell yielded native
geometry score differences of up to about 0.0074 in the examined cases.
All 17 synthetic strict-pass/expected-failure decisions remained the same.
The calibration test retains exact IDs, statuses, failure/check outcomes
and strict-pass decisions, but permits a 0.01 bounded continuous score
difference. This tolerance is NOT the success threshold and does not
prove strict numerical cross-platform reproducibility. Freeze the exact
scorer host/architecture before any formal paid experiment.

Creating symlinks requires extra privileges on some Windows installs.
Only tests that cannot construct the *negative symlink fixture* due
specifically to WinError 1314 are skipped there; all must run on Linux.
Windows also refuses unlinking the read-only source where POSIX can
unlink via parent-directory permission. The tested Windows denial
is accepted as proof that this specific replacement was prevented.
The rights manifest uses POSIX-style relative path strings.

## Reproduction

PowerShell (from the Windows destination):

    $env:PYTHONUTF8='1'
    $env:PYTHONIOENCODING='utf-8'
    $env:UV_CACHE_DIR='D:\Projects\2026-11_bim-markup-bench\.uv-cache'
    cd D:\Projects\2026-11_bim-markup-bench
    & 'C:\Users\Yoo\.local\bin\uv.exe' sync --frozen --python 'D:\AppData\Local\Programs\Python\Python312\python.exe'
    .\.venv\Scripts\python.exe -m unittest discover -s tests -v
    .\.venv\Scripts\python.exe -m tools.pilot_preflight

The full Windows pass on 2026-11-09 was 285 tests: 273 passed,
12 skipped, 0 failed. Skips include unavailable Docker Linux isolation,
Windows symlink privilege and native xmllint validation. The pilot
preflight intentionally exits 2 and prohibits real paid model runs.

## Remaining blockers and data safety

- Windows D: free space at migration: approximately 64.7 GB.
  Additional G: free space: approximately 261.7 GB. Windows RAM: 16 GB.
- Docker Desktop is installed, but its Linux daemon was not running and
  the Windows wsl.exe launcher was not found. The previous worker image
  is built for Mac ARM64 Linux; an independent Windows x64 Linux sandbox
  worker and OS security checks are still necessary for untrusted code.
- Full official IFC/GT corpora, legal rights verification, official
  scorer equivalence, model billing broker and research freeze are
  still blocked. No official scores or paid model calls.
- The Mac local experiment has an ignored .env file (182 bytes).
  This is a credential-bearing *candidate* and has NOT been opened,
  transmitted to Windows or committed to Git. Windows key setup remains
  separate and requires secure provisioning.
- The Mac currently has 22 clean experiment worktrees totalling roughly
  5.6 GiB, almost entirely rebuildable Python virtual environments.
  They and the private Mac .env remain untouched pending explicit
  approval of which exact local paths to delete and validation of
  the future Windows Linux security runner.

Nothing in production Xim/BIXML, Revit or other Windows folders was edited.
