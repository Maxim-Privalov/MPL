import FreeSimpleGUI as sg
from kafka import KafkaProducer
import json

layout = [  
            [sg.Button("Добавить таблицу")],
            [sg.Column([], key="-DYNAMIC-TABLES-"), sg.Column([], key="-HIDE-TABLE-CONTAINER-")],
            [sg.Button("Отправить .json из файла"), 
              sg.Push(), sg.Button("Отправить", button_color=("gray", "white"), disabled=True)]
         ]

window = sg.Window('Работа с kafka', layout)

def collapsible(layout, key, visible=False):
    return sg.pin( sg.Column(
            layout,
            key=key,
            visible=visible,
            pad=(0,0),  
            scrollable=True,
            size=(450, 600),
            expand_x=False,             
            expand_y=False))

def create_table(name : str, existed_names=[]):
    layout = [ [sg.InputText()],
               [sg.Text("Число строк: "), sg.InputText(size=(3, 1), key="-STR-COUNT-")],
               [sg.Text("Введите название столбцов(через `|`): ")],
               [sg.InputText(key="-HEADINGS-")],
               [sg.Button("Добавить"), sg.Button("Отмена")],
               [sg.Text("", key="-ERROR-MODAL-")] ]
    
    modal_window = sg.Window(name, layout, modal = True, finalize = True)
    while True:
        event, values = modal_window.read()
        
        result = None
        if event == "Добавить" and values[0].strip() != "":
            if not(existed_names == [] or not(values[0].strip() in existed_names)):
                modal_window["-ERROR-MODAL-"].update("Такое имя уже существует")
            
            elif not(values["-STR-COUNT-"].isdigit()):
                modal_window["-ERROR-MODAL-"].update("Неверный формат ввода кол-ва строк")

            elif int(values["-STR-COUNT-"]) < 1 or int(values["-STR-COUNT-"]) > 1000:
                modal_window["-ERROR-MODAL-"].update("Кол-во строк должно быть между 1 и 1000")

            else:
                headings = []
                for head in values["-HEADINGS-"].split("|"):
                    if head.strip() != "":
                        headings.append(head.strip())

                if headings == []:
                    modal_window["-ERROR-MODAL-"].update("Не задан ни один столбец")
                
                else:
                    result = (values[0].strip(), values["-STR-COUNT-"], headings)
                    break
        
        else:
            break
                
    
    modal_window.close()
    return result


def main():
    tables = {}
    selected_table = None

    while True:
        event, values = window.read()
        if event == sg.WIN_CLOSED:
            break

        if event == "Добавить таблицу":
            table_format = create_table("Введите название таблицы", tables)
            if table_format:
                lines = []
                table_name = table_format[0]
                line_count = int(table_format[1])
                for li in range(line_count):
                    line = {}
                    for column_name in table_format[2]:
                        line[column_name] = ""
                    
                    lines.append(line)
                tables[table_name] = lines
                window.extend_layout(window["-DYNAMIC-TABLES-"], [
                        [sg.Button(table_name)]
                        ])
                rows = []

                rows.append([sg.Text(head, font=("Arial", 12, "bold")) for head in table_format[2]])
                for index, line in enumerate(lines):
                    rows.append([sg.InputText(default_text="", size=(10, 1), key=f"-{table_name}-{val}-{index}-") for val in line])

                window.extend_layout(window["-HIDE-TABLE-CONTAINER-"], [[collapsible(rows, table_name + "-TABLE-")]])
                selected_table = table_name

        if event == "Отправить":
            for table_name in tables.keys():
                for line_index in range(len(tables[table_name])):
                    line = tables[table_name][line_index]
                    for field in line.keys():
                        line[field] = values[f"-{table_name}-{field}-{line_index}-"]

            producer = KafkaProducer(
                bootstrap_servers='localhost:9092',
                value_serializer=lambda v: json.dumps(v).encode('utf-8'),
                retries=5,
                acks='all',
                compression_type='gzip'
            )
            future = producer.send('tables', value=tables)
            result = future.get(timeout=10)

            print(f"Успешно отправлено: topic=tables, partition={result.partition}, offset={result.offset}")            
            producer.flush()
            producer.close()

        if event in tables.keys():
            selected_table = event

        for index, table in enumerate(tables.keys()):
            if table == selected_table:
                window[table].update(button_color=("black", "white"))
                window[table + "-TABLE-"].update(visible=True)
            else:
                window[table].update(button_color=("white", "gray"))
                window[table + "-TABLE-"].update(visible=False)
        
        if selected_table:
            window["Отправить"].update(button_color=("white", sg.theme_button_color_background()), disabled=False)
        else:
            window["Отправить"].update(button_color=("gray", "white"), disabled=True)

    window.close()

if __name__ == '__main__':
    main()