import argparse
import getpass
import json
import os
import sys
import time
from os.path import expanduser
from turtle import st

import pkg_resources
import requests
from natsort import natsorted
from rapidfuzz import fuzz
from tqdm import tqdm

# from bs4 import BeautifulSoup as bs
# from tabulate import tabulate
# from tenacity import retry, stop_after_attempt, wait_exponential

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


# def auth_from_parser(args):
#     auth()


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
    token_response = response.json()
    return token_response["token"]


# tokenizer()


def products(keyword):
    response = requests.get(
        "https://appeears.earthdatacloud.nasa.gov/api/product")
    product_response = response.json()
    products = {p["ProductAndVersion"]: p for p in product_response}
    for product in products:
        product_dict = products[product]
        if keyword is not None:
            uniform_product_dict = dict(
                (str(k).lower(), str(v).lower()) for k, v in product_dict.items()
            )
            if keyword.lower() in uniform_product_dict.values():
                product_dict["product_id"] = product_dict.pop(
                    "ProductAndVersion")
                print(json.dumps(product_dict, indent=2))
        else:
            product_dict["product_id"] = product_dict.pop("ProductAndVersion")
            print(json.dumps(products, indent=2))


# products(keyword='ecostress')


def layer_info(pid):
    response = requests.get(
        f"https: // appeears.earthdatacloud.nasa.gov/api/product/{pid}"
    )
    layer_response = response.json()
    for layer in layer_response:
        print(layer)


# layer_info(pid)


def task_all():
    token = tokenizer()
    response = requests.get(
        "https://appeears.earthdatacloud.nasa.gov/api/task",
        headers={"Authorization": "Bearer {0}".format(token)},
    )
    status_response = response.json()
    if len(status_response) != 0:
        for tasks in status_response:
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
            print(json.dumps(task_info, indent=2))
    else:
        print("No tasks found")


def task_status(tid):
    token = tokenizer()
    if tid is not None:
        response = requests.get(
            f"https://appeears.earthdatacloud.nasa.gov/api/status/{tid}",
            headers={"Authorization": f"Bearer {token}"},
        )
        status_response = response.json()
        if "state" in status_response:
            print(f"Task state is {status_reponse['state']}")
            print(json.dumps(status_response, indent=2))
        elif status_response["status"] != "pending":
            task_json = status_response
            for key, value in task_json.items():
                if key == "progress":
                    cur_perc = value["summary"]
            with tqdm(total=100) as pbar:
                while cur_perc < 100:
                    time.sleep(30)
                    response = requests.get(
                        "https://appeears.earthdatacloud.nasa.gov/api/status/{0}".format(
                            tid
                        ),
                        headers={"Authorization": f"Bearer {token}"},
                    )
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
        task_all()


# task_status(tid='72cb5024-d3ec-49f4-852a-5a71321b1a31')


def file_bundle(tid):
    token = tokenizer()
    response = requests.get(
        f"https://appeears.earthdatacloud.nasa.gov/api/bundle/{tid}",
        headers={"Authorization": f"Bearer {token}"},
    )
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


# file_bundle(tid='c1bd3576-33ab-447b-83bb-f91b8cbcbd3e')


def download_task(tid):
    token = tokenizer()
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
                dest_dir = r"C:\tmp\opera"
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
                    print(f"File {filename} already exists. Skipping download")
                    i = i + 1


download_task(tid="c1bd3576-33ab-447b-83bb-f91b8cbcbd3e")
