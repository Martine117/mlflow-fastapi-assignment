import mlflow
import mlflow.sklearn
from mlflow.models import infer_signature
from dataset import load_training_data, dataset_sha256
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score
from sklearn.model_selection import train_test_split

from settings import ARTIFACT, EXPERIMENT, PROJECT


def main():
    mlflow.set_experiment(EXPERIMENT)
    x, y = load_training_data()
    x_train, x_test, y_train, y_test = train_test_split(
        x, y, test_size=0.2, random_state=42
    )
    for trees, depth in [(20, 5), (100, 10)]:
        with mlflow.start_run(run_name=f'rf-{trees}-{depth}') as run:
            mlflow.set_tags({'project': PROJECT, 'model_ready': 'false'})
            mlflow.set_tag('dataset_sha256', dataset_sha256())
            model = RandomForestClassifier(n_estimators=trees, max_depth=depth, random_state=42)
            model.fit(x_train, y_train)
            accuracy = accuracy_score(y_test, model.predict(x_test))
            mlflow.log_params({'n_estimators': trees, 'max_depth': depth, 'random_state': 42})
            mlflow.log_metric('accuracy', accuracy)
            mlflow.sklearn.log_model(
                model, ARTIFACT, signature=infer_signature(x_train, model.predict(x_train)),
                input_example=x_train[:2],
            )
            mlflow.set_tag('model_ready', 'true')
            print(f'run_id={run.info.run_id} accuracy={accuracy:.4f}')


if __name__ == '__main__':
    main()
