from flask import Flask
debug = True
app = Flask(__name__)

@app.route("/site-map", methods=["GET"])
def site_map():
    """
    Get a list of all available API endpoints
    This endpoint returns a list of all registered routes in the application
    ---
    responses:
      200:
        description: List of all available endpoints
        schema:
          type: object
          properties:
            links:
              type: array
              items:
                type: array
                items:
                  type: string
                description: Tuple of (URL rule, endpoint name)
        example:
          links:
            - ["/auth/register", "auth.register_user"]
            - ["/auth/login", "auth.login"]
    """
    links = []
    for rule in app.url_map.iter_rules():
        links.append((rule.rule, rule.endpoint))
    return {"links": links}


if __name__ == '__main__':
    if os.environ.get('WERKZEUG_RUN_MAIN') == 'true':
        print(f"{Fore.LIGHTGREEN_EX}API running on http://localhost:5555{Fore.RESET}")
        print(f"{Fore.YELLOW}Documentation running on http://localhost:5555/apidocs{Fore.RESET}")
        print(f"{Fore.WHITE}Other Services running (see Docker) {Fore.RESET}")
    app.register_blueprint(auth_bp, url_prefix="/auth")
    app.register_blueprint(maplibre_bp, url_prefix="/maplibre")
    app.register_blueprint(h3_bp, url_prefix="/h3")
    app.run(host='0.0.0.0', port=5555, debug=debug)
