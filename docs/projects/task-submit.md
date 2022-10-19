# Task submit

The task submit tool allows you to pass a multipoint or a polygon geometry geojson to create a task order. The tool is capable of parsing geometries and for now only support GeoJSON files. It does have the capability to select the layers of choice, projection systems and additional parameters as needed. There are a list of required and optional parameters.

![appeears_task-submit](https://user-images.githubusercontent.com/6677629/196683996-599fbcc0-efd1-44f8-ad39-1fdac6fdb9c5.gif)

```
appeears task-submit -h
usage: appeears task-submit [-h] --name NAME --product PRODUCT --geometry GEOMETRY --start START --end END
                            [--index INDEX [INDEX ...]] [--projection PROJECTION] [--recurring RECURRING]

optional arguments:
  -h, --help            show this help message and exit

Required named arguments.:
  --name NAME           Task name
  --product PRODUCT     Product ID returned from product tool
  --geometry GEOMETRY   Full path to geometry.geojson file point or single polygon
  --start START         Start date in format YYYY-MM-DD
  --end END             End date in format YYYY-MM-DD

Optional named arguments:
  --index INDEX [INDEX ...]
                        space separated index of layers for task
  --projection PROJECTION
                        Spatial projection
  --recurring RECURRING
                        Date range recurring True|False
```
