import argparse
import datetime
import getpass
import json
import os
import sys
import time
from itertools import groupby
from operator import itemgetter
from os.path import expanduser

import pkg_resources
import pygeoj
import requests
from bs4 import BeautifulSoup
from natsort import natsorted
from tqdm import tqdm


class Solution:
    def compareVersion(self, version1, version2):
        versions1 = [int(v) for v in version1.split(".")]
        versions2 = [int(v) for v in version2.split(".")]
        for i in range(max(len(versions1), len(versions2))):
            v1 = versions1[i] if i < len(versions1) else 0
            v2 = versions2[i] if i < len(versions2) else 0
            if v1 > v2:
                return 1
            elif v1 < v2:
                return -1
        return 0


ob1 = Solution()

# Get package version


def appeears_version():
    url = "https://pypi.org/project/appeears/"
    source = requests.get(url)
    html_content = source.text
    soup = BeautifulSoup(html_content, "html.parser")
    company = soup.find("h1")
    vcheck = ob1.compareVersion(
        company.string.strip().split(" ")[-1],
        pkg_resources.get_distribution("appeears").version,
    )
    if vcheck == 1:
        print(
            "\n"
            + "========================================================================="
        )
        print(
            "Current version of appeears is {} upgrade to lastest version: {}".format(
                pkg_resources.get_distribution("appeears").version,
                company.string.strip().split(" ")[-1],
            )
        )
        print(
            "========================================================================="
        )
    elif vcheck == -1:
        print(
            "\n"
            + "========================================================================="
        )
        print(
            "Possibly running staging code {} compared to pypi release {}".format(
                pkg_resources.get_distribution("appeears").version,
                company.string.strip().split(" ")[-1],
            )
        )
        print(
            "========================================================================="
        )


appeears_version()

error_codes = {
    400: "Bad Request - The request could not be understood by the server due to malformed syntax.",
    401: "Unauthorized - Your API key is wrong.",
    403: "Forbidden - The api endpoint requested is only for elevated users.",
    404: "Not Found - The specified endpoint / resource could not be found.",
    405: "Method Not Allowed - You tried to access a endpoint / resource with an invalid method.",
    429: "Too Many Requests - The amount of requests being sent cannot be handled. Please slow the rate of your requests.",
    500: "Internal Server Error - We had a problem with our server. Please try again later.",
    503: "Service Unavailable - We're temporarily offline for maintenance. Please try again later.",
}

suffixes = ["B", "KB", "MB", "GB", "TB", "PB"]


def humansize(nbytes):
    i = 0
    while nbytes >= 1024 and i < len(suffixes) - 1:
        nbytes /= 1024.0
        i += 1
    f = ("%.2f" % nbytes).rstrip("0").rstrip(".")
    return "%s %s" % (f, suffixes[i])


# set credentials
def auth():
    home = expanduser("~/appeears.json")
    usr = input("Enter username: ")
    pwd = getpass.getpass("Enter password: ")
    data = {"username": usr, "password": pwd}
    with open(home, "w") as outfile:
        json.dump(data, outfile)


def auth_from_parser(args):
    auth()


# generate token since token expires every 48 hours
def tokenizer():
    home = expanduser("~/appeears.json")
    if not os.path.exists(home):
        auth()
        with open(home) as json_file:
            data = json.load(json_file)
            username = data.get("username")
            pwd = data.get("password")
    else:
        with open(home) as json_file:
            data = json.load(json_file)
            username = data.get("username")
            pwd = data.get("password")
    response = requests.post(
        "https://appeears.earthdatacloud.nasa.gov/api/login", auth=(username, pwd)
    )
    if response.status_code in error_codes.keys():
        print(error_codes.get(response.status_code))
        sys.exit(response.json()["message"])
    token_response = response.json()
    return token_response["token"]


