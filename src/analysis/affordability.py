import pandas as pd
import numpy as np
import requests
import geopandas as gpd
import folium
import branca.colormap as cm

from shapely.geometry import Point
from fuzzywuzzy import process


DEFAULT_SALARY_ADJUSTMENTS = {
    "inflation_2022": 0.084,
    "inflation_2023": 0.035,
    "salary_alignment_adjustment": 0.35,
}


DEFAULT_MORTGAGE_ASSUMPTIONS = {
    "purchase_cost_rate": 0.105,
    "down_payment_rate": 0.20,
    "annual_interest_rate": 0.03,
    "affordability_threshold": 0.35,
    "fixed_mortgage_years": 30,
    "max_mortgage_years": 120,
}


def load_salary_data(salary_path, section_col: str = "Secciones", salary_col: str = "Total") -> pd.DataFrame:
    """
    Loads census-section salary data.

    The salary file uses Spanish formatting, so salary values are read as strings
    and converted into numeric values after removing thousands separators.
    """
    salaries = pd.read_csv(salary_path, sep=";", encoding="latin8", dtype={salary_col: str})

    salaries = salaries.copy()
    salaries[section_col] = salaries[section_col].str[:10]
    salaries = salaries[salaries[section_col].notna()].reset_index(drop=True)

    salaries[salary_col] = salaries[salary_col].str.replace(".", "", regex=False).astype(float)

    return salaries


def adjust_salary_values(salaries: pd.DataFrame, salary_col: str = "Total", adjustments: dict = DEFAULT_SALARY_ADJUSTMENTS) -> pd.DataFrame:
    """
    Applies salary adjustment assumptions.

    The adjustment is scenario-based. It updates older census-section salary data
    to approximate a more recent income level while preserving local granularity.
    """
    salaries = salaries.copy()

    for _, pct in adjustments.items():
        salaries[salary_col] = salaries[salary_col] * (1 + pct)

    return salaries


def fetch_census_section_geometries() -> gpd.GeoDataFrame:
    """
    Fetches Barcelona census-section geometries from Barcelona Open Data.
    """
    url = (
        "https://opendata-ajuntament.barcelona.cat/resources/bcn/"
        "EstadisticaUnitatsAdministratives/BarcelonaCiutat_SeccionsCensals.json"
    )

    response = requests.get(url)
    response.raise_for_status()

    data = pd.DataFrame(response.json())
    data["geometry"] = gpd.GeoSeries.from_wkt(data["geometria_wgs84"])
    geo_df = gpd.GeoDataFrame(data, geometry="geometry", crs="EPSG:4326")
    geo_df["census_section_code"] = "08019" + geo_df["codi_districte"] + geo_df["codi_seccio_censal"]

    return geo_df


def merge_salaries_with_census_geometries(
    census_geo_df: gpd.GeoDataFrame,
    salaries: pd.DataFrame,
    salary_section_col: str = "Secciones",
    salary_col: str = "Total",
) -> gpd.GeoDataFrame:
    """
    Merges census-section geometries with salary values.
    """
    geo_salaries = pd.merge(census_geo_df, salaries, left_on="census_section_code", right_on=salary_section_col, how="left")
    selected_cols = ["nom_districte", "nom_barri", "geometry", "census_section_code", salary_col]
    geo_salaries = geo_salaries[selected_cols].rename(columns={salary_col: "salary"})

    return gpd.GeoDataFrame(geo_salaries, geometry="geometry", crs="EPSG:4326")


def attach_salary_to_listings(
    listings_df: pd.DataFrame,
    geo_salaries: gpd.GeoDataFrame,
    latitude_col: str = "latitude",
    longitude_col: str = "longitude",
) -> gpd.GeoDataFrame:
    """
    Assigns each listing the salary of the census section where it is located.
    """
    df = listings_df.dropna(subset=[latitude_col, longitude_col]).copy()

    geometry = [Point(xy) for xy in zip(df[longitude_col], df[latitude_col])]
    listings_gdf = gpd.GeoDataFrame(df, geometry=geometry, crs="EPSG:4326")
    listings_with_salary = gpd.sjoin(listings_gdf, geo_salaries, how="left", predicate="within")

    return listings_with_salary


