import os
import json
import boto3

# Cloudflare R2 Credentials (GitHub Secrets ထဲမှ ယူသုံးမည်)
R2_ACCESS_KEY_ID = os.environ.get("R2_ACCESS_KEY_ID")
R2_SECRET_ACCESS_KEY = os.environ.get("R2_SECRET_ACCESS_KEY")
R2_BUCKET_NAME = os.environ.get("R2_BUCKET_NAME")
R2_ENDPOINT_URL = os.environ.get("R2_ENDPOINT_URL")
PUBLIC_R2_DOMAIN = "https://pub-18678a28a2634123aa1c63d0b4feca75.r2.dev"

s3 = boto3.client(
    's3',
    aws_access_key_id=R2_ACCESS_KEY_ID,
    aws_secret_access_key=R2_SECRET_ACCESS_KEY,
    endpoint_url=R2_ENDPOINT_URL
)

def generate_json():
    movies = []
    
    # R2 Bucket ထဲက ဖိုင်များကို ရယူခြင်း
    response = s3.list_objects_v2(Bucket=R2_BUCKET_NAME)
    
    if 'Contents' in response:
        # ဗီဒီယိုဖိုင်များကိုသာ စစ်ထုတ်ခြင်း (.mp4)
        videos = [obj for obj in response['Contents'] if obj['Key'].endswith('.mp4')]
        
        for video in videos:
            filename = video['Key'] # ဥပမာ - videos/MM/mm-collections/filename.mp4
            
            # ဖိုင်နာမည်မှ အလှပဆုံး ဇာတ်ကားနာမည် ဖန်တီးရန် (Extension ဖြုတ်ပြီး spaces ဖန်တီးခြင်း)
            base_filename = os.path.basename(filename).replace('.mp4', '')
            title = base_filename.replace('_', ' ').title()
            
            # Full Video URL
            video_url = f"{PUBLIC_R2_DOMAIN}/{filename}"
            
            # Thumb JPG URL (.thumb/ folder အောက်သို့ ချိတ်ဆက်ခြင်း)
            thumb_url = f"{PUBLIC_R2_DOMAIN}/.thumb/{base_filename}.jpg"
            
            created_at = video['LastModified'].isoformat()
            
            movies.append({
                "title": title,
                "genre": "mm-collections",
                "img": thumb_url,
                "video": video_url,
                "createdAt": created_at
            })
            
    # အသစ်ဆုံးများကို ရှေ့ဆုံးသို့ တင်ရန် (Latest First)
    movies.sort(key=lambda x: x['createdAt'], reverse=True)
    
    # movies.json ဖိုင်အဖြစ် ရေးသားခြင်း
    with open('movies.json', 'w', encoding='utf-8') as f:
        json.dump(movies, f, ensure_ascii=False, indent=4)
        
    print(f"Successfully generated movies.json with {len(movies)} movies from bucket '{R2_BUCKET_NAME}'!")

if __name__ == "__main__":
    generate_json()
