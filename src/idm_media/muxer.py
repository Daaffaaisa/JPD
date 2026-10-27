import os
import shutil


class StreamMuxer:
    """Concatenates or muxes media stream segments into a unified container."""

    def concat_segments(self, segment_paths: list[str], output_path: str) -> str:
        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
        with open(output_path, "wb") as outfile:
            for seg in segment_paths:
                with open(seg, "rb") as infile:
                    shutil.copyfileobj(infile, outfile, length=1024 * 1024)
        return output_path
