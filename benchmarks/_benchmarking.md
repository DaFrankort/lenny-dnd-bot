# Benchmarking
This folder contains benchmarks which tests the performance of certain complex logic. It uses [pytest-benchmark](https://pypi.org/project/pytest-benchmark/) for benchmarking.

To run a benchmark, use pytest:
``python -m pytest benchmarks/desired_benchmark.py``

pytest-benchmark offers handy tools for comparison and can even visualize the tests in a graph. More detailed information can be found [here](https://pytest-benchmark.readthedocs.io/en/stable/comparing.html).

To compare benchmark runs:
- Run a benchmark with the ``--benchmark-autosave`` or ``--benchmark-save=some-name`` flag.
- Make your changes to the software.
- Run your benchmark again with the ``--benchmark-compare`` flag.

More commandline options can be found [here](https://pytest-benchmark.readthedocs.io/en/stable/usage.html#commandline-options).