import cloudinary
import cloudinary.uploader
import os

cloudinary.config(
    cloud_name="daqsvvw0g",
    api_key="817944749621721",
    api_secret="iDHQLyKi_o8OaNOgy1KQJDQpwBo"
)

media_dir = "media/products/"
for filename in os.listdir(media_dir):
    if filename.startswith("ChatGPT_Image"):
        filepath = os.path.join(media_dir, filename)
        print(f"Загружаю {filename}...")
        result = cloudinary.uploader.upload(
            filepath,
            folder="products",
            public_id=os.path.splitext(filename)[0]
        )
        print(f"✅ {filename} -> {result['secure_url']}")

print("Готово!")
