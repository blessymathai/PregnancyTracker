"""
Pregnancy AI Assistant Service using Google Gemini models.
Provides intelligent, compassionate, and medically sound pregnancy and maternal health guidance.
"""
import os
import json
import urllib.request
import urllib.error
from django.conf import settings

GEMINI_MODELS = [
    "gemini-flash-latest",
    "gemini-3.8-flash",
    "gemini-2.0-flash",
    "gemini-1.5-flash",
]

SYSTEM_PROMPT = """You are Nova, a warm, compassionate AI assistant providing general pregnancy and maternal health information. You are not a clinician.
Your primary role is to guide and reassure expectant and new mothers on pregnancy, prenatal wellness, nutrition, baby development, and postpartum recovery.

GUIDELINES:
1. Warm, Empathetic, Reassuring Tone: Pregnancy can be an anxious journey; be encouraging, gentle, and clear.
2. Structured & Readable: Use bullet points, bold key terms, and short paragraphs for readability.
3. Medically Grounded: Align with standard ACOG (American College of Obstetricians and Gynecologists) and WHO maternal guidelines.
4. Context-Aware: Use any provided user context (current pregnancy week, month, baby information) to tailor your advice.
5. Medical Safety & Triage:
   - You provide educational and supportive advice, never a definitive medical diagnosis.
   - For severe red flag symptoms (heavy vaginal bleeding, sudden extreme facial swelling, severe persistent abdominal pain, visual aura/severe headache, absence of fetal movement after 24 weeks, high fever), urge immediate contact with their obstetrician or the emergency room.
6. Scope: Strictly focus on pregnancy, maternal health, prenatal nutrition, safe exercises, labor/delivery, newborn care, and postpartum wellness."""


def get_gemini_api_key(request=None):
    """
    Retrieves Gemini API key from session, environment, or settings.
    """
    if request and request.session.get("gemini_api_key"):
        return request.session.get("gemini_api_key").strip()
    if os.environ.get("GEMINI_API_KEY"):
        return os.environ.get("GEMINI_API_KEY").strip()
    if os.environ.get("GOOGLE_API_KEY"):
        return os.environ.get("GOOGLE_API_KEY").strip()
    if hasattr(settings, "GEMINI_API_KEY") and settings.GEMINI_API_KEY:
        return str(settings.GEMINI_API_KEY).strip()
    return ""


def call_gemini_api(chat_history, user_context=None, api_key=""):
    """
    Calls Google Gemini REST API using urllib.
    chat_history: list of dicts with role ('user' or 'model') and text
    """
    if not api_key:
        return None, "No API key provided."

    # Build context-enriched system prompt
    context_str = ""
    if user_context:
        context_parts = []
        if user_context.get("user_name"):
            context_parts.append(f"User Name: {user_context['user_name']}")
        if user_context.get("pregnancy_week"):
            context_parts.append(f"Current Pregnancy Week: Week {user_context['pregnancy_week']}")
        if user_context.get("due_date"):
            context_parts.append(f"Estimated Due Date: {user_context['due_date']}")
        if user_context.get("baby_name"):
            context_parts.append(f"Baby Name: {user_context['baby_name']}")
        if context_parts:
            context_str = "\n\nCURRENT USER PREGNANCY CONTEXT:\n" + "\n".join(context_parts)

    full_system_instruction = SYSTEM_PROMPT + context_str

    # Format contents for Gemini REST API
    contents = []
    for msg in chat_history[-10:]:  # Keep last 10 messages for context
        role = "user" if msg.get("role") in ["user", "USER"] else "model"
        text = msg.get("text", msg.get("message", "")).strip()
        if text:
            contents.append({
                "role": role,
                "parts": [{"text": text}]
            })

    if not contents:
        return None, "Empty conversation."

    last_error = ""
    for model_name in GEMINI_MODELS:
        endpoint = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={api_key}"
        payload = {
            "systemInstruction": {
                "parts": [{"text": full_system_instruction}]
            },
            "contents": contents,
            "generationConfig": {
                "temperature": 0.7,
                "maxOutputTokens": 1000,
                "topP": 0.9
            }
        }

        try:
            req = urllib.request.Request(
                endpoint,
                data=json.dumps(payload).encode("utf-8"),
                headers={"Content-Type": "application/json"},
                method="POST"
            )
            with urllib.request.urlopen(req, timeout=15) as response:
                if response.status == 200:
                    data = json.loads(response.read().decode("utf-8"))
                    candidates = data.get("candidates", [])
                    if candidates:
                        parts = candidates[0].get("content", {}).get("parts", [])
                        if parts:
                            reply_text = parts[0].get("text", "").strip()
                            if reply_text:
                                return {
                                    "reply": reply_text,
                                    "model": model_name,
                                    "source": "gemini"
                                }, None
        except urllib.error.HTTPError as he:
            err_body = he.read().decode("utf-8", errors="ignore")
            last_error = f"HTTP {he.code}: {he.reason} - {err_body[:100]}"
            # If systemInstruction isn't supported on a legacy model, try inlining
            continue
        except Exception as ex:
            last_error = str(ex)
            continue

    return None, last_error