def calculate_financed_amount(
    property_price: float,
    purchase_cost_rate: float = DEFAULT_MORTGAGE_ASSUMPTIONS["purchase_cost_rate"],
    down_payment_rate: float = DEFAULT_MORTGAGE_ASSUMPTIONS["down_payment_rate"],
) -> float:
    """
    Calculates the amount financed after adding purchase costs and subtracting
    the assumed down payment.
    """
    return property_price + property_price * purchase_cost_rate - property_price * down_payment_rate


def calculate_total_payment_linear(
    property_price: float,
    n_years: int,
    annual_interest_rate: float = DEFAULT_MORTGAGE_ASSUMPTIONS["annual_interest_rate"],
    purchase_cost_rate: float = DEFAULT_MORTGAGE_ASSUMPTIONS["purchase_cost_rate"],
    down_payment_rate: float = DEFAULT_MORTGAGE_ASSUMPTIONS["down_payment_rate"],
) -> float:
    """
    Calculates total repayment using a simplified linear principal repayment model.

    This approach assumes that principal is repaid evenly across years and that
    interest is paid on the remaining balance each year.
    """
    financed_amount = calculate_financed_amount(property_price=property_price, purchase_cost_rate=purchase_cost_rate, down_payment_rate=down_payment_rate)
    annual_principal_payment = financed_amount / n_years
    total_interest = (n_years / 2) * (financed_amount * annual_interest_rate + annual_principal_payment * annual_interest_rate)

    return financed_amount + total_interest


def calculate_annual_payment_linear(
    property_price: float,
    n_years: int,
    annual_interest_rate: float = DEFAULT_MORTGAGE_ASSUMPTIONS["annual_interest_rate"],
    purchase_cost_rate: float = DEFAULT_MORTGAGE_ASSUMPTIONS["purchase_cost_rate"],
    down_payment_rate: float = DEFAULT_MORTGAGE_ASSUMPTIONS["down_payment_rate"],
) -> float:
    """
    Calculates annual payment under the simplified linear repayment model.
    """
    total_payment = calculate_total_payment_linear(
        property_price=property_price,
        n_years=n_years,
        annual_interest_rate=annual_interest_rate,
        purchase_cost_rate=purchase_cost_rate,
        down_payment_rate=down_payment_rate,
    )

    return total_payment / n_years


def find_minimum_affordable_years(
    property_price: float,
    annual_salary: float,
    annual_interest_rate: float = DEFAULT_MORTGAGE_ASSUMPTIONS["annual_interest_rate"],
    affordability_threshold: float = DEFAULT_MORTGAGE_ASSUMPTIONS["affordability_threshold"],
    max_years: int = DEFAULT_MORTGAGE_ASSUMPTIONS["max_mortgage_years"],
    purchase_cost_rate: float = DEFAULT_MORTGAGE_ASSUMPTIONS["purchase_cost_rate"],
    down_payment_rate: float = DEFAULT_MORTGAGE_ASSUMPTIONS["down_payment_rate"],
):
    """
    Finds the minimum number of years needed for the annual mortgage payment
    to be below the affordability threshold.

    Returns missing values if no affordable duration is found within max_years.
    """
    if pd.isna(property_price) or pd.isna(annual_salary) or annual_salary <= 0:
        return pd.Series({"years_mortgage": np.nan, "total_mortgage_amount": np.nan, "annual_payment": np.nan})

    max_affordable_payment = annual_salary * affordability_threshold

    for n_years in range(2, max_years + 1):
        annual_payment = calculate_annual_payment_linear(
            property_price=property_price,
            n_years=n_years,
            annual_interest_rate=annual_interest_rate,
            purchase_cost_rate=purchase_cost_rate,
            down_payment_rate=down_payment_rate,
        )

        if annual_payment <= max_affordable_payment:
            total_payment = calculate_total_payment_linear(
                property_price=property_price,
                n_years=n_years,
                annual_interest_rate=annual_interest_rate,
                purchase_cost_rate=purchase_cost_rate,
                down_payment_rate=down_payment_rate,
            )

            return pd.Series({"years_mortgage": n_years, "total_mortgage_amount": total_payment, "annual_payment": annual_payment})

    return pd.Series({"years_mortgage": np.nan, "total_mortgage_amount": np.nan, "annual_payment": np.nan})


