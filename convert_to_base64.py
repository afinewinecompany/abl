import base64

# Read the image file
with open('attached_assets/bg.png', 'rb') as image_file:
    encoded_string = base64.b64encode(image_file.read()).decode('utf-8')

# Save the base64 string to a file for later use
with open('bg_image_base64.txt', 'w') as text_file:
    text_file.write(encoded_string)

# Print first 50 and last 50 characters to verify
print(f"Success! Base64 conversion complete. Length: {len(encoded_string)} characters")
print(f"Preview: {encoded_string[:50]}...{encoded_string[-50:]}")