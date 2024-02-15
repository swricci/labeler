# TIF Processor lets_go

Simple labeler and new detection adder to tiff files.

## Table of Contents

- [Installation](#installation)
- [Usage](#usage)
- [Contributing](#contributing)
- [License](#license)

## Installation

1. Clone the repository:

   ```shell
   git clone https://github.com/swricci/labeler.git
   ```

### Conda Environment

This project requires a conda environment to run. To set up the environment, follow these steps:

1. Install [Anaconda](https://www.anaconda.com/products/individual) or [Miniconda](https://docs.conda.io/en/latest/miniconda.html) if you haven't already.

2. Create a new conda environment using the provided `environment.yml` file:

```bash
    conda env create -n labeler_env python=3.12
```

3. Activate the environment:

```bash
    conda activate labeler_env
```

4. Install dependencies:

```bash
    pip install -r requirements.txt
```

## Usage

Execute the script:

```bash
python lets_go.py
```

GUI key options:

- `a`: new detection addition mode
- `l`: labeling mode
- - `m`: misclassified
- - `b`: bad classification
- `r`: refresh
- `e`: exit

## Contributing

The tool is too specific. You can't contribute.

## License

This project is released under the Unlicense.
