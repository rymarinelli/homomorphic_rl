import gymnasium as gym
from gymnasium import spaces
import numpy as np
import sqlite3
import random
import time
import csv
from Pyfhel import PyCtxt

from Scripts.generate_data import create_encrypted_db_with_dummy_data
from Scripts.ckks import HE  
from Scripts.homomorphic_sum import HomomorphicSumAggregate  

import logging
from tqdm import tqdm 


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DatabaseIndexEnv(gym.Env):
    def __init__(self, db_name='california_housing.db', max_steps=1):
        super(DatabaseIndexEnv, self).__init__()
        logger.info("Initializing DatabaseIndexEnv...")
        self.db_name = db_name
        self.max_steps = max_steps
        self.current_step = 0
        self.episode_logs = []
        self.conn = self._create_connection()
        self.cursor = self.conn.cursor()
        self.he_instance = HE() 

        # Register homomorphic_sum as an aggregate function
        self.conn.create_aggregate("homomorphic_sum", 1, HomomorphicSumAggregate)
        logger.info("homomorphic_sum aggregate function registered in SQLite.")

        # Set up action and observation spaces
        self.action_space = spaces.Discrete(6)
        self.observation_space = spaces.Box(low=0, high=np.inf, shape=(1,), dtype=np.float32)
        self.state = np.array([0], dtype=np.float32)
        self.queries = [
            ("SELECT homomorphic_sum(MedInc_enc) FROM housing_encrypted WHERE HouseAge_enc > ?", [(10, 50)]),
            ("SELECT homomorphic_sum(Population_enc) FROM housing_encrypted WHERE AveRooms_enc > ?", [(1, 10)]),
            ("SELECT homomorphic_sum(AveOccup_enc) FROM housing_encrypted WHERE Longitude_enc > ? AND Latitude_enc < ?", [(-120, -115), (32, 40)]),
            ("SELECT homomorphic_sum(AveRooms_enc) FROM housing_encrypted WHERE MedInc_enc BETWEEN ? AND ?", [(2, 3), (8, 9)]),
            ("SELECT homomorphic_sum(MedHouseVal_enc) FROM housing_encrypted WHERE AveRooms_enc > ? AND AveBedrms_enc < ?", [(3, 6), (1, 3)]),
            ("SELECT homomorphic_sum(MedInc_enc) FROM housing_encrypted WHERE Population_enc > ? AND Longitude_enc < ?", [(1000, 5000), (-120, -115)]),
        ]

    def _create_connection(self):
        logger.info("Creating database connection...")
        retries = 5
        delay = 1

        for attempt in range(retries):
            try:
                conn = sqlite3.connect(self.db_name, timeout=90)
                conn.execute('PRAGMA busy_timeout = 900000;')
                wal_mode = conn.execute('PRAGMA journal_mode').fetchone()[0]
                if wal_mode.lower() != 'wal':
                    conn.execute('PRAGMA journal_mode=WAL;')
                    logger.info("SQLite journal mode set to WAL.")
                else:
                    logger.info("SQLite journal mode is already WAL.")
                return conn
            except sqlite3.OperationalError as e:
                if 'locked' in str(e):
                    logger.warning(f"Failed to set WAL mode, retrying {attempt + 1}/{retries}...")
                    time.sleep(delay)
                else:
                    logger.error(f"Failed to create connection: {e}")
                    raise sqlite3.OperationalError(f"Failed to create connection: {e}")
        raise sqlite3.OperationalError("Failed to set WAL mode after multiple retries.")

    def step(self, action):
        logger.info(f"Step {self.current_step + 1}/{self.max_steps}: Applying action {action}...")
        self._set_index(action)

        logger.info("Executing queries and measuring execution times...")
        query_times = [self._execute_query(query, param_ranges) for query, param_ranges in self.queries]
        avg_query_time = np.mean(query_times)
        logger.info(f"Average query execution time: {avg_query_time:.6f} seconds")

        reward = -avg_query_time
        self.state = np.array([avg_query_time], dtype=np.float32)
        self.current_step += 1
        terminated = self.current_step >= self.max_steps
        truncated = False

        info = {'avg_query_time': avg_query_time}
        if terminated:
            self.episode_logs.append(avg_query_time)

        return self.state, reward, terminated, truncated, info

    def reset(self, seed=None, options=None):
        logger.info("Resetting environment...")
        if seed is not None:
            np.random.seed(seed)
            random.seed(seed)

        self.state = np.array([0], dtype=np.float32)
        self.current_step = 0
        return self.state, {}

    def _set_index(self, action):
        logger.info(f"Setting index for action {action}...")
        index_names = [
            'idx_medinc',
            'idx_houseage',
            'idx_medinc_houseage',
            'idx_population_ave_rooms',
            'idx_latitude_longitude',
            'idx_ave_rooms_house_age'
        ]
        for index_name in index_names:
            self.cursor.execute(f'DROP INDEX IF EXISTS {index_name}')
        logger.info("Existing indexes dropped.")

        if action == 1:
            self.cursor.execute('CREATE INDEX IF NOT EXISTS idx_medinc ON housing_encrypted (MedInc_enc)')
            logger.info("Index idx_medinc created.")
        elif action == 2:
            self.cursor.execute('CREATE INDEX IF NOT EXISTS idx_houseage ON housing_encrypted (HouseAge_enc)')
            logger.info("Index idx_houseage created.")
        elif action == 3:
            self.cursor.execute('CREATE INDEX IF NOT EXISTS idx_medinc_houseage ON housing_encrypted (MedInc_enc, HouseAge_enc)')
            logger.info("Index idx_medinc_houseage created.")
        elif action == 4:
            self.cursor.execute('CREATE INDEX IF NOT EXISTS idx_population_ave_rooms ON housing_encrypted (Population_enc, AveRooms_enc)')
            logger.info("Index idx_population_ave_rooms created.")
        elif action == 5:
            self.cursor.execute('CREATE INDEX IF NOT EXISTS idx_latitude_longitude ON housing_encrypted (Latitude_enc, Longitude_enc)')
            logger.info("Index idx_latitude_longitude created.")
        elif action == 6:
            self.cursor.execute('CREATE INDEX IF NOT EXISTS idx_ave_rooms_house_age ON housing_encrypted (AveRooms_enc, HouseAge_enc)')
            logger.info("Index idx_ave_rooms_house_age created.")

        self.conn.commit()
        logger.info("Index action committed.")

    def _execute_query(self, query, param_ranges):
        params = [random.uniform(low, high) for low, high in param_ranges]
        logger.info(f"Executing query: {query} with params {params}")
        start_time = time.time()
        self.cursor.execute(query, params)
        self.cursor.fetchall()
        end_time = time.time()
        execution_time = end_time - start_time
        logger.info(f"Query executed in {execution_time:.6f} seconds.")
        return execution_time

    def close(self):
        logger.info("Closing environment and database connection...")
        self.conn.close()
        logger.info("Environment closed.")

    def save_episode_logs(self, filename='episode_logs.csv'):
        logger.info(f"Saving episode logs to {filename}...")
        with open(filename, mode='w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(['Episode', 'Average Query Time'])
            for i, avg_time in enumerate(self.episode_logs):
                writer.writerow([i + 1, avg_time])
        logger.info(f"Episode logs saved to {filename}.")

