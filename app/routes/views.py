from flask import Blueprint, render_template

# No url_prefix: this blueprint serves the site root
bp = Blueprint("views", __name__)


@bp.route("/")
def index():
    """Serve the dashboard page.

    Passes no data to the template - the JavaScript fetches everything
    from the API endpoints. This keeps the separation clean: Flask
    serves HTML, the API serves data.
    """
    return render_template("index.html")