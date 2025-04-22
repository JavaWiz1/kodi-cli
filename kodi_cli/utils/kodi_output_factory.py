# Json Raw 
# Json Formatted
# CSV Formatted
#     CSV only available for specific commands

# https://www.geeksforgeeks.org/convert-json-to-csv-in-python/


# Python program to convert
# JSON file to CSV
 
import json
import csv
import sys

# ===========================================================================
class ObjectFactory:
    def __init__(self):
        self._builders = {}

    def register_builder(self, key, builder):
        self._builders[key] = builder

    def create(self, key, **kwargs):
        builder = self._builders.get(key)
        if not builder:
            raise ValueError(key)
        return builder(**kwargs)

# ===========================================================================
class JSON_OutputServiceBuilder:
    def __init__(self):
        self._instance = None

    def __call__(self, response_text: str, pretty: bool = False, **_ignored):
        if not self._instance:
            self._instance = JSON_OutputService(response_text, pretty)
        return self._instance   


class JSON_OutputService:
    def __init__(self, output_text: str, pretty: bool = False):
        self._output_text = output_text
        self._pretty = pretty
    
    def output_result(self) -> str:
        if self._pretty:
            result = json.dumps(json.loads(self._output_text), indent=2)
        else:
            result = json.dumps(json.loads(self._output_text))
        print(result)
     

# ===========================================================================
class CSV_OutputServiceBuilder:
    def __init__(self):
        self._instance = None

    def __call__(self, response_text: str, list_key: str, **_ignored):
        if not self._instance:
            self._instance = CSV_OutputService(response_text, list_key)
        return self._instance   

class CSV_OutputService:
    def __init__(self, output_text: str, list_key: str):
        self._output_text = output_text
        self._list_key = list_key

    def output_result(self):
        data = json.loads(self._output_text)
        json_list = data['result'][self._list_key]
        sys.stdout.reconfigure(encoding='utf-8')
        csv_writer = csv.writer(sys.stdout, lineterminator='\n')
        # Counter variable used for writing headers to the CSV file
        count = 0
        for item in json_list:
            if count == 0:
                # Writing headers of CSV file
                header = item.keys()
                csv_writer.writerow(header)
                count += 1
        
            # Writing data of CSV file
            csv_writer.writerow(item.values())

