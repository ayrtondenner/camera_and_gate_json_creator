from importlib.metadata import files
import requests, json, unidecode
from lxml import html

class GateCreator:
    
    def __init__(self):
        self.__AUTOMACAO_ADDRESS__ = "http://172.31.255.7:7110/acesso/"
        self.__LISTA_TERMOS_PORTAO__ = [self.__convert_gate_string__(termo) for termo in
            #["Térreo", "Subsolo"]
            ["Garage"]
        ]

        self.__SERVER_FILES__ = ["Servidores.csv", "Servidores1.csv"]

    def __try_extract_valid_id_number_from_table_row__(self, table_row):
        if "id" not in table_row.attrib:
            return None # A primeira linha nunca deve ser lida

        table_row_id = table_row.attrib["id"]
        table_row_id_number = table_row_id.replace("row", "")

        if len(table_row_id_number) == 0:
            return None

        return table_row_id_number

    def __convert_gate_string__(self, gate_string):
        return unidecode.unidecode(gate_string.lower().replace("-", ""))
    
    def __check_if_gate_td_string_is_valid__(self, gate_td):
            gate_string = gate_td.text
            return any(termo in self.__convert_gate_string__(gate_string) for termo in self.__LISTA_TERMOS_PORTAO__)

    def create_gates_json(self, server_name):

        server_gates_list = []

        automacao_request = requests.get(self.__AUTOMACAO_ADDRESS__)
        automacao_html = automacao_request.text
        automacao_html_tree = html.fromstring(automacao_html)

        automacao_container = automacao_html_tree.body.get_element_by_id("container")
        automacao_sortable_table = automacao_container.xpath("//table[@class='sortable']")[0]

        server_table_row = None
        server_table_row_id_number = None

        for index, table_row in enumerate(automacao_sortable_table.getchildren()):
            table_row_id_number = self.__try_extract_valid_id_number_from_table_row__(table_row)

            if table_row_id_number == None:
                continue

            name_tr = table_row.get_element_by_id("nome" + table_row_id_number)

            if unidecode.unidecode(name_tr.text.lower()) == unidecode.unidecode(server_name.lower()):
                # Não vamos considerar os portões se o prédio estar DESATIVADO
                if table_row.get_element_by_id("status" + table_row_id_number).text == "Ativado":
                    server_table_row = table_row
                    server_table_row_id_number = table_row_id_number
                break

        entrance_ip_address = None
        entrance_ip_port = None

        if server_table_row != None:

            entrance_ip_address = server_table_row.get_element_by_id("ip" + server_table_row_id_number).text
            entrance_ip_port = server_table_row.get_element_by_id("port" + server_table_row_id_number).text

            automacao_condo_request = requests.get(f"{self.__AUTOMACAO_ADDRESS__}automacao.php?id={server_table_row_id_number}&nome=")
            automacao_condo_html = automacao_condo_request.text
            automacao_condo_html_tree = html.fromstring(automacao_condo_html)

            automacao_condo_container = automacao_condo_html_tree.get_element_by_id("container")
            automacao_condo_table = [child for child in automacao_condo_container.getchildren() if child.tag == "table"][0]

            for table_row in automacao_condo_table.getchildren():
                table_row_id_number = self.__try_extract_valid_id_number_from_table_row__(table_row)

                if table_row_id_number == None:
                    continue

                for entrance_term in ["entrada_1_", "entrada_2_"]:
                    entrance_td = table_row.get_element_by_id(entrance_term + table_row_id_number)

                    if self.__check_if_gate_td_string_is_valid__(entrance_td):

                        entrance_controller_model_td = table_row.get_element_by_id("modelo" + table_row_id_number)
                        entrance_can_td = table_row.get_element_by_id("end_can" + table_row_id_number)

                        entrance_label_app = entrance_td.text
                        entrance_controller_model = entrance_controller_model_td.text
                        entrance_device_number = entrance_can_td.text
                        entrance_controller_port = entrance_can_td.text
                        entrance_drive_command = entrance_can_td.text

                        server_gates_list.append({
                            "Label APP": entrance_label_app,
                            "EnderecoIP": entrance_ip_address,
                            "PortaIP": entrance_ip_port,
                            "ModeloControladora": entrance_controller_model,
                            "NumeroAparelho": entrance_device_number,
                            "PortaControladora": entrance_controller_port,
                            "ComandoAcionamento": entrance_drive_command,
                            "StatusOK": "OK"
                        })

        else:
            pass
            #files_rows = []
            #for server_file in self.__SERVER_FILES__:
            #    csv_df = pd.read_csv(server_file, index_col=None, header=0)
            #    files_rows.append(csv_df)

            #df = pd.concat(map(pd.read_csv, self.__SERVER_FILES__))

        with open(f'{server_name}_gate_json.json', 'wt', encoding="utf-8") as outfile:
            json.dump(server_gates_list, outfile, indent=2, ensure_ascii=False)