# spot_analysis

This repository contains a simple sqlite3 data base in Python, and required python apps to manage it, retrive data from it and analyze the data. 

Its purpose is to be a database and analysis toolset for the photos taken with the [camera_control](https://github.com/luanviko/camera_control) repository.

[Photos retrieved from SQL database and analyzed with Python](spot.png)

## Repository Structure

```utils``` contains the classes used by the apps on the main tree.

```text
.
├── utils
│   ├── __init__.py 
│   ├── db_tools.py
│   └── jasper.py
├── db_manager.py
├── offline_analisys.py
├── photos.sqlite
├── README.md
└── release_jasper.py
```

## Description

* ```.utils.db_tools.py```: Contains the ```Database``` class, to set up, update and query the SQL database. 

* ```.utils.jasper.py```: Contains the under-construction ```Jasper``` class, my watch dog, to automatically add photos taken with ```camera_control``` app to this database.

* ```.offline_analysis.py```: A bunch of customized visualization tools to analyze the photos in the database.

* ```.db_manager.py```: An example app, invoking the methods in ```Database``` to retrieve tables and add a photo.

* ```.release_jasper.py```: An example app on how to start Jasper and fetch photos; still under construction.


## Offline Analysis

Contains several functions to find the contours of the photos taken with the ```camera_control``` app. In this case, finds the contour of a light spot on a wall. It can be used to generate the frames in the video below.

## Generative AI Disclaimer

This work uses chatGPT and deepseek to organize and refactor code, add docstrings, and anotate types (all the boring stuff). The algorithms and plots (the cool stuff) are developed by humans.


## Acknowledgements 

The algorithms to find contours and prepare the blurred images are built upon Xiaoyue Li's algorithms.