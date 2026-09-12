# Reproduce the judge scenario in a container

This package runs the same Python/MCP service and browser UI. It is a local or
private cloud-runner path; it is not a publicly hosted multi-household service.
The owner PC is not required: GitHub Actions builds and exercises it on every PR.

## Run with Docker

```bash
docker build --pull --tag hestiarelay:judge .
docker volume create hestiarelay-demo
docker run --name hestiarelay-demo --rm \
  --read-only --cap-drop ALL --security-opt no-new-privileges \
  --tmpfs /tmp:rw,noexec,nosuid,size=16m \
  --publish 127.0.0.1:8000:8000 \
  --mount type=volume,source=hestiarelay-demo,target=/data \
  hestiarelay:judge
```

Open `http://127.0.0.1:8000/` and use the three guided session buttons. The MCP
endpoint is `http://127.0.0.1:8000/mcp`. Stop the container and run the same command
again with the same volume: the goal, preferences, sessions and consent persist.
Delete the named volume only when you intend to discard that fictional demo.

The image runs as UID/GID 10001, with writable state only under `/data` and a
temporary `/tmp`. Source, database, environment files and credentials from the
host are not mounted. The build context allowlists application source/static
assets, the dependency lock, Dockerfile and license. AWS configuration is empty
by default, and EC2 metadata credential lookup is disabled.

Python dependencies use the already validated `requirements-proof.txt`. The
official Python base is pinned by version and the content digest observed in the
first CI build. Each run records that reference and its final image ID; build
timestamps can still differ, so byte-identical rebuilds are not claimed.
Inspector 2.6.0 is pinned separately;
its resolved npm lock is included in the CI artifact.

## Cloud validation evidence

The `container-judge` CI job starts real containers with a fresh named volume,
performs three separate MCP sessions, recreates the container between sessions,
checks exact approve/reject decisions, then recreates it again to verify the
consent state. It checks hostile Host/Origin rejection and non-root/read-only
configuration. No tool response or browser request is intercepted.

The official MCP Inspector CLI performs initialization, strict tool listing and
a read-only continuity-brief call. It uses an isolated authentication store and
cannot prompt for OAuth. The existing desktop/mobile browser suite is reused
with a container launcher, at 1440x1000 and 390x844.

Download the `container-judge` artifact from the relevant Actions run for
`container-qa.json`, Inspector JSON, image identities, dependency resolution,
container logs and browser screenshots/traces. An in-progress job is not PASS.
The original Python process/browser and pinned AWS-proof jobs still run.

Verified run: [34719571606](https://github.com/Elinfiny/HestiaRelay/actions/runs/34719571606),
all four jobs PASS. The [durable result](evidence/container-20260912.json)
records the actual PR merge checkout, image digest, protocol, browser results
and artifact hash. The downloaded ZIP passed SHA-256, CRC, path and browser
manifest checks; its desktop/mobile Session 3 screenshots were visually reviewed.

## Public deployment decision

Do not publish this singleton service by changing its port binding. A public
release first needs a defined access model, TLS, exact Host/Origin configuration,
household authorization, persistent storage/restore and operating-cost approval.
The recommended next increment is a restricted fictional judge environment,
using one authenticated household and a short deployment lifetime, before
building general multi-household hosting. Its public endpoint and credentials
are not created by this container package or the consumed one-call AWS approval.
The [restricted judge design](JUDGE_DEPLOYMENT_DESIGN.md) specifies the access,
storage, validation and approval boundaries for the next implementation package.

References checked 2026-09-12:
[official Python image definitions](https://github.com/docker-library/official-images/blob/master/library/python),
[MCP Inspector CLI smoke guide](https://github.com/modelcontextprotocol/inspector/blob/main/docs/cli-smoke-testing.md).
