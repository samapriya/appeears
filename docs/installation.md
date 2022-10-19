# General Installation

This assumes that you have native python & pip installed in your system, you can test this by going to the terminal (or windows command prompt) and trying

```python``` and then ```pip list```

**appeears only support Python v3.7 or higher**

To install **appeears: Simple CLI for NASA AppEEARS API** you can install using two methods.

```pip install appeears```

or you can also try

```
git clone https://github.com/samapriya/appeears.git
cd appeears
python setup.py install
```
For Linux use sudo or try ```pip install appeears --user```.

I recommend installation within a virtual environment. Find more information on [creating virtual environments here](https://docs.python.org/3/library/venv.html).

## Getting started

As usual, to print help:

```
appeears -h
usage: appeears [-h] {auth,products,layers,spatial,task-submit,task-info,delete,download} ...

Simple CLI for NASA AppEEARS API

positional arguments:
  {auth,products,layers,spatial,task-submit,task-info,delete,download}
    auth                Set username and password for authentication
    products            Print product list for all products or keyword match
    layers              Print layer list for product with Product ID
    spatial             List all supported spatial projections
    task-submit         Submit your task
    task-info           Get task information for all tasks or specific tasks or task status type
    delete              Delete a specific task with task ID
    download            Download all files for specific task with task ID

optional arguments:
  -h, --help            show this help message and exit

```

To obtain help for specific functionality, simply call it with _help_ switch, e.g.: `appears task-info -h`. If you didn't install appeears, then you can run it just by going to *appeears* directory and running `python appeears.py [arguments go here]`
