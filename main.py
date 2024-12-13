# -*- coding: utf-8 -*- 

# external imports
import os
from dotenv import load_dotenv
import json
import re
import pymarc
from enum import Enum
import csv
from typing import List, Dict
import xml.etree.ElementTree as ET

# Internal import

# ---------- Init ----------
load_dotenv()

RECORDS_FILE_PATH = os.getenv("RECORDS_FILE")
ERRORS_FILE_PATH = os.path.abspath(os.getenv("ERRORS_FILE"))
KOHA_MARC_FRAMEWORK_FILE = os.getenv("KOHA_MARC_FRAMEWORK_FILE")
KOHA_AUTH_VAL_FILE = os.getenv("KOHA_AUTH_VAL_FILE")
CONTROL_VALUES_FILE = os.getenv("CONTROL_VALUES_FILE")

# ---------- Class def ----------

# ----- Authorised values -----
class Authorized_Value_Value(object):
    def __init__(self, category:str, val:str, lib:str, lib_opac:str) -> None:
        self.category = category
        self.val = val
        self.lib = lib
        self.lib_opac = lib_opac

class Authorized_Value(object):
    def __init__(self, id:str) -> None:
        self.id = id
        self.values_obj:Dict[str, Authorized_Value_Value] = {}
        self.values_list:List[str] = []
    
    def add_value(self, val:Authorized_Value_Value):
        """Adds a value to this autorized value value list"""
        self.values_obj[val.val] = val
        self.values_list.append(val.val)
    
    def get_auth_val_val_obj_from_val(self, val:str) -> Authorized_Value_Value:
        """Returns the Authorized_Value_Value for the wanted value"""
        return self.values_obj[val]
    
    def is_valid_val(self, val:str) -> bool:
        """Returns if this value is part of the values"""
        return val in self.values_list


AUTHORISED_VALUES:Dict[str, Authorized_Value] = {}

# ----- MARC Framework -----
class Field_Type(Enum):
    LEADER = 0
    CONTROLFIELD = 1
    DATAFIELD = 2

class Subfield(object):
    # Koha 22.11, capturing groups :
    # 2 : tag, 4 : code, 6 : Label intranet
    # 8 : repeatable, 10 : mandatory, 12 : tab
    # 14 : authorized value, 16 : value builder
    # 18 : max length
    # pattern :
    #   - Start with : (")
    #   - Get value with : ([^\"]*)
    #   - Skip X field with : (",(?:"[^\"]*",){X}")
    #   - End with : (".*)
    # Yes sometimes it's excessive but it's easier to use the same strcuture
    pattern = r'^(")([^\"]*)(",(?:"[^\"]*",){0}")([^\"]*)(",(?:"[^\"]*",){0}")([^\"]*)(",(?:"[^\"]*",){1}")([^\"]*)(",(?:"[^\"]*",){0}")([^\"]*)(",(?:"[^\"]*",){2}")([^\"]*)(",(?:"[^\"]*",){0}")([^\"]*)(",(?:"[^\"]*",){1}")([^\"]*)(",(?:"[^\"]*",){6}")([^\"]*)(".*)'

    def __init__(self, csv_line:str) -> None:
        self.valid = False
        has_matched = re.match(self.pattern, csv_line)
        if has_matched:
            self.valid = True
            self.tag = has_matched.group(2)
            self.code = has_matched.group(4)
            self.label = has_matched.group(6)
            self.repeatable = bool(int(has_matched.group(8)))
            self.mandatory = bool(int(has_matched.group(10)))
            self.ignored = has_matched.group(12) == "-1"
            self.auth_val = has_matched.group(14)
            self.value_builder = has_matched.group(16)
            self.max_length = int(has_matched.group(18))

    def uses_authorized_values(self) -> bool:
        """Returns if this subfield uses authorized values"""
        return self.auth_val != ""
    
