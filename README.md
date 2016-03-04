# UnSoftMaxMe

Turns cumbersome Molecular Devices Spectramax Softmax data files into a usable tidy CSV.

## Requirements
Python 2.7+ with the following packages installed:

* `docopt`

To install, try `pip install docopt` or if that doesn't work, `easy_install pip && pip install docopt`

## Usage

```
Usage:  unsoftmaxme.py (--help | --version)
        unsoftmaxme.py [-m <metadataFileList>] -o <output> <files>...

Options:
--help, -h                                          Show this message and exit
--version                                           Show version number and exit
-m <metadataFileList>, --meta <metadataFileList>    CSV with one filename per row, indicating location of metadata to join to final table
-o <output>, --output <output>                      Filename to use for output
<files>...                                          Data files from SoftMax in CSV, TSV, or XML format
```

## To come

* Freeze into a standalone "binary"
