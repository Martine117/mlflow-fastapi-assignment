import numpy as np
import pytest
from sklearn.datasets import load_digits
from dataset import export_digits, load_training_data, DATA_PATH


def test_export_matches_original_and_is_reproducible(tmp_path):
    path = tmp_path / 'digits.csv'
    export_digits(path)
    first = path.read_bytes()
    export_digits(path)
    assert first == path.read_bytes() == DATA_PATH.read_bytes()
    x, y = load_training_data(path)
    original_x, original_y = load_digits(return_X_y=True)
    np.testing.assert_array_equal(x, original_x)
    np.testing.assert_array_equal(y, original_y)


def test_missing_data_fails_clearly(tmp_path):
    with pytest.raises(FileNotFoundError, match='dvc pull'):
        load_training_data(tmp_path / 'missing.csv')
