import cv2

print("📷 Scanning for available webcams...")
for index in range(5):
    cap = cv2.VideoCapture(index)
    if cap.read()[0]:
        print(f"✅ Camera found at index {index}")
        cap.release()
    else:
        print(f"❌ No camera at index {index}")