# get product list
def products(keyword):
    response = requests.get(
        "https://appeears.earthdatacloud.nasa.gov/api/product")
    if response.status_code in error_codes.keys():
        print(error_codes.get(response.status_code))
        sys.exit(response.json()["message"])
    product_response = response.json()
    products = {p["ProductAndVersion"]: p for p in product_response}
    if keyword is not None:
        for product in products:
            product_dict = products[product]
            uniform_product_dict = dict(
                (str(k).lower(), str(v).lower()) for k, v in product_dict.items()
            )
            if keyword.lower() in uniform_product_dict.values():
                product_dict["product_id"] = product_dict.pop(
                    "ProductAndVersion")
                print(json.dumps(product_dict, indent=2))
    else:
        for product in products:
            product_dict = products[product]
            product_dict["product_id"] = product_dict.pop("ProductAndVersion")
            print(json.dumps(product_dict, indent=2))


def products_from_parser(args):
    products(keyword=args.keyword)


# get layer info from product id
def layers(pid):
    response = requests.get(
        f"https://appeears.earthdatacloud.nasa.gov/api/product/{pid}"
    )
    if response.status_code in error_codes.keys():
        print(error_codes.get(response.status_code))
        sys.exit(response.json()["message"])
    layer_response = response.json()
    for layer in layer_response:
        print(layer)


def layers_from_parser(args):
    layers(pid=args.pid)


# get spatial projection info
def spatial():
    response = requests.get(
        "https://appeears.earthdatacloud.nasa.gov/api/spatial/proj")
    proj_response = response.json()
    print(json.dumps(proj_response, indent=2))


def spatial_from_parser(args):
    spatial()


# submit a task task_payload
payload = {
    "task_type": "",
    "task_name": "",
    "params": {
        "layers": "",
        "output": {
            "format": {
                "type": "geotiff",
            },
            "projection": "geographic",
        },
        "dates": [
            {
                "startDate": "",
                "endDate": "",
                "recurring": False,
                "yearRange": [
                    1950,
                    2050,
                ],
            },
        ],
        "coordinates": "",
    },
}


# submit a task
def tasksubmit(**kwargs):
    token = tokenizer()
    for key, value in kwargs.items():
        if key == "name":
            payload["task_name"] = value
        if key == "input":
            testfile = pygeoj.load(value)
            coordinates = []
            for feature in testfile:
                if feature.geometry.type == "Point":
                    payload["task_type"] = "point"
                    lat_long_dict = {
                        "latitude": feature.geometry.coordinates[1],
                        "longitude": feature.geometry.coordinates[0],
                    }
                    coordinates.append(lat_long_dict)
                    payload["params"]["coordinates"] = coordinates
                elif feature.geometry.type == "Polygon":
                    payload["task_type"] = "area"
                    geom = {
                        "geo": {
                            "type": "FeatureCollection",
                            "features": [
                                {
                                    "type": "Feature",
                                    "properties": {},
                                    "geometry": {
                                        "type": "Polygon",
                                        "coordinates": feature.geometry.coordinates,
                                    },
                                },
                            ],
                        },
                    }
                    coordinates = feature.geometry.coordinates
                    payload["params"].pop("coordinates")
                    payload["params"].update(geom)
                else:
                    sys.exit("Unknown geometry type")

        if key == "start":
            value = datetime.datetime.strptime(
                value, "%Y-%m-%d").strftime("%m-%d-%Y")
            payload["params"]["dates"][0]["startDate"] = str(value)
        if key == "end":
            value = datetime.datetime.strptime(
                value, "%Y-%m-%d").strftime("%m-%d-%Y")
            payload["params"]["dates"][0]["endDate"] = str(value)
        if key == "recurring":
            payload["params"]["dates"][0]["recurring"] = bool(value)
        if key == "projection":
            payload["params"]["output"]["projection"] = str(value)
        if key == "product":
            response = requests.get(
                f"https://appeears.earthdatacloud.nasa.gov/api/product/{value}"
            )
            layer_response = response.json()
            layer_list = []
            for layer in layer_response:
                layer_json = {"layer": layer, "product": value}
                layer_list.append(layer_json)
            payload["params"]["layers"] = layer_list
    # print(json.dumps(payload, indent=2))

    response = requests.post(
        "https://appeears.earthdatacloud.nasa.gov/api/task",
        headers={"Authorization": f"Bearer {token}"},
        json=payload,
    )
    if response.status_code in error_codes.keys():
        print(error_codes.get(response.status_code))
        sys.exit(response.json()["message"])
    else:
        print(f"Submitted task with task ID {response.json()['task_id']}")


