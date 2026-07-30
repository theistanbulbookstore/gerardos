from google import genai

client = genai.Client()

print("Available models on your API key:")
for m in client.models.list():
    if "generateContent" in m.supported_actions:
        print(f" - {m.name}")