# <<boilergen:imports
from flask import Flask
# boilergen:imports>>

# <<boilergen:init
debug = bool("boilergen:config | debug | True")
app = Flask(__name__)
# boilergen:init>>

# <<boilergen:main
app.run(host='boilergen:config | host | "0.0.0.0"', port=int("boilergen:config | port"), debug=debug)
# boilergen:main>>