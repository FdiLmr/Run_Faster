"""
Chart generation utilities for visualization components.

Handles matplotlib chart creation and styling.
"""

import io
import matplotlib

matplotlib.use("Agg")  # Set non-interactive backend before importing pyplot
import matplotlib.pyplot as plt
import logging
from .config import FEATURE_LABELS, COLORS, CHART_CONFIG

logger = logging.getLogger(__name__)

# Set matplotlib and PIL loggers to WARNING level only
logging.getLogger("matplotlib").setLevel(logging.WARNING)
logging.getLogger("PIL").setLevel(logging.WARNING)


class PerformanceChartGenerator:
    """Generates performance comparison charts."""

    def __init__(self):
        self.colors = COLORS
        self.chart_config = CHART_CONFIG

    def create_performance_chart(
        self, visualization_data, title, xlabel, start_date, end_date
    ):
        """
        Create a horizontal bar chart comparing athlete performance to benchmarks.

        Args:
            visualization_data: DataFrame with processed visualization data
            title: Chart title template
            xlabel: X-axis label
            start_date: Start date for the analysis period
            end_date: End date for the analysis period

        Returns:
            io.BytesIO: Chart image as bytes
        """
        try:
            # Set up the plot
            plt.style.use("default")

            full_title = (
                f"{title}\nFor 3 months before your last PB, between "
                f"{start_date.date()} and {end_date.date()}"
            )

            plt.title(full_title)

            fig = plt.figure(figsize=self.chart_config["figure_size"])

            # Create labels with feature names and athlete scores
            labels = []
            for index, feature in visualization_data.iterrows():
                feature_label = FEATURE_LABELS[feature["feature_name"]]
                athlete_score = str(feature["athlete_score"])
                labels.append(f"{feature_label}\n{athlete_score}")

            ax = fig.add_subplot(111)

            # Create horizontal bars for percentile ranges
            bar_height = self.chart_config["bar_height"]

            # 100th percentile (full range) - light green
            ax.barh(
                labels,
                visualization_data["one-hundredth"],
                tick_label=labels,
                height=bar_height,
                color=self.colors["best_performers"],
            )

            # 90th percentile - gray
            ax.barh(
                labels,
                visualization_data["ninetieth"],
                tick_label=labels,
                height=bar_height,
                color=self.colors["middle_range"],
            )

            # 10th percentile - light red
            ax.barh(
                labels,
                visualization_data["tenth"],
                tick_label=labels,
                height=bar_height,
                color=self.colors["worst_performers"],
            )

            # Plot athlete's position as markers
            ax.plot(
                visualization_data["athlete_percentile"],
                labels,
                marker=self.chart_config["marker_style"],
                markersize=self.chart_config["marker_size"],
                linestyle="",
                label=visualization_data["athlete_score"],
            )

            # Add value labels at 10th and 90th percentiles
            for index, feature in visualization_data.iterrows():
                ax.text(
                    x=float(11),
                    y=index,
                    s=feature["value_at_tenth"],
                    horizontalalignment="left",
                )
                ax.text(
                    x=float(89),
                    y=index,
                    s=feature["value_at_ninetieth"],
                    horizontalalignment="right",
                )

            plt.xlabel(xlabel)
            plt.tight_layout()

            # Save to bytes
            bytes_image = io.BytesIO()
            plt.savefig(bytes_image, format="png")
            bytes_image.seek(0)

            # Clean up
            plt.clf()
            plt.cla()
            plt.close()

            return bytes_image

        except Exception as e:
            logger.error(f"Error creating performance chart: {e}")
            # Clean up on error
            plt.clf()
            plt.cla()
            plt.close()
            return None

    def create_athlete_vs_best_chart(self, visualization_data, start_date, end_date):
        """Create chart comparing athlete to best performers."""
        title = (
            "Your performance relative to the best athletes\n"
            "Ordered by how much each aspect would help your fitness"
        )
        xlabel = "Percentile. 0% = the worst performing athlete. 100% = the best performing athlete."

        return self.create_performance_chart(
            visualization_data, title, xlabel, start_date, end_date
        )

    def create_improvement_potential_chart(
        self, visualization_data, start_date, end_date
    ):
        """Create chart showing improvement potential."""
        title = (
            "Your ability, relative to others, to IMPROVE your fitness\n"
            "Ordered by how much each item will help you improve"
        )
        xlabel = "Percentile. 0% = the least improvement. 100% = the best improvement."

        return self.create_performance_chart(
            visualization_data, title, xlabel, start_date, end_date
        )
