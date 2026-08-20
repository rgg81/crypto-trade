# CUP-50 v2 evaluation sandbox

Every candidate run — research evaluation, charged trial, and sealed observation — happens inside
this image, with no network, a read-only root filesystem, no capabilities, and a non-root user. The
team workspace, the protocol bundle and the team-visible snapshot are mounted read-only; one output
directory is writable.

**Never build this from the repository root.** The build context is this directory alone. Building
from the root would hand the Docker daemon the quarantined acquisition tree, the sealed snapshot and
the organizer's private staging area, which is precisely what the quarantine receipt exists to
prevent.

```
docker build -t cup50v2-evaluator:<date> tournament/cup50v2/sandbox
```

The image is pinned by digest in the activation record, and `require_image_digest` refuses to run
against a tag that resolves to anything else. The dependency lock is exact: a candidate's result has
to be reproducible from the bytes the activation bound, and "numpy, recent" is not a byte.
