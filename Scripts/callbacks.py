from stable_baselines3.common.callbacks import BaseCallback
from tqdm import tqdm
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TQDMCallback(BaseCallback):
    """
    Custom callback for displaying a tqdm progress bar during training.
    """

    def __init__(self, total_timesteps, verbose=0):
        super(TQDMCallback, self).__init__(verbose)
        self.total_timesteps = total_timesteps
        self.pbar = tqdm(total=self.total_timesteps, desc="Training Progress", unit="steps", dynamic_ncols=True)

    def _on_step(self) -> bool:
        """
        Called at every step. Updates the progress bar.
        """
        self.pbar.update(1)
        return True  # Returning False would stop training early

    def _on_training_end(self) -> None:
        """
        Called at the end of training. Closes the progress bar.
        """
        self.pbar.close()
        logger.info("Training completed.")

