import argparse
from typing import Any

import uvicorn
from fastapi import FastAPI, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from logic.roll import Advantage, roll

app = FastAPI(title="Lenny", docs_url="/")


def jsonify(obj: object) -> Any:
    return jsonable_encoder(obj.__dict__)


@app.exception_handler(Exception)
async def handle_exception(_request: Request, exception: Exception):
    message = str(exception)
    return JSONResponse(status_code=400, content={"error": message})


@app.exception_handler(RequestValidationError)
async def handle_validation_exception(_request: Request, exception: RequestValidationError):
    # Combine all errors into a single string
    message = "; ".join([f"{error['loc'][-1]}: {error['msg']}" for error in exception.errors()])
    return JSONResponse(status_code=400, content={"error": message})


@app.get("/roll")
async def get_roll(expression: str, advantage: Advantage = Advantage.NORMAL):
    result = roll(expression, advantage)
    return JSONResponse(status_code=200, content=jsonify(result))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=5000, help="The port to run the server on. Default 5000.")

    args = parser.parse_args()
    port = args.port

    uvicorn.run(app, host="0.0.0.0", port=port)
