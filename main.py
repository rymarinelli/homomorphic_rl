import gymnasium as gym
from stable_baselines3 import PPO
from stable_baselines3.common.env_checker import check_env
import torch
from rl_agent.DatabaseIndexEnv import DatabaseIndexEnv
from Scripts.generate_data import create_encrypted_db_with_dummy_data

def main():
    print("Creating the database and populating it with data...")
    create_encrypted_db_with_dummy_data()  # Create the database and populate it with data

    print("Initializing the environment...")
    env = DatabaseIndexEnv()  

    print("Checking the environment...")
    check_env(env)  # Check if the environment follows Gym's API

    # Check if GPU is available
    device = 'cuda' if torch.cuda.is_available() else 'cpu'
    print(f"Using device: {device}")


    print("Training the PPO model...")
    model = PPO("MlpPolicy", env, verbose=1, device=device)  
    model.learn(total_timesteps=3)


    model.save("ppo_index_optimizer")
    print("Model saved as 'ppo_index_optimizer'.")

   
    env.save_episode_logs("episode_logs.csv")
    print("Episode logs saved to 'episode_logs.csv'.")

   
    env.close()
    print("Environment closed.")

if __name__ == "__main__":
    main()

