# Field Station observation ingestion

Field Station → authenticated HQ pull → existing machine-data publisher → graph consumer.

This collection contains structured observations, **not transcripts or proof of an
unidentified physical cause**. `anomalous` means a human reviewed that object as
anomalous. Machine predictions remain separately attributed to their model hash.

## Public collection

`Field-Station/<station-id>/<capture-event-id>.json` is the latest revision of an
observation. One capture event can reference multiple recordings and annotations;
it is not multiple independent sightings. Each record has schema
`ufo-files-field-observation/v1`, a stable `id`, `revision`, and `source_epoch`.

Only human-confirmed anomalous annotations with a current, verified Internet
Archive bundle are initially published. Verification requires the current review
group revision, archive receipt, and review-annotations checksum to agree. Assets
contain Archive URLs, byte counts and SHA-256 digests, not media or local paths.
Only county/state/country may leave the station. Historical location is unknown
unless a valid capture-time fix exists; present location is never backfilled.

`recording_window_start_epoch` and `recording_window_end_epoch` describe surrounding
recording coverage, **not exact object appearance or sighting duration**. Each
annotation references its original recording frame index and native-pixel bounds.
Review time is separate. CE5 playback is on for measured overlap, off only with
complete playback-log coverage, otherwise unknown. No causal relation is inferred.

`published` records have current verified evidence. `pending_evidence` suppresses
an old public interpretation while a revised bundle is unavailable. `withdrawn`
records remain as tombstones when no current human anomalous review remains.
Consumers must remove pending/withdrawn observations from active graph results.
Missing mounts or an offline station are errors, never mass-deletion instructions.
Manual recordings without object-level anomalous reviews are not auto-published.

## Runtime and persistence

Run the station exporter as:

```sh
PYTHONPATH=/path/to/scripts python3 -m field_observations.export \
  --root /Volumes/UFO-Field --station-id field-1fe259 \
  --journal /Volumes/UFO-Field/machine-data-export/state-v1.sqlite --since 0
```

It reads existing metadata and maintains its own SQLite journal on the field SSD.
It does not change reviews, recordings, training datasets or Archive uploads.
The known migrated review path `/Volumes/UFO-SWR/review-training` is explicitly
supported; arbitrary symlinks are rejected. Journal access uses an exclusive lock.
A consistent snapshot checks review-manifest and group-index signatures before
committing a batch. No UI database lock is held while scanning.

HQ runs `python3 -m field_observations.ingest --config <private-config.json>` every
five minutes. `config/field-observation-ingest.example.json` documents its inputs.
Transport is SSH with shell-quoted remote arguments; credentials stay in the
existing local SSH helper, outside the repository. No public HTTP endpoint is
introduced. Subsequent pages read the journal without rescanning the station.

HQ validates identity, sequence, checksums and the public field allowlist, writes
atomic source records under the transcript publisher's exclusive lock, then
writes one completion record per observation revision. Only then does it advance
its durable cursor. Crash replay is idempotent. A changed journal epoch requires
explicit reconciliation; it cannot silently reset or delete the collection.

The existing publisher handles Git fetch/push and completion acknowledgements.
Full transcript reconciliation preserves this collection because its source lives
inside the existing transcript source tree. Code stays under the publisher's
protected `scripts/` directory. JSON observations do not inflate transcript-count
badges. No additional Git publisher or large-media copy is created.

HQ `state/status.json` records health, cursor, and last success; failures retry on
the next scheduled poll. Both required external mounts must exist before writes.
The deployed service uses the existing headless supervisor, including boot startup.

## Relationship graph integration contract

The current transcript importer does not automatically index these JSON records.
Its dedicated observation adapter must consume this collection and retain type
separation: Observation, Station, Recording, ReviewedObject, Model, CountyRegion,
and ArchiveBundle. Suggested edges are observed-by, recorded-in, reviewed-as,
predicted-by, located-in and evidenced-by. Group independent evidence by recording
source family; several crops of one recording are not independent corroboration.

Frequency mentions in documents and RF measurements are different evidence types.
This first ingestion release links verified RF assets; it does not turn those
samples into graph frequency assertions or correlate sightings automatically.
Future spatial/temporal associations must state uncertainty and county-level
resolution, rather than manufacturing precise co-location.

## Tests

```sh
python3 -m unittest discover -s tests -p test_field_observations.py -v
```

Coverage includes verified-evidence gating, capture/review time separation, original
prediction attribution, review corrections and withdrawals, missing-source safety,
privacy-field rejection, feed integrity, epoch mismatches and crash-safe replay.
