import pytest

from pdfslice_py.filename_template import DEFAULT_TEMPLATE, compile_template


def test_renders_default_template_with_zero_padded_page_numbers():
    t = compile_template(DEFAULT_TEMPLATE)
    assert t.render("sample", 1) == "sample.001.jpg"
    assert t.render("sample", 42) == "sample.042.jpg"
    assert t.render("sample", 999) == "sample.999.jpg"


def test_does_not_pad_page_numbers_1000_and_above():
    t = compile_template(DEFAULT_TEMPLATE)
    assert t.render("sample", 1000) == "sample.1000.jpg"
    assert t.render("sample", 2026) == "sample.2026.jpg"


def test_parses_page_numbers_back_out_of_names_it_rendered():
    t = compile_template(DEFAULT_TEMPLATE)
    assert t.parse_page("sample.001.jpg") == 1
    assert t.parse_page("sample.042.jpg") == 42
    assert t.parse_page("sample.2026.jpg") == 2026


def test_returns_none_when_parsing_a_name_that_does_not_match():
    t = compile_template(DEFAULT_TEMPLATE)
    assert t.parse_page("readme.txt") is None
    assert t.parse_page("sample.jpg") is None


def test_supports_a_page_number_only_template():
    t = compile_template("{{page_number}}.jpg")
    assert t.render("ignored", 1) == "001.jpg"
    assert t.render("ignored", 7) == "007.jpg"
    assert t.parse_page("007.jpg") == 7


def test_supports_filename_before_a_custom_prefix_suffix_arrangement():
    t = compile_template("page-{{page_number}}-{{filename}}.jpg")
    assert t.render("report", 3) == "page-003-report.jpg"
    assert t.parse_page("page-003-report.jpg") == 3


def test_round_trips_page_numbers_for_filenames_containing_dots():
    t = compile_template(DEFAULT_TEMPLATE)
    rendered = t.render("my.report.v2", 5)
    assert rendered == "my.report.v2.005.jpg"
    assert t.parse_page(rendered) == 5


def test_throws_when_template_has_no_page_number_placeholder():
    with pytest.raises(ValueError, match="exactly one"):
        compile_template("{{filename}}.jpg")


def test_throws_when_template_has_more_than_one_page_number_placeholder():
    with pytest.raises(ValueError, match="exactly one"):
        compile_template("{{page_number}}-{{page_number}}.jpg")


def test_parse_page_is_case_insensitive_on_the_jpg_suffix():
    t = compile_template("{{filename}}.{{page_number}}.JPG")
    assert t.parse_page("sample.001.JPG") == 1
