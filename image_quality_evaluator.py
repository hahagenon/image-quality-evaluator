# public\images\20240102
# public\images\20240102\1107010827\2024-01-01T20_29_14.568Z-1.jpg
# public\images\20240102\1165100762\2024-01-01T21_07_08.033Z-1.jpg
# public\images\20240103\1011435681\2024-01-02T23_30_03.792Z-1.jpg
# public\images\20240103\1013869533\2024-01-03T00_11_46.922Z-1.jpg

import cv2
import numpy as np
import os
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont


def evaluate_image(image_path):
    img = cv2.imread(str(image_path))
    
    if img is None:
        return None, f"이미지를 읽을 수 없습니다: {image_path}"
    
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    brightness = np.mean(gray)
    laplacian = cv2.Laplacian(gray, cv2.CV_64F)
    sharpness = np.var(laplacian)
    contrast = gray.std()
    
    # 기존 평가
    brightness_status = "적정" if 58 < brightness < 200 else "부적절"
    sharpness_status = "선명" if sharpness > 50 else "흐림"
    contrast_status = "적정" if 40 < contrast < 80 else "부적절"
    
    # 새로운 필수 평가: 전체적인 어두움 검사
    dark_threshold = 40  # 이 값은 조정이 필요할 수 있습니다
    dark_pixel_ratio = np.sum(gray < dark_threshold) / gray.size
    darkness_status = "정상" if dark_pixel_ratio < 0.9 else "너무 어두움"
    
    result = f"밝기: {brightness:.2f} ({brightness_status})\n"
    result += f"선명도: {sharpness:.2f} ({sharpness_status})\n"
    result += f"대비: {contrast:.2f} ({contrast_status})\n"
    result += f"어두움 비율: {dark_pixel_ratio:.2f} ({darkness_status})"
    
    return img, result

def add_text_to_image(image, text):
    image_pil = Image.fromarray(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
    
    image_height = image.shape[0]
    bar_height = max(150, int(image_height * 0.3))
    font_size = max(20, int(image_height / 30))

    # 평가 결과 확인 (수정된 부분)
    is_too_dark = any("너무 어두움" in line for line in text.split('\n'))
    is_pass = not any("부적절" in line or "흐림" in line or "너무 어두움" in line for line in text.split('\n'))
    
    if is_too_dark:
        bar_color = (255, 165, 0)  # 주황색 (RGB)
        pass_text = "미통과: 필수 검사 필요!"
    elif is_pass:
        bar_color = (0, 0, 255)  # 파란색
        pass_text = "통과"
    else:
        bar_color = (255, 0, 0)  # 빨간색
        pass_text = "미통과"

    bar = Image.new('RGB', (image.shape[1], bar_height), color=bar_color)
    image_with_bar = Image.new('RGB', (image.shape[1], image.shape[0] + bar_height))
    image_with_bar.paste(bar, (0, 0))
    image_with_bar.paste(image_pil, (0, bar_height))

    draw = ImageDraw.Draw(image_with_bar)
    
    font_path = r"C:\Windows\Fonts\malgun.ttf"
    try:
        font = ImageFont.truetype(font_path, font_size)
    except IOError:
        print(f"폰트를 찾을 수 없습니다: {font_path}. 기본 폰트를 사용합니다.")
        font = ImageFont.load_default()

    y0 = int(bar_height * 0.1)
    dy = int(bar_height * 0.18)

    # 통과 여부 텍스트 추가
    draw.text((10, y0), pass_text, font=font, fill=(255, 255, 255))

    # 평가 결과 텍스트 추가
    for i, line in enumerate(text.split('\n'), start=1):
        y = y0 + i*dy
        draw.text((10, y), line, font=font, fill=(255, 255, 255))

    return cv2.cvtColor(np.array(image_with_bar), cv2.COLOR_RGB2BGR)

def process_folders(base_path, target_folders, output_base):
    for folder in target_folders:
        folder_path = Path(base_path) / folder
        if not folder_path.exists():
            print(f"폴더를 찾을 수 없습니다: {folder_path}")
            continue
        
        # jpg, jpeg, png 파일을 모두 처리
        for image_file in folder_path.glob('**/*.*'):
            if image_file.suffix.lower() in ['.jpg', '.jpeg', '.png']:
                img, result = evaluate_image(image_file)
                if img is None:
                    print(result)
                    continue
                
                img_with_text = add_text_to_image(img, result)
                
                # 원본 경로 구조를 유지하면서 출력 경로 생성
                relative_path = image_file.relative_to(base_path)
                output_path = output_base / relative_path
                output_path.parent.mkdir(parents=True, exist_ok=True)
                
                cv2.imwrite(str(output_path), img_with_text)
                print(f"평가된 이미지 저장됨: {output_path}")



# 기본 경로 설정
base_path = Path("public/images/")
output_base = Path("check_cv")

# 처리할 폴더 목록
target_folders = ['20240102', '20240103', '20240104']

# 폴더 처리 실행
process_folders(base_path, target_folders, output_base)
    