# ==============================================================================
# SMART OFFLINE PREGNANCY KNOWLEDGE BASE (FALLBACK ENGINE)
# Guarantees immediate, high quality, medical answers even when offline or without API key.
# ==============================================================================

OFFLINE_PREGNANCY_KNOWLEDGE = [
    {
        "keywords": ["nausea", "morning sickness", "vomit", "sick", "queasy"],
        "title": "Natural Morning Sickness & Nausea Relief",
        "response": """**Soothing Remedies for Pregnancy Nausea & Morning Sickness:**

- **Eat Small, Frequent Meals:** Keep your stomach from getting completely empty. An empty stomach produces excess gastric acid which triggers nausea.
- **Morning Crackers:** Keep whole-wheat crackers or dry toast by your bedside. Nibble 2-3 crackers before sitting up in the morning.
- **Natural Ginger:** Real ginger root tea, ginger candies, or ginger ale can calm stomach hyper-motility.
- **Vitamin B6:** Vitamin B6 (pyridoxine) is clinically recommended by ACOG to soothe pregnancy nausea. Bananas, chickpeas, oats, and avocados are high natural sources.
- **Stay Hydrated:** Sip cold water, electrolyte drinks, or lemon-infused water between meals rather than gulping large amounts during eating.
- **Aromatherapy:** Fresh lemon slices or peppermint scent can instantly interrupt nausea waves.

⚠️ *If you are unable to keep any fluids down for 24+ hours or feel dizzy/dehydrated, contact your doctor for hyperemesis gravidarum evaluation.*"""
    },
    {
        "keywords": ["food to avoid", "avoid", "eat", "safe food", "cheese", "fish", "sushi", "caffeine", "diet"],
        "title": "Pregnancy Nutrition & Foods to Avoid",
        "response": """**Safe Foods & Foods to Avoid During Pregnancy:**

**🚫 Foods to Strictly Avoid or Limit:**
- **Raw or Undercooked Meat & Eggs:** Risk of Salmonella and Toxoplasmosis. Ensure meat is well-done.
- **High-Mercury Fish:** Avoid shark, swordfish, king mackerel, and tilefish. (Safe fish: salmon, cod, canned light tuna, shrimp - up to 8-12 oz/week).
- **Unpasteurized Dairy & Soft Cheeses:** Avoid raw milk and cheeses made from unpasteurized milk (like unpasteurized Brie, Feta, Camembert) to prevent Listeria.
- **Alcohol:** Zero safe amount. Avoid entirely.
- **High Caffeine:** Limit caffeine to under 200 mg per day (approx. 1 standard 12 oz cup of coffee).
- **Unwashed Produce:** Wash all raw fruits and vegetables thoroughly.

**✅ Essential Superfoods to Enjoy:**
- **Folate Powerhouses:** Steamed spinach, lentils, black beans, fortified cereals.
- **Omega-3 DHA:** Wild salmon, chia seeds, walnuts for baby's brain wiring.
- **Bioavailable Calcium:** Greek yogurt, pasteurized cheddar, fortified plant milk for baby's skeleton.
- **Lean Protein & Iron:** Eggs, chicken breast, tofu, pumpkin seeds."""
    },
    {
        "keywords": ["kick", "movement", "flutter", "move", "baby move", "count kick"],
        "title": "Baby Kicks & Fetal Movement Timeline",
        "response": """**Baby Movements & Kick Counting Guide:**

- **First Flutters (Quickening):** First-time mothers typically feel initial butterfly-like flutters between **Weeks 18 and 22**. (Second-time moms may feel them as early as Week 16).
- **Weeks 24-28:** Movements become more distinct kicks, punches, and gentle rolls.
- **Weeks 28+ (Kick Counts):** Doctors recommend tracking movements daily starting around Week 28:
  - Choose a quiet time when baby is usually active (often in the evening after dinner).
  - Sit comfortably or lie on your left side.
  - Count kicks, swishes, and rolls. You should feel **at least 10 distinct movements within 2 hours** (often reached within 20-30 minutes).

⚠️ *If you notice a sudden, noticeable reduction or cessation of baby's movement after Week 24, do not wait until morning — drink cold water, lie on your left side, and contact your maternity hospital or doctor immediately.*"""
    },
    {
        "keywords": ["medicine", "tablet", "pain", "headache", "paracetamol", "tylenol", "ibuprofen", "cold", "fever"],
        "title": "Safe Medications During Pregnancy",
        "response": """**Pregnancy Medication Safety Guidelines:**

- **Pain & Mild Headache:** **Acetaminophen (Paracetamol / Tylenol)** is generally considered the safest first-line over-the-counter pain reliever when taken at recommended dosages.
- **🚫 Avoid NSAIDs (Ibuprofen / Advil / Aleve / Aspirin):** Non-steroidal anti-inflammatory drugs are generally contraindicated, especially in the 3rd trimester, because they can affect fetal kidney function and amniotic fluid levels.
- **Acid Reflux & Heartburn:** Calcium carbonate antacids (like Tums) are generally safe. Eating smaller meals and avoiding lying down after eating also helps.
- **Colds & Allergies:** Saline nasal sprays and humidifiers are 100% drug-free and safe. Always check with your doctor before taking antihistamines or decongestants.

*Always consult your obstetrician or pharmacist before starting any new prescription, over-the-counter medication, or herbal supplement during pregnancy.*"""
    },
    {
        "keywords": ["labor", "contraction", "water break", "sign", "delivery", "hospital", "due date"],
        "title": "Signs of True Labor vs Braxton Hicks",
        "response": """**Signs of Real Labor vs. Braxton Hicks Practice Contractions:**

**False Labor (Braxton Hicks):**
- Irregular, unpredictable intervals (e.g. 10 mins apart, then 20 mins, then stops).
- Often painless or feel like gentle menstrual tightening in front.
- Change in activity (walking, resting, drinking a large glass of warm water) makes them fade away.

**True Labor Contractions:**
- Regular, progressive pattern: they get **longer, stronger, and closer together**.
- The **5-1-1 Rule:** Contractions coming every **5 minutes**, lasting **1 full minute**, for at least **1 hour** indicates active labor.
- Pain starts in the lower back and radiates into the front abdomen; walking makes them stronger.

**Other Signs It's Time for the Hospital:**
- **Water Breaking (Rupture of Membranes):** A gush or continuous trickle of clear fluid.
- **Bloody Show:** Loss of mucus plug tinged with pink or brown blood.
- **Regular Painful Contractions:** That take your breath away."""
    },
    {
        "keywords": ["bleeding", "cramp", "danger", "warning", "emergency", "swelling", "fever", "spotting"],
        "title": "Pregnancy Danger Signs & When to Seek Urgent Care",
        "response": """**🚨 Pregnancy Red Flag Warning Signs:**

Contact your doctor, midwife, or emergency maternity department immediately if you experience:
1. **Vaginal Bleeding:** Any bright red bleeding, especially if accompanied by cramping.
2. **Severe Abdominal Pain:** Sharp, continuous abdominal pain that doesn't subside.
3. **Severe Persistent Headache or Visual Aura:** Flashing lights, blurred vision, or blind spots paired with sudden facial/hand swelling (warning signs of Preeclampsia).
4. **Significant Reduction in Baby Movement:** Baby moving significantly less than usual after Week 24.
5. **High Fever (above 100.4°F / 38°C):** Requires medical evaluation to rule out infection.
6. **Fluid Leakage:** Fluid leaking from the vagina before 37 weeks.
7. **Severe Dizziness or Fainting:** Sudden shortness of breath or chest pain.

*Never hesitate to call your healthcare provider or labor assessment unit. Maternity units are staffed 24/7 specifically to evaluate you and your baby.*"""
    },
    {
        "keywords": ["exercise", "workout", "walk", "yoga", "gym", "squat"],
        "title": "Safe Exercise During Pregnancy",
        "response": """**Safe & Recommended Pregnancy Exercises:**

- **Brisk Walking:** The safest, most effective daily aerobic exercise throughout all three trimesters. Aim for 20-30 minutes daily.
- **Prenatal Yoga & Pilates:** Strengthens your core, opens tight pelvic floor muscles, and relieves lower back aches.
- **Swimming & Water Aerobics:** Water supports your extra pregnancy weight, taking all pressure off your joints and spine.
- **Pelvic Tilts & Kegels:** Tones the pelvic floor muscles supporting bladder, uterus, and bowels to prepare for delivery.

**⚠️ Exercises to Avoid:**
- Contact sports, hot yoga, activities with fall risks (skiing, horseback riding, road cycling).
- Lying flat on your back after the first trimester (which compresses the inferior vena cava vein)."""
    }
]


