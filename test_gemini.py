from google import genai

client = genai.Client()
response = client.models.generate_content(
    model="gemini-3.8-flash",
    contents="Hello! Confirm you can read this travel project test.",
)
print("Response from Gemini:", response.text)
