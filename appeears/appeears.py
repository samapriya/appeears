import argparse
import getpass
import json
import os
import sys
import time
from itertools import groupby
from operator import itemgetter
from os.path import expanduser

import pkg_resources
import requests
from natsort import natsorted
from tqdm import tqdm

# from bs4 import BeautifulSoup as bs
# from tenacity import retry, stop_after_attempt, wait_exponential

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
    usr = input("Enter email: ")
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
        sys.exit(error_codes.get(response.status_code))
    token_response = response.json()
    return token_response["token"]


# get product list
def products(keyword):
    response = requests.get("https://appeears.earthdatacloud.nasa.gov/api/product")
    if response.status_code in error_codes.keys():
        sys.exit(error_codes.get(response.status_code))
    product_response = response.json()
    products = {p["ProductAndVersion"]: p for p in product_response}
    if keyword is not None:
        for product in products:
            product_dict = products[product]
            uniform_product_dict = dict(
                (str(k).lower(), str(v).lower()) for k, v in product_dict.items()
            )
            if keyword.lower() in uniform_product_dict.values():
                product_dict["product_id"] = product_dict.pop("ProductAndVersion")
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
        sys.exit(error_codes.get(response.status_code))
    layer_response = response.json()
    for layer in layer_response:
        print(layer)


def layers_from_parser(args):
    layers(pid=args.pid)


# get task status for all tasks and groupby status
def task_all(status):
    token = tokenizer()
    response = requests.get(
        "https://appeears.earthdatacloud.nasa.gov/api/task",
        headers={"Authorization": f"Bearer {token}"},
    )
    if response.status_code in error_codes.keys():
        sys.exit(error_codes.get(response.status_code))
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
            sys.exit(error_codes.get(response.status_code))
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
                    sys.exit(error_codes.get(response.status_code))
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
                            sys.exit(error_codes.get(response.status_code))
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
        sys.exit(error_codes.get(response.status_code))
    bundle_response = response.json()
    file_size_total = []
    file_id_list = []
    for file in bundle_response["files"]:
        file_id_list.append({file["file_id"]: file["file_name"]})
        file_size_total.append(file["file_size"])
    print(
        "Estimated Download Size for order: {}".format(humansize(sum(file_size_total)))
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
        sys.exit(error_codes.get(response.status_code))
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
                            print(f"Downloading {i} of {len(file_id_list)}: {filename}")
                            with open(filepath, "wb") as f:
                                for data in response.iter_content(chunk_size=8192):
                                    f.write(data)
                            i = i + 1
                        else:
                            print(f"File {filename} already exists. Skipping download")
                            i = i + 1
        else:
            print(f"Task {tid} has not completed processing. Skipping download")


def download_from_parser(args):
    download_task(tid=args.tid, dest_dir=args.dest)


def main(args=None):
    parser = argparse.ArgumentParser(description="Simple CLI for NASA AppEEARS API")
    subparsers = parser.add_subparsers()

    parser_auth = subparsers.add_parser(
        "auth", help="Set username and password for authentication"
    )
    parser_auth.set_defaults(func=auth_from_parser)

    parser_products = subparsers.add_parser(
        "products", help="Print product list for all products or keyword match"
    )
    optional_named = parser_products.add_argument_group("Optional named arguments")
    optional_named.add_argument(
        "--keyword", help="Pass product keyword for example ecostress", default=None
    )
    parser_products.set_defaults(func=products_from_parser)

    parser_layers = subparsers.add_parser(
        "layers", help="Print layer list for product with Product ID"
    )
    required_named = parser_layers.add_argument_group("Required named arguments.")
    required_named.add_argument(
        "--pid", help="Product ID from products tool", required=True
    )
    parser_layers.set_defaults(func=layers_from_parser)

    parser_taskinfo = subparsers.add_parser(
        "taskinfo",
        help="Get task information for all tasks or specific tasks or task status type",
    )
    optional_named = parser_taskinfo.add_argument_group("Optional named arguments")
    optional_named.add_argument("--tid", help="Task ID", default=None)
    optional_named.add_argument(
        "--status", help="Task status processing|done|pending", default=None
    )
    parser_taskinfo.set_defaults(func=taskinfo_from_parser)

    parser_download = subparsers.add_parser(
        "download", help="Download all files for specific task with task ID"
    )
    required_named = parser_download.add_argument_group("Required named arguments.")
    required_named.add_argument("--tid", help="Task ID to download", required=True)
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