def tasksubmit_from_parser(args):
    tasksubmit(
        name=args.name,
        product=args.product,
        start=args.start,
        end=args.end,
        recurring=args.recurring,
        projection=args.projection,
        input=args.geometry,
    )


# delete task using task id
def delete(tid):
    token = tokenizer()
    response = requests.delete(
        f"https://appeears.earthdatacloud.nasa.gov/api/task/{tid}",
        headers={"Authorization": f"Bearer {token}"},
    )
    if response.status_code in error_codes.keys():
        print(error_codes.get(response.status_code))
        sys.exit(response.json()["message"])
    elif response.status_code == 204:
        print(f"Task with task id {tid} deleted")


def delete_from_parser(args):
    delete(tid=args.tid)


# get task status for all tasks and groupby status
def task_all(status):
    token = tokenizer()
    response = requests.get(
        "https://appeears.earthdatacloud.nasa.gov/api/task",
        headers={"Authorization": f"Bearer {token}"},
    )
    if response.status_code in error_codes.keys():
        print(error_codes.get(response.status_code))
        sys.exit(response.json()["message"])
    status_response = response.json()
    if len(status_response) != 0:
        task_list = []
        for tasks in status_response:
            if status is not None:
                if tasks["status"] == status:
                    task_id = tasks["task_id"]
                    task_name = tasks["task_name"]
                    task_status = tasks["status"]
                    task_layers = []
                    for layers in tasks["params"]["layers"]:
                        task_layers.append(layers["layer"])
                    task_info = {
                        "task_id": task_id,
                        "task_name": task_name,
                        "task_status": task_status,
                        "task_layers": task_layers,
                    }
                    task_list.append(task_info)
            else:
                task_id = tasks["task_id"]
                task_name = tasks["task_name"]
                task_status = tasks["status"]
                task_layers = []
                for layers in tasks["params"]["layers"]:
                    task_layers.append(layers["layer"])
                task_info = {
                    "task_id": task_id,
                    "task_name": task_name,
                    "task_status": task_status,
                    "task_layers": task_layers,
                }
                task_list.append(task_info)
        if len(task_list) == 0 and status is not None:
            sys.exit(
                f"No tasks found with status {status} : try processing|done|pending"
            )
        task_list = sorted(task_list, key=itemgetter("task_status"))
        for key, value in groupby(task_list, key=itemgetter("task_status")):
            print("\n" + f"Task Status :{key.upper()}")
            for k in value:
                print(json.dumps(k, indent=2))
    else:
        print("No tasks found")


