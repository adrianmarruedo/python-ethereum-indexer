from datetime import datetime
from typing import List, Tuple, Any
from pydantic import BaseModel
from web3 import Web3


web3 = Web3()


class Argument(BaseModel):
    name: str
    type: str
    value: Any


class ABIArgument(BaseModel):
    parameter_name: str
    parameter_type: str


def chunk_string(string, length):
    return (string[0 + i: length + i] for i in range(0, len(string), length))


def split_to_words(data):
    if data and len(data) > 2:
        data_without_0x = data[2:]
        words = list(chunk_string(data_without_0x, 64))
        words_with_0x = list(map(lambda word: "0x" + word, words))
        return words_with_0x
    return []


def to_normalized_address(address):
    if address is None or not isinstance(address, str):
        return address
    return address.lower()


def word_to_address(param):
    if param is None:
        return None
    elif len(param) >= 40:
        return to_normalized_address("0x" + param[-40:])
    else:
        return to_normalized_address(param)


def decode_array(data: List[str], position: int, type: str):
    result = []
    count = int(web3.toInt(hexstr=data[position]), 16)

    for i in range(count):
        if type == "uint256":
            result.append(web3.toInt(hexstr=data[position + i + 1]))
        else:
            raise Exception(f"Unsupported type {type}")

    return count + 1, result


def get_input_field_data(data: List[str], position: int, type: str) -> Tuple:
    if type == "address":
        return position + 1, word_to_address(data[position])
    elif type == "uint256":
        return position + 1, web3.toInt(hexstr=data[position])
    elif type == "bytes":
        return position + 1, word_to_address(data[position])
    elif type == "uint256[]":
        addition, array = decode_array(data, position, "uint256")
        return position + addition, array
    else:
        raise Exception("Type not supported")


# helper function to decode an argument value based on expected type
def decode_static_argument(raw_value, argument_type):

    if not raw_value:
        return raw_value

    decoded_value = raw_value

    if argument_type == "address":
        if len(raw_value) >= 40:
            decoded_value = "0x" + raw_value[-40:]
        else:
            decoded_value = raw_value

    elif argument_type[:4] == "uint":
        if isinstance(raw_value, str):
            decoded_value = int(raw_value, 16)
        else:
            decoded_value = raw_value

    elif argument_type[:3] == "int":
        if isinstance(raw_value, str):
            decoded_value = int(raw_value, 16)
            if decoded_value & (1 << (256 - 1)):
                decoded_value -= 1 << 256
        else:
            decoded_value = raw_value

    elif argument_type == "bool":
        if int(raw_value, 16) == 0:
            decoded_value = "False"
        else:
            decoded_value = "True"

    elif argument_type == "bytes":
        decoded_value = "0x" + bytes.fromhex(raw_value[2:]).hex()

    elif argument_type[:5] == "bytes":
        if raw_value.startswith("0x"):
            decoded_value = raw_value
        else:
            decoded_value = "0x" + raw_value

    elif argument_type == "byte":
        decoded_value = "0x" + bytes.fromhex(raw_value[2:])[0].hex()

    elif argument_type in ("string", "string32"):
        try:
            if raw_value[:2] == "0x":
                raw_value = raw_value[2:]
            decoded_value = bytes.fromhex(raw_value).decode("utf-8").replace("\x00", "")
        except Exception:
            return raw_value

    elif argument_type == "timestamp":
        if isinstance(raw_value, str):
            decoded_value = str(datetime.utcfromtimestamp(int(raw_value, 16)))
        else:
            decoded_value = str(datetime.utcfromtimestamp(raw_value))

    elif argument_type == "hashmap":
        decoded_value = "[...]"
    elif argument_type == "tuple":
        decoded_value = "(...)"
    elif argument_type == "tuple[]":
        decoded_value = "(...)[]"

    return decoded_value


def funtion_map_to_abi_args(function_map):
    fields = function_map["inputs"]
    types = function_map["types"]
    if len(fields) != len(types):
        raise Exception(
            "Wrong Function Mapper. Lenght of 'inputs' and 'types' doesn't match"
        )

    argument_abi = []
    for i in range(len(fields)):
        argument_abi.append(
            ABIArgument(parameter_name=fields[i], parameter_type=types[i])
        )
    return argument_abi


