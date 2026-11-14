import cv2

def start_camera():
    # Open the default webcam
    camera = cv2.VideoCapture(0)

    # Check if the webcam opened successfully
    if not camera.isOpened():
        print("❌ Error: Could not open webcam.")
        return

    print("✅ Webcam started successfully!")
    print("Press 'Q' to quit.")

    while True:
        # Read a frame from the webcam
        success, frame = camera.read()

        if not success:
            print("❌ Failed to capture frame.")
            break

        # Display the frame
        cv2.imshow("Wield Camera", frame)

        # Exit when Q is pressed
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    # Release the camera and close all windows
    camera.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    start_camera()