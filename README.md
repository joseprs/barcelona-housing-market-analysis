# Barcelona Housing Market Intelligence

This project is an end-to-end data science analysis of Barcelona’s housing listing market.

It combines data acquisition, data preparation, valuation modeling, spatial price analysis, and affordability scenario analysis to understand how listed flat prices vary across the city and how those prices relate to local income levels.

The objective is not only to build a predictive model, but to create a structured analytical workflow that supports market interpretation through reproducible code, clear assumptions, and transparent methodology.

---

## Project Overview

The project is organized into five components:

1. **Listing Data Collection**
2. **Market Snapshot**
3. **Valuation Model**
4. **Relative Price Positioning**
5. **Affordability Scenarios**

The data collection and preparation logic is implemented as reusable Python scripts in `src/`.

The analytical modules are implemented as clean notebooks supported by reusable Python code. The notebooks focus on analysis, interpretation, and outputs, while scraping, data preparation, modeling utilities, and analytical functions are separated into scripts.

---

## 1. Listing Data Collection

**Script:** `src/scraping/collect_listings.py`

This component collects raw housing listing data from the underlying search and property-detail endpoints used by the listing platform.

The collection process retrieves listing IDs from paginated search results and then collects detailed information for each listing, including property characteristics, location fields, price information, multimedia counts, energy indicators, and available amenities.

The collected raw files are saved under:

    data/raw/listings/

These files are then consumed by the data preparation pipeline to build the processed dataset used throughout the analysis.

Main outputs:

- Raw listing CSV files
- Listing-level property attributes
- Price and transaction information
- Location and coordinate fields
- Amenity and feature indicators

---

## 2. Market Snapshot

**Notebook:** `notebooks/01_market_snapshot.ipynb`

This module introduces the dataset used throughout the project.

It documents the structure, scope, and quality of the processed listing data. The data preparation pipeline consolidates raw listing files, standardizes fields, filters invalid observations, removes likely duplicates, applies outlier treatment, and creates derived variables such as price per square meter.

Main outputs:

- Processed listing dataset
- Dataset overview
- Key variable distributions
- Missing values summary
- Data scope and limitations

---

## 3. Valuation Model

**Notebook:** `notebooks/02_valuation_model.ipynb`

This module builds a supervised machine learning model to estimate flat asking prices in Barcelona based on property characteristics and location information.

The modeling workflow includes exploratory data analysis, feature engineering, model training, model comparison, hyperparameter optimization, error analysis, and feature importance evaluation.

Main outputs:

- Baseline model comparison
- Random Forest and XGBoost models
- Optimized valuation model
- Prediction error analysis
- Price-segment evaluation
- Feature importance analysis
- Saved model artifact

---

## 4. Relative Price Positioning

**Notebook:** `notebooks/03_relative_price_positioning.ipynb`

This module analyzes how prices vary across Barcelona districts and neighborhoods.

The analysis compares areas using average asking price, price per square meter, and a Relative Price Pressure Index. This index compares each neighborhood’s average price level against its average property size, providing a structured way to identify areas where prices are proportionally high relative to surface.

Main outputs:

- District-level price summaries
- Neighborhood-level price summaries
- Price per square meter rankings
- Relative Price Pressure Index
- Spatial maps of price indicators

---

## 5. Affordability Scenarios

**Notebook:** `notebooks/04_affordability_scenarios.ipynb`

This module evaluates housing affordability by combining listing prices with local salary estimates.

Each listing is spatially linked to census-section income data. Mortgage burden is then estimated under explicit financing assumptions, including purchase costs, down payment, interest rate, affordability threshold, and single-income versus couple-income scenarios.

Main outputs:

- Listing-level salary estimates
- Minimum affordable mortgage duration
- Fixed 30-year mortgage burden
- District-level affordability summaries
- Neighborhood-level affordability summaries
- Affordability maps

---

## Repository Structure

    barcelona-housing-market-intelligence/
    │
    ├── application/
    │
    ├── data/
    │   ├── raw/
    │   │   └── listings/
    │   ├── processed/
    │   └── external/
    │
    ├── models/
    │
    ├── notebooks/
    │   ├── old/
    │   ├── 01_market_snapshot.ipynb
    │   ├── 02_valuation_model.ipynb
    │   ├── 03_relative_price_positioning.ipynb
    │   └── 04_affordability_scenarios.ipynb
    │
    ├── reports/
    │   ├── figures/
    │   ├── maps/
    │   └── tables/
    │
    ├── src/
    │   ├── paths.py
    │   ├── analysis/
    │   ├── data/
    │   ├── modeling/
    │   └── scraping/
    │       └── collect_listings.py
    │
    ├── .gitignore
    ├── README.md
    └── requirements.txt

---

## Methodology

The project follows a modular data science workflow:

1. **Data acquisition**  
   Housing listing data is collected from paginated search results and listing-detail endpoints. The raw extracted records are stored as CSV files.

2. **Data preparation**  
   Raw files are consolidated, cleaned, standardized, filtered, and transformed into an analysis-ready dataset.

3. **Valuation modeling**  
   Machine learning models estimate listing asking prices from observable property and location features.

4. **Spatial price analysis**  
   Districts and neighborhoods are compared using price, price per square meter, and relative price pressure indicators.

5. **Affordability analysis**  
   Listing prices are combined with local salary estimates to evaluate mortgage burden under explicit assumptions.

---

## Key Assumptions and Limitations

This analysis is based on housing listings, not final transaction prices.

Important limitations:

- Listing prices represent asking prices, not final sale prices.
- The dataset reflects visible market supply at the time of data collection.
- Some listings may correspond to reposted or duplicated properties.
- Listing data can vary in completeness and accuracy.
- Salary estimates are linked geographically and should be interpreted as local income proxies.
- Mortgage calculations are scenario-based and do not reproduce exact bank approval processes or full amortization schedules.
- Data collection depends on the availability and stability of the listing platform endpoints.
- The scraping script is intended for reproducible research and should be used responsibly, with delays between requests.

The results should therefore be interpreted as structured evidence from the listing market, not as definitive estimates of the full housing market.

---

## Technologies Used

- Python
- pandas
- NumPy
- scikit-learn
- XGBoost
- GeoPandas
- Shapely
- Folium
- Matplotlib
- Seaborn
- requests
- tqdm
- Jupyter Notebook

---

## How to Run

Install dependencies:

    pip install -r requirements.txt

Collect raw listing data:

    python -m src.scraping.collect_listings --start-page 1 --end-page 50

Generate the processed dataset:

    python -m src.data.make_dataset

Then run the notebooks in order:

    notebooks/01_market_snapshot.ipynb
    notebooks/02_valuation_model.ipynb
    notebooks/03_relative_price_positioning.ipynb
    notebooks/04_affordability_scenarios.ipynb

---

## Project Status

The analytical workflow is complete.

A future application layer may be added to expose the valuation model through an interactive interface.
