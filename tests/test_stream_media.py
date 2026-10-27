import os
import tempfile
import pytest

from idm_media.parser import StreamParser, StreamSegment
from idm_media.muxer import StreamMuxer


def test_parse_hls_m3u8_playlist():
    m3u8_sample = """#EXTM3U
#EXT-X-VERSION:3
#EXT-X-TARGETDURATION:10
#EXT-X-MEDIA-SEQUENCE:0
#EXTINF:10.000,
segment_0.ts
#EXTINF:10.000,
segment_1.ts
#EXTINF:5.500,
https://cdn.example.com/stream/segment_2.ts
#EXT-X-ENDLIST
"""
    segments = StreamParser.parse_m3u8(m3u8_sample, base_url="https://example.com/stream/")

    assert len(segments) == 3
    assert segments[0].url == "https://example.com/stream/segment_0.ts"
    assert segments[0].duration == 10.0
    assert segments[1].url == "https://example.com/stream/segment_1.ts"
    assert segments[2].url == "https://cdn.example.com/stream/segment_2.ts"
    assert segments[2].duration == 5.5


def test_parse_mpd_dash_manifest():
    mpd_sample = """<?xml version="1.0" encoding="UTF-8"?>
<MPD xmlns="urn:mpeg:dash:schema:mpd:2011" minBufferTime="PT1.5S">
  <Period>
    <AdaptationSet mimeType="video/mp4" contentType="video">
      <Representation id="1080p" bandwidth="4000000" width="1920" height="1080">
        <BaseURL>video/1080p/</BaseURL>
        <SegmentList duration="10">
          <SegmentURL media="seg-1.m4s"/>
          <SegmentURL media="seg-2.m4s"/>
        </SegmentList>
      </Representation>
    </AdaptationSet>
  </Period>
</MPD>"""

    segments = StreamParser.parse_mpd(mpd_sample, base_url="https://example.com/dash/")

    assert len(segments) == 2
    assert segments[0].url == "https://example.com/dash/video/1080p/seg-1.m4s"
    assert segments[1].url == "https://example.com/dash/video/1080p/seg-2.m4s"


def test_muxer_concatenates_stream_segments():
    with tempfile.TemporaryDirectory() as tmpdir:
        seg1 = os.path.join(tmpdir, "seg1.ts")
        seg2 = os.path.join(tmpdir, "seg2.ts")
        out = os.path.join(tmpdir, "final.ts")

        with open(seg1, "wb") as f:
            f.write(b"MPEG-TS-SEGMENT-1-DATA;")
        with open(seg2, "wb") as f:
            f.write(b"MPEG-TS-SEGMENT-2-DATA;")

        muxer = StreamMuxer()
        result_path = muxer.concat_segments([seg1, seg2], out)

        assert os.path.exists(result_path)
        with open(result_path, "rb") as f:
            content = f.read()
        assert content == b"MPEG-TS-SEGMENT-1-DATA;MPEG-TS-SEGMENT-2-DATA;"