# get all or specific task information
def task_status(tid, status):
    token = tokenizer()
    if tid is not None:
        response = requests.get(
            f"https://appeears.earthdatacloud.nasa.gov/api/status/{tid}",
            headers={"Authorization": f"Bearer {token}"},
        )
        if response.status_code in error_codes.keys():
            print(error_codes.get(response.status_code))
            sys.exit(response.json()["message"])
        if response.status_code == 200:
            status_response = response.json()
            if (
                "status" in status_response.keys()
                and status_response["status"] != "pending"
            ):
                print(f"Task status is {status_response['status']}")
                ## fetch additional info like task name from task_id ##
                response = requests.get(
                    "https://appeears.earthdatacloud.nasa.gov/api/task",
                    headers={"Authorization": f"Bearer {token}"},
                )
                if response.status_code in error_codes.keys():
                    print(error_codes.get(response.status_code))
                    sys.exit(response.json()["message"])
                task_response = response.json()
                if len(task_response) != 0:
                    for task in task_response:
                        if task["task_id"] == tid:
                            task_id = task["task_id"]
                            task_name = task["task_name"]
                            task_status = task["status"]
                            task_layers = []
                            for layers in task["params"]["layers"]:
                                task_layers.append(layers["layer"])
                            task_info = {
                                "task_id": task_id,
                                "task_name": task_name,
                                "task_status": task_status,
                                "task_layers": task_layers,
                            }
                            print(json.dumps(task_info, indent=2))
            elif "state" not in status_response.keys():
                print(
                    f"Task {tid} processing : creating progessbar for task completion"
                )
                task_json = status_response
                for key, value in task_json.items():
                    if key == "progress":
                        cur_perc = value["summary"]
                with tqdm(total=100) as pbar:
                    while cur_perc < 100:
                        time.sleep(30)
                        response = requests.get(
                            f"https://appeears.earthdatacloud.nasa.gov/api/status/{tid}",
                            headers={"Authorization": f"Bearer {token}"},
                        )
                        if response.status_code in error_codes.keys():
                            print(error_codes.get(response.status_code))
                            sys.exit(response.json()["message"])
                        task_json = response.json()
                        for key, value in task_json.items():
                            if key == "progress":
                                cur_perc = value["summary"]
                                pbar.update(cur_perc - pbar.n)
                                if cur_perc == 100:
                                    break
            else:
                print(f"Task status {tid} is {status_response['status']}")
    else:
        task_all(status)


def taskinfo_from_parser(args):
    task_status(tid=args.tid, status=args.status)


# get file bundle information used by download tools
def file_bundle(tid):
    token = tokenizer()
    response = requests.get(
        f"https://appeears.earthdatacloud.nasa.gov/api/bundle/{tid}",
        headers={"Authorization": f"Bearer {token}"},
    )
    if response.status_code in error_codes.keys():
        print(error_codes.get(response.status_code))
        sys.exit(response.json()["message"])
    bundle_response = response.json()
    file_size_total = []
    file_id_list = []
    for file in bundle_response["files"]:
        file_id_list.append({file["file_id"]: file["file_name"]})
        file_size_total.append(file["file_size"])
    print(
        "Estimated Download Size for order: {}".format(
            humansize(sum(file_size_total)))
    )
    return natsorted(file_id_list)


# simple download tool
def download_task(tid, dest_dir):
    token = tokenizer()
    ## check if task has been completed ##
    response = requests.get(
        f"https://appeears.earthdatacloud.nasa.gov/api/status/{tid}",
        headers={"Authorization": f"Bearer {token}"},
    )
    if response.status_code in error_codes.keys():
        print(error_codes.get(response.status_code))
        sys.exit(response.json()["message"])
    if response.status_code == 200:
        if "status" in response.json().keys():
            file_id_list = file_bundle(tid)
            if len(file_id_list) > 0:
                i = 1
                for file in file_id_list:
                    for file_id, file_name in file.items():
                        filename = os.path.basename(file_name)
                        response = requests.get(
                            f"https://appeears.earthdatacloud.nasa.gov/api/bundle/{tid}/{file_id}",
                            headers={"Authorization": f"Bearer {token}"},
                            allow_redirects=True,
                            stream=True,
                        )

                        filepath = os.path.join(dest_dir, filename)
                        os.makedirs(os.path.dirname(filepath), exist_ok=True)

                        if not os.path.exists(filepath):
                            print(
                                f"Downloading {i} of {len(file_id_list)}: {filename}")
                            with open(filepath, "wb") as f:
                                for data in response.iter_content(chunk_size=8192):
                                    f.write(data)
                            i = i + 1
                        else:
                            print(
                                f"File {filename} already exists. Skipping download")
                            i = i + 1
        else:
            print(f"Task {tid} has not completed processing. Skipping download")


