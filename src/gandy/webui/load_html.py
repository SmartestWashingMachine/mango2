from flask import send_from_directory, abort, render_template
from gandy.app import app
from gandy.get_envs import ENABLE_WEB_UI
import os
from glob import glob
from gandy.utils.natsort import natsort

if ENABLE_WEB_UI:
    print('CWD:')
    print(os.getcwd())

    def list_files(folder_name, file_extension):
        # Sort folders by date in UI.
        folder_dates = {}

        folder_map = {}

        if file_extension == "mp4":
            videos_folder_path = os.path.expanduser(f"~/Documents/Mango/{folder_name}/")
            videos_path = [f for f in glob(f"{videos_folder_path}*.mp4")]

            for vp in videos_path:
                first_file_date = os.path.getmtime(vp)

                fol_name = os.path.basename(os.path.normpath(vp))
                folder_map[fol_name] = [fol_name]

                folder_dates[fol_name] = first_file_date
        else:
            images_folder_path = os.path.expanduser(f"~/Documents/Mango/{folder_name}/")
            folder_paths = [f for f in glob(f"{images_folder_path}*/")]

            for fol_pth in folder_paths:
                fol_name = os.path.basename(os.path.normpath(fol_pth))
                fol_files = glob(f"{fol_pth}/*.{file_extension}")
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
    
    def get_file(folder_name, user_folder_name, file_name, mimetype):
        images_folder_path = os.path.expanduser(f"~/Documents/Mango/{folder_name}/")

        if user_folder_name is not None:
            fol_path = f"{images_folder_path}/{user_folder_name}"
        else:
            fol_path = images_folder_path

        file_path = f"{fol_path}/{file_name}"

        if not os.path.exists(fol_path) or not os.path.exists(file_path):
            abort(404)

        return send_from_directory(fol_path, file_name, mimetype=mimetype)

    @app.route("/webui", methods=["GET"])
    def webui_route():
        return render_template("index.html")
    
    ### IMAGES

    @app.route("/webui/list", methods=["GET"])
    def list_files_route():
        return list_files(folder_name="images", file_extension="png")

    @app.route("/webui/resources/<folder_name>/<file_name>", methods=["GET"])
    def get_file_route(folder_name: str, file_name: str):
        if folder_name is None:
            raise RuntimeError('Bad folder name.')

        return get_file("images", folder_name, file_name, mimetype="image/png")
    
    ### VIDEOS

    @app.route("/webui/videolist", methods=["GET"])
    def list_video_files_route():
        return list_files(folder_name="videos", file_extension="mp4")

    @app.route("/webui/videoresources/<folder_name>/<file_name>", methods=["GET"])
    def get_video_file_route(folder_name: str, file_name: str):
        return get_file("videos", user_folder_name=None, file_name=file_name, mimetype="video/mp4")