def add_mortgage_duration_metrics(
    df: pd.DataFrame,
    price_col: str = "value",
    salary_col: str = "salary",
    annual_interest_rate: float = DEFAULT_MORTGAGE_ASSUMPTIONS["annual_interest_rate"],
    affordability_threshold: float = DEFAULT_MORTGAGE_ASSUMPTIONS["affordability_threshold"],
    max_years: int = DEFAULT_MORTGAGE_ASSUMPTIONS["max_mortgage_years"],
) -> pd.DataFrame:
    """
    Adds minimum affordable mortgage duration metrics for single-person and
    couple scenarios.
    """
    df = df.copy()

    single_results = df.apply(
        lambda row: find_minimum_affordable_years(
            property_price=row[price_col],
            annual_salary=row[salary_col],
            annual_interest_rate=annual_interest_rate,
            affordability_threshold=affordability_threshold,
            max_years=max_years,
        ),
        axis=1,
    )

    couple_results = df.apply(
        lambda row: find_minimum_affordable_years(
            property_price=row[price_col],
            annual_salary=row[salary_col] * 2,
            annual_interest_rate=annual_interest_rate,
            affordability_threshold=affordability_threshold,
            max_years=max_years,
        ),
        axis=1,
    )

    df["years_mortgage"] = single_results["years_mortgage"]
    df["total_mortgage_amount"] = single_results["total_mortgage_amount"]
    df["annual_payment"] = single_results["annual_payment"]

    df["years_mortgage_couple"] = couple_results["years_mortgage"]
    df["total_mortgage_amount_couple"] = couple_results["total_mortgage_amount"]
    df["annual_payment_couple"] = couple_results["annual_payment"]

    return df


def add_fixed_term_burden_metrics(
    df: pd.DataFrame,
    n_years: int = DEFAULT_MORTGAGE_ASSUMPTIONS["fixed_mortgage_years"],
    price_col: str = "value",
    salary_col: str = "salary",
    annual_interest_rate: float = DEFAULT_MORTGAGE_ASSUMPTIONS["annual_interest_rate"],
) -> pd.DataFrame:
    """
    Adds fixed-term mortgage payment burden metrics.

    The burden is calculated as annual mortgage payment divided by annual salary.
    """
    df = df.copy()

    df[f"annual_payment_{n_years}y"] = df[price_col].apply(lambda price: calculate_annual_payment_linear(property_price=price,n_years=n_years,annual_interest_rate=annual_interest_rate))
    df[f"salary_burden_{n_years}y"] = df[f"annual_payment_{n_years}y"] / df[salary_col]
    df[f"salary_burden_{n_years}y_couple"] = df[f"annual_payment_{n_years}y"] / (df[salary_col] * 2)

    return df


