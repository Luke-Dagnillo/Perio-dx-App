import numpy as np
import cv2


# DEFINES
RELATIVE_SCALE_FACTOR = 0.0006  # for text relative scale factor, A smaller value will produce smaller text, and vice versa
MIN_AREA_PRCENTAGE = 0.0015 # for minimum area threshold for intensity categorization


class RedRecognition:
    def __init__(self, image_path):
        self.image = cv2.imread(image_path)
        self.original_copy = self.image.copy()

    def apply_blur(self):
        self.blurred_image = cv2.GaussianBlur(self.image, (5, 5), 0)

    def convert_to_hsv(self):
        self.hsv_image = cv2.cvtColor(self.blurred_image, cv2.COLOR_BGR2HSV)

    def create_red_masks(self):
        # Define the range for the first red region (0-7)
        red_lower1 = np.array([0, 50, 50], np.uint8)
        red_upper1 = np.array([7, 255, 255], np.uint8)
        red_mask1 = cv2.inRange(self.hsv_image, red_lower1, red_upper1)

        # Define the range for the second red region (165-180)
        red_lower2 = np.array([165, 50, 50], np.uint8)
        red_upper2 = np.array([180, 255, 255], np.uint8)
        red_mask2 = cv2.inRange(self.hsv_image, red_lower2, red_upper2)

        # Combine the masks for the full range of red
        self.full_red_mask = cv2.bitwise_or(red_mask1, red_mask2)
            

    def dilate_masks(self):
        # Morphological Transform, Dilation
        # bitwise_and operator between image and mask determines
        # to detect only that particular color
        kernel = np.ones((5, 5), "uint8")
            
        # For red color
        self.full_red_mask = cv2.dilate(self.full_red_mask, kernel)
        self.res_red = cv2.bitwise_and(self.image, self.image, mask = self.full_red_mask)
        

    def find_and_categorize_contours(self):
        # Find contours in the red mask
        contours, _ = cv2.findContours(self.full_red_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE) 

        # Determine the minimum area threshold
        # This could be a fixed value or a percentage of the image area
        # For example, 0.5% of the image area:
        min_area_threshold = self.image.shape[0] * self.image.shape[1] * MIN_AREA_PRCENTAGE   

        # Filter contours by area
        self.large_contours = [cnt for cnt in contours if cv2.contourArea(cnt) > min_area_threshold]

        # Initialize a list to store the categories of red
        self.red_categories = []
        self.mean_saturations = []

        self.contour_areas = []

        # Iterate through the contours and categorize each red region
        for contour in self.large_contours:

            # Create a mask for the current contour
            mask_roi = np.zeros_like(self.hsv_image)
            cv2.drawContours(mask_roi, [contour], -1, (255, 255, 255), thickness=cv2.FILLED)

            mean_saturation = np.mean(np.array(self.hsv_image[:, :, 1][mask_roi[:, :, 0] == 255], dtype=np.float32))

            category = self.saturation_categorize(mean_saturation)
            
            self.red_categories.append(category)
            self.mean_saturations.append(mean_saturation)

            self.add_text_to_image(contour, category)

            # Calculate and store the area of each contour and its category
            contour_area = cv2.contourArea(contour)
            category = self.saturation_categorize(mean_saturation)
            self.contour_areas.append((contour, contour_area, category))

            

    def add_text_to_image(self, contour, category):
        # Get the resolution of the image for scaling the font
        image_height, image_width = self.image.shape[:2]

        # Calculate the font scale based on image width
        font_scale = RELATIVE_SCALE_FACTOR * image_width

        # Define font color and thickness
        font_color = (0, 255, 0)  # Green color
        font_thickness = 1  # Adjust thickness as needed
        font = cv2.FONT_HERSHEY_SIMPLEX

        # Find the center of the contour to place the text
        M = cv2.moments(contour)
        if M["m00"] != 0:
            cX = int(M["m10"] / M["m00"])
            cY = int(M["m01"] / M["m00"])
        else:
            # If the moment "m00" is zero, avoid division by zero
            cX, cY = 0, 0

        # Use cv2.putText() to label the contour
        cv2.putText(self.image, category, (cX - 20, cY), font, font_scale, font_color, font_thickness)

    
    def saturation_categorize(self, saturation):
        # Categorize based on saturation threshold values
        if saturation >= 200:
            return "High"
        elif saturation >= 125:
            return "Medium"
        else:
            return "Low"


    def get_largest_contour_info(self):
        if not self.contour_areas:
            return None

        # Find the contour with the maximum area
        largest_contour, _, category = max(self.contour_areas, key=lambda x: x[1])

        return "test_antigen", category
   

    def display_results(self):
        # print results to terminal
        for i, (category, mean_saturation) in enumerate(zip(self.red_categories, self.mean_saturations)):
            print(f"Region {i + 1}: Category: {category} Saturation, Mean Saturation: {mean_saturation:.2f}")

        # Set the window name and initial window size
        cv2.namedWindow('Original Image', cv2.WINDOW_NORMAL)  # WINDOW_NORMAL allows resizing
        cv2.namedWindow('HSV Image', cv2.WINDOW_NORMAL)
        cv2.namedWindow('Original Image (Only Red Areas)', cv2.WINDOW_NORMAL)
        cv2.namedWindow('Red Mask', cv2.WINDOW_NORMAL)
        cv2.namedWindow('Original Image w/ Contours', cv2.WINDOW_NORMAL)

        # Display the images with the applied masks and contours
        cv2.drawContours(self.image, self.large_contours, -1, (0, 255, 0), 2)
        cv2.imshow('HSV Image', self.hsv_image)
        cv2.imshow('Original Image w/ Contours', self.image)
        cv2.imshow('Original Image (Only Red Areas)', self.res_red)
        cv2.imshow("Red Mask", self.full_red_mask)
        cv2.imshow('Original Image', self.original_copy)

        cv2.waitKey(0)
        cv2.destroyAllWindows()


    def run(self):
        self.apply_blur()
        self.convert_to_hsv()
        self.create_red_masks()
        self.dilate_masks()
        self.find_and_categorize_contours()
        # self.display_results() # only display results for testing purposes

        # Get and return the largest contour
        return self.get_largest_contour_info()



# red_recognizer = RedRecognition('test_images/lab_test2.jpeg')
# result = red_recognizer.run()

# if result is not None:
#     largest_contour, category = result
#     print("Largest contour category:", category)
#     print("Largest contour area:", cv2.contourArea(largest_contour))
# else:
#     print("No contours found.")