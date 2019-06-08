# Chord-gRPC-Python README

Reference
* Chord: A Scalable Peer-to-peer Lookup Service for Internet Applications\
    http://nms.lcs.mit.edu/papers/chord.pdf
* How to Make Chord Correct\
    https://arxiv.org/pdf/1502.06461.pdf

Generation of grpc/protobuf files:
* In src directory, run `gen_proto.sh` to generate python files from `*.proto`

Execution:
1. Local execution
    - Modify `server-list.csv`
    - `python scripts/run_chord_servers.py`
2. Remote setup (for new machine `pip` environment)
    - Modify `remote-server.csv`
    - `python scripts/run_chord_servers.py remote-server.csv --pem_file path/to/pemfile --remote --setup`
3. Remote exeution
    - `python scripts/run_chord_servers.py remote-server.csv --pem_file path/to/pemfile --remote`
    - If you don't need to sync source code, add `--no_sync`, which can speedup the script
