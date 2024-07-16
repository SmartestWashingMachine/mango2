from flask import send_from_directory, abort, render_template
from gandy.app import app
from gandy.get_envs import ENABLE_WEB_UI
import os
from glob import glob
from gandy.utils.natsort import natsort

if ENABLE_WEB_UI:

    @app.route("/webui", methods=["GET"])
    def webui_route():
        return render_template("index.html")

    @app.route("/webui/list", methods=["GET"])
    def list_files_route():
        images_folder_path = os.path.expanduser("~/Documents/Mango/images/")
        folder_paths = [f for f in glob(f"{images_folder_path}*/")]

        # Sort folders by date in UI.
        folder_dates = {}

        folder_map = {}
        for fol_pth in folder_paths:
            fol_name = os.path.basename(os.path.normpath(fol_pth))
            fol_files = glob(f"{fol_pth}/*.png")
            if len(fol_files) == 0:
                continue

            file_paths = sorted(
                [os.path.basename(os.path.normpath(x)) for x in fol_files], key=natsort
            )
            first_file_date = os.path.getmtime(fol_files[0])

            folder_map[fol_name] = file_paths
            folder_dates[fol_name] = first_file_date

        return {
            "folderMap": folder_map,
            "folderDates": folder_dates,
        }, 200

    @app.route("/webui/resources/<folder_name>/<file_name>", methods=["GET"])
    def get_file_route(folder_name: str, file_name: str):
        images_folder_path = os.path.expanduser("~/Documents/Mango/images/")
        fol_path = f"{images_folder_path}/{folder_name}"
        file_path = f"{fol_path}/{file_name}"
        if not os.path.exists(fol_path) or not os.path.exists(file_path):
            abort(404)

        return send_from_directory(fol_path, file_name, mimetype="image/png")
