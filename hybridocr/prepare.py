from core import *
from PIL import Image, ImageFilter
import numpy as np
import cv2

file = Path(sys.argv[1])

img_arr = pdf_extract(file)

img = img_arr[0]
show_image(img)

img = img.convert("L")
show_image(img)

img = img.filter(ImageFilter.GaussianBlur(1))
show_image(img)

# threshold = 200
# binary_image = img.point(lambda p: p > threshold and 255)
# show_image(binary_image)
#
# cv_image = np.array(img)
# cv2.threshold(cv_image, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
# show_image(Image.fromarray(cv_image))

cv_image = np.array(img)

thresh = cv2.adaptiveThreshold(cv_image, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                cv2.THRESH_BINARY_INV, 11, 2)


contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

# Filter out contours that are too small or too large to be words
filtered_contours = [cnt for cnt in contours if cv2.contourArea(cnt) > 100 and cv2.contourArea(cnt) < 1000]

# Draw bounding boxes
for contour in filtered_contours:
    # Get the rectangle bounding the contour
    x, y, w, h = cv2.boundingRect(contour)
    # Draw the rectangle
    cv2.rectangle(cv_image, (x, y), (x+w, y+h), (0, 255, 0), 2)

show_image(Image.fromarray(cv_image))

