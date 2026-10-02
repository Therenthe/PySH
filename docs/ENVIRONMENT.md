# Environment index

Current facts and commands are maintained in [HARDWARE](HARDWARE.md), [DEVELOPMENT](DEVELOPMENT.md), [ARCHITECTURE](ARCHITECTURE.md) and [OPERATIONS](OPERATIONS.md). Original raw device evidence remains in the legacy local workspace and is not part of this repository.

Local migration checks use the installed Node 24.19.0 runtime and the legacy Python 3.12 environment against the new source directory. Clean GitHub runner dependency installs, frontend build, and backend checks on Python 3.12/3.13 subsequently passed (CI run 37030198002). A real Pi run remains separate hardware acceptance.
