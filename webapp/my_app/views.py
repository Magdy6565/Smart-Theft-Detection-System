# views.py

from django.shortcuts import render
from .forms import VideoForm
from .models import Video
from transformers import VivitForVideoClassification, VivitImageProcessor
import torch
from django.views.decorators.csrf import csrf_exempt
import cv2
import numpy as np
import torch
from transformers import VivitImageProcessor
# ----------------------------------------------------------------------------- #
# Load the model and processor
processor = VivitImageProcessor.from_pretrained("yehiawp4/ViViT-b-16x2-ShopLifting-Dataset")
model = VivitForVideoClassification.from_pretrained("yehiawp4/ViViT-b-16x2-ShopLifting-Dataset")
# ----------------------------------------------------------------------------- #

def home(request):
    print("Hello I am inside Home")
    return render(request, 'my_app/home.html')
# ----------------------------------------------------------------------------- #

def upload_video(request):
    print("Hello I am inside upload video")
    form = VideoForm()
    return render(request, 'my_app/upload.html', {'form': form})

# ----------------------------------------------------------------------------- #

def load_video_as_tensor(video_path, target_size=(224, 224), max_frames=32):
    """Load video and convert it to a tensor of shape (num_frames, num_channels, height, width)."""
    cap = cv2.VideoCapture(video_path)
    frames = []

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
        # Resize frame to the model's expected input size
        frame = cv2.resize(frame, target_size)
        # Convert frame to float and normalize to [0, 1]
        frame = frame.astype(np.float32) / 255.0  # Scale to [0, 1]
        frames.append(frame)

        # Limit the number of frames
        if len(frames) == max_frames:
            break

    cap.release()

    # Convert frames to a numpy array and then to a tensor
    video_tensor = torch.tensor(np.array(frames)).permute(0, 3, 1, 2) 
     # Shape: (num_frames, num_channels, height, width)

    # Add a batch dimension at the start
    video_tensor = video_tensor.unsqueeze(0)  # Now shape is (1, num_frames, 3, height, width)

    return video_tensor  # Return tensor of shape (1, 16, 3, height, width)

# ----------------------------------------------------------------------------- #

def run_inference(model, video_tensor):
    """Utility to run inference given a model and test video tensor."""
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model = model.to(device)
    video_tensor = video_tensor.to(device)

    # Forward pass
    with torch.no_grad():
        outputs = model(video_tensor)
        logits = outputs.logits

    return logits

# ----------------------------------------------------------------------------- #

@csrf_exempt  # Disable CSRF protection for this view
def detect_theft(request):
    result = None
    print("Hello I am here")
    print(f"The request method is {request.method}")

    if request.method == 'POST':
        print("Finally post")
        form = VideoForm(request.POST, request.FILES)
        if form.is_valid():
            print("form valid")
            video = form.save()
            video_path = video.video.path

            # Load the video and convert it to tensor
            video_tensor = load_video_as_tensor(video_path)

            # Check shape before inference
            print("Video tensor shape:", video_tensor.shape)

            # Run inference
            logits = run_inference(model, video_tensor)
            predicted_class_idx = logits.argmax(-1).item()

            # Interpret the result
            if predicted_class_idx == 1:  # Assuming 1 is for "Theft Detected"
                result = "Theft Detected"
            else:
                result = "No Theft Detected"

    return render(request, 'my_app/result.html', {'result': result})
