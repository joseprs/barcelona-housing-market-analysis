import pandas as pd
import numpy as np
import folium
import branca.colormap as cm
import matplotlib.pyplot as plt
import seaborn as sns

def compute_area_price_summary(df: pd.DataFrame, group_cols: list[str], price_col: str = "value", surface_col: str = "surface") -> pd.DataFrame:
    """
    Computes price, surface, and price-per-square-meter summaries by area.

    Price per sqm is calculated as total price divided by total surface.
    This avoids giving excessive weight to very small properties.
    """
    summary = (
        df.groupby(group_cols)
        .agg(
            value_mean=(price_col, "mean"),
            value_median=(price_col, "median"),
            value_sum=(price_col, "sum"),
            listing_count=(price_col, "count"),
            sqm_mean=(surface_col, "mean"),
            sqm_median=(surface_col, "median"),
            sqm_sum=(surface_col, "sum"),
        )
        .reset_index()
    )

    summary["value_per_sqm"] = summary["value_sum"] / summary["sqm_sum"]

    return summary


def add_relative_price_pressure(area_summary: pd.DataFrame, df: pd.DataFrame, price_col: str = "value", surface_col: str = "surface") -> pd.DataFrame:
    """
    Adds a relative price pressure index.

    The index compares each area's average price ratio against its average
    surface ratio, using the full dataset averages as reference points.

    Values above 1 indicate that average prices are proportionally higher
    than average surface. Values below 1 indicate that average surface is
    proportionally higher than average prices.
    """
    area_summary = area_summary.copy()

    general_price_mean = df[price_col].mean()
    general_surface_mean = df[surface_col].mean()

    area_summary["price_ratio_vs_market"] = area_summary["value_mean"] / general_price_mean
    area_summary["surface_ratio_vs_market"] = area_summary["sqm_mean"] / general_surface_mean
    area_summary["relative_price_pressure_index"] = area_summary["price_ratio_vs_market"] / area_summary["surface_ratio_vs_market"]

    return area_summary


def prepare_district_summary(df: pd.DataFrame) -> pd.DataFrame:
    district_summary = compute_area_price_summary(df=df, group_cols=["level7"])
    district_summary = add_relative_price_pressure(area_summary=district_summary, df=df)

    return district_summary.sort_values("value_per_sqm", ascending=False)


def prepare_neighborhood_summary(df: pd.DataFrame) -> pd.DataFrame:
    neighborhood_summary = compute_area_price_summary(df=df, group_cols=["level8", "level7"])
    neighborhood_summary = add_relative_price_pressure(area_summary=neighborhood_summary, df=df)

    return neighborhood_summary.sort_values("value_per_sqm", ascending=False)


def plot_price_vs_price_per_sqm(df: pd.DataFrame, neighborhood_summary: pd.DataFrame):
    fig, axes = plt.subplots(nrows=1, ncols=2, figsize=(20, 7), gridspec_kw={"width_ratios": [2, 1]})
    sns.scatterplot(data=df, x="value", y="price_per_sqm", hue="level7", alpha=0.6, ax=axes[0])
    sns.regplot(data=df, x="value", y="price_per_sqm", scatter=False, color="black", order=2, ax=axes[0])
    axes[0].set_title("Listing-Level Price vs Price per sqm")
    axes[0].set_xlabel("Asking price")
    axes[0].set_ylabel("Price per sqm")

    sns.scatterplot(data=neighborhood_summary, x="value_mean", y="value_per_sqm", hue="level7", alpha=0.8, ax=axes[1])
    sns.regplot(data=neighborhood_summary, x="value_mean", y="value_per_sqm", scatter=False, color="black", order=2, ax=axes[1])
    axes[1].set_title("Neighborhood-Level Price vs Price per sqm")
    axes[1].set_xlabel("Mean asking price")
    axes[1].set_ylabel("Price per sqm")

    plt.tight_layout()
    plt.show()


def plot_price_pressure_components(neighborhood_summary: pd.DataFrame):
    plot_df = neighborhood_summary.sort_values("relative_price_pressure_index", ascending=False)

    fig, ax = plt.subplots(figsize=(16, 6))
    sns.lineplot(data=plot_df, x="level8", y="price_ratio_vs_market", marker="o", label="Price ratio vs market", ax=ax)
    sns.lineplot(data=plot_df, x="level8", y="surface_ratio_vs_market", marker="o", label="Surface ratio vs market", ax=ax)

    ax.set_title("Price and Surface Ratios by Neighborhood")
    ax.set_xlabel("Neighborhood")
    ax.set_ylabel("Ratio vs market average")
    ax.tick_params(axis="x", rotation=90)
    ax.legend()

    plt.tight_layout()
    plt.show()


def plot_neighborhood_price_pressure(neighborhood_summary: pd.DataFrame):
    plot_df = neighborhood_summary.sort_values("relative_price_pressure_index", ascending=False)

    fig, ax = plt.subplots(figsize=(16, 6))
    sns.barplot(data=plot_df, x="level8", y="relative_price_pressure_index", ax=ax)

    ax.axhline(1, linestyle="--", color="black")
    ax.set_title("Relative Price Pressure Index by Neighborhood")
    ax.set_xlabel("Neighborhood")
    ax.set_ylabel("Relative price pressure index")
    ax.tick_params(axis="x", rotation=90)

    plt.tight_layout()
    plt.show()


def create_listing_price_map(df: pd.DataFrame, price_col: str = "value", latitude_col: str = "latitude", longitude_col: str = "longitude"):
    map_df = df.dropna(subset=[latitude_col, longitude_col, price_col]).copy()

    min_value = map_df[price_col].min()
    max_value = map_df[price_col].max()

    m = folium.Map(location=[41.3851, 2.1734], zoom_start=13, tiles="cartodbpositron")
    colormap = cm.LinearColormap(["green", "yellow", "red"], vmin=min_value, vmax=max_value)

    for _, row in map_df.iterrows():
        fill_color = colormap(row[price_col])

        folium.CircleMarker(
            location=[row[latitude_col], row[longitude_col]],
            radius=3,
            popup=f"{row[price_col]:,.0f} €",
            fill=True,
            fill_color=fill_color,
            color=None,
            fill_opacity=0.7,
        ).add_to(m)

    colormap.caption = "Listing asking price"
    m.add_child(colormap)

    return m


def create_choropleth_map(geo_df: pd.DataFrame, value_col: str, popup_cols: list[str], caption: str):
    min_value = geo_df[value_col].min()
    max_value = geo_df[value_col].max()

    m = folium.Map(location=[41.3851, 2.1734], zoom_start=12, tiles="cartodbpositron")
    colormap = cm.LinearColormap(["green", "yellow", "red"], vmin=min_value, vmax=max_value)

    for _, row in geo_df.iterrows():
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
