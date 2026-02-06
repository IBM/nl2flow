# Contributing to NL2Flow

Adding new features, improving documentation, fixing bugs, or writing tutorials are all examples of helpful contributions.
Furthermore, if you are building on the research work, we strongly encourage you to read our paper
on workflow construction using natural language [here](https://link.springer.com/chapter/10.1007/978-3-031-16168-1_8).

Bug fixes can be initiated through GitHub pull requests or PRs.
When making code contributions to NL2Flow, we ask that you follow the `PEP 8` coding standard
and that you provide unit tests for the new features.

This project uses [DCO](https://developercertificate.org/).
You must sign off your commits using the `-s` flag in the commit message.

### Example commit message

```commandline
git commit -s -m 'informative commit message'
```

## Installing locally 

#### Clone the repository

```commandline
user:~$ git clone git@github.com:IBM/nl2flow.git
user:~$ cd nl2flow
```

#### Change to a virtual environment

We also strongly recommend using a virtual environment, such
as [anaconda](https://www.anaconda.com/), for development.

```commandline
user:~$ conda create --name nl2flow
user:~$ conda activate nl2flow
```

#### Install Dependencies

```commandline
(nl2flow) user:~$ pip install -e .
```




## Setting up the dev environment

![BLACK](https://img.shields.io/badge/code%20style-black-black)
![PYLINT](https://img.shields.io/badge/linting-pylint-yellow)
![FLAKE8](https://img.shields.io/badge/linting-flake8-yellow)
![MYPY](https://img.shields.io/badge/typing-mypy-orange)

First, follow the general setup instructions [here](../README.md). Then install the dev-specific dependencies and pre-commit hooks.

```bash
(nl2flow) user:~$ pip install -e '.[dev]'
(nl2flow) user:~$ pre-commit install
```

Whether you are contributing a new interaction pattern or addressing an existing issue, you need to ensure that the unit tests pass.
The existing tests are housed [here](../tests).

Once all the tests have passed, and you are satisfied with your contribution, open a pull request into the `main` branch
from **your fork of the repository** to request adding your contributions to the main code base.
