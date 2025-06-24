"""
Configuration for visualization components.

Contains feature labels, color schemes, and other visualization settings.
"""

# Feature labels for visualization display
FEATURE_LABELS = {
    "f_slope_run_distance_before_taper": "Week on week distance increase\n(metres)",
    "f_taper_factor_run_distance": "Distance tapering\n(ratio decreased for last two weeks)",
    "f_slope_run_time_before_taper": "Week on week running time increase\n(seconds)",
    "f_taper_factor_run_time": "Decrease in time when tapering\n(ratio)",
    "f_slope_mean_hr_before_taper": "Week on week intensity increase\n(average HR)",
    "f_taper_factor_mean_hr": "Heart rate (intensity) tapering\n(ratio)",
    "f_avg_weekly_run_distance": "Weekly run distance\n(metres)",
    "r_avg_weekly_run_distance": "RELATIVE: Average weekly run distance\n(ratio: this period vs all your data)",
    "f_avg_weekly_non_run_distance": "Weekly non-run distance\n(metres)",
    "r_avg_weekly_non_run_distance": "RELATIVE: Weekly non-run distance\n(ratio: this period vs all your data)",
    "f_avg_weekly_run_time": "Weekly run time\n(seconds)",
    "r_avg_weekly_run_time": "RELATIVE: Weekly run time\n(ratio: this period vs all your data)",
    "f_avg_weekly_non_run_time": "Weekly time spent on other activities\n(seconds)",
    "r_avg_weekly_non_run_time": "RELATIVE: Weekly time spent on other activities\n(ratio: this period vs all your data)",
    "f_avg_weekly_run_elevation": "Weekly run elevation\n(metres)",
    "r_avg_weekly_run_elevation": "RELATIVE: Weekly run elevation\n(ratio: this period vs all your data)",
    "f_avg_weekly_athlete_count": "How many athletes you trained with on average\n(people)",
    "r_avg_weekly_athlete_count": "RELATIVE: Athletes trained with\n(ratio: this period vs all your data)",
    "f_avg_f_time_in_z1_runs": "Weekly time in Z1 for runs\n(out of 1)",
    "f_avg_f_time_in_z2_runs": "Weekly time in Z2 for runs\n(out of 1)",
    "f_avg_f_time_in_z3_runs": "Weekly time in Z3 for runs\n(out of 1)",
    "f_avg_f_time_in_z4_runs": "Weekly time in Z4 for runs\n(out of 1)",
    "f_avg_f_time_in_z5_runs": "Weekly time in Z5 for runs\n(out of 1)",
    "r_avg_f_time_in_z1_runs": "RELATIVE: Weekly time in Z1 for runs\n(ratio: this period vs all your data)",
    "r_avg_f_time_in_z2_runs": "RELATIVE: Weekly time in Z2 for runs\n(ratio: this period vs all your data)",
    "r_avg_f_time_in_z3_runs": "RELATIVE: Weekly time in Z3 for runs\n(ratio: this period vs all your data)",
    "r_avg_f_time_in_z4_runs": "RELATIVE: Weekly time in Z4 for runs\n(ratio: this period vs all your data)",
    "f_proportion_distance_activities": "Proportion of long runs\n(ratio)",
    "f_proportion_intense_activities": "Proportion of intense runs\n(ratio)",
    "f_proportion_varying_activities": "Proportion of interval runs\n(ratio)",
    "r_proportion_distance_activities": "RELATIVE: Proportion of long runs\n(ratio: this period vs all your data)",
    "r_proportion_intense_activities": "RELATIVE: Proportion of intense runs\n(ratio: this period vs all your data)",
    "r_proportion_varying_activities": "RELATIVE: Proportion of interval runs\n(ratio: this period vs all your data)",
    "f_proportion_rides": "Proportion of rides\n(ratio)",
    "f_proportion_swims": "Proportion of swims\n(ratio)",
    "f_proportion_walks_hikes": "Proportion of walks or hikes\n(ratio)",
    "f_proportion_alpine_ski": "Proportion of alpine skiing\n(ratio)",
    "f_proportion_workout": "Proportion of workouts\n(ratio)",
    "f_proportion_yoga": "Proportion of yoga sessions\n(ratio)",
    "f_proportion_crossfit": "Proportion of crossfit sessions\n(ratio)",
}

# Default features to use when no model outputs are available
DEFAULT_FEATURES = [
    "f_avg_weekly_run_distance",
    "f_avg_weekly_run_time",
    "f_avg_weekly_run_elevation",
    "f_avg_weekly_athlete_count",
    "f_avg_f_time_in_z1_runs",
    "f_avg_f_time_in_z2_runs",
    "f_avg_f_time_in_z3_runs",
    "f_avg_f_time_in_z4_runs",
    "f_avg_f_time_in_z5_runs",
    "f_proportion_distance_activities",
    "f_proportion_intense_activities",
    "f_proportion_varying_activities",
]

# Features to skip during processing
PROBLEMATIC_FEATURES = ["f_proportion_other", "r_proportion_other"]

# Visualization color scheme
COLORS = {
    "best_performers": "#afffd3",  # Light green
    "middle_range": "#bbbbc1",  # Light gray
    "worst_performers": "#ffa4a4",  # Light red
}

# Chart settings
CHART_CONFIG = {
    "figure_size": (12, 12.5),
    "bar_height": 0.8,
    "marker_size": 15,
    "marker_style": 10,
}