def download_from_parser(args):
    download_task(tid=args.tid, dest_dir=args.dest)


def main(args=None):
    parser = argparse.ArgumentParser(
        description="Simple CLI for NASA AppEEARS API")
    subparsers = parser.add_subparsers()

    parser_auth = subparsers.add_parser(
        "auth", help="Set username and password for authentication"
    )
    parser_auth.set_defaults(func=auth_from_parser)

    parser_products = subparsers.add_parser(
        "products", help="Print product list for all products or keyword match"
    )
    optional_named = parser_products.add_argument_group(
        "Optional named arguments")
    optional_named.add_argument(
        "--keyword", help="Pass product keyword for example ecostress", default=None
    )
    parser_products.set_defaults(func=products_from_parser)

    parser_layers = subparsers.add_parser(
        "layers", help="Print layer list for product with Product ID"
    )
    required_named = parser_layers.add_argument_group(
        "Required named arguments.")
    required_named.add_argument(
        "--pid", help="Product ID from products tool", required=True
    )
    parser_layers.set_defaults(func=layers_from_parser)

    parser_spatial = subparsers.add_parser(
        "spatial", help="List all supported spatial projections"
    )
    parser_spatial.set_defaults(func=spatial_from_parser)

    parser_tasksubmit = subparsers.add_parser(
        "task-submit", help="Submit your task")
    required_named = parser_tasksubmit.add_argument_group(
        "Required named arguments.")
    required_named.add_argument("--name", help="Task name", required=True)
    required_named.add_argument(
        "--product", help="Product ID returned from product tool", required=True
    )
    required_named.add_argument(
        "--geometry",
        help="Full path to geometry.geojson file point or single polygon",
        required=True,
    )
    required_named.add_argument(
        "--start", help="Start date in format YYYY-MM-DD", required=True
    )
    required_named.add_argument(
        "--end", help="End date in format YYYY-MM-DD", required=True
    )
    optional_named = parser_tasksubmit.add_argument_group(
        "Optional named arguments")
    optional_named.add_argument(
        "--projection", help="Spatial projection", default="geographic"
    )
    optional_named.add_argument(
        "--recurring", help="Date range recurring True|False", default=False
    )
    parser_tasksubmit.set_defaults(func=tasksubmit_from_parser)

    parser_taskinfo = subparsers.add_parser(
        "task-info",
        help="Get task information for all tasks or specific tasks or task status type",
    )
    optional_named = parser_taskinfo.add_argument_group(
        "Optional named arguments")
    optional_named.add_argument("--tid", help="Task ID", default=None)
    optional_named.add_argument(
        "--status", help="Task status processing|done|pending", default=None
    )
    parser_taskinfo.set_defaults(func=taskinfo_from_parser)

    parser_delete = subparsers.add_parser(
        "delete", help="Delete a specific task with task ID"
    )
    required_named = parser_delete.add_argument_group(
        "Required named arguments.")
    required_named.add_argument(
        "--tid", help="Task ID to delete", required=True)
    parser_delete.set_defaults(func=delete_from_parser)

    parser_download = subparsers.add_parser(
        "download", help="Download all files for specific task with task ID"
    )
    required_named = parser_download.add_argument_group(
        "Required named arguments.")
    required_named.add_argument(
        "--tid", help="Task ID to download", required=True)
    required_named.add_argument(
        "--dest", help="Full path to destination directory", required=True
    )
    parser_download.set_defaults(func=download_from_parser)

    args = parser.parse_args()

    try:
        func = args.func
    except AttributeError:
        parser.error("too few arguments")
    func(args)

    if __name__ == "__main__":
        main()