def summarize_affordability_by_area(
    df: pd.DataFrame,
    area_col: str,
    fixed_years: int = DEFAULT_MORTGAGE_ASSUMPTIONS["fixed_mortgage_years"],
) -> pd.DataFrame:
    """
    Aggregates affordability metrics by district or neighborhood.

    The function includes fixed-term salary burden metrics only if they have
    already been calculated.
    """
    aggregation_dict = {
        "listing_count": ("value", "count"),
        "mean_price": ("value", "mean"),
        "median_price": ("value", "median"),
        "mean_salary": ("salary", "mean"),
        "median_salary": ("salary", "median"),
        "mean_years_mortgage": ("years_mortgage", "mean"),
        "median_years_mortgage": ("years_mortgage", "median"),
        "mean_years_mortgage_couple": ("years_mortgage_couple", "mean"),
        "median_years_mortgage_couple": ("years_mortgage_couple", "median"),
    }

    salary_burden_col = f"salary_burden_{fixed_years}y"
    salary_burden_couple_col = f"salary_burden_{fixed_years}y_couple"

    if salary_burden_col in df.columns:
        aggregation_dict["mean_salary_burden"] = (salary_burden_col, "mean")
        aggregation_dict["median_salary_burden"] = (salary_burden_col, "median")

    if salary_burden_couple_col in df.columns:
        aggregation_dict["mean_salary_burden_couple"] = (
            salary_burden_couple_col,
            "mean",
        )
        aggregation_dict["median_salary_burden_couple"] = (
            salary_burden_couple_col,
            "median",
        )

    summary = (
        df.groupby(area_col)
        .agg(**aggregation_dict)
        .reset_index()
    )

    return summary


def fetch_neighborhood_geometries() -> gpd.GeoDataFrame:
    """
    Fetches Barcelona neighborhood geometries from Barcelona Open Data.
    """
    url = (
        "https://opendata-ajuntament.barcelona.cat/data/api/action/"
        "datastore_search?resource_id=b21fa550-56ea-4f4c-9adc-b8009381896e"
    )

    response = requests.get(url)
    response.raise_for_status()

    records = response.json()["result"]["records"]
    neighborhoods = pd.DataFrame(records)
    neighborhoods["geometry"] = gpd.GeoSeries.from_wkt(neighborhoods["geometria_wgs84"])

    return gpd.GeoDataFrame(neighborhoods, geometry="geometry", crs="EPSG:4326")


def merge_geometries_with_summary(geo_df: gpd.GeoDataFrame, geo_name_col: str, summary_df: pd.DataFrame, summary_name_col: str) -> gpd.GeoDataFrame:
    """
    Merges geographic boundaries with summary data using fuzzy name matching.
    """
    matches = {}

    for value in geo_df[geo_name_col].unique():
        matches[value] = process.extractOne(value, summary_df[summary_name_col].dropna().unique())[0]

    matches_df = pd.DataFrame(matches.items(), columns=[geo_name_col, summary_name_col])
    geo_with_names = pd.merge(geo_df, matches_df, on=geo_name_col, how="left")
    merged = pd.merge(geo_with_names, summary_df, on=summary_name_col, how="inner")

    return gpd.GeoDataFrame(merged, geometry="geometry", crs="EPSG:4326")


def create_affordability_choropleth(geo_df: gpd.GeoDataFrame, value_col: str, popup_cols: list[str], caption: str, center: list[float] = [41.3851, 2.1734]):
    """
    Creates a Folium choropleth map for affordability indicators.
    """
    map_df = geo_df.dropna(subset=[value_col]).copy()

    min_value = map_df[value_col].min()
    max_value = map_df[value_col].max()

    m = folium.Map(location=center, zoom_start=12, tiles="cartodbpositron")

    colormap = cm.LinearColormap(["green", "yellow", "red"], vmin=min_value, vmax=max_value)

    for _, row in map_df.iterrows():
        color = colormap(row[value_col])

        popup_text = " | ".join([f"{col}: {row[col]}" for col in popup_cols])

        polygon = folium.GeoJson(
            row["geometry"],
            style_function=lambda x, color=color: {
                "fillColor": color,
                "color": color,
                "weight": 1,
                "fillOpacity": 0.7,
            },
        )

        polygon.add_child(folium.Popup(popup_text))
        m.add_child(polygon)

    colormap.caption = caption
    m.add_child(colormap)

    return m
