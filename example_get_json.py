import os
import ctypes
import struct
import json

token = ""

# This function prints the returned integer value as hexadecimal
def print_formatted_return(function_name, retval, t = None):
  code = struct.pack('>i', retval).hex().upper()
  if t == None:
    print(function_name + " returned: " + code)
  else:
    print(function_name + " returned: " + code + " ({} s)".format(t))
  if code != "DE000000":
      exit()


# Add the current working directoy to the DLL serch path
os.add_dll_directory(os.getcwd())

# Load the DLL
libdll = ctypes.cdll.LoadLibrary("denk.dll")

retval = libdll.TokenLogin(token.encode('utf-8'), b'\x00')
print_formatted_return("TokenLogin", retval)

# Allocate a buffer for the model information
modelinfo = b'\x00' * 10000
modelinfo_size = ctypes.c_int(len(modelinfo))
modelinfo_size_pnt = ctypes.pointer(modelinfo_size)

# Read all model files in the "models" directory, write the model info into "buffer" (will be ignored in this example), select the CPU (-1) as the evaluation device
retval = libdll.ReadAllModels(b'models', modelinfo, modelinfo_size_pnt, -1)
print_formatted_return("ReadAllModels", retval)


# Get the default JSON
buffer1_size = ctypes.c_int(1000000)
buffer1 = b'\x00' * buffer1_size.value
retval = libdll.GetDefaultJson(buffer1, ctypes.byref(buffer1_size))
print_formatted_return("GetDefaultJson", retval)

default_json = json.loads(buffer1[:buffer1_size.value].decode('utf-8'))

with open("networkconfig_default.json", 'w') as file:
  json.dump(default_json, file, indent=2)


# Add entries for the loaded networks
buffer2_size = ctypes.c_int(1000000)
buffer2 = b'\x00' * buffer2_size.value
retval = libdll.CreateJsonEntries(buffer1, buffer1_size.value, buffer2, ctypes.byref(buffer2_size))
print_formatted_return("CreateJsonEntries", retval)

default_json_with_models = json.loads(buffer2[:buffer2_size.value].decode('utf-8'))

with open("networkconfig_default_with_models.json", 'w') as file:
  json.dump(default_json_with_models, file, indent=2)