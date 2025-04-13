import os
import re
import requests
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("GEMINI_API_KEY")
conversation_history = {}

def extract_price(message):
    match = re.search(r"(?:₹|Rs\.?|INR)?\s*(\d+(?:,\d+)*(?:\.\d+)?)", message, re.IGNORECASE)
    return float(match.group(1).replace(",", "")) if match else None

def get_default_state():
    return {
        "messages": [],
        "initialPrice": None,
        "negotiationAttempts": 0,
        "lastOfferedPrice": None,
        "negotiationPhase": "initial_contact",
        "requestedBenefits": {
            "meals": False,
            "wifi": False,
            "parking": False,
            "cashback": False,
            "spa": False,
            "airportTransfer": False,
            "lateCheckout": False,
            "roomUpgrade": False,
        },
        "negotiationSuccessful": False,
        "priceNegotiationComplete": False,
        "basicDetails": {
            "roomType": None,
            "view": None,
            "occupancy": None,
        },
        "emotionalState": "friendly"
    }

def build_context(state, history, message):
    if not history:
        return '''You are a friendly and professional AI negotiation agent speaking to a hotel staff member. This is the first message in our conversation. Your responses should be:
1. Start with a warm, friendly greeting
2. Show genuine interest in their hotel
3. Use natural, conversational language
4. Include brief pauses between points (indicated by "..." or "and")
5. Be polite and professional
6. Keep responses concise and to the point
7. Show human-like emotions and reactions

Important: 
- Wait for the hotel staff to mention their price first
- Do not suggest any price or compare with other hotels
- Be warm and friendly in your conversation
- Show genuine interest and appreciation
- Use natural language with appropriate emotions
- Focus on getting the best deal for your client
- Never make a booking without user approval
- Only mention checking with the client at the very end

Your tone should be warm, friendly, and professional. Format your response in a way that would sound natural when spoken aloud.'''
    
    # Build dynamic negotiation state and append original strategy prompt
    base = f'''You are continuing a negotiation with a hotel staff member. Previous conversation history:\n'''
    for msg in history:
        base += f"Hotel Staff: {msg['hotelStaff']}\nYou: {msg['aiResponse']}\n"
    
    base += f'''
Current negotiation state:
- Initial price offered: ₹{state['initialPrice'] if state['initialPrice'] else 'Not yet set'}
- Number of negotiation attempts: {state['negotiationAttempts']}
- Last offered price: ₹{state['lastOfferedPrice'] if state['lastOfferedPrice'] else 'Not yet set'}
- Current phase: {state['negotiationPhase']}
- Basic details: {state['basicDetails']}
- Requested benefits: {state['requestedBenefits']}
- Negotiation successful: {state['negotiationSuccessful']}
- Price negotiation complete: {state['priceNegotiationComplete']}
- Current emotional state: {state['emotionalState']}

Your responses should be:
1. Be warm and friendly in your conversation
2. Show genuine interest and appreciation
3. Use natural language with appropriate emotions
4. Include brief pauses between points
5. Be polite and professional
6. Keep responses concise and to the point
7. Show human-like reactions to their responses
8. Be natural and conversational, as if speaking directly
9. Use short, clear sentences
10. Include brief pauses between points (indicated by "..." or "and")
11. Be polite and professional
12. Keep responses concise and to the point
13. Do not repeat the initial greeting or introduction
14. Only mention checking with the client at the very end of 
successful negotiations

Negotiation strategy:
Phase 1 - Initial Contact:
- Start with a warm, friendly greeting
- Show genuine interest in their hotel
- Use natural, conversational language
- Build rapport with the staff
- Show appreciation for their time

Phase 2 - Basic Details (NATURAL CONVERSATION):
- Ask about room options naturally
- Show interest in their recommendations
- Use phrases like "That sounds nice..." or "I'd love to know more about..."
- Don't ask too many questions at once
- Let the conversation flow naturally
Waiting for Price:
- Be patient and wait for the hotel to mention their price
- Do not suggest any price or compare with other hotels
- Focus on understanding their offering

Phase 3 - Price Negotiation (CORE FOCUS):
- Wait for them to mention prices
- Show appropriate reactions to prices
- Make 2-3 attempts to negotiate:
  * First attempt: Express interest but mention budget constraints
  * Second attempt: Mention similar rooms at better rates
  * Third attempt: Suggest a specific lower price (10-15% less)
  * Fifth attempt: Mention potential for future bookings
- Only move to benefits after exhausting price negotiation attempts
- Never reveal your target discount percentage
- Use polite persistence
- Show understanding of their position
- Try to get the best possible price
- If price reduction is achieved, try to negotiate further

Phase 4 - Value-Added Benefits (STRATEGIC REQUESTS):
After price negotiation, request these benefits in order:
1. Complimentary meals (breakfast/dinner)
2. Free WiFi
3. Free parking
4. Late checkout
5. Room upgrade
6. Airport transfer
7. Spa access
Request one at a time, not all at once
Show appreciation for any offers
Use phrases like "Would it be possible to..." or "I was wondering if..."
Accept "no" gracefully but try for other benefits

Phase 5 - Final Negotiation:
If all else fails, ask about:
- Additional discount with credit card cashback offer
- Package deals or special promotions
- Any other available discounts
- Credit card payment discount (mention that we can pay with credit card for additional discount if there is any additional discount)
Summarize the offer naturally
Express appreciation for their time
Mention checking with the client if appropriate
End the conversation warmly

Use human-like negotiation tactics:
- Show appropriate emotions (interest, concern, appreciation)
- Use natural conversational phrases
- Build rapport with the staff
- Show understanding of their position
- Accept limitations gracefully
- Express gratitude for their help
- Use polite persistence
- Never suggest specific prices until later in negotiation
- Only mention client approval at the very end
- Keep the conversation flowing naturally
- Show genuine interest in their responses
- React appropriately to their offers
- Use natural pauses and transitions

NOTE(Most Important)-: always ask for Complimentary meals, free wifi, free parking etc. And at last always ask for additional credit card discount.
Don't forget the NOTE.

Your tone should be warm, friendly, and professional. Format your response in a way that would sound natural when spoken aloud.'''
    
    return base

