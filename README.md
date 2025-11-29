# Log Analysis Engine — Rival Assignment

This project implements a high-performance log analysis system that processes large JSON log datasets and generates an analytics report in a single pass. The solution is optimized, production-style, and fully tested.

---

## ✨ Features

### ✔ Core Features
- **Single-pass processing (O(N))**
- **Summary section**: unique endpoints, users, time range, total/invalid logs
- **Endpoint statistics**: avg/median/95th percentile response time, status code distribution, success rate
- **Hourly request distribution**
- **Top users**
- **Performance issue detection** (medium/high/critical)
- **Error rate analysis**
- **Validation of all logs** (invalid logs counted)

### ✔ Advanced Options Implemented
- **A — Cost Analysis**  
  Estimates total request cost based on a configurable per-request cost.
  
- **C — Rate Limiting Analysis**  
  Sliding window (60s) analysis to detect users/endpoints exceeding limits.

### ✔ Recommendations Engine
Generates actionable recommendations from:
- performance issues  
- rate-limit violations  
- high error-rate endpoints  

---

## 📂 Project Structure
├── README.md                     # Main documentation
├── DESIGN.md                     # Design decisions & approach
├── function.py # Main function 
├── config.py  # Configuration
├── utils.py   # Helper functions
├── tests/
│   ├── test_function.py   # Test files
│   ├── test_edge_cases.py
│   └── test_data/
│       ├── sample_small.json     
│       ├── sample_medium.json
│       └── sample_large.json
├── requirements.txt             



## 💻 Getting Started with the Project

Here is the setup and execution guide for the  project:

---

### 1️⃣ Clone the Repository

Clone the project from GitHub and navigate into the directory.

```bash
git clone [https://github.com/SuryaYadav707/SuryaPratapYadav_rival_assignment.git](https://github.com/SuryaYadav707/SuryaPratapYadav_rival_assignment.git)
cd SuryaPratapYadav_rival_assignment
````

-----

### 2️⃣ Create a Virtual Environment

It's recommended to use a virtual environment to manage dependencies.

#### On Linux / macOS

```bash
python3 -m venv venv
source venv/bin/activate
```

#### On Windows (PowerShell)

```bash
python -m venv venv
venv\Scripts\activate
```

-----

### 3️⃣ Install Dependencies

Install the required Python packages using **pip**.

```bash
pip install -r requirements.txt
```

-----

### 4️⃣ Run the Analysis

Execute the main script to run the analysis function.

```bash
python function.py
```

-----

### 5️⃣ Run Tests

Verify the functionality by running the tests using **pytest**.

```bash
pytest -q
```

