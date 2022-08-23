from PIL import Image as PILImage
import cv2
import base64


def expand2square(pil_img, background_color):
    width, height = pil_img.size
    if width == height:
        return pil_img
    elif width > height:
        result = PILImage.new(pil_img.mode, (width, width), background_color)
        result.paste(pil_img, (0, (width - height) // 2))
        return result
    else:
        result = PILImage.new(pil_img.mode, (height, height), background_color)
        result.paste(pil_img, ((height - width) // 2, 0))
        return result


def resize_image(self, image_type, image_path):
    """resize image based on previous image size
    and encoded base64 for input image
    """
    # load image
    img = cv2.imread(image_path, cv2.IMREAD_UNCHANGED)
    # scale down image
    scale_percent = 10  # percent of original size
    width = int(img.shape[1] * scale_percent / 100)
    height = int(img.shape[0] * scale_percent / 100)
    dim = (width, height)
    # resize image
    resized_image = cv2.resize(img, dim, interpolation=cv2.INTER_AREA)
    # get encode type
    encode_type = ".jpg" if image_type.lower() in ["jpg", "jpeg"] else ".png"
    # encode image
    encoded_image = cv2.imencode(encode_type, resized_image)[1]
    # encode image to base64
    encoded_image_base64 = str(base64.b64encode(encoded_image))[2:-1]
    return encoded_image_base64
