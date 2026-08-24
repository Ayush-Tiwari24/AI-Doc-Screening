from ml.ocr_service import parse_mrz, extract_non_mrz_fields

# A syntactically valid TD3 MRZ (passport) with correct checksums,
# built by hand from the ICAO 9303 checksum algorithm.
VALID_LINE1 = "P<UTOERIKSSON<<ANNA<MARIA<<<<<<<<<<<<<<<<<<"
VALID_LINE2 = "L898902C36UTO7408122F1204159ZE184226B<<<<<10"


def test_parse_mrz_valid_extracts_fields():
    result = parse_mrz([VALID_LINE1, VALID_LINE2])
    assert result is not None
    assert result["doc_number"] == "L898902C3"
    assert result["nationality"] == "UTO"
    assert result["gender"] == "F"
    assert "ERIKSSON" in result["full_name"].upper()
    assert "ANNA" in result["full_name"].upper()


def test_parse_mrz_valid_checksums_pass():
    result = parse_mrz([VALID_LINE1, VALID_LINE2])
    assert result["checksum_valid"]["doc_number"] is True
    assert result["checksum_valid"]["dob"] is True
    assert result["checksum_valid"]["expiry"] is True
    assert result["checksum_valid"]["composite"] is True


def test_parse_mrz_corrupted_checksum_detected():
    # Corrupt the document-number check digit (position 9 of line 2)
    corrupted_line2 = VALID_LINE2[:9] + "9" + VALID_LINE2[10:]
    result = parse_mrz([VALID_LINE1, corrupted_line2])
    assert result is not None
    assert result["checksum_valid"]["doc_number"] is False


def test_parse_mrz_no_mrz_present_returns_none():
    result = parse_mrz(["Just some random text", "Nothing MRZ-like here at all"])
    assert result is None


def test_parse_mrz_finds_mrz_among_noise():
    noisy_lines = ["REPUBLIC OF UTOPIA", "PASSPORT", VALID_LINE1, VALID_LINE2, "Some footer text"]
    result = parse_mrz(noisy_lines)
    assert result is not None
    assert result["doc_number"] == "L898902C3"


def test_extract_non_mrz_fields_basic():
    lines = ["Name: John Smith", "DOB: 01/02/1990", "License No: DL-12345"]
    result = extract_non_mrz_fields(lines, "license")
    assert result["full_name"] == "John Smith"
    assert result["doc_number"] == "DL-12345"
    assert result["dob_raw"] == "01/02/1990"