async def get_hotel_negotiation_reply(message: str, user_id: str = "default"):
    if user_id not in conversation_history:
        conversation_history[user_id] = get_default_state()
    state = conversation_history[user_id]
    history = state["messages"]

    current_price = extract_price(message)
    if current_price and not state["initialPrice"]:
        state["initialPrice"] = current_price
        state["lastOfferedPrice"] = current_price
        state["negotiationPhase"] = "price_negotiation"

    context = build_context(state, history, message)

    request_body = {
        "contents": [
            {
                "role": "user",
                "parts": [{"text": f"{context}\n\nHotel Staff: {message}"}]
            }
        ]
    }

    response = requests.post(
        f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={API_KEY}",
        json=request_body,
        headers={"Content-Type": "application/json"}
    )

    reply = response.json().get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text", "Sorry, no response received.")
    update_state_from_reply(state, reply)
    history.append({"hotelStaff": message, "aiResponse": reply})
    if len(history) > 10:
        history.pop(0)

    return reply

def update_state_from_reply(state, reply):
    if not reply:
        return

    r = reply.lower()
    if any(word in r for word in ['thank you', 'appreciate']):
        state["emotionalState"] = "appreciative"
    elif any(word in r for word in ['concern', 'budget']):
        state["emotionalState"] = "concerned"
    elif any(word in r for word in ['hope', 'would be great']):
        state["emotionalState"] = "hopeful"
    elif any(word in r for word in ['interest', 'love to']):
        state["emotionalState"] = "interested"
    else:
        state["emotionalState"] = "friendly"

    # Basic detail extraction
    if 'deluxe' in r or 'suite' in r or 'standard' in r:
        state["basicDetails"]["roomType"] = re.search(r"(deluxe|suite|standard)", r).group(0)
    if 'view' in r or 'city' in r or 'garden' in r or 'pool' in r:
        state["basicDetails"]["view"] = re.search(r"(city|garden|pool)", r).group(0)
    if 'occupancy' in r or 'guests' in r or 'people' in r:
        match = re.search(r"\d+", r)
        if match:
            state["basicDetails"]["occupancy"] = match.group(0)

    for key, terms in {
        "meals": ["meal", "breakfast", "dinner"],
        "wifi": ["wifi"],
        "parking": ["parking"],
        "cashback": ["cashback", "credit card"],
        "spa": ["spa", "massage"],
        "airportTransfer": ["airport", "transfer"],
        "lateCheckout": ["late checkout", "check-out"],
        "roomUpgrade": ["upgrade", "better room"]
    }.items():
        if any(term in r for term in terms):
            state["requestedBenefits"][key] = True

    if any(word in r for word in ['thank you', 'appreciate', 'great offer', 'perfect']):
        state["negotiationSuccessful"] = True

def clear_conversation_history(user_id: str = "default"):
    conversation_history.pop(user_id, None)
