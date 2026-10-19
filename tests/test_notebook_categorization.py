from pathlib import Path

from organize_files import categorize


def test_jupyter_notebooks_have_a_dedicated_category():
    assert categorize(Path("analysis.ipynb")) == "Notebooks"


def test_notebook_extension_is_case_insensitive():
    assert categorize(Path("ANALYSIS.IPYNB")) == "Notebooks"
