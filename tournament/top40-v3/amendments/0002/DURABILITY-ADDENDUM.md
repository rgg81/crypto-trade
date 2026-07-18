# Amendment 0002 durability addendum

Status: prospective until its unique durability-freeze commit is verified.

The frozen Amendment 0002 validation journal is absent at activation. Its append primitive fsyncs
each record file, but the generic journal opener does not fsync the parent directory when that first
file is created. A power loss after accepting the first probe could therefore lose the directory
entry and make the consumed observation appear absent after restart.

This addendum changes no evaluator, model, identity, data, split, cost, floor, metric, packet, or
probe rule. Before the first probe, its only state-changing command uses the organizer's exclusive
file creator to create a zero-byte mode-0600 validation journal. That primitive fsyncs the file and
its parent directory before returning. Amendment 0002 then appends to an already durable inode, and
its existing per-record file fsync is sufficient for later observations.

The durability freeze binds the exact Amendment 0002 activation, the addendum implementation
commit, and serial passing outputs from the parent focused tests and the addendum tests. The freeze
and initialization both require that the private validation output namespace remains unopened.
