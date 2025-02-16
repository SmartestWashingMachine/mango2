from flask import send_from_directory, send_file, abort, render_template, request
from gandy.app import app, web_app
from gandy.get_envs import ENABLE_WEB_UI
from gandy.tasks.task1.task1_routes import translate_task1_background_job, socketio
import os
from glob import glob
from gandy.utils.natsort import natsort
import zipfile
from uuid import uuid4
from PIL import Image
from io import BytesIO

if ENABLE_WEB_UI:
    print('CWD:')
    print(os.getcwd())

    def list_files(folder_name, file_extension):
        # Sort folders by date in UI.
        folder_dates = {}

        folder_map = {}

        if file_extension == "mp4":
            videos_folder_path = os.path.expanduser(f"~/Documents/Mango/{folder_name}/")
            videos_path = [f for f in glob(f"{videos_folder_path}*")]

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
    
    def get_file(folder_name, user_folder_name, file_name, mimetype, load_image=False):
        images_folder_path = os.path.expanduser(f"~/Documents/Mango/{folder_name}/")

        if user_folder_name is not None:
            fol_path = f"{images_folder_path}/{user_folder_name}"
        else:
            fol_path = images_folder_path

        file_path = f"{fol_path}/{file_name}"

        if not os.path.exists(fol_path) or not os.path.exists(file_path):
            abort(404)

        if load_image:
            img = Image.open(file_path)
            if img.mode != 'RGB':
                img = img.convert('RGB')

            buffer = BytesIO()
            img.save(buffer, format="JPEG")
            buffer.seek(0)

            return send_file(buffer, mimetype='image/jpeg')

        return send_file(file_path, mimetype)

    @web_app.route("/webui", methods=["GET"])
    def webui_route():
        return render_template("index.html")
    
    ### IMAGES

    @web_app.route("/webui/list", methods=["GET"])
    def list_files_route():
        return list_files(folder_name="images", file_extension="png")

    @web_app.route("/webui/resources/<folder_name>/<file_name>", methods=["GET"])
    def get_file_route(folder_name: str, file_name: str):
        if folder_name is None:
            raise RuntimeError('Bad folder name.')

        return get_file("images", folder_name, file_name, mimetype="image/png", load_image=True)
    
    ### VIDEOS

    @web_app.route("/webui/videolist", methods=["GET"])
    def list_video_files_route():
        return list_files(folder_name="videos", file_extension="mp4")

    @web_app.route("/webui/videoresources/<folder_name>/<file_name>", methods=["GET"])
    def get_video_file_route(folder_name: str, file_name: str):
        return get_file("videos", user_folder_name=None, file_name=file_name, mimetype="video/mp4")
    
    # Note that this route uses the main app - not the web app.
    @app.route("/webui/processziptask1", methods=["POST"])
    def process_zipped_images():
        zip_file = request.files.getlist("file")
        if zip_file is None or not isinstance(zip_file, list) or len(zip_file) > 1:
            return {}, 400
        
        zip_file = zip_file[0]

        files = []
        with zipfile.ZipFile(zip_file, 'r') as f:
            for file_name in f.namelist():
                file_data = f.read(file_name)
                file_data = BytesIO(file_data)
                files.append(file_data)

        task_id = uuid4().hex

        images_folder_path = os.path.expanduser(f"~/Documents/Mango/images/")

        def _on_image_done(image: Image.Image, img_idx: int, img_name_no_ext: str):
            new_fol = f'{images_folder_path}/{task_id}/'
            os.makedirs(new_fol, exist_ok=True)

            image.save(f'{new_fol}{img_name_no_ext}.png')

        socketio.start_background_task(
            translate_task1_background_job,
            files,
            task_id,
            _on_image_done
        )

        return {}, 200