import os
from pathlib import Path
import json
import pandas as pd
from music21 import converter, note, stream, articulations

"""
This script creates REMI formatted tokens from .xml files, and attaches associated metadata to REMI tokens. This utilises the PDMX dataset available from
https://github.com/pnlong/PDMX/blob/main/README.md



"""

# Duration labels
DURATION_LABELS = {
    4.0: "Duration_1", 3.0: "Duration_d2", 2.0: "Duration_1/2", 1.5: "Duration_d1/4",
    1.0: "Duration_1/4", 2/3: "Duration_1/4t", 0.75: "Duration_d1/8", 0.5: "Duration_1/8",
    1/3: "Duration_1/8t", 0.375: "Duration_d1/16", 0.25: "Duration_1/16",
    1/6: "Duration_1/16t", 0.125: "Duration_1/32", 1/12: "Duration_1/32t"
}

# Define directories and filepaths
PROJECT_ROOT = Path("/mnt/c/Users/james/projects/transmusetate/project_root")
MXL_DIR = PROJECT_ROOT / "mxl"
METADATA_DIR = PROJECT_ROOT / "metadata"
RESULTS_DIR = PROJECT_ROOT / "results"
PDMX_CSV = PROJECT_ROOT / "PDMX.csv"

# Load CSV mapping: mxl path => metadata path
PDMX = pd.read_csv(PDMX_CSV)
PDMX_DICT = dict(zip(PDMX["mxl"], PDMX["metadata"]))

def quantize_position(offset, quarter_length=1.0, steps_per_quarter=4):
    """
    Quantize a musical event's offset into a discrete position index.

    Parameters
    ----------
    offset : float
        Offset (timing) of the event within the measure.
    quarter_length : float, optional
        Duration of a quarter note, default is 1.0.
    steps_per_quarter : int, optional
        Number of quantization steps per quarter note, default is 4.

    Returns
    -------
    int
        Quantized step index corresponding to the event's position.
    """
    step = quarter_length / steps_per_quarter
    return int(offset / step)

def quantize_duration(duration):
    """
    Map a musical duration to the closest predefined REMI duration label.

    Parameters
    ----------
    duration : float
        Duration of a note or rest in quarter lengths.

    Returns
    -------
    str
        REMI duration label (e.g., 'Duration_1/4', 'Duration_1/8').
    """
    closest = min(DURATION_LABELS.keys(), key=lambda x: abs(x - duration))
    return DURATION_LABELS[closest]

def load_external_metadata(mxl_path_relative):
    """
    Load external metadata JSON corresponding to a given MusicXML file.

    Parameters
    ----------
    mxl_path_relative : str
        Relative path to the .mxl file as listed in the PDMX mapping.

    Returns
    -------
    dict
        Metadata dictionary, or empty dictionary if not found.
    """
    if mxl_path_relative not in PDMX_DICT:
        print(f"⚠️ No metadata entry in PDMX for: {mxl_path_relative}")
        return {}
    json_rel_path = PDMX_DICT[mxl_path_relative].lstrip("./")
    json_path = PROJECT_ROOT / json_rel_path
    try:
        with open(json_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"❌ Failed to load metadata: {json_path} — {e}")
        return {}

def convert_xml_to_remi_musicbert(file_path, rel_mxl_path, steps_per_quarter=4):
    """
    Convert a MusicXML file into a sequence of REMI tokens and extract its metadata.

    Parameters
    ----------
    file_path : Path or str
        Full path to the .mxl file.
    rel_mxl_path : str
        Relative path used for metadata lookup.
    steps_per_quarter : int, optional
        Number of steps per quarter note for position quantization (default 4).

    Returns
    -------
    tokens : list of str
        List of REMI formatted tokens extracted from the file.
    metadata : dict
        Metadata dictionary associated with the file.
    """
    score = converter.parse(file_path)
    tokens = []
    metadata = load_external_metadata(rel_mxl_path)
    metadata["filename"] = os.path.basename(file_path)

    for part in score.parts:
        measures = part.getElementsByClass(stream.Measure)
        for measure in measures:
            tokens.append("Bar")
            for el in measure.notesAndRests:
                pos = quantize_position(el.offset, steps_per_quarter)
                tokens.append(f"Position_{pos}")

                if isinstance(el, note.Note):
                    tokens.append(f"Pitch_{el.pitch.midi}")
                    tokens.append(quantize_duration(el.duration.quarterLength))
                    for art in el.articulations:
                        tokens.append(f"Articulation_{art.classes[0]}")
                elif isinstance(el, note.Rest):
                    tokens.append("Rest")
                    tokens.append(quantize_duration(el.duration.quarterLength))

    return tokens, metadata

def save_tokens(tokens, file_path, output_dir):
    """
    Save the list of REMI tokens to a text file.

    Parameters
    ----------
    tokens : list of str
        REMI tokens to be saved.
    file_path : Path or str
        Original MusicXML file path (used to name output).
    output_dir : Path or str
        Directory where the token file will be saved.

    Returns
    -------
    None
    """
    os.makedirs(output_dir, exist_ok=True)
    base = Path(file_path).stem
    out_path = output_dir / f"{base}.remi.txt"
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(" ".join(tokens))

def save_metadata_json(metadata, file_path, output_dir):
    """
    Save the metadata dictionary to a JSON file.

    Parameters
    ----------
    metadata : dict
        Metadata to save.
    file_path : Path or str
        Original MusicXML file path (used to name output).
    output_dir : Path or str
        Directory where the metadata file will be saved.

    Returns
    -------
    None
    """
    os.makedirs(output_dir, exist_ok=True)
    base = Path(file_path).stem
    out_path = output_dir / f"{base}.metadata.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)

def batch_process(input_dir, output_dir=RESULTS_DIR):
    """
    Batch process all .mxl files in the input directory into REMI tokens and metadata.

    Parameters
    ----------
    input_dir : Path or str
        Directory containing .mxl files to process.
    output_dir : Path or str, optional
        Directory where results will be saved (default RESULTS_DIR).

    Returns
    -------
    None
    """
    input_path = Path(input_dir)
    os.makedirs(output_dir, exist_ok=True)

    metadata_csv_path = output_dir / "all_metadata.csv"
    first_row = True

    for file in input_path.rglob("*.mxl"):
        rel_path = "./" + str(file.relative_to(PROJECT_ROOT).as_posix())
        print(f"🎼 Processing: {rel_path}")

        try:
            tokens, metadata = convert_xml_to_remi_musicbert(file, rel_path)
            save_tokens(tokens, file, output_dir)
            save_metadata_json(metadata, file, output_dir)

            df_row = pd.DataFrame([metadata])
            df_row.to_csv(metadata_csv_path, mode='a', index=False, header=first_row)
            first_row = False

        except Exception as e:
            print(f"❌ Error processing {file}: {e}")

    print(f"\n✅ Metadata written to {metadata_csv_path}")

    
# Run it
if __name__ == "__main__":
    batch_process(input_dir=MXL_DIR)