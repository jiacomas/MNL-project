# backend/tests/test_data_loader.py

from pathlib import Path

from backend import data_loader


def test_load_movies_from_kaggle_with_mocker(tmp_path, mocker):
    """Test load_movies_from_kaggle using mocks so we don't hit real Kaggle or real filesystem."""

    # Create a fake Kaggle cache directory
    fake_cache_root = tmp_path / "kaggle_cache"
    fake_cache_root.mkdir(parents=True, exist_ok=True)

    # Create some fake files: only .csv and .json should be copied
    csv_file = fake_cache_root / "movieReviews.csv"
    json_file = fake_cache_root / "metadata.json"
    txt_file = fake_cache_root / "README.txt"

    csv_file.write_text("id,title\n1,Test Movie")
    json_file.write_text('{"foo": "bar"}')
    txt_file.write_text("ignore me")

    # 1) Mock kagglehub.dataset_download to return our fake cache path
    mocker.patch(
        "backend.data_loader.kagglehub.dataset_download",
        return_value=str(fake_cache_root),
    )

    # 2) Mock settings.MOVIE_DATA_PATH so it writes into a temp directory
    mocker.patch(
        "backend.data_loader.settings.MOVIE_DATA_PATH",
        tmp_path / "data",  # this will be used as target_root
    )

    # 3) Mock create_movies_data.main and convert_movies_json_to_csv.main
    fake_create_main = mocker.patch("backend.data_loader.create_movies_data.main")
    fake_convert_main = mocker.patch(
        "backend.data_loader.convert_movies_json_to_csv.main"
    )

    # --- call function under test ---
    summary = data_loader.load_movies_from_kaggle()

    # --- assertions ---

    # a) files_copied should be 2 (csv + json, txt should be ignored)
    assert summary["files_copied"] == 2

    # b) target_root should be our mocked MOVIE_DATA_PATH
    target_root = Path(summary["target_root"])
    assert target_root.exists()
    assert target_root.is_dir()
    assert target_root == tmp_path / "data"

    # c) copied files exist in target_root
    assert (target_root / "movieReviews.csv").exists()
    assert (target_root / "metadata.json").exists()
    assert not (target_root / "README.txt").exists()

    # d) helper functions are called once
    fake_create_main.assert_called_once()
    fake_convert_main.assert_called_once()
