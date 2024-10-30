# Homomorphic Index Optimization

## Overview
This project implements a reinforcement learning (RL) environment using Gymnasium to optimize the execution time of queries in a SQLite database by dynamically managing indexes. The project utilizes homomorphic encryption via the Pyfhel library to securely perform calculations on encrypted data.

## Features
- **Reinforcement Learning Environment**: Custom environment to train RL agents.
- **Homomorphic Encryption**: Perform calculations on encrypted data using CKKS scheme.
- **SQLite Integration**: Efficiently manage and query an encrypted SQLite database.
- **Dynamic Index Management**: Optimize query performance by adding and dropping indexes based on RL actions.

## Getting Started
To run train the agent, one needs to run ```Script/generate_keys.py```

### Prerequisites
- Python 3.10 or higher
- Required packages:
  - gymnasium
  - stable-baselines3
  - Pyfhel
  - sqlite3
  - numpy

### Installation
1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/homomorphic_index_optimization.git
   cd homomorphic_index_optimization

