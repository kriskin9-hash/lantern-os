"""Round-trip test for the per-user CSF profile pack (one file, KB-grounded)."""
import json
import pathlib
import tempfile

from csf import csf_pack, profile_pack


def test_profile_round_trip(monkeypatch):
    with tempfile.TemporaryDirectory() as d:
        d = pathlib.Path(d)
        # Fake repo layout: a user cube + a KB index.
        (d / "data" / "cubes" / "u1.private" / "deltas").mkdir(parents=True)
        (d / "data" / "cubes" / "u1.private" / "manifest.json").write_text('{"user":"u1"}')
        (d / "data" / "cubes" / "u1.private" / "deltas" / "deltas.jsonl").write_text('{"d":1}\n{"d":2}\n')
        (d / "data" / "knowledge").mkdir(parents=True)
        kb = d / "data" / "knowledge" / "index.jsonl"
        kb.write_text('{"id":"a","text":"grounding section"}\n')

        monkeypatch.setattr(profile_pack, "REPO", d)
        monkeypatch.setattr(profile_pack, "KB_INDEX", kb)
        monkeypatch.setattr(profile_pack, "KB_META", d / "data" / "knowledge" / "index.meta.json")

        out = str(d / "u1.csf")
        m = profile_pack.pack_profile("u1", out)
        assert m["user"] == "u1"
        assert m["user_file_count"] == 2          # manifest + deltas
        assert m["grounding"]["knowledge_index"] == "knowledge/index.jsonl"

        # info reads the embedded manifest without extracting
        meta = profile_pack.info(out)
        assert meta["user"] == "u1" and meta["grounding"]["sections"] == 1

        # unpack restores user data + embedded KB grounding
        dest = d / "restore"
        written = csf_pack.unpack(out, str(dest))
        assert any("user/u1.private/deltas/deltas.jsonl" in w.replace("\\", "/") for w in written)
        assert (dest / "knowledge" / "index.jsonl").exists()
        assert (dest / "_profile.json").exists()
        prof = json.loads((dest / "_profile.json").read_text())
        assert prof["format"] == "csf-profile"
