import os
import time
import ctypes
import struct
import results_pb2
import numpy as np
from PIL import Image


use_dongle = False # False: Use a token (see "token" below), True: Use a USB-Dongle that is plugged into the system
token = ""

example_image_file = ""

json_filename = "networkconfig_default.json"


# This function prints the returned integer value in hexadecimal
def print_formatted_return(function_name, retval, t = None):
  code = struct.pack('>i', retval).hex().upper()
  if t == None:
    print(function_name + " returned: " + code)
  else:
    print(function_name + " returned: " + code + " ({} s)".format(round(t, 4)))
  if code != "DE000000":
      exit()


# This function will be used to display the output image
def display_image(img_buffer, img_w, img_h, img_c):
  array = np.frombuffer(img_buffer, dtype=np.uint8, count=(img_w * img_h * img_c), offset=0)
  array.shape = (img_h, img_w, img_c) # h, w, c
  img = Image.fromarray(array)
  img.show()


# Add the current working directoy to the DLL search path
os.add_dll_directory(os.getcwd())

# Load the DLL
libdll = ctypes.cdll.LoadLibrary("denk.dll")

if use_dongle:
  retval = libdll.FindDongle()
  print_formatted_return("FindDongle", retval)
else:
  retval = libdll.TokenLogin(token.encode('utf-8'), b'\x00')
  print_formatted_return("TokenLogin", retval)

# Allocate a buffer for the model information
modelinfo = b'\x00' * 10000
modelinfo_size = ctypes.c_int(len(modelinfo))

# Read all model files in the "models" directory, write the model info into "buffer" (will be ignored in this example), select the CPU (-1) as the evaluation device
retval = libdll.ReadAllModels(b'models', modelinfo, ctypes.byref(modelinfo_size), -1)
print_formatted_return("ReadAllModels", retval)

# Set the JSON
with open(json_filename, 'rb') as file:
    json_data = file.read()
retval = libdll.SetDefaultJson(json_data, len(json_data))
print_formatted_return("SetDefaultJson", retval)

# Open the image file in the "read bytes" mode and read the data
with open(example_image_file, 'rb') as file:
    img_data = file.read()

# Allocate the variable for the dataset index
index = ctypes.c_int(0)

# Load the image data
retval = libdll.LoadImageData(ctypes.byref(index), img_data, len(img_data))
print_formatted_return("LoadImageData", retval)

# Evaluate the image
t1 = time.time()
retval = libdll.EvaluateImage(index)
t2 = time.time()
print_formatted_return("EvaluateImage", retval, t2 - t1)

# Process the features with the filters defined in the JSON
retval = libdll.ProcessFeatures(index)
print_formatted_return("ProcessFeatures", retval)

# Allocate a buffer for the results of the evaluation
results = b'\x00' * 100000
results_size = ctypes.c_int(len(results))

# Get the results of the evaluation
retval = libdll.GetResults(index, results, ctypes.byref(results_size))
print_formatted_return("GetResults", retval)

# Parse the results
results_proto = results_pb2.Results()
results_proto.ParseFromString(results[:results_size.value])

# Print some results
print()
for otpt in results_proto.output:
  for ftr in otpt.feature:
    print("Found {} at\tx = {}\tand y = {}".format(ftr.label, ftr.rect_x, ftr.rect_y))
print()

# To allocate the correct buffer size, the image dimensions will be taken from the original image
w = ctypes.c_int(0) # width
h = ctypes.c_int(0) # height
c = ctypes.c_int(0) # channels
retval = libdll.GetOriginalImageDimensions(index, ctypes.byref(w), ctypes.byref(h), ctypes.byref(c))
print_formatted_return("GetOriginalImageDimensions", retval)

# DrawBoxes will always return an RGB image
c.value = 3

image_buffer_size = w.value * h.value * c.value

# Allocate a buffer for the resulting image data
image = b'\x00' * image_buffer_size
image_size = ctypes.c_int(image_buffer_size)

# Get the image with drawn in boxes and segmentations
overlap_threshold = 1.0
alpha_boxes = 0.5
alpha_segmentations = 0.5

retval = libdll.DrawBoxes(index, ctypes.c_double(overlap_threshold), ctypes.c_double(alpha_boxes), ctypes.c_double(alpha_segmentations), image, ctypes.byref(image_size))
print_formatted_return("DrawBoxes", retval)

# Properly end the session
retval = libdll.EndSession()
print_formatted_return("EndSession", retval)

display_image(image, w.value, h.value, c.value)