# -*- coding: utf-8 -*-
# @Time    : 2024/1/21 上午12:22
# @Author  : sudoskys
# @File    : __init__.py.py
# @Software: PyCharm
import numpy as np
import onnxruntime
from PIL import Image
from scipy.special import softmax


def predict_image(image_path):
    model_path = "anime_or_not_model.onnx"
    ort_session = onnxruntime.InferenceSession(model_path)

    # Open the image
    img = Image.open(image_path)
    width, height = img.size
    assert width > 224 and height > 224, "Image should be at least 224x224"

    # Resize the image
    img = img.resize((224, 224))

    # Convert image to numpy array and normalize
    img_array = np.asarray(img, dtype=np.float32) / 255.0

    # Apply the mean and standard devation normalization
    img_array = (
        img_array - np.array([0.485, 0.456, 0.406], dtype=np.float32)
    ) / np.array([0.229, 0.224, 0.225], dtype=np.float32)

    # Transpose array from (HxWxC) to (CxHxW)
    img_array = np.transpose(img_array, (2, 0, 1))

    # Add a batch dimension
    img_array = np.expand_dims(img_array, axis=0)

    ort_inputs = {ort_session.get_inputs()[0].name: img_array}
    ort_outs = ort_session.run(None, ort_inputs)

    img.close()  # Close the image to free up memory

    t = np.array(ort_outs[0][0])
    return round(softmax(t)[1] * 100, 2)


if __name__ == "__main__":
    image_path = "666.png"
    prediction = predict_image(image_path)
    print(prediction)
