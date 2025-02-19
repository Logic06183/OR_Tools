from PIL import Image, ImageDraw, ImageFont, ImageEnhance, ImageFilter
import os
import random
import math

def create_research_collage():
    # A4 size at 300 DPI
    width, height = 2480, 3508
    # Create a subtle gradient background
    collage = Image.new('RGB', (width, height), (248, 249, 250))
    
    # Get all images from the extracted_images folder
    image_folder = 'extracted_images'
    image_files = [f for f in os.listdir(image_folder) if f.endswith('.png')]
    print(f"\nTotal images found: {len(image_files)}")
    
    # Calculate grid parameters
    columns = 4      # 4 columns
    rows = 11        # Increased to 11 rows
    
    # Calculate margins and spacing
    margin_x = 90    # Slightly reduced margin
    margin_y = 100   # Reduced top margin
    spacing_x = 45   # Slightly reduced horizontal spacing
    spacing_y = 60   # Reduced vertical spacing
    
    cell_width = (width - (2 * margin_x) - (spacing_x * (columns - 1))) // columns
    cell_height = (height - (2 * margin_y) - (spacing_y * (rows - 1))) // rows
    
    # Priority images that must be included
    priority_images = ['slide32_shape3.png', 'slide55_shape1.png', 'slide60_shape3.png']
    
    # Process each image
    processed_images = []
    priority_processed = []
    skipped_images = []
    
    # Process priority images first
    for img_file in priority_images:
        if img_file in image_files:
            try:
                img_path = os.path.join(image_folder, img_file)
                img = Image.open(img_path)
                
                if img.mode != 'RGB':
                    img = img.convert('RGB')
                
                # Calculate aspect ratio preserving resize
                aspect = img.width / img.height
                if aspect > 1:
                    new_width = min(cell_width - 8, int(cell_height * aspect))
                    new_height = int(new_width / aspect)
                else:
                    new_height = min(cell_height - 8, int(cell_width / aspect))
                    new_width = int(new_height * aspect)
                
                # Enhanced image processing for priority images
                img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
                
                # Enhance image quality
                enhancer = ImageEnhance.Contrast(img)
                img = enhancer.enhance(1.15)
                enhancer = ImageEnhance.Sharpness(img)
                img = enhancer.enhance(1.2)
                
                # Create shadow with slightly more prominence
                shadow = Image.new('RGBA', (new_width + 10, new_height + 10), (0, 0, 0, 0))
                shadow_draw = ImageDraw.Draw(shadow)
                shadow_draw.rectangle([5, 5, new_width + 5, new_height + 5], fill=(0, 0, 0, 50))
                shadow = shadow.filter(ImageFilter.GaussianBlur(3))
                
                # Create background with very slight warm tint
                img_bg = Image.new('RGB', (new_width, new_height), (255, 254, 252))
                img_bg.paste(img, (0, 0))
                
                # Add refined border
                draw = ImageDraw.Draw(img_bg)
                draw.rectangle([0, 0, new_width-1, new_height-1], outline=(170, 170, 170), width=1)
                
                priority_processed.append((img_bg, shadow, new_width, new_height, img_file))
                
            except Exception as e:
                print(f"Error processing priority image {img_file}: {e}")
                skipped_images.append(img_file)
    
    # Process remaining images
    for img_file in image_files:
        if img_file not in priority_images:
            try:
                img_path = os.path.join(image_folder, img_file)
                img = Image.open(img_path)
                
                if img.mode != 'RGB':
                    img = img.convert('RGB')
                
                # Calculate aspect ratio preserving resize
                aspect = img.width / img.height
                if aspect > 1:
                    new_width = min(cell_width - 10, int(cell_height * aspect))
                    new_height = int(new_width / aspect)
                else:
                    new_height = min(cell_height - 10, int(cell_width / aspect))
                    new_width = int(new_height * aspect)
                
                # Resize image with high-quality settings
                img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
                
                # Enhance image slightly
                enhancer = ImageEnhance.Contrast(img)
                img = enhancer.enhance(1.1)
                enhancer = ImageEnhance.Sharpness(img)
                img = enhancer.enhance(1.1)
                
                # Create slightly larger shadow for more depth
                shadow = Image.new('RGBA', (new_width + 8, new_height + 8), (0, 0, 0, 0))
                shadow_draw = ImageDraw.Draw(shadow)
                shadow_draw.rectangle([4, 4, new_width + 4, new_height + 4], fill=(0, 0, 0, 45))
                shadow = shadow.filter(ImageFilter.GaussianBlur(3))
                
                # Create a white background with very slight warm tint
                img_bg = Image.new('RGB', (new_width, new_height), (255, 254, 252))
                img_bg.paste(img, (0, 0))
                
                # Add refined border
                draw = ImageDraw.Draw(img_bg)
                draw.rectangle([0, 0, new_width-1, new_height-1], outline=(180, 180, 180), width=1)
                
                processed_images.append((img_bg, shadow, new_width, new_height, img_file))
                
            except Exception as e:
                print(f"Error processing {img_file}: {e}")
                skipped_images.append(img_file)
    
    # Combine priority and regular images
    processed_images = priority_processed + processed_images
    
    # Sort non-priority images by size
    processed_images[len(priority_processed):] = sorted(
        processed_images[len(priority_processed):],
        key=lambda x: (x[2] * x[3]),
        reverse=True
    )
    
    # Track included and excluded images
    included_images = []
    excluded_images = []
    
    # Place images on the canvas
    images_placed = 0
    for row in range(rows):
        for col in range(columns):
            if images_placed >= len(processed_images):
                break
                
            img, shadow, img_width, img_height, img_file = processed_images[images_placed]
            
            # Calculate position
            x = margin_x + (col * (cell_width + spacing_x))
            y = margin_y + (row * (cell_height + spacing_y))
            
            # Center image in its cell
            x_offset = (cell_width - img_width) // 2
            y_offset = (cell_height - img_height) // 2
            
            # Paste shadow first
            collage.paste(shadow, (x + x_offset - 4, y + y_offset - 4), shadow)
            # Then paste image
            collage.paste(img, (x + x_offset, y + y_offset))
            
            included_images.append(img_file)
            images_placed += 1
    
    # Track excluded images
    excluded_images = [img_file for img_file in image_files if img_file not in included_images]
    
    # Save with high quality
    output_path = 'wits_climate_research_collage.png'
    collage.save(output_path, 'PNG', quality=95, dpi=(300, 300))
    
    # Print summary
    print(f"\nCollage created with {images_placed} images")
    print("\nIncluded images:")
    for idx, img in enumerate(included_images, 1):
        print(f"{idx}. {img}")
    
    print("\nExcluded images:")
    for idx, img in enumerate(excluded_images, 1):
        print(f"{idx}. {img}")
    
    if skipped_images:
        print("\nSkipped images (due to errors):")
        for idx, img in enumerate(skipped_images, 1):
            print(f"{idx}. {img}")

if __name__ == "__main__":
    create_research_collage()