def get_offline_pregnancy_response(user_message, user_context=None):
    """
    Returns a structured, compassionate pregnancy answer based on medical knowledge base.
    """
    text_lower = user_message.lower()

    # Search for matching knowledge item
    best_match = None
    max_score = 0
    for item in OFFLINE_PREGNANCY_KNOWLEDGE:
        score = sum(1 for kw in item["keywords"] if kw in text_lower)
        if score > max_score:
            max_score = score
            best_match = item

    if best_match and max_score > 0:
        return best_match["response"]

    # Personalized conversational fallback
    user_name = (user_context.get("user_name") if user_context else "") or "Mama"
    week_info = f"at Week {user_context.get('pregnancy_week')}" if (user_context and user_context.get("pregnancy_week")) else "on your pregnancy journey"

    return f"""Hello {user_name}! I am **Nova**, your AI Pregnancy & Maternal Health Assistant.

I am here to support you {week_info} with evidence-based guidance on:
- 🥗 **Pregnancy Nutrition:** What superfoods to eat and foods to safely avoid.
- 🤰 **Weekly Body Changes:** Symptoms, morning sickness, and baby development milestones.
- 🦶 **Baby Movements:** Tracking kicks, ultrasound milestones, and fetal growth.
- 🧘 **Comfort & Wellness:** Safe exercises, sleeping positions, and easing back pain.
- 🏥 **Labor & Birth Readiness:** Signs of contractions, hospital bag checklists, and delivery preparation.

*Could you tell me a little more about what you're experiencing or specific questions you have about your pregnancy today?*"""