# helper function to decode ABI 2.0
def decode_tuple(data, argument_abi, is_list):
    slots = 0

    if is_list:
        count = int(data[:64], 16)
        data = data[64:]
        decoded_argument = []

        for c in range(count):
            do_offset = any(a.dynamic for a in argument_abi)
            if do_offset:
                raw_value = data[c * 64 : (c + 1) * 64]
                offset = int(raw_value, 16) * 2
                sub_bytes = data[offset:]
            else:
                sub_bytes = data

            decoded, num = decode_struct(sub_bytes, argument_abi)
            for i, parameter in enumerate(decoded):
                decoded[i] = Argument(**parameter)
            decoded_argument.append(decoded)
            slots += num

    else:
        decoded_argument, num = decode_struct(data, argument_abi)
        for i, parameter in enumerate(decoded_argument):
            decoded_argument[i] = Argument(**parameter)
        slots += num

    return decoded_argument, slots


# helper function to decode dynamic arrays
def decode_dynamic_array(data, array_type):
    count = int(data[:64], 16) if data else 0
    sub_data = data[64:]
    decoded_argument = []

    for i in range(count):
        if array_type in ("bytes", "string"):
            offset = int(sub_data[64 * i : 64 * (i + 1)], 16) * 2
            decoded = decode_dynamic_argument(sub_data[offset:], array_type)
        else:
            offset = 64 * i
            if offset >= len(sub_data):
                break
            decoded = decode_static_argument(sub_data[offset : offset + 64], array_type)

        decoded_argument.append(decoded)

    return decoded_argument


# helper function to decode a dynamic argument
def decode_dynamic_argument(argument_bytes, argument_type):
    if len(argument_bytes):
        length = int(argument_bytes[:64], 16) * 2
        value = argument_bytes[64 : 64 + length]

        if argument_type == "string":
            hex_bytes = bytes.fromhex(value)
            decoded_value = hex_bytes.decode("utf-8", "ignore").replace("\x00", "")
        else:
            decoded_value = "0x" + value
    else:
        decoded_value = bytes(0).decode()

    return decoded_value


# helper function to decode ABI 2.0 structs
def decode_struct(data, arguments_abi):
    def decode_array(raw_value, argument_type, slot):

        array_type = argument_type.rsplit("[", 1)[0]
        if argument_type[-2:] == "[]":
            offset = int(raw_value, 16) * 2 if raw_value else 0
            array_values = decode_dynamic_array(data[offset:], array_type)
            slot += 1
        else:
            array_size = int(argument_type[:-1].split("[")[-1])
            array_values = []
            for _ in range(array_size):
                if array_type[-1] == "]":
                    array_subvalues, slot = decode_array(raw_value, array_type, slot)
                    array_values.append(array_subvalues)
                else:
                    array_values.append(decode_static_argument(raw_value, array_type))
                    slot += 1
                raw_value = data[slot * 64 : (slot + 1) * 64]

        return array_values, slot

    if arguments_abi:
        no_arguments = len(arguments_abi)
    else:
        no_arguments = len(data) // 64 + 1

    arguments_list = []
    slot = 0
    for i in range(no_arguments):
        raw_value = data[slot * 64: (slot + 1) * 64]

        if arguments_abi:

            argument_name = arguments_abi[i].parameter_name
            argument_type = arguments_abi[i].parameter_type

            if argument_type[:5] == "tuple":
                do_offset = arguments_abi[i].dynamic or any(
                    a.dynamic for a in arguments_abi[i].components
                )
                if do_offset:
                    offset = int(raw_value, 16) * 2
                    sub_arguments = data[offset:]
                else:
                    sub_arguments = data[i * 64 :]

                argument_value, slots = decode_tuple(
                    sub_arguments,
                    arguments_abi[i].components,
                    argument_type[5:] == "[]",
                )

                if do_offset:
                    slot += 1
                else:
                    slot += slots

            elif argument_type in ("bytes", "string"):
                offset = int(raw_value, 16) * 2 if raw_value else 0
                argument_value = decode_dynamic_argument(data[offset:], argument_type)
                slot += 1

            elif argument_type[-1:] == "]":
                argument_value, slot = decode_array(raw_value, argument_type, slot)

            else:
                argument_value = decode_static_argument(raw_value, argument_type)
                slot += 1
        else:
            argument_name = f"arg_{i + 1}"
            argument_type = "unknown"
            argument_value = "0x" + raw_value

        if argument_type != "unknown" or argument_value != "0x":
            arguments_list.append(
                dict(name=argument_name, type=argument_type, value=argument_value)
            )

    return arguments_list, slot
