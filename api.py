from groq import Groq

client = Groq(api_key="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")

response = client.chat.completions.create(
    model="llama-3.3-70b-versatile",  # Updated model - newer and more capable
    messages=[
        {"role": "user", "content": "Say 'API working' in one line"}
    ],
)

print(" Response:", response.choices[0].message.content)