class Field(object):
    # Koha 22.11, capturing groups :
    # 2 : tag, 4 : Label intranet, 6 : repeatable
    # 8 : mandatory, 10 : authorized value
    # pattern :
    #   - Start with : (")
    #   - Get value with : ([^\"]*)
    #   - Skip X field with : (",(?:"[^\"]*",){X}")
    #   - End with : (".*)
    # Yes sometimes it's excessive but it's easier to use the same strcuture
    pattern = r'^(")([^\"]*)(",(?:"[^\"]*",){0}")([^\"]*)(",(?:"[^\"]*",){1}")([^\"]*)(",(?:"[^\"]*",){0}")([^\"]*)(",(?:"[^\"]*",){1}")([^\"]*)(".*)'

    def __init__(self, csv_line:str) -> None:
        self.valid = False
        has_matched = re.match(self.pattern, csv_line)
        if has_matched:
            self.valid = True
            self.tag = has_matched.group(2)
            self.label = has_matched.group(4)
            self.repeatable = bool(int(has_matched.group(6)))
            self.mandatory = bool(int(has_matched.group(8)))
            self.auth_val = has_matched.group(10)
            self.subfields:Dict[str, Subfield] = {}
            self.non_repeatable_subfields:List[Subfield] = []
            self.controlfield = int(self.tag) < 10

    def is_control_field(self) -> bool:
        """Returns if this field is a control field"""
        return self.controlfield

    def add_subfield(self, subf:Subfield):
        """Adds a subfield to this field list"""
        self.subfields[subf.code] = subf
        if not subf.repeatable:
            self.non_repeatable_subfields.append(subf)

    def is_code_valid(self, code:str) -> bool:
        """Returns if a code is a valid code for this field"""
        return code in self.subfields
    
    def get_subfield_from_code(self, code:str) -> Subfield:
        """Returns the subfield for this code"""
        if not code in self.subfields:
            return None
        return self.subfields[code]

MAPPED_FIELDS:Dict[str, Field] = {}
MANDATORY_FIELDS:List[Field] = []
MANDATORY_SUBFIELDS:List[Subfield] = []
NON_REPEATABLE_FIELDS:List[Field] = []

# ----- Control values -----
class Controled_Value(object):
    def __init__(self, tag:str, xml_subf:ET.Element) -> None:
        self.tag = tag
        self.code = xml_subf.attrib["code"]
        self.start_position = -1
        self.end_position = -1
        if "startPosition" in xml_subf.attrib:
            if re.match(r"^\d+$", xml_subf.attrib["startPosition"]):
                self.start_position = int(xml_subf.attrib["startPosition"])
        if "endPosition" in xml_subf.attrib:
            if re.match(r"^\d+$", xml_subf.attrib["endPosition"]):
                self.end_position = int(xml_subf.attrib["endPosition"])
        self.values = {}
        for xml_val in xml_subf.findall("value"):
            if "name" in xml_val.attrib:
                self.values[xml_val.attrib["value"]] = xml_val.attrib["name"]
            else:
                self.values[xml_val.attrib["value"]] = xml_val.attrib["value"]

    def is_valid_val(self, val:str):
        """Returns if this value is part of the values"""
        return val in self.values
    
    def get_start_position(self) -> int:
        """Returns the start position (None if none)"""
        if self.start_position == -1:
            return None
        return self.start_position
    
    def get_end_position(self) -> int:
        """Returns the end position (None if no start position, start_position+1 if onyl strat position)"""
        if self.start_position == -1:
            return None
        if self.start_position > -1 and self.end_position == -1:
            return self.start_position + 1
        return self.end_position + 1

CONTROLED_VALUES:List[Controled_Value] = []

# ----- Error handling def -----
class Errors(Enum):
    CHUNK_ERROR = 0
    NO_RECORD_ID = 1
    # Analysis errors
    UNMAPPED_FIELD = 100
    UNMAPPED_SUBFIELD = 101
    MISSING_MANDATORY_FIELD = 102
    MISSING_MANDATORY_SUBFIELD = 103
    NON_REPEATABLE_FIELD = 104
    NON_REPEATABLE_SUBFIELD = 105
    ILLEGAL_AUTHORIZED_VALUE = 106
    MISSING_FIELD_WITH_MANDATORY_SUBFIELD = 107
    EMPTY_SUBFIELD = 108
    SUBFIELD_CONTENT_IS_ONLY_WHITESPACE = 109
    ILLEGAL_CONTROLED_VALUE = 110
    DATAFIELD_WITHOUT_SUBFIELD = 111

