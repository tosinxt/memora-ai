from rembg.sessions import u2net
import os

# Create the model directory if it doesn't exist
model_dir = os.path.expanduser("~/.u2net")
os.makedirs(model_dir, exist_ok=True)

# Download the model
print("Downloading u2net model...")
u2net.download()
print("Model downloaded successfully!")
