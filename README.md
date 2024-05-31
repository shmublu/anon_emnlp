# LLM-based Puzzle Grader

## Overview
This project implements a system to automatically solve and grade logic puzzles using large language models (LLMs). It features a multi-agent setup with distinct roles for solvers, graders, and decomposers, integrating SMT-LIB for formal reasoning. 

## Running the Workflow

**Running the Puzzle Solver and Grader**
1. Goto the directory where `LLM-based-puzzle-grader.py` is located.
2. Modify parameters as needed at line 368 to adjust configurations such as the model type or the number of retries.
3. Execute the script to start the puzzle solving and grading process

## Analyzing the Solver

Replace `graded_file` with your actual CSV file path to evaluate the results in llm_csv_processor.py. Then, run it.

## File Structure
- `data/puzzles`: Contains directories for each puzzle, which include:
  - `answers.txt`: Correct answers for the puzzle.
  - `clues.txt`: Clues provided to solve the puzzle.
  - `entities.txt`: Entities involved in the puzzle.
- `solvers.py`: Contains logic for different agent roles such as solver, grader, and decomposer.

## Usage
Modify configurations in the `Config` class within `LLM-based-puzzle-grader.py` to change behavior of the solvers and graders. Parameters like `max_tries`, `temperatures`, and `use_smt` can be adjusted. The Flask app settings such as `SECRET_KEY` and `SESSION_TYPE` can also be modified to fit different operational environments or security requirements.

Participants in the user study can upload CSV files containing puzzle solutions. They will grade these solutions based on interpretability and correctness, following instructions provided on the web interface.