class Error_File_Headers(Enum):
    INDEX = "index"
    ID = "id"
    ERROR = "error"
    TXT = "error_message"
    DATA = "data"

class Error_obj(object):
    def __init__(self, index:int, id:str, error:Errors, txt:str, data:str) -> None:
        self.index = index
        self.id = id
        self.error = error
        self.txt = txt
        self.data = data
    
    def to_dict(self):
        return {
            Error_File_Headers.INDEX.value:self.index,
            Error_File_Headers.ID.value:self.id,
            Error_File_Headers.ERROR.value:self.error.name,
            Error_File_Headers.TXT.value:self.txt,
            Error_File_Headers.DATA.value:self.data
        }

class Error_File(object):
    def __init__(self, file_path:str) -> None:
        self.file = open(file_path, "w", newline="", encoding='utf-8')
        self.headers = []
        for member in Error_File_Headers:
            self.headers.append(member.value)
        self.writer = csv.DictWriter(self.file, extrasaction="ignore", fieldnames=self.headers, delimiter=";")
        self.writer.writeheader()

    def write(self, content:dict):
        self.writer.writerow(content)

    def close(self):
        self.file.close()

# ---------- Func def ----------

# ----- Authorized values -----

def get_auth_val_from_id(id:str) -> Authorized_Value:
    """Returns the Authorized_Value corresponding to this id"""
    if not id in AUTHORISED_VALUES:
        return None
    return AUTHORISED_VALUES[id]

def add_auth_val(id:str) -> Authorized_Value:
    """Create a new Authroized_Value for this id"""
    AUTHORISED_VALUES[id] = Authorized_Value(id)
    return AUTHORISED_VALUES[id]

# ----- Fields -----

def get_field_from_tag(tag:str) -> Field:
    """Returns the field corresponding to this tag"""
    if not tag in MAPPED_FIELDS:
        return None
    return MAPPED_FIELDS[tag]

def is_mapped_field(tag:str) -> bool:
    """Returns if field with this tag are mapped"""
    return get_field_from_tag(tag) != None

def add_field_to_mapped_fields(csv_line:str) -> Field:
    """Creates a new Field in mapped fields"""
    field = Field(csv_line)
    MAPPED_FIELDS[field.tag] = field
    return MAPPED_FIELDS[field.tag]

def add_subfield_to_field(csv_line:str) -> Subfield:
    """Creates a new subfield and adds it to it's field"""
    subf = Subfield(csv_line)
    get_field_from_tag(subf.tag).add_subfield(subf)
    return subf

# ----- Subfields -----

def get_subfield_from_tag_code(tag:str, code:str) -> Subfield:
    """Returns the subfield corerspondign to this code in this tag"""
    if not get_field_from_tag(tag):
        return None
    if not get_field_from_tag(tag).is_code_valid(code):
        return None
    return get_field_from_tag(tag).get_subfield_from_code(code)

# ----- Controled values -----
def add_controled_value(tag:str, xml_subf:ET.Element) -> Controled_Value:
    """Creates a new controled value and returns it"""
    cont_val = Controled_Value(tag, xml_subf)
    CONTROLED_VALUES.append(cont_val)
    return cont_val

def get_controled_values_for_tag_and_code(tag:str, code:str) -> List[Controled_Value]:
    """Returns all controeld values for these tag and code"""
    output = []
    for cont_val in CONTROLED_VALUES:
        if cont_val.tag == tag and cont_val.code == code:
            output.append(cont_val)
    return output

# ----- Errors -----

def trigger_error(index:int, id:str, error:Errors, txt:str, data:str, file:Error_File):
    """Trigger an error"""
    file.write(Error_obj(index, id, error, txt, data).to_dict())

