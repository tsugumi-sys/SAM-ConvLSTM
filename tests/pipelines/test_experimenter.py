import os
import tempfile
from unittest.mock import patch

import torch
from torch import nn
from torch.optim import Adam

from pipelines.experimenter import Experimenter
from pipelines.trainer import TrainingParams
from pipelines.utils.early_stopping import EarlyStopping
from tests.test_model.model import TestModel
from tests.utils import MockMovingMNISTDataLoaders


def mocked_save_model(model: nn.Module, save_path: str):
    torch.save({"model_state_dict": model.state_dict()}, save_path)


@patch("pipelines.utils.early_stopping.save_seq2seq_model")
def test_run(mocked_save_seq2seq_model):
    mocked_save_seq2seq_model.side_effect = mocked_save_model
    with tempfile.TemporaryDirectory() as tempdirpath:
        model = TestModel()
        training_params: TrainingParams = {
            "epochs": 1,
            "batch_size": 1,
            "loss_criterion": nn.MSELoss(),
            "accuracy_criterion": nn.L1Loss(),
            "optimizer": Adam(model.parameters(), lr=0.0005),
            "early_stopping": EarlyStopping(
                patience=30,
                verbose=True,
                delta=0.0001,
                model_save_path=os.path.join(tempdirpath, "train", "model.pt"),
            ),
            "metrics_filename": "metrics.csv",
        }
        dataset_length = 3
        data_loaders = MockMovingMNISTDataLoaders(
            dataset_length=dataset_length, train_batch_size=1, split_ratio=10
        )
        experimenter = Experimenter(tempdirpath, data_loaders, model, training_params)
        experimenter.run()

        # testing trainer artifacts
        assert os.path.exists(os.path.join(tempdirpath, "train", "model.pt"))
        assert os.path.exists(os.path.join(tempdirpath, "train", "metrics.csv"))
        # testing evaluator artifacts
        for i in range(dataset_length):
            assert os.path.exists(
                os.path.join(tempdirpath, "evaluation", f"test-case{i}.png")
            )
