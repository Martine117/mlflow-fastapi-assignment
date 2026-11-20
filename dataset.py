"""Deterministic, headered CSV export; no network or private data required."""
from pathlib import Path
import hashlib
import numpy as np
from sklearn.datasets import load_digits

DATA_PATH = Path(__file__).resolve().parent / 'data' / 'digits.csv'
HEADER = ','.join([f'pixel_{i}' for i in range(64)] + ['target'])


def export_digits(path=DATA_PATH):
    x, y = load_digits(return_X_y=True)
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('w', encoding='utf-8', newline='\n') as stream:
        np.savetxt(stream, np.column_stack([x, y]), fmt='%d', delimiter=',',
                   header=HEADER, comments='')


def load_training_data(path=DATA_PATH):
    path = Path(path)
    if not path.is_file():
        raise FileNotFoundError('Dataset missing: run dvc pull or python dataset.py first')
    with path.open(encoding='utf-8') as stream:
        if stream.readline().strip() != HEADER:
            raise ValueError('Unexpected digits CSV header')
    values = np.loadtxt(path, delimiter=',', skiprows=1, ndmin=2)
    if values.shape != (1797, 65) or not np.isfinite(values).all():
        raise ValueError('Expected 1797 finite digits rows with 65 columns')
    if not np.equal(values, np.floor(values)).all():
        raise ValueError('Expected integer pixels and labels')
    if not ((values[:, :64] >= 0) & (values[:, :64] <= 16)).all():
        raise ValueError('Pixels must be between 0 and 16')
    if not ((values[:, 64] >= 0) & (values[:, 64] <= 9)).all():
        raise ValueError('Labels must be between 0 and 9')
    return values[:, :64], values[:, 64].astype(int)


def dataset_sha256():
    return hashlib.sha256(DATA_PATH.read_bytes()).hexdigest()


if __name__ == '__main__':
    export_digits()
    print(f'Exported 1797 rows to {DATA_PATH.name}; sha256={dataset_sha256()}')
