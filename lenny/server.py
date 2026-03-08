import argparse

from flask import Flask, jsonify, request
from flask_restx import Api, Resource
from gevent.pywsgi import WSGIServer

from logic.roll import Advantage, roll

app = Flask(__name__)
api = Api(app)


@api.errorhandler(Exception)  # type: ignore
def handle_exception(exception: Exception):
    message = str(exception)
    return {"message": message}, 400


@api.route("/roll")
class RollEndpoint(Resource):
    @api.param(
        "expression",
        "The expression of the dice roll.",
        type=str,
        required=True,
    )
    @api.param(
        "advantage",
        f"The advantage to use on the roll. Allowed values are {', '.join(Advantage.values())}. (default: {Advantage.NORMAL.value})",
        type=str,
        required=False,
        choices=Advantage.values(),
    )
    def get(self):
        expression = request.args.get("expression")
        if expression is None:
            raise ValueError("Missing dice expression in query variables.")

        advantage = request.args.get("advantage") or Advantage.NORMAL.value
        advantage = Advantage(advantage)

        result = roll(expression, advantage)
        return jsonify(result.__dict__)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=5000, help="The port to run the server on. Default 5000.")

    args = parser.parse_args()
    port = args.port

    print(f"Launching Lenny server on localhost:{port}")
    server = WSGIServer(("0.0.0.0", port), app)
    server.serve_forever()
