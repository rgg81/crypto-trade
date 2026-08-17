# CUP-50 evaluator sandbox

The evaluator image contains only the pinned Python runtime and numeric/Parquet dependencies.
CUP-50 protocol code, the sanitized team source, and the appropriate immutable snapshot are bind
mounted read-only. The writable output mount is separate. Every official invocation additionally
uses no network, a read-only root filesystem, no Linux capabilities, and no-new-privileges.

Build this directory as the complete Docker context. Never build from the repository root: doing
so would send quarantined organizer data to the Docker daemon.
