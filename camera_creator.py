import requests, json, unidecode

class CameraCreator:

    def __init__(self):
        #SERVER_ADDRESS = "https://cameras.acesso.srv.br:8081/api"
        #SERVER_ADDRESS = "https://179.108.90.250:8081/api/"

        self.__IP__ = "https://cameras.acesso.srv.br"
        self.__SERVER_ADDRESS__ = f"{self.__IP__}:8081/api"
        self.__HEADERS__ = { 'Content-type':'application/json', 'Accept':'application/json' }
        self.__BEARER_PREFIX__ = "Bearer"

        self.__USERNAME__ = "admin"
        self.__PASSWORD__ = "1Sucesso2020"

        self.__SESSION__ = requests.Session()

    def __format_api_call__(self, api_suffix):
        return self.__SERVER_ADDRESS__ + api_suffix

    def __format_address_with_username_and_password__(self):
        return self.__IP__.replace("://", f"://{self.__USERNAME__}:{self.__PASSWORD__}@")

    def __call_requests__(self, requests_method, api_suffix, requests_data = None, convert_to_json = True):
        request_result = requests_method(self.__format_api_call__(api_suffix), headers=self.__HEADERS__, json=requests_data)

        if convert_to_json:
            return request_result.json()
        else:
            return request_result.content

    def __login__(self, username, password):
        login_result = self.__call_requests__(self.__SESSION__.post, "/login", { "username": username, "password": password })

        userToken = login_result["login"]["userToken"]
        self.__HEADERS__["Authorization"] = self.__BEARER_PREFIX__ + userToken

    def __get_server__(self, server_name):
        servers = self.__call_requests__(self.__SESSION__.get, "/servers")["servers"]
        servers_with_same_name = [server for server in servers if unidecode.unidecode(server_name.lower()) in unidecode.unidecode(server["name"].lower())]

        return servers_with_same_name


    def __get_server_by_guid__(self, server_guid):
        server = self.__call_requests__(self.__SESSION__.get, f"/servers/{server_guid}")["server"]
        return server

    def __get_cameras_names__(self, server_contact_id_code, server_name):
        request_result = requests.get(f"{self.__format_address_with_username_and_password__()}/camerasnomes.cgi?server={server_contact_id_code}", verify=False)

        cameras_names_text = request_result.text.split("&")
        cameras_names_list = []

        for camera_name_text in cameras_names_text:
            camera_number = camera_name_text.split("=")[0]
            camera_name = camera_name_text.split("=")[1].replace(server_name + ".", "")

            cameras_names_list.append({"number": camera_number, "name": camera_name})

        return cameras_names_list

    def __get_server_cameras__(self, server_guid):
        cameras = self.__call_requests__(self.__SESSION__.get, f"/servers/{server_guid}/cameras")["cameras"]
        return cameras

    def __get_camera_image__(self, server_guid, camera_id):
        #image = call_requests(SESSION.get, "/servers/{serverGuid}/cameras/{cameraId}/image.jpg".format(serverGuid = server_guid, cameraId = camera_id), convert_to_json=False)
        image_link = f"/servers/{server_guid}/cameras/{camera_id}/image.jpg"
        return image_link

    def __format_camera_name__(self, server_guid, camera_number):
        server_guid_without_bracket = server_guid.replace("{", "").replace("}", "")
        server_ip_without_protocol = self.__format_address_with_username_and_password__().replace('https://', '').replace('http://', '')
        return f"rtsp://{server_ip_without_protocol}:6000/servers/{server_guid_without_bracket}/cameras/{camera_number}"

    def __format_camera_thumbnail__(self, server_camera_name):
        return f"{self.__format_address_with_username_and_password__()}/camera.cgi?camera={server_camera_name}"

    def create_cameras_json(self):
        self.__login__(self.__USERNAME__, self.__PASSWORD__)

        while True:
            #server_name = input("Digite o nome do condomínio: ")
            server_name = "KANAXUÊ" #"LAGO DO BOSQUE" #"Kanaxue"
            servers = self.__get_server__(server_name)

            if len(servers) == 0:
                print("Nenhum server encontrado com esse nome!")
            #elif len(servers) > 1:
            #    print("Mais de um server encontrado com o mesmo nome!")
            else:
                break

        server_cameras_list = [{"name": "Câmeras", "description": "Câmeras", "cameras": []}]

        for server in servers:
            #server = servers[0]
            server_guid = server["guid"]

            server = self.__get_server_by_guid__(server_guid)
            server_contact_id_code = server["contactIdCode"]

            server_cameras_names = self.__get_cameras_names__(server_contact_id_code, server["name"])
            server_cameras = self.__get_server_cameras__(server_guid)

            for server_camera_name in server_cameras_names:
                server_camera = [server_camera for server_camera in server_cameras if server_camera["name"] == server_camera_name["name"]]

                if len(server_camera) == 0:
                    continue

                server_camera = server_camera[0]

                server_cameras_list[0]["cameras"].append({
                    "name": server_camera["name"],
                    "url": self.__format_camera_name__(server_guid, server_camera["id"]),
                    "thumbnail": self.__format_camera_thumbnail__(server_camera_name["number"])
                })

        with open(f'{server_name}_camera_json.json', 'wt', encoding="utf-8") as outfile:
            json.dump(server_cameras_list, outfile, indent=2, ensure_ascii=False)

        return server_name
