def register_filters(app):
    """Register custom template filters."""

    @app.template_filter("getattr")
    def getattr_filter(obj, name):
        """Allow attribute access in templates."""
        return getattr(obj, name)

    @app.template_filter("format_time")
    def format_time_filter(seconds):
        """Format time in seconds to readable format."""
        try:
            seconds = float(seconds)
        except (ValueError, TypeError):
            return str(seconds)

        # Delegate to the format_time function from race_prediction.py for consistency
        try:
            from race_prediction import format_time

            return format_time(seconds)
        except ImportError:
            # Fallback if import fails
            hours = int(seconds // 3600)
            minutes = int((seconds % 3600) // 60)
            seconds = int(seconds % 60)
            if hours > 0:
                return f"{hours}:{minutes:02d}:{seconds:02d}"
            else:
                return f"{minutes}:{seconds:02d}"
