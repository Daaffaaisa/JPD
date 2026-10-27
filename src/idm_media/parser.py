from dataclasses import dataclass
from typing import Optional
from urllib.parse import urljoin
import xml.etree.ElementTree as ET


@dataclass
class StreamSegment:
    url: str
    duration: float = 0.0
    sequence_number: int = 0


class StreamParser:
    """Parses streaming manifests (HLS .m3u8 and MPEG-DASH .mpd)."""

    @staticmethod
    def parse_m3u8(playlist_text: str, base_url: str = "") -> list[StreamSegment]:
        segments: list[StreamSegment] = []
        lines = [line.strip() for line in playlist_text.splitlines() if line.strip()]
        
        current_duration = 0.0
        seq = 0
        for line in lines:
            if line.startswith("#EXTINF:"):
                # e.g. #EXTINF:10.000,
                duration_part = line[8:].split(",")[0].strip()
                try:
                    current_duration = float(duration_part)
                except ValueError:
                    current_duration = 0.0
            elif not line.startswith("#"):
                seg_url = urljoin(base_url, line) if base_url else line
                segments.append(
                    StreamSegment(
                        url=seg_url,
                        duration=current_duration,
                        sequence_number=seq,
                    )
                )
                seq += 1
                current_duration = 0.0
        return segments

    @staticmethod
    def parse_mpd(mpd_xml: str, base_url: str = "") -> list[StreamSegment]:
        segments: list[StreamSegment] = []
        try:
            root = ET.fromstring(mpd_xml)
        except ET.ParseError:
            return []

        # Remove namespaces if present for easier tag finding
        for elem in root.iter():
            if "}" in elem.tag:
                elem.tag = elem.tag.split("}", 1)[1]

        # Look for BaseURL inside Representation or Period
        curr_base = base_url
        base_elem = root.find(".//BaseURL")
        if base_elem is not None and base_elem.text:
            curr_base = urljoin(curr_base, base_elem.text.strip())

        seq = 0
        for seg_url_elem in root.findall(".//SegmentURL"):
            media = seg_url_elem.get("media")
            if media:
                full_url = urljoin(curr_base, media) if curr_base else media
                segments.append(
                    StreamSegment(
                        url=full_url,
                        duration=0.0,
                        sequence_number=seq,
                    )
                )
                seq += 1

        return segments