# ----- Subfield analysis -----
def subfield_analysis(field:pymarc.field.Field, code:str, val:str, field_type:Field_Type, record_index:int):
    """Subfield analysis (field can only be a str if iot's the leader)"""
    # Leader & control field management
    tag = "000"
    if field_type != Field_Type.LEADER:
        tag = field.tag
    if field_type in [Field_Type.CONTROLFIELD, Field_Type.LEADER]:
        code = "@"
    
    # get mapepd field
    subf_obj = get_subfield_from_tag_code(tag, code)
    # Skip if unmapped field (already an errior at this point)
    if not subf_obj:
        return

    # Empty subfield
    if val == "":
        trigger_error(record_index, record_id, Errors.EMPTY_SUBFIELD, f"{tag} ${code}", str(field), ERRORS_FILE)
    # Whitespace only subfield content
    elif re.match("^\s+$", val):
        trigger_error(record_index, record_id, Errors.SUBFIELD_CONTENT_IS_ONLY_WHITESPACE, f"{tag} ${code}", str(field), ERRORS_FILE)

    # Authorised values
    if subf_obj.uses_authorized_values():
        if not get_auth_val_from_id(subf_obj.auth_val).is_valid_val(val):
            trigger_error(record_index, record_id, Errors.ILLEGAL_AUTHORIZED_VALUE, f"{tag} ${code} ({subf_obj.auth_val})", val, ERRORS_FILE)
    
    # Controled values
    for cont_val in get_controled_values_for_tag_and_code(tag, code):
        extracted_val = val[cont_val.get_start_position():cont_val.get_end_position()]
        if not cont_val.is_valid_val(extracted_val):
            position_err_msg = ""
            if not cont_val.get_start_position():
                pass
            elif cont_val.get_start_position() + 1 == cont_val.get_end_position():
                position_err_msg = f"position : {cont_val.get_start_position()}"
            else:
                position_err_msg = f"position : {cont_val.get_start_position()}-{cont_val.get_end_position()-1}"
            trigger_error(record_index, record_id, Errors.ILLEGAL_CONTROLED_VALUE, f"{tag} ${code} {position_err_msg}", extracted_val, ERRORS_FILE)


# ---------- Preparing Main ----------
MARC_READER = pymarc.MARCReader(open(RECORDS_FILE_PATH, 'rb'), to_unicode=True, force_utf8=True) # DON'T FORGET ME
ERRORS_FILE = Error_File(ERRORS_FILE_PATH) # DON'T FORGET ME

# ---------- Load authorised values ----------
with open(KOHA_AUTH_VAL_FILE, 'r') as f:
    reader = csv.DictReader(f, fieldnames=["category", "authorised_value", "lib", "lib_opac"], delimiter=";")
    next(reader) # Skip header line
    for row in reader:
        auth_val_val = Authorized_Value_Value(row["category"], row["authorised_value"], row["lib"], row["lib_opac"])
        auth_val = get_auth_val_from_id(auth_val_val.category)
        if not auth_val:
            auth_val = add_auth_val(auth_val_val.category)
        auth_val.add_value(auth_val_val)

# ---------- Load MARC framework ----------
is_first_page = True
with open(KOHA_MARC_FRAMEWORK_FILE, mode="r", encoding="utf-8") as f:
    for index, line in enumerate(f.readlines()):
        # Line separators : change type of data retrieved
        if '"#-#","#-#","#-#","#-#","#-#","#-#","#-#","#-#","#-#","#-#"' in line:
            is_first_page = False
            continue
        # Empty line : skip
        if len(line.split(",")) < 2:
            continue
        # headers : skip
        if '"tagfield"' in line and '"repeatable","mandatory","important"' in line:
            continue
        # Fields
        if is_first_page:
            mapped_field = add_field_to_mapped_fields(line)
            if mapped_field.mandatory:
                MANDATORY_FIELDS.append(mapped_field)
            if not mapped_field.repeatable:
                NON_REPEATABLE_FIELDS.append(mapped_field)
        # Subfields
        else:
            subfield = add_subfield_to_field(line)
            if subfield.mandatory and not subfield.ignored:
                MANDATORY_SUBFIELDS.append(subfield)

# ---------- Load controled values ----------
with open(CONTROL_VALUES_FILE, mode="r+", encoding="utf-8") as f:
    root = ET.fromstring(f.read())
    for xml_field in root.findall("field"):
        for xml_subf in xml_field.findall("subfield"):
            add_controled_value(xml_field.attrib["tag"], xml_subf)


