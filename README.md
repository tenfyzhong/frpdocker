# frpdocker

FRP 0.20.0 Docker image, rebuilt from the pinned upstream source commit with Go 1.26.10.
The FRP version, INI files, entrypoint, ports, and runtime base remain unchanged.

The small `patches/go-vet.patch` treats error messages as data rather than format strings,
allowing the original unit tests (including their default vet checks) to pass with the patched compiler.
The source archive is SHA-256 checked before compilation, and the build checks the Go
version embedded in both executables. This replaces the old prebuilt FRP executables;
updating a Go directive alone would not update their standard library.

Run `docker build -t frpdocker .`. Pull requests build and smoke-test the image without
pushing it to a registry. Existing published images are not changed by a source merge;
rebuilding and deploying an image remain separate steps.

This targeted Go runtime update is not a general modernization of the legacy FRP or
Alpine versions. In particular, it does not claim that all other security issues in
those versions have been addressed.

Full standalone `go vet` still reports pre-existing copylocks, sigchanyzer, duplicate JSON-tag, and unreachable
code findings in the 2018 upstream source. Those are not suppressed or claimed fixed by
this compiler-focused change.
