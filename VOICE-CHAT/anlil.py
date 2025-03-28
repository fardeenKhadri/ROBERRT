import cv2
import requests
from together import Together
import base64
API_KEY = '99c0398a7d67df14aa70ab08597fd43e779736922611c10e9a76c773544d02b3'
client = Together(api_key=API_KEY)
def send_frame_to_together(frame):
    _, buffer = cv2.imencode('.jpg', frame)
    image_bytes = buffer.tobytes()
    image_b64 = base64.b64encode(image_bytes).decode('utf-8')
    payload = {
        "model": "meta-llama/Llama-Vision-Free",
        "messages": [
            # prompting karo bhao
            {"role": "system", "content": "Provide analysis for the following image."},
            {"role": "user", "content": [{"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_b64}"}}]}]}
    response = client.chat.completions.create(**payload)                                                                        
    if response and response.choices:
        print(response.choices[0].message.content)
    else:
        print("No response received or error occurred.")
cap = cv2.VideoCapture(0)
while True:
    ret, frame = cap.read()
    if not ret:
        break
    cv2.imshow('Live Camera Feed', frame)
    send_frame_to_together(frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break
cap.release()
cv2.destroyAllWindows()