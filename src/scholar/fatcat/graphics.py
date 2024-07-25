from typing import List, Dict

import pygal
from pygal.style import CleanStyle


def preservation_by_date_histogram(rows: List[Dict]) -> pygal.Graph:
    """
    Note: this returns a raw pygal chart; it does not render it to SVG/PNG

    Rows are dict with keys as preservation types and values as counts (int).
    There is also a 'date' key with str value.
    """

    dates = sorted(rows, key=lambda x: x["date"])

    CleanStyle.colors = ("red", "darkolivegreen", "limegreen")
    label_count = len(dates)
    if len(dates) > 30:
        label_count = 10
    chart = pygal.StackedBar(
        dynamic_print_values=True,
        style=CleanStyle,
        width=1000,
        height=500,
        x_labels_major_count=label_count,
        show_minor_x_labels=False,
        x_label_rotation=20,
    )
    # chart.title = "Preservation by Date"
    chart.x_title = "Date"
    # chart.y_title = "Count"
    chart.x_labels = [str(y["date"]) for y in dates]
    chart.add("None", [y["none"] + y["shadows_only"] for y in dates])
    chart.add("Dark", [y["dark"] for y in dates])
    chart.add("Bright", [y["bright"] for y in dates])
    return chart

def preservation_by_year_histogram(rows: List[Dict]) -> pygal.Graph:
    """
    Note: this returns a raw pygal chart; it does not render it to SVG/PNG

    Rows are dict with keys as preservation types and values as counts (int).
    There is also a 'year' key with float/int value.
    """
    years = sorted(rows, key=lambda x: x["year"])

    CleanStyle.colors = ("red", "darkolivegreen", "limegreen")
    label_count = len(years)
    if len(years) > 30:
        label_count = 10
    chart = pygal.StackedBar(
        dynamic_print_values=True,
        style=CleanStyle,
        width=1000,
        height=500,
        x_labels_major_count=label_count,
        show_minor_x_labels=False,
        x_label_rotation=20,
    )
    # chart.title = "Preservation by Year"
    chart.x_title = "Year"
    # chart.y_title = "Count"
    chart.x_labels = [str(y["year"]) for y in years]
    chart.add("None", [y["none"] + y["shadows_only"] for y in years])
    chart.add("Dark", [y["dark"] for y in years])
    chart.add("Bright", [y["bright"] for y in years])
    return chart