# ---------- Main ----------
# Loop through records
for record_index, record in enumerate(MARC_READER):
    # If record is invalid
    if record is None:
        trigger_error(record_index, "", Errors.CHUNK_ERROR, "", "", ERRORS_FILE)
        continue # Fatal error, skipp

    # Gets the record ID
    record_id = record.get("001")
    if not record_id:
        # if no 001, check 035
        if not record.get("035"):
            trigger_error(record_index, "", Errors.NO_RECORD_ID, "No 001 or 035", "", ERRORS_FILE)
        elif not record.get("035").get("a"):
            trigger_error(record_index, "", Errors.NO_RECORD_ID, "No 001 or 035$a", "", ERRORS_FILE)
        else:
            record_id = record.get("035").get("a")

    # Mandatory fields
    for mandatory_f in MANDATORY_FIELDS:
        # Skip the leader
        if mandatory_f.tag == "000":
            continue
        
        if len(record.get_fields(mandatory_f.tag)) == 0:
            trigger_error(record_index, record_id, Errors.MISSING_MANDATORY_FIELD, mandatory_f.tag, "", ERRORS_FILE)

    # Non repeatable fields
    for non_repeatable_f in NON_REPEATABLE_FIELDS:
        if len(record.get_fields(non_repeatable_f.tag)) > 1:
            trigger_error(record_index, record_id, Errors.NON_REPEATABLE_FIELD, non_repeatable_f.tag, f"Nb : {len(record.get_fields(non_repeatable_f.tag))}", ERRORS_FILE)

    # Mandatory subfields
    for mandatory_subf in MANDATORY_SUBFIELDS:
        fields = record.get_fields(mandatory_subf.tag)
        if len(fields) == 0:
            trigger_error(record_index, record_id, Errors.MISSING_FIELD_WITH_MANDATORY_SUBFIELD, f"{mandatory_subf.tag} for ${mandatory_subf.code}", "", ERRORS_FILE)
        for field in fields:
            if mandatory_subf.code not in field.subfields_as_dict():
                trigger_error(record_index, record_id, Errors.MISSING_MANDATORY_SUBFIELD, f"{mandatory_subf.tag} ${mandatory_subf.code}", str(field), ERRORS_FILE)

    # Leader analysis
    subfield_analysis(record.leader, "", str(record.leader), Field_Type.LEADER, record_index)

    # Field analysis
    for field in record.fields:
        field:pymarc.field.Field # VS PLEASE DETECT THE TYPE AAAAAAAAAAAAAAAAAh
        # Unmapped fields
        if not is_mapped_field(field.tag):
            trigger_error(record_index, record_id, Errors.UNMAPPED_FIELD, field.tag, str(field), ERRORS_FILE)
            continue #Skip to next field

        # Controlfield content analysis
        if field.is_control_field():
            subfield_analysis(field, "", field.data, Field_Type.DATAFIELD, record_index)
            continue # No need to end the script
        else:
            if len(field.subfields) < 1:
                trigger_error(record_index, record_id, Errors.DATAFIELD_WITHOUT_SUBFIELD, field.tag, str(field), ERRORS_FILE)

        # Unmapped subfields
        for code in field.subfields_as_dict():
            if not get_field_from_tag(field.tag).is_code_valid(code):
                trigger_error(record_index, record_id, Errors.UNMAPPED_SUBFIELD, f"{field.tag} ${code}", str(field), ERRORS_FILE)
                continue # Skip to next subfield

            # Non repeatable subfield
            if not get_subfield_from_tag_code(field.tag, code).repeatable and len(field.subfields_as_dict()[code]) > 1:
                trigger_error(record_index, record_id, Errors.NON_REPEATABLE_SUBFIELD, f"{field.tag} ${code}", str(field), ERRORS_FILE)

        # Datafield subfield content analysis
        for subf in field.subfields:
            subfield_analysis(field, subf.code, subf.value, Field_Type.DATAFIELD, record_index)

MARC_READER.close()
ERRORS_FILE.close()