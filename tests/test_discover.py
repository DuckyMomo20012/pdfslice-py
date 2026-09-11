from pathlib import Path

from pdfslice_py.discover import (
    find_images_deep,
    find_pdfs,
    page_image_name,
    parse_page_from_image_name,
)


class TestPageImageName:
    def test_pads_page_numbers_under_1000_to_3_digits(self):
        assert page_image_name("sample", 1) == "sample.001.jpg"
        assert page_image_name("sample", 42) == "sample.042.jpg"
        assert page_image_name("sample", 999) == "sample.999.jpg"

    def test_does_not_pad_page_numbers_1000_and_above(self):
        assert page_image_name("sample", 1000) == "sample.1000.jpg"
        assert page_image_name("sample", 2026) == "sample.2026.jpg"


class TestParsePageFromImageName:
    def test_extracts_the_page_number_from_a_well_formed_name(self):
        assert parse_page_from_image_name("sample.001.jpg") == 1
        assert parse_page_from_image_name("sample.2026.jpg") == 2026

    def test_returns_none_for_names_without_a_page_number(self):
        assert parse_page_from_image_name("sample.jpg") is None
        assert parse_page_from_image_name("readme.txt") is None


class TestFindPdfs:
    def test_returns_the_file_itself_when_input_is_a_single_pdf(self, tmp_path: Path):
        file = tmp_path / "a.pdf"
        file.write_text("fake")
        assert find_pdfs(file) == [str(file)]

    def test_returns_empty_list_when_input_is_a_single_non_pdf_file(self, tmp_path: Path):
        file = tmp_path / "a.txt"
        file.write_text("fake")
        assert find_pdfs(file) == []

    def test_finds_pdfs_directly_in_root_at_level_1_default(self, tmp_path: Path):
        (tmp_path / "one.pdf").write_text("x")
        (tmp_path / "two.pdf").write_text("x")
        (tmp_path / "note.txt").write_text("x")
        found = sorted(find_pdfs(tmp_path))
        assert found == sorted([str(tmp_path / "one.pdf"), str(tmp_path / "two.pdf")])

    def test_does_not_descend_into_subfolders_at_level_1(self, tmp_path: Path):
        (tmp_path / "top.pdf").write_text("x")
        sub = tmp_path / "sub"
        sub.mkdir()
        (sub / "nested.pdf").write_text("x")
        assert find_pdfs(tmp_path, 1) == [str(tmp_path / "top.pdf")]

    def test_descends_one_level_with_level_2(self, tmp_path: Path):
        (tmp_path / "top.pdf").write_text("x")
        sub = tmp_path / "sub"
        sub.mkdir()
        (sub / "nested.pdf").write_text("x")
        found = sorted(find_pdfs(tmp_path, 2))
        assert found == sorted([str(tmp_path / "top.pdf"), str(sub / "nested.pdf")])

    def test_does_not_find_a_pdf_two_levels_deep_at_level_2(self, tmp_path: Path):
        sub2 = tmp_path / "sub1" / "sub2"
        sub2.mkdir(parents=True)
        (sub2 / "deep.pdf").write_text("x")
        assert find_pdfs(tmp_path, 2) == []


class TestFindImagesDeep:
    def test_finds_jpg_jpeg_files_at_any_depth(self, tmp_path: Path):
        (tmp_path / "a.jpg").write_text("x")
        sub = tmp_path / "nested" / "deeper"
        sub.mkdir(parents=True)
        (sub / "b.jpeg").write_text("x")
        (sub / "c.png").write_text("x")  # should be ignored
        found = sorted(find_images_deep(tmp_path))
        assert found == sorted([str(tmp_path / "a.jpg"), str(sub / "b.jpeg")])

    def test_returns_empty_list_when_no_images_present(self, tmp_path: Path):
        (tmp_path / "doc.pdf").write_text("x")
        assert find_images_deep(tmp_path) == []
